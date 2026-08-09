# Physics AI Project Bootstrap

This file is intentionally short. The canonical instructions live under `.ai/`.

<!-- SHARED_AGENTS -->

Before doing substantive work in this project:

Read each file below completely through EOF — not an excerpt, a preview, or an initial line range. If a tool call truncates output, issue further reads until the file has been read in full. A partial read of any of these files does not satisfy the step that names it.

1. Read `.ai/CORE.md`.
2. Read `.ai/PROJECT_CONTEXT.md`.
3. Read `.ai/SESSION.md` if it exists. If it is absent, infer the mode only from the user's current request; do not recover an old objective from logs.
4. Read the mode file named by `Active mode` in `.ai/SESSION.md` (or the clearly inferred current mode).
5. Read only the canonical state files relevant to the current task.
6. Read `.ai/HANDOFF.md` only when continuing an actual handoff from another agent/session.

Follow the instruction precedence defined in `.ai/CORE.md`.

Do not duplicate the full blueprint into this file. The `.ai/` files are the canonical instructions.
