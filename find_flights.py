import itertools
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import pandas as pd
import json
import os
import threading
import time
from fast_flights import FlightQuery, Passengers, create_query
from fast_flights.parser import parse_js
from primp import Client
from selectolax.lexbor import LexborHTMLParser

# 1. Focused list of actual budget hubs that connect Denmark & Portugal
dk_airports = ["AAR", "BLL", "AAL", "CPH"]
pt_airports = ["OPO", "LIS", "FAO"]
hub_airports = [  # CRL, EIN, LTN, MXP, PMI dropped 2026-11-18: never part of a found trip in either direction
    "STN", "LGW", "MAN", "EDI", "BRS", "DUB",  # UK & Ireland
    "BGY", "FCO",                              # Italy
    "BVA",                                     # France
    "BCN", "MAD", "AGP", "ALC",                # Spain
    "GDN", "WMI", "KRK", "BUD", "VIE"          # Central Europe
]

outbound_dates = ["2026-12-17", "2026-12-18", "2026-12-19", "2026-12-20", "2026-12-21", "2026-12-22"]
return_dates = ["2026-12-28","2026-12-29","2026-12-30","2026-12-31", "2027-01-01", "2027-01-02", "2027-01-03", "2027-01-04", "2027-01-05"]
MIN_CONNECTION = timedelta(hours=3)  # Self-transfer: time to collect bags, re-check-in, clear security
MAX_WORKERS = 4  # Parallel requests; Google answers 429 (rate limited) when this is much higher

# Answers from recent runs are reused instead of asking Google again (see fetch_many).
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "query_cache.json")
CACHE_HOURS = 12  # Older answers are fetched again; prices move, so keep this short

# SOCS cookie skips Google's EU "Before you continue" consent page
CONSENT_COOKIES = {"SOCS": "CAESEwgDEgk0ODE3Nzk3MjQaAmVuIAEaBgiA_LyaBg"}

# Hooks for the app: progress reports, a Cancel button, and lookups that failed for good.
CANCEL = threading.Event()
PROGRESS = None  # fn(stage, done, total) or None
STAGE = ""       # what fetch_many is working on, e.g. "Outbound: first flights"
FAILED = []      # (orig, dest, date) lookups that still failed after every retry

# Who travels: Google prices the whole group, cabin bags included (one per adult when cabin=1).
# Checked bags are not here: Google ignores that option, so the UI adds the user's own fee estimate.
FARE = {"adults": 1, "cabin": 0}
DEFAULT_FARE = "a1c0"  # Rows and cache entries from before fares existed

def fare_tag():
    return f"a{FARE['adults']}c{FARE['cabin']}"

class Cancelled(Exception):
    pass

def pause(seconds):
    """time.sleep that a Cancel interrupts."""
    if CANCEL.wait(seconds):
        raise Cancelled()

def get_flights(query):
    """fast_flights.get_flights, plus consent cookie, 'best flights' list, and priceless results dropped."""
    client = Client(impersonate="chrome_145", impersonate_os="macos", referer=True, cookie_store=True)
    for attempt in range(5):  # Back off when Google rate-limits (HTTP 429)
        if CANCEL.is_set():
            raise Cancelled()
        res = client.get("https://www.google.com/travel/flights", params=query.params(), cookies=CONSENT_COOKIES)
        script = LexborHTMLParser(res.text).css_first(r"script.ds\:1")
        if script:
            break
        pause(5 * 2 ** attempt)
    else:
        raise RuntimeError(f"HTTP {res.status_code}, no flight data after retries")
    js = script.text()
    data = js.split("data:", 1)[1].rsplit(",", 1)[0]
    if data.endswith("errorHasStatus: true"):
        return []  # Google's "no flights found" response (same check as fast_flights' parse_js)
    payload = json.loads(data)
    results = [k for section in (payload[2], payload[3]) if section and section[0] for k in section[0]]
    payload[3] = [[k for k in results if k[1] and k[1][0]]]
    if not payload[3][0]:
        return []  # No flights: Google also omits the airline metadata parse_js expects
    flights = parse_js("data:" + json.dumps(payload) + ",")
    for f, raw in zip(flights, payload[3][0]):  # parse_js drops these; segment[22] = ["SK", "2802", None, "Scandinavian Airlines"]
        f.seg_info = [(seg[22][0] + seg[22][1], seg[22][3] or "") if len(seg) > 22 and seg[22] and seg[22][1] else ("", "")
                      for seg in raw[0][2]]  # (flight number, airline) per plane, same order as f.flights
    return flights

