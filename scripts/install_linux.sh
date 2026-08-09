#!/usr/bin/env bash
set -euo pipefail

# Build (if needed) and install Physics AI Manager for the current Linux user.
# No root privileges are required for the application install itself.

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "Error: install_linux.sh is intended for Linux." >&2
    exit 1
fi

APP_DIR="${PHYSAI_INSTALL_DIR:-$HOME/.local/opt/physics-ai-manager}"
BIN_DIR="${PHYSAI_BIN_DIR:-$HOME/.local/bin}"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
DESKTOP_DIR="$DATA_HOME/applications"
DESKTOP_FILE="$DESKTOP_DIR/physics-ai-manager.desktop"
ICON_DIR="$DATA_HOME/icons/hicolor/512x512/apps"
ICON_FILE="$ICON_DIR/physics-ai-manager.png"
LINK_PATH="$BIN_DIR/physics-ai-manager"
BUILD_DIR="$ROOT_DIR/dist/PhysicsAIManager"
BUILD_EXE="$BUILD_DIR/PhysicsAIManager"
REFRESH_LIBRARY=0

for arg in "$@"; do
    case "$arg" in
        --refresh-library) REFRESH_LIBRARY=1 ;;
        -h|--help)
            cat <<HELP
Usage: ./scripts/install_linux.sh [--refresh-library]

Installs Physics AI Manager for the current user:
  Application bundle: $APP_DIR
  Terminal command:   $LINK_PATH
  Desktop launcher:   $DESKTOP_FILE

If no compiled bundle exists yet, the script builds it first.

--refresh-library  Replace an existing editable installed blueprint library.
                   The previous library is backed up first.
HELP
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            exit 2
            ;;
    esac
done

if [[ ! -x "$BUILD_EXE" ]]; then
    echo "No compiled bundle found; building it first..."
    "$ROOT_DIR/scripts/build_macos_linux.sh"
fi

if [[ ! -x "$BUILD_EXE" ]]; then
    echo "Error: build did not produce $BUILD_EXE" >&2
    exit 1
fi

mkdir -p "$APP_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$ICON_DIR"

# Replace only the compiled bundle files. Preserve an external editable library
# unless the user explicitly asks to refresh it.
echo "Installing application bundle to: $APP_DIR"
find "$APP_DIR" -mindepth 1 -maxdepth 1 ! -name library -exec rm -rf {} + 2>/dev/null || true
cp -a "$BUILD_DIR"/. "$APP_DIR"/
chmod +x "$APP_DIR/PhysicsAIManager"

if [[ -d "$APP_DIR/library" ]]; then
    if [[ "$REFRESH_LIBRARY" -eq 1 ]]; then
        stamp=$(date +%Y%m%d-%H%M%S)
        backup="$APP_DIR/library.backup-$stamp"
        echo "Backing up existing blueprint library to: $backup"
        mv "$APP_DIR/library" "$backup"
        cp -a "$ROOT_DIR/library" "$APP_DIR/library"
        echo "Installed refreshed editable blueprint library."
    else
        echo "Preserving existing editable blueprint library: $APP_DIR/library"
    fi
else
    cp -a "$ROOT_DIR/library" "$APP_DIR/library"
    echo "Installed editable blueprint library: $APP_DIR/library"
fi

ln -sfn "$APP_DIR/PhysicsAIManager" "$LINK_PATH"

if [[ -f "$ROOT_DIR/assets/icon.png" ]]; then
    cp "$ROOT_DIR/assets/icon.png" "$ICON_FILE"
    chmod 0644 "$ICON_FILE"
fi

cat > "$DESKTOP_FILE" <<DESKTOP
[Desktop Entry]
Type=Application
Version=1.0
Name=Physics AI Manager
Comment=Create and manage portable AI workspaces for physics
Exec=$APP_DIR/PhysicsAIManager
TryExec=$APP_DIR/PhysicsAIManager
Icon=physics-ai-manager
Terminal=false
Categories=Science;Education;Development;
Keywords=Physics;AI;Research;Codex;Claude;Gemini;Antigravity;
StartupNotify=true
DESKTOP
chmod 0644 "$DESKTOP_FILE"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$DATA_HOME/icons/hicolor" >/dev/null 2>&1 || true
fi

echo
echo "Physics AI Manager is installed."
echo "  Applications menu: Physics AI Manager"
echo "  Terminal command:  physics-ai-manager"
echo "  Application files: $APP_DIR"
echo "  Blueprint library: $APP_DIR/library"
echo

case ":${PATH:-}:" in
    *":$BIN_DIR:"*) ;;
    *)
        echo "Note: $BIN_DIR is not currently on PATH."
        echo "Ubuntu normally adds ~/.local/bin after a new login when the directory exists."
        echo "For the current shell, run:"
        echo "  export PATH=\"$BIN_DIR:\$PATH\""
        echo
        ;;
esac

echo "You can launch it now with:"
echo "  $APP_DIR/PhysicsAIManager"
