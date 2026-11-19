"""Desktop app for find_flights.py: native Qt window, Chromium-rendered UI (ui.html). Run: python flights_app.py"""
import json
import os
import re
import signal
import sys
import threading
from datetime import date, datetime, timedelta
import pandas as pd
from PySide6.QtCore import QLockFile, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMessageBox
import find_flights as ff

HERE = os.path.dirname(os.path.abspath(__file__))
RES = getattr(sys, "_MEIPASS", HERE)  # ui.html, airports.js, fonts: inside the bundle when built with PyInstaller


def data_dir():
    """Where results, settings and the cache live. From source: next to the script, as always.
    Built app: the user's data folder, since the install folder may be read-only."""
    if not getattr(sys, "frozen", False):
        return HERE
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "Flight Finder")


DATA = data_dir()
os.makedirs(DATA, exist_ok=True)
os.chdir(DATA)  # CSVs live here, even when launched from the app menu
ff.CACHE_FILE = os.path.join(DATA, "query_cache.json")
SETTINGS = os.path.join(DATA, "settings.json")
FAVOURITES = os.path.join(DATA, "favourites.json")
CODE = re.compile(r"^[A-Z]{3}$")
LEG = re.compile(r"^(.*) \((\d\d:\d\d) -> (\d\d:\d\d)\)$")


def parse_leg(day, text, eur, no=""):
    m = LEG.match(text or "")
    if not m:
        return None
    airline, dep, arr = m.groups()
    dep_dt = datetime.fromisoformat(f"{day} {dep}")
    arr_dt = datetime.fromisoformat(f"{day} {arr}")
    if arr_dt < dep_dt:  # Landed after midnight
        arr_dt += timedelta(days=1)
    return {"date": day, "airline": airline, "dep": dep, "arr": arr, "eur": eur, "no": no,
            "dep_dt": dep_dt.isoformat(), "arr_dt": arr_dt.isoformat()}


def load_trips(path):
    """CSV rows -> [{route: [codes], legs: [...], total, checked}] for the UI."""
    if not os.path.exists(path):
        return []
    df = pd.read_csv(path, dtype=str).fillna("")
    trips = []
    for r in df.to_dict("records"):
        if "Flight" in r:  # direct_*.csv layout
            legs = [parse_leg(r["Date"], r["Flight"], r["Total_EUR"], r.get("Flight_No", ""))]
        else:
            legs = [parse_leg(r["Leg1_Date"], r["Leg1"], r["Leg1_EUR"], r.get("Leg1_No", ""))]  # *_No: absent in pre-flight-number CSVs
            if r["Leg2"]:
                legs.append(parse_leg(r["Leg2_Date"], r["Leg2"], r["Leg2_EUR"], r.get("Leg2_No", "")))
        if None in legs:
            continue
        trips.append({"route": [c.strip() for c in r["Route"].split("→")], "legs": legs,
                      "total": float(r["Total_EUR"]), "checked": r.get("Checked", ""),
                      "ticket": r.get("Ticket", ""),  # "one" = airline-sold connection, else separate tickets
                      "fare": r.get("Fare") or ff.DEFAULT_FARE})  # who the price is for: a<adults>c<cabin bag>
    return trips


def date_list(start, end, what="Outbound"):
    try:
        s, e = date.fromisoformat(start), date.fromisoformat(end)
    except (TypeError, ValueError):
        raise ValueError(f"{what}: pick both a first and a last day.")
    if e < s:
        raise ValueError(f"{what}: the last day ({end}) is before the first day ({start}).")
    if s < date.today():
        raise ValueError(f"{what}: the first day ({start}) is in the past.")
    if (e - s).days > 30:
        raise ValueError(f"{what}: pick at most 31 days; longer ranges take many hours.")
    return [(s + timedelta(days=i)).isoformat() for i in range((e - s).days + 1)]


