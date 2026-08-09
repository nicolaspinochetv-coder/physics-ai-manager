from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable


class DeploymentError(RuntimeError):
    pass


@dataclass
class DeploymentRequest:
    path: Path
    title: str
    project_type: str
    agents: list[str]
    modes: list[str] = field(default_factory=list)
    primary_mode: str | None = None
    objective: str = ""
    git_init: bool = True
    existing_project: bool = False
    refresh_blueprints: bool = False
    reset_session: bool = False


@dataclass
class DeploymentResult:
    path: Path
    project_type: str
    primary_mode: str
    installed_modes: list[str]
    installed_agents: list[str]
    copied: list[str]
    conflicts: list[str]
    notes: list[str]
    git_initialized: bool


@dataclass
class ProjectInfo:
    path: Path
    title: str
    project_type: str
    primary_mode: str
    modes: list[str]
    agents: list[str]
    library_version: str | None
    updated_at: str | None


def load_manifest(library_root: Path) -> dict:
    path = library_root / "MASTER_MANIFEST.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DeploymentError(f"Missing manifest: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DeploymentError(f"Invalid manifest JSON: {path}: {exc}") from exc
    return data


def slugify(title: str) -> str:
    value = title.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "physics-project"


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


def _install_managed_text(
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


def _append_gitignore(target: Path, library_root: Path) -> None:
    snippet_path = library_root / "templates" / "gitignore_snippet.txt"
    if not snippet_path.exists():
        return
    snippet = snippet_path.read_text(encoding="utf-8").strip().splitlines()
    path = target / ".gitignore"
    existing_lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    existing = {line.strip() for line in existing_lines}
    missing = [line for line in snippet if line.strip() and line.strip() not in existing]
    if not missing:
        return
    text = "\n".join(existing_lines).rstrip()
    if text:
        text += "\n\n"
    text += "\n".join(missing) + "\n"
    atomic_write(path, text)


def _render_session(primary_mode: str, active_agent: str, objective: str = "") -> str:
    objective_value = objective.strip() or "<single concrete objective>"
    return (
        "# Session\n\n"
        f"- Active mode: {primary_mode}\n"
        f"- Objective: {objective_value}\n"
        "- Scope: <what to work on now>\n"
        "- Deliverable: <what should exist when done>\n"
        f"- Active agent: {active_agent}\n"
        "- Constraints: <optional>\n"
        "- Related files: <optional>\n"
    )


def _render_project_context(template: str, title: str, objective: str) -> str:
    text = template.replace("<TITLE>", title, 1)
    if objective.strip():
        marker = "<What is the project trying to understand or calculate?>"
        text = text.replace(marker, objective.strip(), 1)
    return text


def _scaffold_mode(target: Path, mode: str, manifest: dict, library_root: Path) -> tuple[int, int]:
    spec = manifest["mode_scaffolds"][mode]
    made_dirs = 0
    made_files = 0
    for rel in spec.get("dirs", []):
        path = target / rel
        if not path.exists():
            made_dirs += 1
        path.mkdir(parents=True, exist_ok=True)

    template_root = library_root / "templates" / "state"
    for rel, template_rel in spec.get("files", {}).items():
        dst = target / rel
        if dst.exists():
            continue
        src = template_root / template_rel
        if not src.is_file():
            raise DeploymentError(f"Missing scaffold template: {src}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        made_files += 1
    return made_dirs, made_files


def _adapter_paths(agent_spec: dict) -> list[str]:
    paths = agent_spec.get("adapter_paths")
    if paths:
        return list(paths)
    adapter = agent_spec.get("adapter")
    return [adapter] if adapter else []


def inspect_project(path: Path) -> ProjectInfo:
    target = Path(path).expanduser().resolve()
    marker = target / ".ai" / "DEPLOYMENT.json"
    if not marker.is_file():
        raise DeploymentError("This folder is not a managed Physics AI project (missing .ai/DEPLOYMENT.json).")
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DeploymentError("DEPLOYMENT.json is invalid JSON.") from exc
    return ProjectInfo(
        path=target,
        title=data.get("project_title", target.name),
        project_type=data.get("project_type", "unknown"),
        primary_mode=data.get("primary_mode", ""),
        modes=list(data.get("installed_modes", [])),
        agents=list(data.get("installed_agents", [])),
        library_version=data.get("library_version"),
        updated_at=data.get("updated_at"),
    )


def doctor_project(path: Path, library_root: Path) -> list[tuple[str, str]]:
    info = inspect_project(path)
    manifest = load_manifest(library_root)
    target = info.path
    checks: list[tuple[str, str]] = []

    required = [".ai/CORE.md", ".ai/PROJECT_CONTEXT.md", ".ai/SESSION.md", ".ai/HANDOFF.md", ".ai/DEPLOYMENT.json"]
    required += [f".ai/modes/{m}.md" for m in info.modes]
    for rel in required:
        checks.append(("ok" if (target / rel).exists() else "missing", rel))

    for agent in info.agents:
        spec = manifest.get("agents", {}).get(agent)
        if not spec:
            checks.append(("warning", f"Unknown agent recorded in deployment: {agent}"))
            continue
        for rel in _adapter_paths(spec):
            checks.append(("ok" if (target / rel).exists() else "missing", rel))

    for mode in info.modes:
        spec = manifest.get("mode_scaffolds", {}).get(mode, {})
        for rel in spec.get("files", {}):
            checks.append(("ok" if (target / rel).exists() else "missing", rel))

    marker = target / ".ai" / "DEPLOYMENT.json"
    try:
        deployment = json.loads(marker.read_text(encoding="utf-8"))
        managed = deployment.get("managed_files", {})
        if isinstance(managed, dict):
            for rel, meta in managed.items():
                path = target / rel
                baseline = meta.get("sha256") if isinstance(meta, dict) else None
                if path.exists() and baseline and sha256_file(path) != baseline:
                    checks.append(("modified", f"Locally modified managed file: {rel}"))
    except (OSError, json.JSONDecodeError):
        pass
    return checks


def deploy_project(request: DeploymentRequest, library_root: Path) -> DeploymentResult:
    manifest = load_manifest(library_root)
    valid_modes = set(manifest["mode_scaffolds"])
    target = Path(request.path).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    marker = target / ".ai" / "DEPLOYMENT.json"
    nonempty = any(target.iterdir())
    if nonempty and not marker.exists() and not request.existing_project:
        raise DeploymentError(
            "Destination is non-empty and is not already managed. Choose an empty/new folder, "
            "or explicitly allow adding Physics AI files to an existing project."
        )

    previous: dict = {}
    if marker.exists():
        try:
            previous = json.loads(marker.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            previous = {}

    project_type = request.project_type or previous.get("project_type")
    if project_type not in manifest["project_types"]:
        raise DeploymentError(f"Unsupported project type: {project_type}")
    project_spec = manifest["project_types"][project_type]

    modes: list[str] = []
    for mode in previous.get("installed_modes", []):
        if mode in valid_modes and mode not in modes:
            modes.append(mode)
    default_primary = project_spec.get("primary_mode")
    if default_primary and default_primary not in modes:
        modes.append(default_primary)
    for mode in request.modes:
        mode = mode.upper()
        if mode not in valid_modes:
            raise DeploymentError(f"Unsupported mode: {mode}")
        if mode not in modes:
            modes.append(mode)
    if project_type == "hybrid" and not modes:
        raise DeploymentError("Hybrid projects require at least one mode.")

    primary = request.primary_mode or previous.get("primary_mode") or default_primary or (modes[0] if modes else None)
    if not primary or primary not in valid_modes:
        raise DeploymentError("Could not determine a valid primary mode.")
    if primary not in modes:
        modes.insert(0, primary)

    requested_agents = request.agents or previous.get("installed_agents", [])
    if not requested_agents:
        raise DeploymentError("Select at least one AI environment.")
    agent_keys: list[str] = []
    for key in requested_agents:
        if key not in manifest["agents"]:
            raise DeploymentError(f"Unsupported agent: {key}")
        if key not in agent_keys:
            agent_keys.append(key)
    active_agent = manifest["agents"][agent_keys[0]]["label"]

    previous_managed = previous.get("managed_files", {}) if isinstance(previous.get("managed_files", {}), dict) else {}
    current_managed = dict(previous_managed)
    copied: list[str] = []
    conflicts: list[str] = []
    notes: list[str] = []

    core_text = (library_root / "blueprints" / "CORE.md").read_text(encoding="utf-8")
    _install_managed_text(
        target=target, rel=".ai/CORE.md", text=core_text, refresh=request.refresh_blueprints,
        previous_managed=previous_managed, current_managed=current_managed, copied=copied, conflicts=conflicts,
    )

    handoff_dst = target / ".ai" / "HANDOFF.md"
    if not handoff_dst.exists():
        handoff_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(library_root / "blueprints" / "HANDOFF.md", handoff_dst)
        copied.append(".ai/HANDOFF.md")

    for mode in modes:
        rel = f".ai/modes/{mode}.md"
        text = (library_root / "blueprints" / "modes" / f"{mode}.md").read_text(encoding="utf-8")
        _install_managed_text(
            target=target, rel=rel, text=text, refresh=request.refresh_blueprints,
            previous_managed=previous_managed, current_managed=current_managed, copied=copied, conflicts=conflicts,
        )

    adapter_template = (library_root / manifest["adapter_template"]).read_text(encoding="utf-8")
    seen_adapter_paths: set[str] = set()
    for key in agent_keys:
        spec = manifest["agents"][key]
        for adapter_path in _adapter_paths(spec):
            if adapter_path in seen_adapter_paths:
                continue
            seen_adapter_paths.add(adapter_path)
            _install_managed_text(
                target=target, rel=adapter_path, text=adapter_template, refresh=request.refresh_blueprints,
                previous_managed=previous_managed, current_managed=current_managed, copied=copied, conflicts=conflicts,
            )
        note = spec.get("post_create_note")
        if note and note not in notes:
            notes.append(note)

    context = target / ".ai" / "PROJECT_CONTEXT.md"
    if not context.exists():
        template = (library_root / "templates" / "PROJECT_CONTEXT_TEMPLATE.md").read_text(encoding="utf-8")
        atomic_write(context, _render_project_context(template, request.title or target.name, request.objective))
        copied.append(".ai/PROJECT_CONTEXT.md")

    session = target / ".ai" / "SESSION.md"
    if not session.exists() or request.reset_session:
        atomic_write(session, _render_session(primary, active_agent, request.objective))
        copied.append(".ai/SESSION.md")

    for rel in [".ai/handoffs", ".ai/scratch", ".ai/runtime"]:
        (target / rel).mkdir(parents=True, exist_ok=True)

    for mode in modes:
        _scaffold_mode(target, mode, manifest, library_root)
    _append_gitignore(target, library_root)

    installed_modes = list(dict.fromkeys(previous.get("installed_modes", []) + modes))
    installed_agents = list(dict.fromkeys(previous.get("installed_agents", []) + agent_keys))
    deployment = {
        "schema_version": manifest.get("schema_version", 1),
        "library_version": manifest.get("library_version"),
        "project_type": project_type,
        "project_title": request.title or previous.get("project_title") or target.name,
        "primary_mode": primary,
        "installed_modes": installed_modes,
        "installed_agents": installed_agents,
        "managed_files": current_managed,
        "source_library": str(library_root),
        "source_manifest_sha256": sha256_file(library_root / "MASTER_MANIFEST.json"),
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    atomic_write(marker, json.dumps(deployment, indent=2) + "\n")

    git_initialized = False
    if request.git_init and not (target / ".git").exists():
        try:
            proc = subprocess.run(["git", "init"], cwd=target, check=False, capture_output=True, text=True)
            git_initialized = proc.returncode == 0
            if proc.returncode != 0:
                notes.append("Git initialization was requested but `git init` did not succeed.")
        except FileNotFoundError:
            notes.append("Git initialization was requested, but Git was not found on PATH.")

    if conflicts:
        notes.append("Local blueprint edits were preserved; review the generated *.new files before merging updates.")

    return DeploymentResult(
        path=target,
        project_type=project_type,
        primary_mode=primary,
        installed_modes=installed_modes,
        installed_agents=installed_agents,
        copied=copied,
        conflicts=conflicts,
        notes=notes,
        git_initialized=git_initialized,
    )
