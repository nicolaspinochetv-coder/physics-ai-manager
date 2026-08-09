# Changelog

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
