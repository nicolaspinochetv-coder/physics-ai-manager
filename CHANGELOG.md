# Physics AI Manager — Changelog

## 1.6.0

- Renamed the "Prior documents" control to "Import documents" in both the New Project and Manage Project tabs.
- Bundled library bumped to `1.6.0`: bootstrap/CORE.md now require instruction files to be read completely (not as an excerpt) before work begins, and LEARNING.md gained sharper self-containedness, source-reconstruction, and mastery-vs-material-produced guidance. See `library/CHANGELOG.md`.

## 1.5.0

- Added an "Import documents" control to both the New Project and Manage Project tabs: pick existing files and they're copied into the project's shared `documents/` folder (creation-time or added later), so prior literature/reference material doesn't have to be placed manually. Re-adding an identical file is a no-op; a same-named file with different content is kept alongside under a disambiguated name.
- `documents/` is created for every project regardless of which modes are installed, with a managed `documents/README.md` explaining it's a staging area — an agent still has to catalog anything relevant into the active mode's canonical literature/notes file.
- Bumped bundled library to `1.5.0` (see `library/CHANGELOG.md`).

## 1.3.0

- Deployed bootstrap files (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.agents/rules/physics-ai.md`) now declare a "Shared AI environments" note listing every AI environment configured for the project, so this is visible in the first file each agent reads rather than only in `SESSION.md`'s single, hand-edited `Active agent` field. The note is generated from `installed_agents` and omitted entirely for single-agent projects.
- Adding a new agent to an existing project immediately writes this note into that agent's own (newly created) bootstrap file; previously-deployed bootstrap files pick up the updated list the next time "Refresh managed blueprints" is used, consistent with how every other managed file already refreshes.
- `SESSION.md` now points to the bootstrap file's note as the authoritative, auto-synced source, clarifying that `Active agent` only means "who is driving this session."
- Bumped bundled library to `1.3.0` (see `library/CHANGELOG.md`).

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
