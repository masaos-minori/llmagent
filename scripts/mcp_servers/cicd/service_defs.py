#!/usr/bin/env python3
"""mcp_servers/cicd/service_defs.py

Constants and CiBackend protocol for cicd-mcp.

Extracted to break circular dependency between service_init and service_business.
"""

from __future__ import annotations

from typing import Protocol

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

GITHUB_REPO_PARTS_COUNT = 2

_GITHUB_API_BASE = "https://api.github.com"
# GitHub Actions REST API version header
_GH_API_VERSION = "2022-11-28"
# Maximum number of jobs to fetch logs for in a single get_workflow_logs call
_MAX_JOBS_FOR_LOGS = 5


# ──────────────────────────────────────────────────────────────────────────────
# CiBackend protocol (extensible for future GitLab CI / Jenkins backends)
# ──────────────────────────────────────────────────────────────────────────────


class CiBackend(Protocol):
    """Protocol for CI/CD system backends.

    Implement this Protocol to add support for GitLab CI, Jenkins, etc.
    CiCdService delegates API calls to an injected CiBackend instance.
    """

    async def trigger_workflow(
        self,
        owner: str,
        repo: str,
        workflow: str,
        ref: str,
        inputs: dict[str, str],
    ) -> str: ...

    async def get_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow: str,
        limit: int,
    ) -> str: ...

    async def get_workflow_status(self, owner: str, repo: str, run_id: int) -> str: ...

    async def get_workflow_logs(self, owner: str, repo: str, run_id: int) -> str: ...


def build_auth_headers(token: str | None) -> dict[str, str]:
    """Build GitHub API request headers with authentication.

    NEVER pass the return value to any logger — it contains the Bearer token.
    """
    headers: dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": _GH_API_VERSION,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers
