from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from physai.deployment import DeploymentRequest, deploy_project, doctor_project, inspect_project, load_manifest

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "library"


class DeploymentTests(unittest.TestCase):
    def test_research_claude(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test-project"
            result = deploy_project(
                DeploymentRequest(
                    path=path,
                    title="Test Research",
                    project_type="research",
                    agents=["claude"],
                    modes=["RESEARCH"],
                    primary_mode="RESEARCH",
                    objective="Study a test physics question.",
                    git_init=False,
                ),
                LIBRARY,
            )
            self.assertTrue((path / "CLAUDE.md").is_file())
            self.assertTrue((path / "research" / "research_notes.md").is_file())
            self.assertIn("Study a test physics question.", (path / ".ai" / "PROJECT_CONTEXT.md").read_text())
            self.assertEqual(result.primary_mode, "RESEARCH")

    def test_antigravity_adapter(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ag-project"
            deploy_project(
                DeploymentRequest(
                    path=path,
                    title="Antigravity Project",
                    project_type="coding",
                    agents=["antigravity"],
                    modes=["CODING"],
                    primary_mode="CODING",
                    git_init=False,
                ),
                LIBRARY,
            )
            self.assertTrue((path / ".agents" / "rules" / "physics-ai.md").is_file())
            self.assertFalse((path / "GEMINI.md").exists())

    def test_codex_opencode_share_agents_md(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "multi-project"
            deploy_project(
                DeploymentRequest(
                    path=path,
                    title="Multi",
                    project_type="research",
                    agents=["codex", "opencode"],
                    modes=["RESEARCH"],
                    primary_mode="RESEARCH",
                    git_init=False,
                ),
                LIBRARY,
            )
            self.assertTrue((path / "AGENTS.md").is_file())
            info = inspect_project(path)
            self.assertEqual(info.agents, ["codex", "opencode"])

    def test_hybrid_and_doctor(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "hybrid"
            deploy_project(
                DeploymentRequest(
                    path=path,
                    title="Hybrid",
                    project_type="hybrid",
                    agents=["claude", "codex"],
                    modes=["RESEARCH", "CODING", "WRITING"],
                    primary_mode="RESEARCH",
                    git_init=False,
                ),
                LIBRARY,
            )
            checks = doctor_project(path, LIBRARY)
            self.assertFalse([item for status, item in checks if status == "missing"])

    def test_refresh_preserves_local_edit(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "refresh"
            request = DeploymentRequest(
                path=path,
                title="Refresh",
                project_type="research",
                agents=["claude"],
                modes=["RESEARCH"],
                primary_mode="RESEARCH",
                git_init=False,
            )
            deploy_project(request, LIBRARY)
            core = path / ".ai" / "CORE.md"
            core.write_text(core.read_text() + "\nLOCAL CUSTOMIZATION\n")
            request.existing_project = True
            request.refresh_blueprints = True
            result = deploy_project(request, LIBRARY)
            self.assertTrue((path / ".ai" / "CORE.md.new").is_file())
            self.assertTrue(result.conflicts)


if __name__ == "__main__":
    unittest.main()
