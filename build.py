"""Builds Flight Finder for the OS this runs on: python build.py  (PyInstaller can't build for another OS.)

Linux:   dist/flight-finder-linux.tar.gz  (unpack, run install.sh)
Windows: dist/FlightFinder-Setup.exe      (Inno Setup installer; a .zip when Inno Setup isn't installed)
macOS:   dist/FlightFinder-mac.dmg        (drag the app to Applications; Apple Silicon, macOS 13+)

Builds in a clean venv (from Anaconda it would bundle ~1.5 GB of unused libraries), then starts the
built app once to check it really opens (see FLIGHT_FINDER_SMOKE in flights_app.py)."""
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import venv
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = Path(os.environ.get("BUILD_DIR") or Path.home() / ".cache" / "flight-finder-build")  # on disk: /tmp is RAM on some Linux setups
VERSION = "1.0.0"
PACKAGES = ["PySide6==6.11.0", "pandas==3.0.3", "fast-flights==3.1.0", "primp==2.0.1", "selectolax==1.0.2",
            "typing_extensions==4.16.0",  # fast-flights imports it without declaring it
            "pyinstaller==6.22.3"]


def run(*cmd, **kw):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def smoke_test(exe):
    """Start the built app with a throwaway data folder; it reports how many airport chips and airports it loaded."""
    tmp = Path(tempfile.mkdtemp())
    out = tmp / "smoke.txt"
    env = {**os.environ, "FLIGHT_FINDER_SMOKE": str(out), "XDG_DATA_HOME": str(tmp), "APPDATA": str(tmp), "HOME": str(tmp)}
    if sys.platform.startswith("linux"):
        env.setdefault("QT_QPA_PLATFORM", "offscreen")  # build machines may have no screen
    try:
        subprocess.run([str(exe)], env=env, timeout=180, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        sys.exit("Smoke test failed: the app didn't finish loading within 3 minutes.")
    result = out.read_text() if out.exists() else ""
    if not re.fullmatch(r"[1-9]\d*:\d{4,}", result):
        sys.exit(f"Smoke test failed: expected '<chips>:<airports>', got {result!r}.")
    print(f"Smoke test passed: {result.replace(':', ' airport chips, ')} airports loaded.")
    shutil.rmtree(tmp, ignore_errors=True)


def main():
    py = WORK / "venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not py.exists():
        venv.create(WORK / "venv", with_pip=True)
    run(py, "-m", "pip", "install", "-q", *PACKAGES)
    built = WORK / "dist"
    run(py, "-m", "PyInstaller", HERE / "flight_finder.spec", "--noconfirm", "--distpath", built, "--workpath", WORK / "work")
    out = HERE / "dist"
    out.mkdir(exist_ok=True)

    if sys.platform == "win32":
        smoke_test(built / "flight-finder" / "flight-finder.exe")
        iscc = shutil.which("iscc") or r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
        if Path(iscc).exists():
            run(iscc, f"/DSrc={built / 'flight-finder'}", f"/DOut={out}", f"/DVersion={VERSION}", HERE / "installer.iss")
            result = out / "FlightFinder-Setup.exe"
        else:
            print("Inno Setup not found: making a .zip instead of an installer.")
            result = Path(shutil.make_archive(str(out / "flight-finder-windows"), "zip", built, "flight-finder"))
    elif sys.platform == "darwin":
        app = built / "Flight Finder.app"
        smoke_test(app / "Contents" / "MacOS" / "flight-finder")
        stage = WORK / "dmg"  # the .app plus an Applications shortcut to drag it onto
        shutil.rmtree(stage, ignore_errors=True)
        stage.mkdir()
        shutil.copytree(app, stage / app.name, symlinks=True)
        os.symlink("/Applications", stage / "Applications")
        result = out / "FlightFinder-mac.dmg"
        result.unlink(missing_ok=True)
        run("hdiutil", "create", "-volname", "Flight Finder", "-srcfolder", stage, "-ov", "-format", "UDZO", result)
    else:
        smoke_test(built / "flight-finder" / "flight-finder")
        shutil.copy(HERE / "install.sh", built)
        result = out / "flight-finder-linux.tar.gz"
        with tarfile.open(result, "w:gz") as t:
            t.add(built / "flight-finder", "flight-finder")
            t.add(built / "install.sh", "install.sh")
    print(f"Built {result} ({result.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
