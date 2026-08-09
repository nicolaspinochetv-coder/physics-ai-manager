# Physics AI Manager

A small desktop application for creating and maintaining portable AI workspaces for physics research, scientific coding, paper writing, learning, and local research assistance.

## Run from source

Python 3.10+ is recommended. The application itself uses only the Python standard library. On Debian/Ubuntu, Tkinter is commonly provided by the separate `python3-tk` system package.

```bash
python app.py
```

The **New project** tab asks for only the essentials:

- project title;
- parent directory and generated folder name;
- project profile/modes;
- one or more AI environments;
- optional initial objective;
- whether to initialize Git.

The **Manage project** tab can inspect an existing Physics AI project, add modes or agents, safely refresh managed blueprints, reset the session skeleton, and run a basic integrity check.

## AI adapters

The bundled library currently deploys:

- Claude Code → `CLAUDE.md`
- Codex → `AGENTS.md`
- Google Antigravity → `.agents/rules/physics-ai.md`
- Gemini Code Assist → `GEMINI.md`
- OpenCode → `AGENTS.md`

Codex and OpenCode intentionally share one `AGENTS.md` when both are selected.

## Adding a new mode

Modes (Research, Coding, Writing, Learning, Assistant, …) live entirely in `library/`, not in the app code — adding one is a content change, not a code change. See `library/README.md` → "Adding a new mode" for the steps.

## Build a standalone application

Use the included build script for your platform:

```bash
# macOS / Linux
./scripts/build_macos_linux.sh
```

```text
# Windows
scripts\build_windows.bat
```

On macOS/Linux the script creates a project-local `.build-venv/`, installs PyInstaller there, and builds from that isolated environment. This avoids modifying an OS-managed Python installation (including Debian/Ubuntu systems that enforce PEP 668). The build now performs a Tcl/Tk preflight both before and inside the virtual environment and refuses to create an executable if Tkinter is unavailable. If Ubuntu/Debian reports that virtual environments or Tkinter are unavailable, install the corresponding system packages with `sudo apt install python3-venv python3-tk`, then rerun the script.

PyInstaller creates the application under `dist/PhysicsAIManager/` or the platform-equivalent app bundle. Build on the operating system you intend to distribute for; PyInstaller is not a cross-compiler.

The build embeds the blueprint `library/`. If you put an editable `library/` directory beside the executable, the application will prefer that external copy, so blueprints can evolve without recompiling. You can also set the `PHYSAI_LIBRARY` environment variable to point at a different master library.

## Safety behavior

The deployment engine refuses to write into a non-empty unmanaged folder unless you explicitly opt in. Managed blueprint refreshes use recorded hashes; if a blueprint was locally edited, the app preserves it and writes the new master version beside it as `*.new` for manual review. Scientific state files are not replaced by routine refreshes.

## First use

1. Launch the app.
2. Enter a title and choose the parent directory.
3. Pick a profile such as Research.
4. Select Claude Code, Codex, Antigravity, Gemini Code Assist, OpenCode, or several.
5. Optionally enter the initial research objective.
6. Click **Create Project**.
7. Open the resulting folder in the selected AI environment.

The deployed agent bootstrap points the AI to `.ai/CORE.md`, `.ai/PROJECT_CONTEXT.md`, `.ai/SESSION.md`, and the active mode blueprint.

## Install as a normal Linux application

On Ubuntu/Debian, first make sure the build prerequisites are available:

```bash
sudo apt update
sudo apt install python3-venv python3-tk
```

Then, from the project directory, run:

```bash
./scripts/install_linux.sh
```

The installer will build the application if needed and install it **for your user only** (no sudo required for the install):

- compiled bundle: `~/.local/opt/physics-ai-manager/`
- terminal launcher: `~/.local/bin/physics-ai-manager`
- desktop launcher: `~/.local/share/applications/physics-ai-manager.desktop`
- editable blueprints: `~/.local/opt/physics-ai-manager/library/`

After installation, launch it from your Applications menu by searching for **Physics AI Manager**, or from a terminal with:

```bash
physics-ai-manager
```

If `~/.local/bin` was just created and is not yet on your current shell's `PATH`, either log out and back in or run:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Reinstalling preserves the installed editable blueprint library. To deliberately replace it with the library shipped in the new source package (while backing up the old one), run:

```bash
./scripts/install_linux.sh --refresh-library
```

To uninstall the application without deleting your projects or user configuration:

```bash
./scripts/uninstall_linux.sh
```
