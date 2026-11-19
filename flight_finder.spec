# PyInstaller recipe, used by build.py on Linux, Windows and macOS (each OS builds its own; no cross-building).
import sys

a = Analysis(
    ["flights_app.py"],
    datas=[("ui.html", "."), ("airports.js", "."), ("fonts", "fonts"), ("icons/icon.png", "icons")],
    excludes=["tkinter", "matplotlib", "IPython", "notebook", "scipy", "PyQt5", "PyQt6"],
)
pyz = PYZ(a.pure)
icon = {"win32": "icons/icon.ico", "darwin": "icons/icon.icns"}.get(sys.platform)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="flight-finder", console=False, icon=icon)
coll = COLLECT(exe, a.binaries, a.datas, name="flight-finder")
if sys.platform == "darwin":
    app = BUNDLE(coll, name="Flight Finder.app", icon=icon, bundle_identifier="app.flightfinder",
                 info_plist={"NSHighResolutionCapable": True, "CFBundleShortVersionString": "1.0.0"})
