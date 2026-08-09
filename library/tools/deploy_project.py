#!/usr/bin/env python3
"""Deploy or extend a Physics AI project from the master blueprint library.

The deployer is deterministic and non-destructive by default. Reusable blueprints
are managed files; scientific/project state is never overwritten by refreshes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

MASTER_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = MASTER_ROOT / "MASTER_MANIFEST.json"


def load_manifest() -> dict:
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def next_sidecar(path: Path) -> Path:
    candidate = path.with_name(path.name + ".new")
    if not candidate.exists():
        return candidate
    i = 2
    while True:
        candidate = path.with_name(path.name + f".new.{i}")
        if not candidate.exists():
            return candidate
        i += 1


def install_managed_text(
    *,
    target: Path,
    rel: str,
    text: str,
    refresh: bool,
    previous_managed: dict,
    current_managed: dict,
    copied: list[str],
    conflicts: list[str],
) -> None:
    """Install/refresh one managed file without clobbering local customization.

    A refresh is safe when the destination still matches the hash recorded when
    this system last managed it. Legacy deployments without a recorded baseline
    are handled conservatively: if their file differs from the new master copy,
    the new copy is written beside it as *.new instead of overwriting it.
    """
    dst = target / rel
    new_hash = sha256_text(text)
    baseline = previous_managed.get(rel, {}).get("sha256")

    if not dst.exists():
        atomic_write(dst, text)
        current_managed[rel] = {"sha256": new_hash}
        copied.append(rel)
        return

    current_hash = sha256_file(dst)

    if not refresh:
        if current_hash == new_hash:
            current_managed[rel] = {"sha256": new_hash}
        elif baseline:
            # Preserve the previous baseline so a later refresh can still detect
            # whether the deployed file was customized after installation.
            current_managed[rel] = {"sha256": baseline}
        return

    if current_hash == new_hash:
        current_managed[rel] = {"sha256": new_hash}
        return

    if baseline and current_hash == baseline:
        atomic_write(dst, text)
        current_managed[rel] = {"sha256": new_hash}
        copied.append(rel)
        return

    sidecar = next_sidecar(dst)
    atomic_write(sidecar, text)
    conflicts.append(f"{rel} -> {sidecar.name}")
    if baseline:
        current_managed[rel] = {"sha256": baseline}


def append_gitignore(target: Path) -> bool:
    snippet = (MASTER_ROOT / "templates" / "gitignore_snippet.txt").read_text(encoding="utf-8").strip().splitlines()
    path = target / ".gitignore"
    existing_lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    existing = {line.strip() for line in existing_lines}
    missing = [line for line in snippet if line.strip() and line.strip() not in existing]
    if not missing:
        return False
    text = "\n".join(existing_lines).rstrip()
    if text:
        text += "\n\n"
    text += "\n".join(missing) + "\n"
    atomic_write(path, text)
    return True


def make_mode_normalizer(valid_modes: set[str]):
    aliases = {
        "R": "RESEARCH",
        "CODE": "CODING", "C": "CODING",
        "WRITE": "WRITING", "W": "WRITING",
        "LEARN": "LEARNING", "L": "LEARNING",
        "A": "ASSISTANT",
    }

    def normalize(value: str) -> str:
        raw = value.strip().upper()
        mode = aliases.get(raw, raw)
        if mode not in valid_modes:
            allowed = ", ".join(sorted(valid_modes))
            raise argparse.ArgumentTypeError(f"Unknown mode: {value}. Available modes: {allowed}")
        return mode

    return normalize


def render_session(primary_mode: str, active_agent: str) -> str:
    return (
        "# Session\n\n"
        f"- Active mode: {primary_mode}\n"
        "- Objective: <single concrete objective>\n"
        "- Scope: <what to work on now>\n"
        "- Deliverable: <what should exist when done>\n"
        f"- Active agent: {active_agent}\n"
        "- Constraints: <optional>\n"
        "- Related files: <optional>\n"
    )


def scaffold_mode(target: Path, mode: str, manifest: dict) -> tuple[int, int]:
    spec = manifest["mode_scaffolds"][mode]
    made_dirs = 0
    made_files = 0
    for rel in spec.get("dirs", []):
        path = target / rel
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            made_dirs += 1
        else:
            path.mkdir(parents=True, exist_ok=True)

    template_root = MASTER_ROOT / "templates" / "state"
    for rel, template_rel in spec.get("files", {}).items():
        dst = target / rel
        if dst.exists():
            continue
        src = template_root / template_rel
        if not src.is_file():
            raise SystemExit(f"Missing scaffold template: {src}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        made_files += 1

    return made_dirs, made_files


def main() -> int:
    manifest = load_manifest()
    project_choices = sorted(manifest["project_types"])
    agent_choices = sorted(manifest["agents"])
    valid_modes = set(manifest["mode_scaffolds"])
    normalize_mode = make_mode_normalizer(valid_modes)

    parser = argparse.ArgumentParser(description="Deploy or extend a Physics AI project workspace.")
    parser.add_argument("--path", required=True, help="Destination project directory")
    parser.add_argument("--title", help="Project title; defaults to destination folder name")
    parser.add_argument("--project-type", choices=project_choices,
                        help="Project type; for an existing deployment, defaults to its recorded type")
    parser.add_argument("--agent", action="append", choices=agent_choices,
                        help="Agent adapter to install; repeat for multiple agents. Existing deployments may omit it.")
    parser.add_argument("--mode", action="append", type=normalize_mode, default=[],
                        help="Additional mode to install; repeat as needed")
    parser.add_argument("--primary-mode", type=normalize_mode,
                        help="Initial active mode; required for ambiguous new hybrid setups")
    parser.add_argument("--existing-project", action="store_true",
                        help="Allow deployment into a non-empty directory not previously managed by this system")
    parser.add_argument("--refresh-blueprints", action="store_true",
                        help="Refresh managed blueprint/adapter files; customized copies are preserved and receive a *.new candidate")
    parser.add_argument("--reset-session", action="store_true",
                        help="Replace .ai/SESSION.md with a fresh session skeleton")
    parser.add_argument("--git-init", action="store_true", help="Initialize Git if the target is not already a repository")
    args = parser.parse_args()

    target = Path(args.path).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    marker = target / ".ai" / "DEPLOYMENT.json"
    nonempty = any(target.iterdir())
    if nonempty and not marker.exists() and not args.existing_project:
        raise SystemExit(
            "Destination is non-empty and is not marked as a Physics AI deployment. "
            "Re-run with --existing-project only if you intentionally want to add the workspace to it."
        )

    previous = {}
    if marker.exists():
        try:
            previous = json.loads(marker.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            previous = {}

    project_type = args.project_type or previous.get("project_type")
    if not project_type:
        raise SystemExit("New deployments require --project-type.")
    if project_type not in manifest["project_types"]:
        raise SystemExit(f"Recorded project type is not supported by this master library: {project_type}")

    project_spec = manifest["project_types"][project_type]
    modes: list[str] = []
    for mode in previous.get("installed_modes", []):
        if mode in valid_modes and mode not in modes:
            modes.append(mode)
    default_primary = project_spec.get("primary_mode")
    if default_primary and default_primary not in modes:
        modes.append(default_primary)
    for mode in args.mode:
        if mode not in modes:
            modes.append(mode)
    if project_type == "hybrid" and not modes and not previous.get("installed_modes"):
        raise SystemExit("New hybrid projects require at least one --mode.")

    primary = args.primary_mode or previous.get("primary_mode") or default_primary or (modes[0] if modes else None)
    if not primary:
        raise SystemExit("Could not determine a primary mode.")
    if primary not in valid_modes:
        raise SystemExit(f"Primary mode is not supported by this master library: {primary}")
    if primary not in modes:
        modes.insert(0, primary)

    requested_agents = args.agent or previous.get("installed_agents", [])
    if not requested_agents:
        raise SystemExit("New deployments require at least one --agent.")
    agent_keys: list[str] = []
    for key in requested_agents:
        if key not in manifest["agents"]:
            raise SystemExit(f"Unknown recorded agent: {key}")
        if key not in agent_keys:
            agent_keys.append(key)
    active_agent = manifest["agents"][agent_keys[0]]["label"]

    previous_managed = previous.get("managed_files", {}) if isinstance(previous.get("managed_files", {}), dict) else {}
    current_managed = dict(previous_managed)
    copied: list[str] = []
    conflicts: list[str] = []

    core_text = (MASTER_ROOT / "blueprints" / "CORE.md").read_text(encoding="utf-8")
    install_managed_text(
        target=target, rel=".ai/CORE.md", text=core_text, refresh=args.refresh_blueprints,
        previous_managed=previous_managed, current_managed=current_managed,
        copied=copied, conflicts=conflicts,
    )

    handoff_dst = target / ".ai" / "HANDOFF.md"
    if not handoff_dst.exists():
        handoff_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MASTER_ROOT / "blueprints" / "HANDOFF.md", handoff_dst)
        copied.append(".ai/HANDOFF.md")

    for mode in modes:
        rel = f".ai/modes/{mode}.md"
        text = (MASTER_ROOT / "blueprints" / "modes" / f"{mode}.md").read_text(encoding="utf-8")
        install_managed_text(
            target=target, rel=rel, text=text, refresh=args.refresh_blueprints,
            previous_managed=previous_managed, current_managed=current_managed,
            copied=copied, conflicts=conflicts,
        )

    adapter_template = (MASTER_ROOT / manifest["adapter_template"]).read_text(encoding="utf-8")
    seen_adapter_paths: set[str] = set()
    for key in agent_keys:
        adapter_name = manifest["agents"][key]["adapter"]
        if adapter_name in seen_adapter_paths:
            continue
        seen_adapter_paths.add(adapter_name)
        install_managed_text(
            target=target, rel=adapter_name, text=adapter_template, refresh=args.refresh_blueprints,
            previous_managed=previous_managed, current_managed=current_managed,
            copied=copied, conflicts=conflicts,
        )

    context = target / ".ai" / "PROJECT_CONTEXT.md"
    if not context.exists():
        text = (MASTER_ROOT / "templates" / "PROJECT_CONTEXT_TEMPLATE.md").read_text(encoding="utf-8")
        text = text.replace("<TITLE>", args.title or previous.get("project_title") or target.name, 1)
        atomic_write(context, text)
        copied.append(".ai/PROJECT_CONTEXT.md")

    session = target / ".ai" / "SESSION.md"
    if not session.exists() or args.reset_session:
        atomic_write(session, render_session(primary, active_agent))
        copied.append(".ai/SESSION.md")

    (target / ".ai" / "handoffs").mkdir(parents=True, exist_ok=True)
    (target / ".ai" / "scratch").mkdir(parents=True, exist_ok=True)
    (target / ".ai" / "runtime").mkdir(parents=True, exist_ok=True)

    made_dirs = made_files = 0
    for mode in modes:
        d, f = scaffold_mode(target, mode, manifest)
        made_dirs += d
        made_files += f

    append_gitignore(target)

    installed_modes = list(dict.fromkeys(previous.get("installed_modes", []) + modes))
    installed_agents = list(dict.fromkeys(previous.get("installed_agents", []) + agent_keys))
    deployment = {
        "schema_version": manifest["schema_version"],
        "library_version": manifest.get("library_version"),
        "project_type": project_type,
        "project_title": args.title or previous.get("project_title") or target.name,
        "primary_mode": primary,
        "installed_modes": installed_modes,
        "installed_agents": installed_agents,
        "managed_files": current_managed,
        "source_library": str(MASTER_ROOT),
        "source_manifest_sha256": sha256_file(MANIFEST_PATH),
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    atomic_write(marker, json.dumps(deployment, indent=2) + "\n")

    if args.git_init and not (target / ".git").exists():
        subprocess.run(["git", "init"], cwd=target, check=False)

    print(f"Physics AI project deployed: {target}")
    print(f"Project type: {project_type}")
    print(f"Primary mode: {primary}")
    print("Installed modes: " + ", ".join(installed_modes))
    print("Installed agents: " + ", ".join(manifest["agents"][k]["label"] for k in installed_agents))
    print(f"Managed/context files created or refreshed: {len(copied)}")
    print(f"Mode scaffold: {made_dirs} directories, {made_files} files created")
    if conflicts:
        print("Refresh preserved locally modified managed files. New master copies were written beside them:")
        for item in conflicts:
            print(f"  - {item}")
        print("Review and merge the *.new files manually; nothing customized was overwritten.")
    print("Next: fill .ai/PROJECT_CONTEXT.md and set the current objective in .ai/SESSION.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