def fetch_one_way(orig, dest, date_str, max_stops=0):
    """Every priced one-way option for one query, cheapest first ([] = no flight); raises on errors.
    max_stops=1 adds connections the airline sells as one ticket (e.g. SAS LIS-CPH-AAR)."""
    res = get_flights(create_query(
        flights=[FlightQuery(date=date_str, from_airport=orig, to_airport=dest)],
        trip="one-way",
        seat="economy",
        passengers=Passengers(adults=FARE["adults"]),
        currency="EUR",
        max_stops=max_stops,
        carry_on_bags=FARE["adults"] * FARE["cabin"],
    ))
    out = []
    for f in sorted(res, key=lambda f: f.price):
        segs = [{"from": sf.from_airport.code, "to": sf.to_airport.code, "airline": name or ", ".join(f.airlines),
                 "flight_no": no,  # e.g. "FR2619"; lets the UI open this exact flight
                 "dep_dt": datetime(*sf.departure.date, *sf.departure.time),
                 "arr_dt": datetime(*sf.arrival.date, *sf.arrival.time)}
                for sf, (no, name) in zip(f.flights, getattr(f, "seg_info", [("", "")] * len(f.flights)))]
        out.append({
            "orig": orig, "dest": dest, "date": date_str, "price": f.price,
            "airline": ", ".join(f.airlines), "flight_no": " ".join(sg["flight_no"] for sg in segs),
            "dep_time": segs[0]["dep_dt"].strftime("%H:%M"), "arr_time": segs[-1]["arr_dt"].strftime("%H:%M"),
            "dep_dt": segs[0]["dep_dt"], "arr_dt": segs[-1]["arr_dt"], "segments": segs})
    return out

def load_cache():
    """{"ORIG|DEST|DATE[|STOPS]": {"at": iso time, "res": fetch_one_way result}}, minus expired entries."""
    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
    except (OSError, ValueError):
        return {}  # Missing or corrupt cache: just fetch everything
    cutoff = datetime.now() - timedelta(hours=CACHE_HOURS)
    return {k: v for k, v in cache.items() if datetime.fromisoformat(v["at"]) > cutoff}

def save_cache(cache):
    tmp = CACHE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cache, f, default=lambda d: d.isoformat())
    os.replace(tmp, CACHE_FILE)  # Atomic: a crash mid-write never leaves a half-written cache

def revive(o):
    """JSON from the cache -> the datetimes fetch_one_way returned (every *_dt key)."""
    if isinstance(o, list):
        return [revive(x) for x in o]
    if isinstance(o, dict):
        return {k: datetime.fromisoformat(v) if k.endswith("_dt") else revive(v) for k, v in o.items()}
    return o

def from_cache(entry):
    res = entry["res"]
    return revive(res if isinstance(res, list) else [res] if res else [])  # Older caches held one dict or None

def fetch_many(tasks, retry_rounds=3, cheapest_only=True):
    """fetch_one_way for each (orig, dest, date[, max_stops]); the cheapest option per query, or all of them. Answers younger than CACHE_HOURS come from the cache.
    Failed queries (timeouts, 429s) are retried one at a time after a pause, so they get a second
    chance instead of silently going missing; failures are never cached."""
    cache = load_cache()
    tasks = list(tasks)
    tag = "" if fare_tag() == DEFAULT_FARE else "|" + fare_tag()  # old cache keys stay valid for 1 adult, no bags
    key = lambda t: "|".join(map(str, t)) + tag
    pick = (lambda res: res[:1]) if cheapest_only else (lambda res: res)
    hits = [t for t in tasks if key(t) in cache]
    found = [r for t in hits for r in pick(from_cache(cache[key(t)]))]
    if hits:
        print(f"  {len(hits)}/{len(tasks)} queries answered from the last {CACHE_HOURS}h cache")
    todo = [t for t in tasks if key(t) not in cache]
    done = len(hits)
    report = lambda stage: PROGRESS and PROGRESS(stage, done, len(tasks))
    report(STAGE)
    def attempt(t):
        if CANCEL.is_set():
            return t, None, Cancelled()
        try:
            return t, fetch_one_way(*t), None
        except Exception as e:
            return t, None, e
    for rnd in range(retry_rounds + 1):
        if not todo:
            break
        if rnd:
            print(f"  Retrying {len(todo)} failed queries (round {rnd}/{retry_rounds})...")
            report(f"{STAGE} (retrying {len(todo)} failed)")
            pause(30 * rnd)  # Give Google's rate limit time to cool down
        failed = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS if rnd == 0 else 1) as executor:
            for t, res, err in executor.map(attempt, todo):
                if err:
                    failed.append(t)
                else:
                    cache[key(t)] = {"at": datetime.now().isoformat(), "res": res}  # [] = no flight, also worth remembering
                    found.extend(pick(res))
                if rnd == 0 or not err:
                    done += 1
                    report(STAGE if rnd == 0 else f"{STAGE} (retrying)")
        save_cache(cache)  # After every round, so an interrupted scan keeps what it already paid for
        if CANCEL.is_set():
            raise Cancelled()
        todo = failed
    for t in todo:
        print(f"  ! {t[0]}->{t[1]} {t[2]} still failing after {retry_rounds} retries")
    FAILED.extend(t[:3] for t in todo)
    return found

