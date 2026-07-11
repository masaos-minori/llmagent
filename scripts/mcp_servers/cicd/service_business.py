#!/usr/bin/env python3
"""mcp_servers/cicd/service_business.py

CiCdService: dispatch handlers with allowlist guards, assembled from domain modules.

Dependency direction: service_business → service_guards, service_github_actions
Import from here:  from mcp_servers.cicd.service_business import CiCdService, GitHubActionsBackend
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from mcp_servers.cicd.models import CicdConfig
from mcp_servers.cicd.service_defs import CiBackend
from mcp_servers.server import ToolArgs
from shared.json_utils import dumps as _json_dumps

from .service_guards import CiCdGuards

logger = logging.getLogger(__name__)


class CiCdService(CiCdGuards):
    """CiCdService: repo/workflow allowlist guards + dispatch handlers."""

    def __init__(self, cfg: CicdConfig, backend: CiBackend) -> None:
        super().__init__(backend, cfg.repo_allowlist, cfg.workflow_allowlist)

    @staticmethod
    def _parse_repo(repo: str) -> tuple[str, str]:
        """Split 'owner/repo' slug; raise CicdValidationError on bad format."""
        try:
            # Import here to avoid circular dependency
            from .service_github_actions_composite import (  # noqa: PLC0415
                GitHubActionsCompositeBackend,
            )

            return GitHubActionsCompositeBackend._split_repo(repo)
        except ValueError as e:
            from mcp_servers.cicd.models import CicdValidationError  # noqa: PLC0415

            raise CicdValidationError(str(e)) from e

    def _validate_and_parse_repo(self, repo: str) -> tuple[str, str]:
        """Validate repo is allowed and parse into (owner, repo)."""
        self._assert_allowed_repo(repo)
        return self._parse_repo(repo)

    # ── Dispatch handlers ──────────────────────────────────────────────────────

    async def handle_trigger_workflow(self, args: ToolArgs) -> str:
        from mcp_servers.cicd.models import TriggerWorkflowRequest  # noqa: PLC0415

        req = TriggerWorkflowRequest(**args)
        self._assert_allowed_repo(req.repo)
        self._assert_allowed_workflow(req.workflow)
        if req.dry_run:
            preview = (
                f"Would trigger workflow '{req.workflow}' on ref '{req.ref}'"
                f" in repo '{req.repo}'"
            )
            if req.inputs:
                preview += f" with inputs={req.inputs}"
            result: str = _json_dumps({"preview": preview, "dry_run": True})
            return result
        owner, repo = self._parse_repo(req.repo)
        result2: str = await self._backend.trigger_workflow(
            owner,
            repo,
            req.workflow,
            req.ref,
            req.inputs,
        )
        return result2

    async def handle_get_workflow_runs(self, args: ToolArgs) -> str:
        from mcp_servers.cicd.models import GetWorkflowRunsRequest  # noqa: PLC0415

        req = GetWorkflowRunsRequest(**args)
        owner, repo = self._validate_and_parse_repo(req.repo)
        result3: str = await self._backend.get_workflow_runs(
            owner,
            repo,
            req.workflow,
            req.limit,
        )
        return result3

    async def handle_get_workflow_status(self, args: ToolArgs) -> str:
        from mcp_servers.cicd.models import GetWorkflowStatusRequest  # noqa: PLC0415

        req = GetWorkflowStatusRequest(**args)
        owner, repo = self._validate_and_parse_repo(req.repo)
        result4: str = await self._backend.get_workflow_status(owner, repo, req.run_id)
        return result4

    async def handle_get_workflow_logs(self, args: ToolArgs) -> str:
        from mcp_servers.cicd.models import GetWorkflowLogsRequest  # noqa: PLC0415

        req = GetWorkflowLogsRequest(**args)
        owner, repo = self._validate_and_parse_repo(req.repo)
        result5: str = await self._backend.get_workflow_logs(owner, repo, req.run_id)
        return result5

    def get_dispatch_table(
        self,
    ) -> dict[str, Callable[[ToolArgs], Awaitable[str]]]:
        return {
            "trigger_workflow": self.handle_trigger_workflow,
            "get_workflow_runs": self.handle_get_workflow_runs,
            "get_workflow_status": self.handle_get_workflow_status,
            "get_workflow_logs": self.handle_get_workflow_logs,
        }
