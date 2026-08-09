# Physics AI Manager — Changelog

## 0.1.1 / package v1.2.2

- Harden Linux/macOS packaging against missing or broken Tkinter/Tcl-Tk installations.
- `scripts/build.py` now performs its own Tkinter/Tcl preflight, so manual PyInstaller builds cannot silently omit the GUI.
- `scripts/build_macos_linux.sh` validates both the system interpreter and the exact virtual-environment interpreter used for packaging.
- Improved Debian/Ubuntu guidance for installing `python3-tk` and `python3-venv`.

## 0.1.0 / package v1.2.1

- Initial Physics AI Manager desktop GUI.
- Project creation, project management, doctor checks, safe blueprint refresh, and multi-agent adapters.
- PEP 668-compatible isolated PyInstaller build environment.

## 1.2.3

- Added a Linux user-local installer (`scripts/install_linux.sh`).
- Installs the compiled bundle under `~/.local/opt/physics-ai-manager`.
- Adds `physics-ai-manager` to `~/.local/bin` via a symlink.
- Registers Physics AI Manager in the desktop Applications menu via a `.desktop` file.
- Keeps an editable blueprint `library/` beside the installed executable.
- Added `scripts/uninstall_linux.sh`.
- Made PyInstaller's `--onedir` layout explicit for predictable Linux installation.
