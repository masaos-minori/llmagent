#!/usr/bin/env python3
"""mcp/cicd/service.py
CiBackend protocol, GitHubActionsBackend, CiCdService, and lazy singleton proxy.

Security guards:
  - repo_allowlist: empty list = deny all repositories (fail-closed)
  - workflow_allowlist: empty list = allow all workflows
  - max_log_size_kb: log output is capped to prevent large data dumps
  - GITHUB_TOKEN: stored in _token field; never logged or included in __repr__
"""

from __future__ import annotations

import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import httpx
import orjson
from fastapi import HTTPException

from mcp.cicd.models import (
    GetWorkflowLogsRequest,
    GetWorkflowRunsRequest,
    GetWorkflowStatusRequest,
    TriggerWorkflowRequest,
    _get_cfg,
)
from mcp.server import ToolArgs

logger = logging.getLogger(__name__)

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


# ──────────────────────────────────────────────────────────────────────────────
# GitHubActionsBackend
# ──────────────────────────────────────────────────────────────────────────────


class GitHubActionsBackend:
    """GitHub Actions REST API client.

    NEVER log self._auth_headers() return value — it contains the Bearer token.
    """

    def __init__(
        self,
        github_token: str,
        http: httpx.AsyncClient,
        max_log_size_kb: int = 256,
    ) -> None:
        # Store token privately; never expose via __repr__ or logging (R-4)
        self._token = github_token
        self._http = http
        self._max_log_size_kb = max_log_size_kb

    def __repr__(self) -> str:
        # Mask token value to prevent accidental log exposure (R-4)
        token_status = "set" if self._token else "not set"
        return f"GitHubActionsBackend(token={token_status!r})"

    def _auth_headers(self) -> dict[str, str]:
        """Return request headers; NEVER pass return value to any logger."""
        headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": _GH_API_VERSION,
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _check_response(self, resp: httpx.Response, context: str) -> None:
        """Raise HTTPException for non-2xx responses with contextual messages."""
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Not found: {context}")
        if resp.status_code == 422:
            try:
                msg_422 = orjson.loads(resp.content).get(
                    "message",
                    "Unprocessable Entity",
                )
            except Exception:
                msg_422 = "Unprocessable Entity"
            raise HTTPException(status_code=422, detail=f"Validation failed: {msg_422}")
        if resp.status_code in (401, 403):
            try:
                body = orjson.loads(resp.content)
                msg: str = body.get("message", "Access denied")
            except Exception:
                msg = "Access denied"
            if "rate limit" in msg.lower():
                reset_ts = resp.headers.get("X-RateLimit-Reset", "unknown")
                raise HTTPException(
                    status_code=403,
                    detail=f"GitHub API rate limit exceeded. Reset at epoch: {reset_ts}",
                )
            raise HTTPException(status_code=403, detail=f"Access denied: {msg}")
        if not resp.is_success:
            raise HTTPException(
                status_code=502,
                detail=f"GitHub API error (status={resp.status_code}): {context}",
            )

    @staticmethod
    def _split_repo(repo: str) -> tuple[str, str]:
        """Split 'owner/repo' slug into (owner, repo); raises ValueError on bad format."""
        parts = repo.split("/", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(
                f"Invalid repo slug {repo!r}: expected 'owner/repo' format",
            )
        return parts[0], parts[1]

    async def trigger_workflow(
        self,
        owner: str,
        repo: str,
        workflow: str,
        ref: str,
        inputs: dict[str, str],
    ) -> str:
        """Trigger a workflow dispatch event."""
        url = f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches"
        body = orjson.dumps({"ref": ref, "inputs": inputs})
        resp = await self._http.post(
            url,
            headers={**self._auth_headers(), "Content-Type": "application/json"},
            content=body,
        )
        # 204 No Content = success (no body returned by GitHub)
        if resp.status_code == 204:
            logger.info(
                "trigger_workflow: dispatched repo=%s/%s workflow=%s ref=%s",
                owner,
                repo,
                workflow,
                ref,
            )
            return f"Workflow dispatched: {owner}/{repo} workflow={workflow} ref={ref}"
        self._check_response(resp, f"trigger_workflow {owner}/{repo}/{workflow}")
        return f"Workflow dispatched: {owner}/{repo} workflow={workflow} ref={ref}"

    async def get_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow: str,
        limit: int,
    ) -> str:
        """Return a list of recent workflow runs."""
        url = (
            f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/actions/workflows/{workflow}/runs"
        )
        resp = await self._http.get(
            url,
            headers=self._auth_headers(),
            params={"per_page": min(limit, 50)},
        )
        self._check_response(resp, f"get_workflow_runs {owner}/{repo}/{workflow}")
        data = orjson.loads(resp.content)
        runs = data.get("workflow_runs", [])[:limit]
        formatted = [
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "status": r.get("status"),
                "conclusion": r.get("conclusion"),
                "created_at": r.get("created_at"),
                "updated_at": r.get("updated_at"),
                "html_url": r.get("html_url"),
                "head_branch": r.get("head_branch"),
                "head_sha": (r.get("head_sha") or "")[:8],
            }
            for r in runs
        ]
        result = {
            "repo": f"{owner}/{repo}",
            "workflow": workflow,
            "total_count": data.get("total_count", len(runs)),
            "runs": formatted,
        }
        encoded: bytes = orjson.dumps(result, option=orjson.OPT_INDENT_2)
        return encoded.decode()

    async def get_workflow_status(self, owner: str, repo: str, run_id: int) -> str:
        """Return details for a single workflow run."""
        url = f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/actions/runs/{run_id}"
        resp = await self._http.get(url, headers=self._auth_headers())
        self._check_response(resp, f"get_workflow_status {owner}/{repo} run={run_id}")
        r = orjson.loads(resp.content)
        result = {
            "id": r.get("id"),
            "name": r.get("name"),
            "status": r.get("status"),
            "conclusion": r.get("conclusion"),
            "workflow_id": r.get("workflow_id"),
            "created_at": r.get("created_at"),
            "updated_at": r.get("updated_at"),
            "run_started_at": r.get("run_started_at"),
            "html_url": r.get("html_url"),
            "head_branch": r.get("head_branch"),
            "head_sha": (r.get("head_sha") or "")[:8],
            "event": r.get("event"),
            "run_attempt": r.get("run_attempt"),
        }
        encoded2: bytes = orjson.dumps(result, option=orjson.OPT_INDENT_2)
        return encoded2.decode()

    @staticmethod
    def _format_job_header(job: dict[str, Any]) -> str:
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

    async def get_workflow_logs(self, owner: str, repo: str, run_id: int) -> str:
        """Return job summaries and log text for a workflow run.

        Fetches job details (with step metadata) and plain-text log content for
        each job up to _MAX_JOBS_FOR_LOGS.  Total output is capped at max_log_size_kb.
        """
        jobs_url = f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
        jobs_resp = await self._http.get(jobs_url, headers=self._auth_headers())
        self._check_response(
            jobs_resp,
            f"get_workflow_logs jobs {owner}/{repo} run={run_id}",
        )
        jobs_data = orjson.loads(jobs_resp.content)
        jobs = jobs_data.get("jobs", [])

        if not jobs:
            return f"No jobs found for run {run_id} in {owner}/{repo}."

        max_bytes = self._max_log_size_kb * 1024
        output_parts: list[str] = []
        total_bytes = 0

        for job in jobs[:_MAX_JOBS_FOR_LOGS]:
            job_id: int = job.get("id", 0)
            header = self._format_job_header(job)
            output_parts.append(header)
            total_bytes += len(header.encode())

            if job_id:
                log_url = f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
                try:
                    log_resp = await self._http.get(
                        log_url,
                        headers=self._auth_headers(),
                        follow_redirects=True,
                    )
                    if log_resp.is_success:
                        log_text = log_resp.text
                        log_bytes = len(log_text.encode())
                        remaining = max_bytes - total_bytes
                        if log_bytes > remaining:
                            # Truncate at byte boundary and append notice
                            truncated = log_text.encode()[
                                : max(0, remaining - 60)
                            ].decode("utf-8", errors="replace")
                            output_parts.append(
                                truncated
                                + f"\n[TRUNCATED: exceeded {self._max_log_size_kb} KB limit]\n",
                            )
                            total_bytes = max_bytes
                            break
                        output_parts.append(log_text + "\n")
                        total_bytes += log_bytes
                    else:
                        output_parts.append(
                            f"(log fetch failed: HTTP {log_resp.status_code})\n",
                        )
                except Exception as e:
                    logger.warning(
                        "get_workflow_logs: log fetch error job=%d: %s",
                        job_id,
                        e,
                    )
                    output_parts.append(f"(log fetch error: {e})\n")

            if total_bytes >= max_bytes:
                break

        return "".join(output_parts)


