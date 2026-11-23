#!/usr/bin/env python3
"""tests/mcp_servers/git/test_git_approval_independence.py

ADR-012 INV-04: the Git MCP write-validation path neither assumes nor requires
Agent-side approval state. Stage 3 decides from the operation destination and the
protected-branch configuration alone, and the package holds no Agent import or
approval identifier.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import git
import pytest
from mcp_servers.git.repository_state import RepositoryState
from mcp_servers.git.write_protection_pipeline import WriteProtectionPipeline

_PKG = Path(__file__).resolve().parents[3] / "scripts" / "mcp_servers" / "git"
_APPROVAL_MARKERS = ("approv", "grant", "plan_mode")

PROTECTED = "main"


@pytest.fixture()
def working_repo(tmp_path: Path) -> str:
    """Create a working git repo with one commit on main."""
    repo_dir = tmp_path / "working_repo"
    repo_dir.mkdir()
    repo = git.Repo.init(str(repo_dir))
    repo.git.branch("-M", PROTECTED)
    f = repo_dir / "README.md"
    f.write_text("# test")
    repo.index.add([str(f)])
    repo.index.commit("initial")
    return str(repo_dir)


class TestStageThreeWithoutApprovalState:
    """The decision comes from the destination and the protected configuration only."""

    def test_protected_branch_denied_with_no_approval_state(
        self, working_repo: str
    ) -> None:
        state = RepositoryState.snapshot(working_repo)
        allowed, reason = state.verify_authorization(
            "git_checkout", PROTECTED, [PROTECTED]
        )
        assert allowed is False
        assert "protected branch" in reason

        pipeline = WriteProtectionPipeline(state)
        result = pipeline.run(
            "git_checkout",
            lambda: "",
            requested_branch=PROTECTED,
            protected_branches=[PROTECTED],
        )
        assert result.ok is False
        assert result.rejected_at_stage == "Stage 3"

    def test_non_protected_branch_allowed_with_no_approval_state(
        self, working_repo: str
    ) -> None:
        state = RepositoryState.snapshot(working_repo)
        allowed, reason = state.verify_authorization(
            "git_checkout", "feature", [PROTECTED]
        )
        assert allowed is True
        assert reason == ""

        pipeline = WriteProtectionPipeline(state)
        result = pipeline.run(
            "git_checkout",
            lambda: "",
            dry_run=True,
            requested_branch="feature",
            protected_branches=[PROTECTED],
        )
        assert result.ok is True
        assert result.rejected_at_stage is None

    def test_approval_shaped_input_cannot_reach_the_decision(
        self, working_repo: str
    ) -> None:
        """An approval-shaped value bound in the caller's scope cannot change Stage 3:
        the pipeline takes no such parameter, so the decision is identical to the
        no-approval call."""
        state = RepositoryState.snapshot(working_repo)
        pipeline = WriteProtectionPipeline(state)

        params = inspect.signature(pipeline.run).parameters
        assert not [
            name for name in params if any(m in name for m in _APPROVAL_MARKERS)
        ]

        # The decision is the same as the plain call: the Agent-side state cannot reach
        # Stage 3 because no parameter carries it.
        denied = pipeline.run(
            "git_checkout",
            lambda: "",
            requested_branch=PROTECTED,
            protected_branches=[PROTECTED],
        )
        assert denied.rejected_at_stage == "Stage 3"

    def test_protected_config_is_not_read_from_the_agent_config(
        self, working_repo: str
    ) -> None:
        """With no protected branches configured the same destination is allowed, so the
        denial above came from the argument, not from an Agent-side store."""
        state = RepositoryState.snapshot(working_repo)
        allowed, _ = state.verify_authorization("git_checkout", PROTECTED, None)
        assert allowed is True


class TestGitPackageHasNoApprovalDependency:
    @pytest.mark.repo_scan
    def test_git_package_never_references_agent_or_approval_state(self) -> None:
        """Scan the package: no Agent import, and no identifier named with an approval
        marker in a function, argument, or attribute."""
        files = sorted(p for p in _PKG.glob("*.py") if p.is_file())
        assert len(files) > 0, f"no package files found under {_PKG}"
        findings: list[str] = []
        for path in files:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    names = []
                if any(name == "agent" or name.startswith("agent.") for name in names):
                    findings.append(f"{path.name}: imports {sorted(names)}")
                for identifier in _identifiers(node):
                    if any(marker in identifier for marker in _APPROVAL_MARKERS):
                        findings.append(f"{path.name}: {identifier}")
        assert not findings, "; ".join(findings)
        assert len(files) >= 11, "the scan must cover the whole package"


def _identifiers(node: ast.AST) -> list[str]:
    """Names a function definition, an argument, or an attribute access declares."""
    if isinstance(node, ast.FunctionDef):
        return [node.name] + [arg.arg for arg in node.args.args]
    if isinstance(node, ast.Attribute):
        return [node.attr]
    return []
