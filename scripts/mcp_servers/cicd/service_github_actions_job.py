#!/usr/bin/env python3
"""mcp_servers/cicd/service_github_actions_job.py

GitHubActionsJobBackend: GitHub Actions job log operations.

Dependency direction: service_github_actions_job → service_defs, models
Import from here:  from mcp_servers.cicd.service_github_actions_job import GitHubActionsJobBackend
"""

from __future__ import annotations

import logging
from typing import cast

import httpx
import orjson
from shared.json_utils import parse_http_json

from mcp_servers.cicd.models import CicdUpstreamError

from .service_defs import _GITHUB_API_BASE, _MAX_JOBS_FOR_LOGS, build_auth_headers

logger = logging.getLogger(__name__)


class GitHubActionsJobBackend:
    """GitHub Actions job log operations.

    NEVER log build_auth_headers() return value — it contains the Bearer token.
    """

    def __init__(
        self,
        github_token: str,
        http: httpx.AsyncClient,
        max_log_size_kb: int = 256,
    ) -> None:
        """Initialize the GitHub Actions job backend with auth token, HTTP client, and log size limit."""
        # Store token privately; never expose via __repr__ or logging (R-4)
        self._token = github_token
        self._http = http
        self._max_log_size_kb = max_log_size_kb

    def __repr__(self) -> str:
        """Return a string representation with masked token for safe logging."""
        # Mask token value to prevent accidental log exposure (R-4)
        token_status = "set" if self._token else "not set"
        return f"GitHubActionsJobBackend(token={token_status!r})"

    @staticmethod
    def _format_job_header(job: dict) -> str:
        """Format job name, status, conclusion, and step list as a section header."""
        job_name: str = job.get("name", "unknown")
        conclusion: str = job.get("conclusion") or "in_progress"
        status: str = job.get("status", "unknown")
        step_lines = [
            f"  step {s.get('number')}: {s.get('name')} [{s.get('conclusion') or s.get('status')}]"
            for s in job.get("steps", [])
        ]
        return (
            f"=== Job: {job_name} [status={status}, conclusion={conclusion}] ===\n"
            + "\n".join(step_lines)
            + "\n"
        )

    async def _append_job_log(
        self,
        owner: str,
        repo: str,
        job_id: int,
        output_parts: list[str],
        total_bytes: int,
        max_bytes: int,
    ) -> tuple[list[str], int]:
        """Fetch and append log for a single job, respecting the byte limit.

        Returns (output_parts, total_bytes) which may be updated if truncation occurred.
        """

        log_url = f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
        try:
            log_resp = await self._http.get(
                log_url,
                headers=build_auth_headers(self._token),
                follow_redirects=True,
            )
            if log_resp.is_success:
                return self._truncate_if_needed(
                    output_parts, total_bytes, log_resp.text, max_bytes
                )
            output_parts.append(f"(log fetch failed: HTTP {log_resp.status_code})\n")
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
        ) as e:
            logger.warning(
                "get_workflow_logs: log fetch error job=%d: %s",
                job_id,
                e,
            )
            output_parts.append(f"(log fetch error: {e})\n")

        return output_parts, total_bytes

    def _truncate_if_needed(
        self,
        output_parts: list[str],
        total_bytes: int,
        log_text: str,
        max_bytes: int,
    ) -> tuple[list[str], int]:
        """Truncate log text if it exceeds the byte limit.

        Returns (output_parts, total_bytes) which may be updated if truncation occurred.
        """
        log_bytes = len(log_text.encode())
        remaining = max_bytes - total_bytes
        if log_bytes > remaining:
            truncated = log_text.encode()[: max(0, remaining - 60)].decode(
                "utf-8", errors="replace"
            )
            output_parts.append(
                truncated
                + f"\n[TRUNCATED: exceeded {self._max_log_size_kb} KB limit]\n",
            )
            return output_parts, max_bytes
        output_parts.append(log_text + "\n")
        total_bytes += log_bytes
        return output_parts, total_bytes

    async def get_workflow_logs(self, owner: str, repo: str, run_id: int) -> str:
        """Return job summaries and log text for a workflow run.

        Fetches job details (with step metadata) and plain-text log content for
        each job up to _MAX_JOBS_FOR_LOGS.  Total output is capped at max_log_size_kb.
        """
        jobs_data = await self._fetch_jobs(owner, repo, run_id)
        jobs = jobs_data.get("jobs", [])

        if not jobs:
            return f"No jobs found for run {run_id} in {owner}/{repo}."

        max_bytes = self._max_log_size_kb * 1024
        output_parts: list[str] = []
        total_bytes = 0

        for job in jobs[:_MAX_JOBS_FOR_LOGS]:
            if await self._append_job_output(
                owner, repo, job, output_parts, total_bytes, max_bytes
            ):
                break

        return "".join(output_parts)

    async def _fetch_jobs(self, owner: str, repo: str, run_id: int) -> dict:
        """Fetch and return the jobs data for a workflow run."""
        jobs_url = f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
        jobs_resp = await self._http.get(
            jobs_url, headers=build_auth_headers(self._token)
        )
        # Use try/except to handle non-2xx responses gracefully since this is called from a loop
        if not jobs_resp.is_success:
            raise CicdUpstreamError(
                f"GitHub API error (status={jobs_resp.status_code}): get_workflow_logs jobs {owner}/{repo} run={run_id}"
            )
        return cast(dict, parse_http_json(jobs_resp))

    async def _append_job_output(
        self,
        owner: str,
        repo: str,
        job: dict,
        output_parts: list[str],
        total_bytes: int,
        max_bytes: int,
    ) -> bool:
        """Append job header and log; return True when truncation occurred."""
        job_id: int = job.get("id", 0)
        header = self._format_job_header(job)
        output_parts.append(header)
        total_bytes += len(header.encode())

        if job_id:
            output_parts, total_bytes = await self._append_job_log(
                owner, repo, job_id, output_parts, total_bytes, max_bytes
            )

        return total_bytes >= max_bytes
