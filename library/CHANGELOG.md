# Changelog

## 1.6.0

- `adapters/_BOOTSTRAP_TEMPLATE.md` and `CORE.md` §1 now require every listed context file to be read completely through EOF, not as an excerpt or truncated preview, before substantive work begins. Placed in both files deliberately: the bootstrap file is the very first thing an agent opens, so the completeness requirement has to be visible there to be self-enforcing, before an agent could otherwise partially-read its way past the instruction to read `CORE.md` in full.
- `LEARNING.md` strengthened in three places, integrated with existing content rather than duplicating it:
  - §5 (Lecture design) sharpens the existing "define assumptions and notation" line into an explicit self-containedness requirement — a lecture has no live back-and-forth to fall back on, so notation carried from a source cannot be assumed self-explanatory.
  - §9 (Research-readiness transition) now points at `CORE.md` §3's existing epistemic categories when reconstructing a source for teaching, instead of introducing a second, competing taxonomy.
  - §2 (`learning_log.md`) and §10 (Completion checklist) now distinguish material having been *produced* (a lecture, a problem set) from mastery having been *demonstrated*; only the learner's own performance counts as evidence of mastery.
  - §10 also adds an explicit pre-completion check against `CORE.md` §15's Markdown formatting contract for finished lectures.

## 1.5.0

- Added a shared, mode-agnostic `documents/` staging folder, created for every project regardless of installed modes, with a managed `documents/README.md` (new `blueprints/DOCUMENTS_README.md`) explaining that files there are unreviewed until an agent catalogs them into the active mode's canonical literature/notes file.
- `CORE.md` §5 (Literature discipline) gained a "User-supplied documents" subsection describing the `documents/` convention, so it applies to every mode without duplicating text into each mode blueprint.
- The desktop app can now copy user-selected files into `documents/` at project creation or later via Manage Project; re-importing an identical file is a no-op, and a same-named file with different content is kept alongside under a disambiguated name rather than overwritten.

## 1.4.0

- `adapters/_BOOTSTRAP_TEMPLATE.md` gained a `<!-- SHARED_AGENTS -->` marker, filled in at deploy time with a "Shared AI environments" note listing every agent installed for the project. Omitted for single-agent projects. This closes the gap where a project configured for multiple agents (e.g. Claude Code + Codex) never declared that fact in any `.md` file the agents actually read — only in `SESSION.md`'s single, hand-edited `Active agent` field and in `.ai/DEPLOYMENT.json`, which `CORE.md` never lists as a file to read.
- `SESSION_TEMPLATE.md` now clarifies that `Active agent` is session-local and points to the bootstrap file's note as the authoritative, deployer-synced list.

## 1.3.0

- Added `CORE.md` §15: Markdown formatting rules for Markdown Preview Enhanced compatibility (math delimiters, left-margin display equations, no display math in lists/blockquotes, blank-line and heading-hierarchy conventions). Applies to every agent adapter and every mode.

## 1.2.0

- Separate Google Antigravity from Gemini Code Assist.
- Antigravity projects install a workspace rule at `.agents/rules/physics-ai.md`.
- Manifest agent adapters now support one or more adapter paths.
- This library version is bundled with Physics AI Manager.

## 1.1.0 — architecture validation update

- Corrected OpenCode bootstrap mapping to `AGENTS.md`.
- Replaced duplicated agent bootstrap sources with one canonical `_BOOTSTRAP_TEMPLATE.md`.
- Added managed-file hashes and conservative refresh conflict handling in the deployer.
- Added library versioning to deployment metadata.
- Made extension deployments infer existing project type and agents when omitted.
- Removed hardcoded mode registry logic from the deployer.
- Removed the WRITING-specific scaffold branch; all scaffold files are now manifest-driven.
- Clarified managed blueprints vs project-specific rules.
- Clarified HANDOFF lifecycle, handoff archives, and runtime directory ownership.
- Defined RESEARCH/WRITING literature canonicality in hybrid projects.
- Folded the orphan user-profile template into the active assistant profile templates.
- Removed the nonexistent `physai` CLI reference.
