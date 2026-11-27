#!/usr/bin/env python3
"""scripts/mcp_servers/cicd/cicd_service_business.py

CiCdService: dispatch handlers with allowlist guards, assembled from domain modules.

Each handler canonicalizes the request identifiers at entry, before the guard and the
backend call, so the guard comparison and the URL see the same canonical value (REQ-005).
A form the canonicalizer rejects is denied as the guard denies it, so the observable
authorization behavior is unchanged.

Dependency direction: service_business → service_guards, service_github_actions
Import from here:  from mcp_servers.cicd.cicd_service_business import CiCdService, GitHubActionsBackend
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import asdict

from shared.json_utils import dumps as _json_dumps

from mcp_servers.cicd.cicd_models import (
    CicdAuthorizationError,
    CicdConfig,
    CicdUpstreamError,
    CicdValidationError,
    LogFetchResult,
    canonical_repo_key,
    canonical_workflow_id,
)
from mcp_servers.cicd.cicd_service_defs import CiBackend
from mcp_servers.server import ToolArgs

from .cicd_service_guards import CiCdGuards

logger = logging.getLogger(__name__)


def _canonical_or_denied(value: str, canonicalizer: Callable[[str], str]) -> str:
    """Return the canonical form of a request value, denying a form it rejects.

    The guard's denial policy is the observable behavior for a tool call, so a value the
    canonicalizer rejects stays an authorization error here too. The returned value is the
    one both the guard and the backend use, so the two cannot diverge (REQ-005).
    """
    try:
        return canonicalizer(value)
    except CicdValidationError as exc:
        raise CicdAuthorizationError(str(exc)) from exc


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
            from .cicd_service_github_actions_composite import (
                GitHubActionsCompositeBackend,
            )

            return GitHubActionsCompositeBackend._split_repo(repo)
        except ValueError as e:
            from mcp_servers.cicd.cicd_models import (
                CicdValidationError,
            )

            raise CicdValidationError(str(e)) from e

    def _validate_and_parse_repo(self, repo: str) -> tuple[str, str]:
        """Canonicalize the slug, validate repo is allowed, and parse into (owner, repo)."""
        key = _canonical_or_denied(repo, canonical_repo_key)
        self._assert_allowed_repo(key)
        return self._parse_repo(key)

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
        repo_key = _canonical_or_denied(req.repo, canonical_repo_key)
        workflow = _canonical_or_denied(req.workflow, canonical_workflow_id)
        self._assert_allowed_repo(repo_key)
        self._assert_allowed_workflow(workflow)
        if req.dry_run:
            preview = f"Would trigger workflow '{workflow}' on ref '{req.ref}' in repo '{repo_key}'"
            if req.inputs:
                # REQ-006: keys and count only; input values never enter the preview.
                keys = ", ".join(sorted(req.inputs))
                preview += f" with inputs [{len(req.inputs)}]: {keys}"
            dry_run_result: str = _json_dumps({"preview": preview, "dry_run": True})
            return dry_run_result
        owner, repo = self._parse_repo(repo_key)
        outcome = await self._backend.trigger_workflow(
            owner, repo, workflow, req.ref, req.inputs
        )
        # The handler contract stays `-> str`: the structured outcome is JSON-serialized
        # here, so dispatch_tool and the audit outcome mapping are unchanged.
        return _json_dumps(
            {
                "state": outcome.state,
                "run_id": outcome.run_id,
                "run_url": outcome.run_url,
                "run_status": outcome.run_status,
                "workflow": outcome.workflow,
                "ref": outcome.ref,
            }
        )

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
        logs_result: LogFetchResult = await self._backend.get_workflow_logs(
            owner, repo, req.run_id
        )
        # REQ-004: total failure is a tool error, not a successful result with an
        # empty output. The decision is from the per-job statuses, never from text.
        if logs_result.jobs and all(job.status == "failed" for job in logs_result.jobs):
            raise CicdUpstreamError(
                f"get_workflow_logs: every job failed for {owner}/{repo} run={req.run_id}"
            )
        # The handler contract stays `-> str`: the structured result is JSON-serialized
        # here, so dispatch_tool and the audit outcome mapping are unchanged.
        return _json_dumps(asdict(logs_result))

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
