"""tests/mcp_servers/cicd/test_service_github_actions_composite.py

Characterization tests for GitHubActionsCompositeBackend (composite of
GitHubActionsBackend and GitHubActionsJobBackend).

Locks: constructor wiring (both sub-backends built with the given credentials),
_split_repo delegation to GitHubActionsBackend, and delegation-ordering/routing
of the four CiBackend Protocol methods (which sub-backend each is forwarded to).
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest
from mcp_servers.cicd.service_github_actions import GitHubActionsBackend
from mcp_servers.cicd.service_github_actions_composite import (
    GitHubActionsCompositeBackend,
)
from mcp_servers.cicd.service_github_actions_job import GitHubActionsJobBackend

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _make_composite(
    max_log_size_kb: int = 256,
) -> GitHubActionsCompositeBackend:
    http = httpx.AsyncClient(timeout=1.0)
    return GitHubActionsCompositeBackend(
        github_token="tok-123",
        http=http,
        max_log_size_kb=max_log_size_kb,
    )


# ──────────────────────────────────────────────────────────────────────────────
# __init__ — sub-backend construction
# ──────────────────────────────────────────────────────────────────────────────


class TestInit:
    def test_builds_workflow_and_job_sub_backends(self) -> None:
        composite = _make_composite()
        assert isinstance(composite._workflow, GitHubActionsBackend)
        assert isinstance(composite._job, GitHubActionsJobBackend)

    def test_default_max_log_size_kb_is_256(self) -> None:
        # Exercise GitHubActionsCompositeBackend's own default directly (not
        # the test helper's default) to characterize the __init__ signature.
        http = httpx.AsyncClient(timeout=1.0)
        composite = GitHubActionsCompositeBackend(github_token="tok-123", http=http)
        # GitHubActionsJobBackend does not expose max_log_size_kb publicly;
        # verify indirectly via repr/attr access on the private attribute.
        assert composite._job._max_log_size_kb == 256  # noqa: SLF001 — characterization test, internal wiring check

    def test_custom_max_log_size_kb_is_passed_through(self) -> None:
        composite = _make_composite(max_log_size_kb=64)
        assert composite._job._max_log_size_kb == 64  # noqa: SLF001 — characterization test, internal wiring check

    def test_github_token_passed_to_both_sub_backends(self) -> None:
        composite = _make_composite()
        assert composite._workflow._token == "tok-123"  # noqa: SLF001 — characterization test, internal wiring check
        assert composite._job._token == "tok-123"  # noqa: SLF001 — characterization test, internal wiring check


# ──────────────────────────────────────────────────────────────────────────────
# _split_repo — delegation to GitHubActionsBackend
# ──────────────────────────────────────────────────────────────────────────────


class TestSplitRepo:
    def test_valid_slug_splits_into_owner_and_repo(self) -> None:
        assert GitHubActionsCompositeBackend._split_repo("myorg/myrepo") == (
            "myorg",
            "myrepo",
        )

    def test_invalid_slug_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid repo slug"):
            GitHubActionsCompositeBackend._split_repo("nodash")


# ──────────────────────────────────────────────────────────────────────────────
# Delegation routing — workflow methods forward to self._workflow
# ──────────────────────────────────────────────────────────────────────────────


class TestDelegationRouting:
    @pytest.mark.asyncio
    async def test_trigger_workflow_delegates_to_workflow_backend(self) -> None:
        composite = _make_composite()
        composite._workflow = AsyncMock()
        composite._workflow.trigger_workflow.return_value = "dispatched"
        composite._job = AsyncMock()

        result = await composite.trigger_workflow(
            "owner", "repo", "ci.yml", "main", {"k": "v"}
        )

        assert result == "dispatched"
        composite._workflow.trigger_workflow.assert_awaited_once_with(
            "owner", "repo", "ci.yml", "main", {"k": "v"}
        )
        composite._job.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_workflow_runs_delegates_to_workflow_backend(self) -> None:
        composite = _make_composite()
        composite._workflow = AsyncMock()
        composite._workflow.get_workflow_runs.return_value = '{"runs": []}'
        composite._job = AsyncMock()

        result = await composite.get_workflow_runs("owner", "repo", "ci.yml", 10)

        assert result == '{"runs": []}'
        composite._workflow.get_workflow_runs.assert_awaited_once_with(
            "owner", "repo", "ci.yml", 10
        )
        composite._job.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_workflow_status_delegates_to_workflow_backend(self) -> None:
        composite = _make_composite()
        composite._workflow = AsyncMock()
        composite._workflow.get_workflow_status.return_value = '{"id": 1}'
        composite._job = AsyncMock()

        result = await composite.get_workflow_status("owner", "repo", 123)

        assert result == '{"id": 1}'
        composite._workflow.get_workflow_status.assert_awaited_once_with(
            "owner", "repo", 123
        )
        composite._job.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_workflow_logs_delegates_to_job_backend_not_workflow(
        self,
    ) -> None:
        composite = _make_composite()
        composite._workflow = AsyncMock()
        composite._job = AsyncMock()
        composite._job.get_workflow_logs.return_value = "=== Job: build ==="

        result = await composite.get_workflow_logs("owner", "repo", 456)

        assert result == "=== Job: build ==="
        composite._job.get_workflow_logs.assert_awaited_once_with("owner", "repo", 456)
        composite._workflow.assert_not_called()
