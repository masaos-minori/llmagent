#!/usr/bin/env python3
"""mcp_servers/cicd/service_github_actions_composite.py

GitHubActionsCompositeBackend: composite of workflow and job backends.

Dependency direction: service_github_actions_composite → service_github_actions, service_github_actions_job, service_defs
Import from here:  from mcp_servers.cicd.service_github_actions_composite import GitHubActionsCompositeBackend
"""

from __future__ import annotations

import httpx

from .service_defs import CiBackend


class GitHubActionsCompositeBackend(CiBackend):
    """Composite backend combining GitHubActionsBackend and GitHubActionsJobBackend."""

    def __init__(
        self,
        github_token: str,
        http: httpx.AsyncClient,
        max_log_size_kb: int = 256,
    ) -> None:
        from .service_github_actions import GitHubActionsBackend  # noqa: PLC0415
        from .service_github_actions_job import (  # noqa: PLC0415
            GitHubActionsJobBackend,
        )

        self._workflow = GitHubActionsBackend(
            github_token=github_token,
            http=http,
        )
        self._job = GitHubActionsJobBackend(
            github_token=github_token,
            http=http,
            max_log_size_kb=max_log_size_kb,
        )

    @staticmethod
    def _split_repo(repo: str) -> tuple[str, str]:
        """Split 'owner/repo' slug into (owner, repo)."""
        from .service_github_actions import GitHubActionsBackend  # noqa: PLC0415

        return GitHubActionsBackend._split_repo(repo)

    async def trigger_workflow(
        self,
        owner: str,
        repo: str,
        workflow: str,
        ref: str,
        inputs: dict[str, str],
    ) -> str:
        return await self._workflow.trigger_workflow(owner, repo, workflow, ref, inputs)

    async def get_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow: str,
        limit: int,
    ) -> str:
        return await self._workflow.get_workflow_runs(owner, repo, workflow, limit)

    async def get_workflow_status(self, owner: str, repo: str, run_id: int) -> str:
        return await self._workflow.get_workflow_status(owner, repo, run_id)

    async def get_workflow_logs(self, owner: str, repo: str, run_id: int) -> str:
        return await self._job.get_workflow_logs(owner, repo, run_id)
