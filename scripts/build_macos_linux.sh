#!/usr/bin/env sh
set -eu

# Build Physics AI Manager without installing Python packages into the
# operating system's managed Python environment (PEP 668 compatible).

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
cd "$ROOT_DIR"

PYTHON_BIN=${PYTHON_BIN:-python3}
VENV_DIR=${PHYSAI_BUILD_VENV:-"$ROOT_DIR/.build-venv"}

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Error: $PYTHON_BIN was not found." >&2
    echo "Install Python 3 and try again." >&2
    exit 1
fi

check_tk() {
    CHECK_PYTHON=$1
    if ! "$CHECK_PYTHON" -c 'import tkinter, _tkinter; t=tkinter.Tcl(); t.eval("info patchlevel")' >/dev/null 2>&1; then
        echo "Error: Tkinter/Tcl-Tk is not usable by $CHECK_PYTHON." >&2
        echo "On Debian/Ubuntu, install it with:" >&2
        echo "  sudo apt update" >&2
        echo "  sudo apt install python3-tk" >&2
        echo >&2
        echo "Then verify with:" >&2
        echo "  python3 -c 'import tkinter, _tkinter; print(tkinter.TkVersion)'" >&2
        exit 1
    fi
}

# Check the system interpreter before doing any package installation.
check_tk "$PYTHON_BIN"

# Create a project-local virtual environment. If Debian/Ubuntu omitted the
# venv module, provide the distribution-native remedy rather than suggesting
# --break-system-packages.
if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "Creating isolated build environment: $VENV_DIR"
    if ! "$PYTHON_BIN" -m venv "$VENV_DIR"; then
        echo >&2
        echo "Could not create a Python virtual environment." >&2
        echo "On Debian/Ubuntu, install venv support with:" >&2
        echo "  sudo apt update && sudo apt install python3-venv" >&2
        echo "Then run this build script again." >&2
        exit 1
    fi
fi

VENV_PYTHON="$VENV_DIR/bin/python"

# A pre-existing venv may have been created before Tkinter was installed.
# Check the exact interpreter PyInstaller will use too.
check_tk "$VENV_PYTHON"

echo "Installing build dependency inside the isolated environment..."
"$VENV_PYTHON" -m pip install -r requirements-build.txt

echo "Building Physics AI Manager..."
"$VENV_PYTHON" scripts/build.py

echo
echo "Build complete. Look in:"
echo "  $ROOT_DIR/dist/"
