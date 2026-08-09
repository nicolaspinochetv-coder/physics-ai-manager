# Physics AI Master Library

This directory is the **master source library** for deploying AI-assisted physics workspaces. It is intentionally separate from individual research, coding, writing, learning, and assistant projects.

Current library version: **1.3.0**.

## Main entry point

Give a filesystem-capable model access to this folder and ask it to read:

```text
INITIATE.md
```

The model will ask for the project type, target AI environment, destination directory, and only the additional choices needed for hybrid/multi-agent setups. It then uses `tools/deploy_project.py` to build or extend the target project outside the master library.

## Master structure

```text
physics_ai_master/
├── INITIATE.md
├── START_HERE.md
├── MASTER_MANIFEST.json
├── CHANGELOG.md
├── blueprints/
│   ├── CORE.md
│   ├── HANDOFF.md
│   └── modes/
│       ├── RESEARCH.md
│       ├── CODING.md
│       ├── WRITING.md
│       ├── LEARNING.md
│       └── ASSISTANT.md
├── adapters/
│   └── _BOOTSTRAP_TEMPLATE.md
├── templates/
│   ├── PROJECT_CONTEXT_TEMPLATE.md
│   ├── SESSION_TEMPLATE.md
│   ├── gitignore_snippet.txt
│   └── state/
└── tools/
    └── deploy_project.py
```

The deployer renders the same canonical bootstrap template to the native filename expected by each environment:

```text
Claude Code          -> CLAUDE.md
Codex in VS Code     -> AGENTS.md
Gemini Code Assist   -> GEMINI.md
Antigravity          -> .agents/rules/physics-ai.md
OpenCode             -> AGENTS.md
```

Codex and OpenCode intentionally share `AGENTS.md` when both are installed.

## Design rules

- The master library is the source of truth for reusable blueprints.
- Individual projects receive copies of the shared core plus only their selected mode blueprint(s).
- `.ai/CORE.md`, `.ai/modes/*.md`, and root agent adapters are **managed copies**; project-specific rules belong in `.ai/PROJECT_CONTEXT.md`.
- Project scientific state is never overwritten by blueprint refreshes.
- Refresh safety is tracked with hashes in `.ai/DEPLOYMENT.json`; local edits to managed files are preserved and proposed master updates are written as `*.new`.
- Deployment is non-destructive by default.
- A project can be extended later with another mode or model adapter.
- The model used to deploy a project does not need to be the model used to work on it.

## Adding a new mode

Modes are entirely data/content-driven — adding one does not require changing `tools/deploy_project.py` or the desktop app. Provide, consistently:

1. **`MASTER_MANIFEST.json`** — add a key under `mode_scaffolds`, e.g. `"SIMULATION"`, with:
   - `dirs`: directories to create under the project root;
   - `files`: a map of `<target path>` → `<template path under templates/state/>`.

   The key alone makes it a selectable mode checkbox in the app; no other wiring is needed.

2. **`blueprints/modes/<MODE>.md`** — the mode's instructions. The filename must match the manifest key exactly (case-sensitive: `SIMULATION` → `blueprints/modes/SIMULATION.md`). Follow the shape of the existing mode files — Mission, canonical file structure, file roles, workflow, completion checklist — and stay consistent with `blueprints/CORE.md` (equation numbering in §4, Markdown formatting in §15, literature discipline in §5) rather than restating or contradicting it.

3. **`templates/state/<mode>/...`** — starter content for every file referenced in that mode's `files` mapping.

4. **Optional** — a `project_types` entry if the mode should be selectable as a primary project type in "New Project", rather than only addable as an extra mode on a hybrid project.

Bump `library_version` in `MASTER_MANIFEST.json` and add a `CHANGELOG.md` entry describing the new mode. Keep new mode files as narrow and specific as their purpose warrants — a mode that duplicates most of an existing one is a sign it should be a variant/section within that mode instead.

## Manual deployment

```bash
python tools/deploy_project.py \
  --path ~/research/example \
  --title "Example" \
  --project-type research \
  --agent claude \
  --git-init
```

For an existing marked deployment, unchanged project type and agents can be inferred from `.ai/DEPLOYMENT.json`, so adding only a mode can be as small as:

```bash
python tools/deploy_project.py \
  --path ~/research/example \
  --mode CODING
```

Run `python tools/deploy_project.py --help` for all options. See `CHANGELOG.md` for architecture changes.
