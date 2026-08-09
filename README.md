# Physics AI Manager

A small desktop application for creating and maintaining portable AI workspaces for physics research, scientific coding, paper writing, learning, and local research assistance.

*Built with AI assistance across several tools (ChatGPT, Codex, and Claude Code) rather than written by hand end-to-end.*

## Run from source

Python 3.10+, standard library only. On Debian/Ubuntu, Tkinter comes from the separate `python3-tk` package.

```bash
python app.py
```

The **New project** tab asks for the essentials:

- project title;
- parent directory and generated folder name;
- project profile/modes;
- one or more AI environments;
- optional initial objective;
- whether to initialize Git.

The **Manage project** tab can inspect an existing Physics AI project, add modes or agents, safely refresh managed blueprints, reset the session skeleton, and run a basic integrity check.

## AI adapters

Supported AI environments:

- Claude Code → `CLAUDE.md`
- Codex → `AGENTS.md`
- Google Antigravity → `.agents/rules/physics-ai.md`
- Gemini Code Assist → `GEMINI.md`
- OpenCode → `AGENTS.md`

Codex and OpenCode intentionally share one `AGENTS.md` when both are selected.

## Adding a new mode

Modes (Research, Coding, Writing, Learning, Assistant, …) live entirely in `library/`, not in the app code — adding one is a content change, not a code change. See `library/README.md` → "Adding a new mode" for the steps.

## Building a standalone app

Use the build script for your platform:

```bash
# macOS / Linux
./scripts/build_macos_linux.sh
```

```text
# Windows
scripts\build_windows.bat
```

On macOS/Linux the script builds in an isolated, project-local `.build-venv/` rather than touching your system Python (this sidesteps PEP 668 on Debian/Ubuntu). It preflights Tcl/Tk before building and refuses to produce an executable if Tkinter isn't available — if that happens, `sudo apt install python3-venv python3-tk` and rerun.

PyInstaller creates the application under `dist/PhysicsAIManager/` or the platform-equivalent app bundle. Build on the operating system you intend to distribute for; PyInstaller is not a cross-compiler.

The build embeds the blueprint `library/`. If you put an editable `library/` directory beside the executable, the application will prefer that external copy, so blueprints can evolve without recompiling. You can also set the `PHYSAI_LIBRARY` environment variable to point at a different master library.

## Deployment safety

The deployer refuses to write into a non-empty, unmanaged folder unless you explicitly opt in. Managed blueprint refreshes use recorded hashes: a locally-edited blueprint is left alone and the new master version is written beside it as `*.new` for you to review. Scientific state files are never touched by a routine refresh.

## First use

1. Launch the app.
2. Enter a title and choose the parent directory.
3. Pick a profile such as Research.
4. Select Claude Code, Codex, Antigravity, Gemini Code Assist, OpenCode, or several.
5. Optionally enter the initial research objective.
6. Click **Create Project**.
7. Open the resulting folder in the selected AI environment.

The deployed agent bootstrap points the AI to `.ai/CORE.md`, `.ai/PROJECT_CONTEXT.md`, `.ai/SESSION.md`, and the active mode blueprint.

## Linux install

On Ubuntu/Debian, install the build prerequisites first:

```bash
sudo apt update
sudo apt install python3-venv python3-tk
```

Then, from the project directory:

```bash
./scripts/install_linux.sh
```

Builds the app if needed and installs it for your user only — no sudo required:

- compiled bundle: `~/.local/opt/physics-ai-manager/`
- terminal launcher: `~/.local/bin/physics-ai-manager`
- desktop launcher: `~/.local/share/applications/physics-ai-manager.desktop`
- editable blueprints: `~/.local/opt/physics-ai-manager/library/`

After installing, launch it from your Applications menu (search "Physics AI Manager"), or from a terminal:

```bash
physics-ai-manager
```

If `~/.local/bin` was just created and isn't on your shell's `PATH` yet, log out and back in, or run:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Reinstalling keeps your editable blueprint library as-is. To replace it with the version shipped in this source (the old one is backed up first):

```bash
./scripts/install_linux.sh --refresh-library
```

To uninstall without touching your projects or user config:

```bash
./scripts/uninstall_linux.sh
```
