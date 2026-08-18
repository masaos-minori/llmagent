#!/usr/bin/env python3
"""scripts/mcp_servers/cicd/service_business.py

CiCdService: dispatch handlers with allowlist guards, assembled from domain modules.

Dependency direction: service_business → service_guards, service_github_actions
Import from here:  from mcp_servers.cicd.service_business import CiCdService, GitHubActionsBackend
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from shared.json_utils import dumps as _json_dumps

from mcp_servers.cicd.cicd_models import CicdConfig
from mcp_servers.cicd.service_defs import CiBackend
from mcp_servers.server import ToolArgs

from .service_guards import CiCdGuards

logger = logging.getLogger(__name__)


class CiCdService(CiCdGuards):
    """CiCdService: repo/workflow allowlist guards + dispatch handlers."""

    def __init__(self, cfg: CicdConfig, backend: CiBackend) -> None:
        """Initialize with CI/CD configuration and backend implementation."""
        super().__init__(backend, cfg.repo_allowlist, cfg.workflow_allowlist)

    @staticmethod
    def _parse_repo(repo: str) -> tuple[str, str]:
        """Split 'owner/repo' slug; raise CicdValidationError on bad format."""
        try:
            # Import here to avoid circular dependency
            from .service_github_actions_composite import (
                GitHubActionsCompositeBackend,
            )

            return GitHubActionsCompositeBackend._split_repo(repo)
        except ValueError as e:
            from mcp_servers.cicd.cicd_models import (
                CicdValidationError,
            )

            raise CicdValidationError(str(e)) from e

    def _validate_and_parse_repo(self, repo: str) -> tuple[str, str]:
        """Validate repo is allowed and parse into (owner, repo)."""
        self._assert_allowed_repo(repo)
        return self._parse_repo(repo)

    # ── Dispatch handlers ──────────────────────────────────────────────────────

    async def handle_trigger_workflow(self, args: ToolArgs) -> str:
        """Trigger a CI/CD workflow run with optional dry-run support."""
        from mcp_servers.cicd.cicd_models import TriggerWorkflowRequest

        req = TriggerWorkflowRequest(
            repo=args["repo"],
            workflow=args["workflow"],
            ref=args.get("ref", "main"),
            inputs=args.get("inputs", {}),
            dry_run=args.get("dry_run", False),
        )
        self._assert_allowed_repo(req.repo)
        self._assert_allowed_workflow(req.workflow)
        if req.dry_run:
            preview = f"Would trigger workflow '{req.workflow}' on ref '{req.ref}' in repo '{req.repo}'"
            if req.inputs:
                preview += f" with inputs={req.inputs}"
            dry_run_result: str = _json_dumps({"preview": preview, "dry_run": True})
            return dry_run_result
        owner, repo = self._parse_repo(req.repo)
        trigger_result: str = await self._backend.trigger_workflow(
            owner,
            repo,
            req.workflow,
            req.ref,
            req.inputs,
        )
        return trigger_result

    async def handle_get_workflow_runs(self, args: ToolArgs) -> str:
        """Retrieve the list of workflow runs for a given workflow."""
        from mcp_servers.cicd.cicd_models import GetWorkflowRunsRequest

        req = GetWorkflowRunsRequest(
            repo=args["repo"],
            workflow=args["workflow"],
            limit=args.get("limit", 10),
        )
        owner, repo = self._validate_and_parse_repo(req.repo)
        runs_result: str = await self._backend.get_workflow_runs(
            owner,
            repo,
            req.workflow,
            req.limit,
        )
        return runs_result

    async def handle_get_workflow_status(self, args: ToolArgs) -> str:
        """Get the status of a specific workflow run."""
        from mcp_servers.cicd.cicd_models import (
            GetWorkflowStatusRequest,
        )

        req = GetWorkflowStatusRequest(
            repo=args["repo"],
            run_id=args["run_id"],
        )
        owner, repo = self._validate_and_parse_repo(req.repo)
        status_result: str = await self._backend.get_workflow_status(
            owner, repo, req.run_id
        )
        return status_result

    async def handle_get_workflow_logs(self, args: ToolArgs) -> str:
        """Retrieve the logs for a specific workflow run."""
        from mcp_servers.cicd.cicd_models import GetWorkflowLogsRequest

        req = GetWorkflowLogsRequest(
            repo=args["repo"],
            run_id=args["run_id"],
        )
        owner, repo = self._validate_and_parse_repo(req.repo)
        logs_result: str = await self._backend.get_workflow_logs(
            owner, repo, req.run_id
        )
        return logs_result

    def get_dispatch_table(
        self,
    ) -> dict[str, Callable[[ToolArgs], Awaitable[str]]]:
        """Return the mapping of tool names to their handler methods."""
        return {
            "trigger_workflow": self.handle_trigger_workflow,
            "get_workflow_runs": self.handle_get_workflow_runs,
            "get_workflow_status": self.handle_get_workflow_status,
            "get_workflow_logs": self.handle_get_workflow_logs,
        }
