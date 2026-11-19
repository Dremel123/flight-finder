#!/bin/sh
# Installs the built app for the current user: copies it to ~/.local/opt and adds it to the app menu.
# Run from the folder that holds flight-finder/ (the PyInstaller output). Remove with: rm -r ~/.local/opt/flight-finder ~/.local/share/applications/flight-finder.desktop
set -e
src="$(cd "$(dirname "$0")" && pwd)/flight-finder"
[ -x "$src/flight-finder" ] || { echo "No flight-finder/ folder next to this script. Build it first." >&2; exit 1; }
dest="$HOME/.local/opt/flight-finder"
mkdir -p "$HOME/.local/opt" "$HOME/.local/share/applications"
rm -rf "$dest" && cp -r "$src" "$dest"
cat > "$HOME/.local/share/applications/flight-finder.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Flight Finder
Comment=Find cheap flights and self-transfers
Exec="$dest/flight-finder"
Icon=$dest/_internal/icons/icon.png
Terminal=false
Categories=Utility;
StartupWMClass=flight-finder
DESKTOP
echo "Installed. Open Flight Finder from your app menu. Your results are kept in ~/.local/share/Flight Finder."
