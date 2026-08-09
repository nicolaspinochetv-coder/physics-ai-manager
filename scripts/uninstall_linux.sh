#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${PHYSAI_INSTALL_DIR:-$HOME/.local/opt/physics-ai-manager}"
BIN_DIR="${PHYSAI_BIN_DIR:-$HOME/.local/bin}"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
DESKTOP_DIR="$DATA_HOME/applications"
ICON_FILE="$DATA_HOME/icons/hicolor/512x512/apps/physics-ai-manager.png"

rm -f "$BIN_DIR/physics-ai-manager"
rm -f "$DESKTOP_DIR/physics-ai-manager.desktop"
rm -f "$ICON_FILE"
rm -rf "$APP_DIR"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$DATA_HOME/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "Physics AI Manager has been uninstalled."
echo "Your projects and ~/.config/physics-ai-manager were not removed."