# ──────────────────────────────────────────────────────────────────────────────
# CiCdService: guard checks + backend delegation
# ──────────────────────────────────────────────────────────────────────────────


class CiCdService:
    """Applies repo/workflow allowlist guards then delegates to CiBackend."""

    def __init__(
        self,
        cfg: dict[str, Any],
        backend: CiBackend,
    ) -> None:
        self._backend = backend
        # Empty allowlist = deny all (fail-closed, U-3)
        self._repo_allowlist: list[str] = list(cfg.get("repo_allowlist", []))
        # Empty allowlist = allow all for workflow names
        self._workflow_allowlist: list[str] = list(cfg.get("workflow_allowlist", []))

        if not self._repo_allowlist:
            logger.warning(
                "cicd-mcp: repo_allowlist is empty — all repository operations will be denied",
            )

    def _assert_allowed_repo(self, repo: str) -> None:
        """Raise HTTPException(403) when repo is not in the allowlist.

        Empty allowlist = deny all (fail-closed per U-3).
        """
        if not self._repo_allowlist:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Repository '{repo}' is denied:"
                    " repo_allowlist is empty (fail-closed mode)"
                ),
            )
        if repo not in self._repo_allowlist:
            raise HTTPException(
                status_code=403,
                detail=f"Repository not in repo_allowlist: {repo}",
            )

    def _assert_allowed_workflow(self, workflow: str) -> None:
        """Raise HTTPException(403) when workflow_allowlist is set and workflow is absent.

        Empty allowlist = allow all workflows.
        """
        if not self._workflow_allowlist:
            return
        if workflow not in self._workflow_allowlist:
            raise HTTPException(
                status_code=403,
                detail=f"Workflow not in workflow_allowlist: {workflow}",
            )

    @staticmethod
    def _parse_repo(repo: str) -> tuple[str, str]:
        """Split 'owner/repo' slug; raise HTTPException(400) on bad format."""
        try:
            return GitHubActionsBackend._split_repo(repo)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    # ── Dispatch handlers ──────────────────────────────────────────────────────

    async def handle_trigger_workflow(self, args: ToolArgs) -> str:
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
            return orjson.dumps({"preview": preview, "dry_run": True}).decode()
        owner, repo = self._parse_repo(req.repo)
        return await self._backend.trigger_workflow(
            owner,
            repo,
            req.workflow,
            req.ref,
            req.inputs,
        )

    async def handle_get_workflow_runs(self, args: ToolArgs) -> str:
        req = GetWorkflowRunsRequest(**args)
        self._assert_allowed_repo(req.repo)
        owner, repo = self._parse_repo(req.repo)
        return await self._backend.get_workflow_runs(
            owner,
            repo,
            req.workflow,
            req.limit,
        )

    async def handle_get_workflow_status(self, args: ToolArgs) -> str:
        req = GetWorkflowStatusRequest(**args)
        self._assert_allowed_repo(req.repo)
        owner, repo = self._parse_repo(req.repo)
        return await self._backend.get_workflow_status(owner, repo, req.run_id)

    async def handle_get_workflow_logs(self, args: ToolArgs) -> str:
        req = GetWorkflowLogsRequest(**args)
        self._assert_allowed_repo(req.repo)
        owner, repo = self._parse_repo(req.repo)
        return await self._backend.get_workflow_logs(owner, repo, req.run_id)

    def get_dispatch_table(
        self,
    ) -> dict[str, Callable[[ToolArgs], Awaitable[str]]]:
        return {
            "trigger_workflow": self.handle_trigger_workflow,
            "get_workflow_runs": self.handle_get_workflow_runs,
            "get_workflow_status": self.handle_get_workflow_status,
            "get_workflow_logs": self.handle_get_workflow_logs,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Lazy singleton
# ──────────────────────────────────────────────────────────────────────────────


class _LazyCiCdService:
    """Lazy singleton proxy: defers CiCdService init until first attribute access."""

    _instance: CiCdService | None = None

    def __getattr__(self, name: str) -> Any:
        if _LazyCiCdService._instance is None:
            cfg = _get_cfg()
            # Read token from env (set via /etc/conf.d/cicd-mcp by OpenRC)
            github_token = os.environ.get("GITHUB_TOKEN", cfg.get("github_token", ""))
            if not github_token:
                logger.warning(
                    "cicd-mcp: GITHUB_TOKEN is not set; API rate limit will be 60 req/hr",
                )
            max_log_size_kb = int(cfg.get("max_log_size_kb", 256))
            http = httpx.AsyncClient(timeout=30.0)
            backend: CiBackend = GitHubActionsBackend(
                github_token=github_token,
                http=http,
                max_log_size_kb=max_log_size_kb,
            )
            _LazyCiCdService._instance = CiCdService(cfg=cfg, backend=backend)
        return getattr(_LazyCiCdService._instance, name)


# _LazyCiCdService is a proxy whose __getattr__ delegates to CiCdService.
_service: CiCdService = _LazyCiCdService()  # type: ignore[assignment]