def validate(p):
    """Settings from the UI -> run_scan jobs. Raises ValueError with a message the UI shows."""
    for key in ("home", "away", "hubs"):
        bad = [c for c in p[key] if not CODE.match(c)]
        if bad:
            raise ValueError(f"Not an airport code: {', '.join(bad)}. Use 3-letter IATA codes like CPH.")
    if not p["home"] or not p["away"]:
        raise ValueError("Add at least one home and one destination airport.")
    if not p["hubs"] and not p["direct"]:
        raise ValueError("Add at least one hub, or switch on direct flights only.")
    if not 1 <= float(p["conn"]) <= 24:
        raise ValueError("Min. connection must be between 1 and 24 hours: separate tickets need time to collect bags and check in again.")
    if float(p["max1"]) < 0 or float(p["max2"]) < 0 or float(p["bagfee"]) < 0:
        raise ValueError("Prices can't be negative.")
    if not 1 <= int(p["adults"]) <= 9:
        raise ValueError("Adults must be between 1 and 9.")
    if not 0 <= int(p["checked"]) <= 2:
        raise ValueError("Checked bags must be 0, 1 or 2 per person.")
    jobs = []
    if p["outbound"]:
        jobs.append(("outbound", p["home"], p["away"], date_list(p["out_from"], p["out_to"], "Outbound")))
    if p["return"]:
        jobs.append(("return", p["away"], p["home"], date_list(p["ret_from"], p["ret_to"], "Return")))
    if not jobs:
        raise ValueError("Pick outbound, return, or both.")
    if p["outbound"] and p["return"] and p["ret_to"] < p["out_from"]:
        raise ValueError("The return days are all before the outbound days.")
    return jobs


class Backend(QObject):
    log = Signal(str)
    progress = Signal(str)  # JSON {stage, step, steps, done, total}
    finished = Signal(str)  # "" on success, else a message for the user

    def __init__(self):
        super().__init__()
        self.busy = False

    @Slot(result=str)
    def settings(self):
        saved = {}
        try:
            with open(SETTINGS) as f:
                saved = json.load(f)
        except (OSError, ValueError):
            pass  # Missing or corrupt: start from the defaults
        return json.dumps({
            "home": ff.dk_airports, "away": ff.pt_airports, "hubs": ff.hub_airports,
            "out_from": ff.outbound_dates[0], "out_to": ff.outbound_dates[-1],
            "ret_from": ff.return_dates[0], "ret_to": ff.return_dates[-1],
            "max1": 130, "max2": 160, "conn": 3, "workers": ff.MAX_WORKERS,
            "adults": 1, "cabin": False, "checked": 0, "bagfee": 40,
            "outbound": True, "return": True, "direct": False, **saved})

    @Slot(bool, result=str)
    def results(self, direct):
        prefix = "direct" if direct else "cheapest"
        return json.dumps({d: load_trips(f"{prefix}_{d}.csv") for d in ("outbound", "return")})

    @Slot(result=str)
    def favourites(self):
        """{trip key: trip snapshot} so starred trips survive even after they drop out of the CSVs."""
        if not os.path.exists(FAVOURITES):
            return "{}"
        with open(FAVOURITES) as f:
            return f.read()

    @Slot(str)
    def save_favourites(self, text):
        if not isinstance(json.loads(text), dict):  # Never overwrite the file with something unreadable
            return
        tmp = FAVOURITES + ".tmp"
        with open(tmp, "w") as f:
            f.write(text)
        os.replace(tmp, FAVOURITES)

    @Slot(str)
    def open_url(self, url):
        """Booking links open in the system browser; only web links are allowed through."""
        if url.startswith(("https://", "http://")):
            QDesktopServices.openUrl(QUrl(url))

    @Slot()
    def cancel(self):
        ff.CANCEL.set()

    @Slot(str, result=str)
    def search(self, params):
        """Starts a scan in the background. Returns an error message, or "" when it started."""
        if self.busy:
            return "A search is already running."
        p = json.loads(params)
        try:
            jobs = validate(p)
            max1, max2 = int(p["max1"]), int(p["max2"])
            ff.MIN_CONNECTION = timedelta(hours=float(p["conn"]))
            ff.MAX_WORKERS = max(1, min(6, int(p["workers"])))  # More makes Google throttle harder, not faster
            ff.FARE = {"adults": int(p["adults"]), "cabin": 1 if p["cabin"] else 0}
        except (ValueError, KeyError, TypeError) as e:
            return str(e)
        tmp = SETTINGS + ".tmp"
        with open(tmp, "w") as f:
            json.dump(p, f, indent=2)
        os.replace(tmp, SETTINGS)  # Atomic: a crash mid-write never leaves a broken settings file
        self.busy = True
        ff.CANCEL.clear()
        ff.FAILED.clear()
        steps, seen = len(jobs) * (1 if p["direct"] else 3), []

        def progress(stage, done, total):
            base = stage.split(" (")[0]
            if base not in seen:
                seen.append(base)
            self.progress.emit(json.dumps({"stage": stage, "step": len(seen), "steps": steps, "done": done, "total": total}))
        ff.PROGRESS = progress

        def work():
            msg = ""
            try:
                for label, o, d, dates in jobs:
                    ff.run_scan(label, o, d, p["hubs"], dates, p["direct"], max1, max2)
                if ff.FAILED:
                    msg = (f"Results are incomplete: {len(ff.FAILED)} lookups failed because Google kept refusing them. "
                           "Search again later to fill the gaps; everything already found is reused, so it's quick.")
            except ff.Cancelled:
                msg = "Search cancelled. Lookups already done are saved, so searching again continues where it stopped."
            except Exception as e:
                msg = "Search stopped: " + str(e)
            ff.PROGRESS = None
            self.busy = False
            self.finished.emit(msg)

        threading.Thread(target=work, daemon=True).start()
        return ""


