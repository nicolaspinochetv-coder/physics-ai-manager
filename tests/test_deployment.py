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

    def test_single_agent_has_no_shared_agents_note(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "solo"
            deploy_project(
                DeploymentRequest(
                    path=path,
                    title="Solo",
                    project_type="research",
                    agents=["claude"],
                    modes=["RESEARCH"],
                    primary_mode="RESEARCH",
                    git_init=False,
                ),
                LIBRARY,
            )
            self.assertNotIn("Shared AI environments", (path / "CLAUDE.md").read_text())

    def test_adding_agent_declares_shared_agents_in_new_bootstrap_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "grows"
            deploy_project(
                DeploymentRequest(
                    path=path,
                    title="Grows",
                    project_type="research",
                    agents=["claude", "codex"],
                    modes=["RESEARCH"],
                    primary_mode="RESEARCH",
                    git_init=False,
                ),
                LIBRARY,
            )
            claude_text = (path / "CLAUDE.md").read_text()
            self.assertIn("Shared AI environments", claude_text)
            self.assertIn("Claude Code, Codex", claude_text)

            # Adding a third agent later, without an explicit refresh, updates the
            # newly created bootstrap file immediately...
            result = deploy_project(
                DeploymentRequest(
                    path=path,
                    title="Grows",
                    project_type="research",
                    agents=["gemini"],
                    modes=[],
                    git_init=False,
                    existing_project=True,
                ),
                LIBRARY,
            )
            self.assertEqual(result.installed_agents, ["claude", "codex", "gemini"])
            gemini_text = (path / "GEMINI.md").read_text()
            self.assertIn("Claude Code, Codex, Gemini Code Assist", gemini_text)

            # ...while the previously-deployed CLAUDE.md is left untouched, consistent
            # with how every other managed file behaves without an explicit refresh.
            self.assertIn("Claude Code, Codex.", (path / "CLAUDE.md").read_text())

            # Explicitly refreshing managed blueprints brings CLAUDE.md up to date too.
            deploy_project(
                DeploymentRequest(
                    path=path,
                    title="Grows",
                    project_type="research",
                    agents=[],
                    modes=[],
                    git_init=False,
                    existing_project=True,
                    refresh_blueprints=True,
                ),
                LIBRARY,
            )
            self.assertIn("Claude Code, Codex, Gemini Code Assist", (path / "CLAUDE.md").read_text())

    def test_import_documents_dedup_and_collision(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "docs-project"
            sources = root / "sources"
            sources.mkdir()
            paper1 = sources / "paper1.pdf"
            paper1.write_text("content A")

            result = deploy_project(
                DeploymentRequest(
                    path=path,
                    title="Docs",
                    project_type="research",
                    agents=["claude"],
                    modes=["RESEARCH"],
                    primary_mode="RESEARCH",
                    git_init=False,
                    import_documents=[paper1],
                ),
                LIBRARY,
            )
            self.assertEqual(result.imported_documents, ["documents/paper1.pdf"])
            self.assertTrue((path / "documents" / "README.md").is_file())

            # Same content, same name -> idempotent no-op (not a duplicate copy).
            result2 = deploy_project(
                DeploymentRequest(
                    path=path,
                    title="Docs",
                    project_type="research",
                    agents=["claude"],
                    modes=[],
                    git_init=False,
                    existing_project=True,
                    import_documents=[paper1],
                ),
                LIBRARY,
            )
            self.assertEqual(result2.imported_documents, [])
            self.assertIn("paper1.pdf (already imported)", result2.skipped_documents)

            # Same filename, different content -> kept alongside under a new name.
            other_dir = root / "sources2"
            other_dir.mkdir()
            (other_dir / "paper1.pdf").write_text("content B, different from paper1.pdf")
            result3 = deploy_project(
                DeploymentRequest(
                    path=path,
                    title="Docs",
                    project_type="research",
                    agents=["claude"],
                    modes=[],
                    git_init=False,
                    existing_project=True,
                    import_documents=[other_dir / "paper1.pdf"],
                ),
                LIBRARY,
            )
            self.assertEqual(result3.imported_documents, ["documents/paper1 (2).pdf"])
            self.assertEqual(
                (path / "documents" / "paper1 (2).pdf").read_text(), "content B, different from paper1.pdf"
            )

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