def lands_in_time(flight, dates):
    return flight["arr_dt"].strftime("%Y-%m-%d") <= max(dates)

def scan_fast_self_transfers(origins, destinations, hubs, dates, label="Outbound", max_leg1=130, max_leg2=160):
    global STAGE
    STAGE = f"{label}: first flights to hubs"
    print(f"\n [{label}] Step 1: Scanning Leg 1 ({len(origins)*len(hubs)*len(dates)} queries in parallel)...")
    
    # --- STEP 1: Fetch all Leg 1 (Origin -> Hub) in parallel ---
    leg1_tasks = list(itertools.product(origins, hubs, dates))
    leg1_results = [r for r in fetch_many(leg1_tasks, cheapest_only=False) if r["price"] <= max_leg1 * FARE["adults"]]  # limits are per person  # Prune expensive first legs

    if not leg1_results:
        print(f"No cheap Leg 1 flights found for {label}.")
        return pd.DataFrame()

    print(f" Found {len(leg1_results)} cheap Leg 1 flights! Pruning Leg 2 queries...")

    # --- STEP 2: Only query (Hub, Date) pairs that actually succeeded in Step 1 ---
    needed_leg2 = set()
    for r in leg1_results:
        hub = r["dest"]
        d1 = r["date"]
        d2_next = (datetime.strptime(d1, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        for dest in destinations:
            needed_leg2.add((hub, dest, d1))       # Same-day transfer
            if d2_next <= max(dates):  # Never search a final leg after the last trip day
                needed_leg2.add((hub, dest, d2_next))  # Next-day transfer

    STAGE = f"{label}: second flights from hubs"
    print(f" [{label}] Step 2: Scanning {len(needed_leg2)} targeted Leg 2 queries in parallel...")
    # Final leg must land by the last trip day (an evening flight can land after midnight)
    leg2_results = [r for r in fetch_many(needed_leg2, cheapest_only=False) if r["price"] <= max_leg2 * FARE["adults"] and lands_in_time(r, dates)]

    # --- STEP 3: Stitch Leg 1 and Leg 2 in memory ---
    combos = []
    for l1 in leg1_results:
        d1_dt = datetime.strptime(l1["date"], "%Y-%m-%d")
        valid_d2 = {l1["date"], (d1_dt + timedelta(days=1)).strftime("%Y-%m-%d")}
        
        for l2 in leg2_results:
            if (l2["orig"] == l1["dest"] and l2["date"] in valid_d2
                    and l2["dep_dt"] >= l1["arr_dt"] + MIN_CONNECTION):
                combos.append({
                    "Route": f"{l1['orig']} → {l1['dest']} → {l2['dest']}",
                    "Leg1_Date": l1["date"],
                    "Leg1": f"{l1['airline']} ({l1['dep_time']} -> {l1['arr_time']})",
                    "Leg1_EUR": l1["price"],
                    "Leg1_No": l1["flight_no"],
                    "Leg2_Date": l2["date"],
                    "Leg2": f"{l2['airline']} ({l2['dep_time']} -> {l2['arr_time']})",
                    "Leg2_EUR": l2["price"],
                    "Leg2_No": l2["flight_no"],
                    "Total_EUR": l1["price"] + l2["price"]
                })

    return pd.DataFrame(combos).sort_values(by="Total_EUR") if combos else pd.DataFrame()

def scan_direct(origins, destinations, dates, max_stops=1, label="Direct"):
    """Every origin->destination option Google sells as one ticket: nonstop, plus (max_stops=1) airline
    connections like SAS LIS-CPH-AAR. One row per option; a connection's planes go in Leg1/Leg2 with Ticket="one"."""
    global STAGE
    STAGE = f"{label}: direct flights" if not max_stops else f"{label}: direct and one-ticket flights"
    tasks = [(*t, max_stops) if max_stops else t for t in itertools.product(origins, destinations, dates)]
    found = [r for r in fetch_many(tasks, cheapest_only=False) if lands_in_time(r, dates) and len(r["segments"]) <= 2]
    print(f" {len(found)} options from {len(tasks)} queries")
    leg = lambda sg: f"{sg['airline']} ({sg['dep_dt']:%H:%M} -> {sg['arr_dt']:%H:%M})"
    rows = []
    for r in found:
        segs = r["segments"]
        row = {"Route": " → ".join([segs[0]["from"]] + [sg["to"] for sg in segs]), "Total_EUR": r["price"],
               "Ticket": "one" if len(segs) > 1 else ""}
        for i, sg in enumerate(segs, 1):
            row.update({f"Leg{i}_Date": f"{sg['dep_dt']:%Y-%m-%d}", f"Leg{i}": leg(sg), f"Leg{i}_No": sg["flight_no"]})
        if len(segs) == 1:
            row["Leg1_EUR"] = r["price"]  # One-ticket connections only have a total price
        rows.append(row)
    return pd.DataFrame(rows).sort_values(by="Total_EUR") if rows else pd.DataFrame()

def save_merged(df, path, keys):
    """Merge new rows into the CSV from earlier runs; same flight seen again keeps the newest price."""
    if os.path.exists(path):
        df = pd.concat([pd.read_csv(path, dtype=str), df.astype(str)], ignore_index=True).fillna("")
        df = df.replace({"<NA>": "", "nan": ""})
        if "Fare" in df:
            df.loc[df["Fare"] == "", "Fare"] = DEFAULT_FARE
        df = df.drop_duplicates(subset=keys, keep="last")
    if not df.empty:
        df = df.sort_values(by="Total_EUR", key=lambda c: pd.to_numeric(c))
    df.to_csv(path, index=False)
    return df

def run_scan(label, o, d, hubs, dates, direct_only=False, max_leg1=130, max_leg2=160):
    """Direct + self-transfer scan for one direction; merges into the CSV and returns the merged table."""
    print(f"\n================ DIRECT {label.upper()} ================")
    direct = scan_direct(o, d, dates, max_stops=0 if direct_only else 1, label=label.capitalize())
    print(direct.to_string(index=False))
    if direct_only:
        if not direct.empty:
            direct["Checked"] = datetime.now().strftime("%Y-%m-%d")
            direct["Fare"] = fare_tag()
        return save_merged(direct, f"direct_{label}.csv", ["Route", "Leg1_Date", "Leg1", "Fare"])
    combos = scan_fast_self_transfers(o, d, hubs, dates, label.capitalize(), max_leg1, max_leg2)
    cols = ["Route", "Leg1_Date", "Leg1", "Leg1_EUR", "Leg1_No", "Leg2_Date", "Leg2", "Leg2_EUR", "Leg2_No", "Total_EUR", "Ticket", "Fare"]
    df = pd.concat([direct, combos], ignore_index=True).reindex(columns=cols).astype({"Leg1_EUR": "Int64", "Leg2_EUR": "Int64"})
    df["Checked"] = datetime.now().strftime("%Y-%m-%d")  # Rows from older runs keep their old date
    df["Fare"] = fare_tag()  # Prices for 2 adults never overwrite prices for 1
    # Ticket in the key: the same two planes can be a self-transfer and an airline-sold connection
    found = df.sort_values(by="Total_EUR")
    df = save_merged(df, f"cheapest_{label}.csv", ["Route", "Leg1_Date", "Leg1", "Leg2_Date", "Leg2", "Ticket", "Fare"])
    # Only this search: the merged file also holds older searches, which made this list look random
    print(f"\n================ TOP 15 CHEAPEST {label.upper()} FROM THIS SEARCH (direct, one-ticket and self-transfer) ================")
    print(found.head(15).to_string(index=False) if len(found) else "Nothing found.")
    return df

if __name__ == "__main__":
    import sys
    for label, o, d, dates in [("outbound", dk_airports, pt_airports, outbound_dates),
                               ("return", pt_airports, dk_airports, return_dates)]:
        run_scan(label, o, d, hub_airports, dates, "--direct" in sys.argv)
