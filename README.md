# Flight Finder

A desktop app that finds cheap flights between two groups of airports. It combines direct flights, connections sold as one ticket, and **self-transfers**: two separate cheap tickets joined at a hub airport, where you collect your bags and check in again.

Prices come from Google Flights. They're for the number of adults you set, optionally with a cabin bag each. Checked bags use your own fee estimate, because Google doesn't price them.

## Download

Get the installer for your system from the [latest release](https://github.com/Dremel123/flight-finder/releases/latest):

| System | File | How to install |
|---|---|---|
| Windows 10/11 | `FlightFinder-Setup.exe` | Run it. Windows may say "Windows protected your PC" because the app isn't signed: click **More info → Run anyway**. |
| macOS 13+ (Apple Silicon) | `FlightFinder-mac.dmg` | Open it and drag Flight Finder to Applications. The app isn't signed, so the first time, **right-click it → Open → Open**. If macOS says it's damaged, run `xattr -cr "/Applications/Flight Finder.app"` in Terminal. |
| Linux (x86-64) | `flight-finder-linux.tar.gz` | Unpack it and run `./install.sh`. Flight Finder then appears in your app menu. |

Your results and settings are kept in your user data folder (`%APPDATA%\Flight Finder`, `~/Library/Application Support/Flight Finder` or `~/.local/share/Flight Finder`), so they survive updates and uninstalling.

## Things to know

- Self-transfers aren't protected: if the first flight is late and you miss the second, that airline owes you nothing.
- Changing planes outside the Schengen area (UK, Ireland) means passport control. The UK may require an ETA bought in advance.
- A full search makes thousands of requests and can take 30–90 minutes. Repeats within 12 hours are much faster.
- Prices can change. Trips checked before today are marked.
- This app reads Google Flights pages, which Google doesn't officially allow. It can stop working whenever Google changes its site.

## Run from source

Python 3.11+ with `PySide6 pandas fast-flights primp selectolax typing_extensions`:

```
python flights_app.py         # the app
python test_find_flights.py   # tests (prints "ok")
python build.py               # build the installer for this OS
```

## Credits

- Airport data: [OpenFlights](https://openflights.org/data) (Open Database License) and [OurAirports](https://ourairports.com/data/) (public domain).
- Font: [Archivo](https://github.com/Omnibus-Type/Archivo), SIL Open Font License (`fonts/OFL.txt`).