class LogStream:
    """print() from the scan threads -> Backend.log signal (Qt queues it to the UI thread)."""
    def __init__(self, backend):
        self.backend = backend
    def write(self, s):
        if s:
            self.backend.log.emit(s)
    def flush(self):
        pass


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # Ctrl+C quits at once; Qt's event loop never lets Python see it otherwise
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--lang=en-GB")  # Day/month/year in date pickers
    app = QApplication(sys.argv)
    app.setApplicationName("Flight Finder")
    app.setDesktopFileName("flight-finder")
    app.setWindowIcon(QIcon(os.path.join(RES, "icons", "icon.png")))
    lock = QLockFile(os.path.join(DATA, ".flight-finder.lock"))  # One window: two would overwrite each other's files
    if not lock.tryLock(100):
        QMessageBox.information(None, "Flight Finder", "Flight Finder is already open.")
        return
    backend = Backend()
    sys.stdout = LogStream(backend)
    if sys.stderr is None:  # Windowed app on Windows has no stderr: send warnings to the search log
        sys.stderr = sys.stdout
    view = QWebEngineView()
    channel = QWebChannel()
    channel.registerObject("backend", backend)
    view.page().setWebChannel(channel)
    view.load(QUrl.fromLocalFile(os.path.join(RES, "ui.html")))
    view.setWindowTitle("Flight Finder")
    view.resize(1440, 900)
    view.show()
    smoke = os.environ.get("FLIGHT_FINDER_SMOKE")
    if smoke:  # Build check (build.py): page, Python bridge and airport data all load; writes "<chips>:<airports>" and quits
        def report(result):
            with open(smoke, "w") as f:
                f.write(str(result))
            app.exit(0)
        js = "document.querySelectorAll('.chip').length + ':' + AIRPORTS.length"
        view.loadFinished.connect(lambda ok: QTimer.singleShot(3000, lambda: view.page().runJavaScript(js, 0, report)))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
