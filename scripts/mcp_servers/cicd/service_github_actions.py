#!/usr/bin/env python3
"""mcp_servers/cicd/service_github_actions.py

GitHubActionsBackend: GitHub Actions REST API client (HTTP).

Dependency direction: service_github_actions → service_defs, models
Import from here:  from mcp_servers.cicd.service_github_actions import GitHubActionsBackend
"""

from __future__ import annotations

import logging
from http import HTTPStatus

import httpx
import orjson
from mcp_servers.cicd.models import (
    CicdAuthorizationError,
    CicdNotFoundError,
    CicdValidationError,
)

from .service_defs import (
    _GH_API_VERSION,
    _GITHUB_API_BASE,
    GITHUB_REPO_PARTS_COUNT,
)

logger = logging.getLogger(__name__)


class GitHubActionsBackend:
    """GitHub Actions REST API client for workflow dispatch/status operations.

    NEVER log self._auth_headers() return value — it contains the Bearer token.
    """

    def __init__(
        self,
        github_token: str,
        http: httpx.AsyncClient,
    ) -> None:
        # Store token privately; never expose via __repr__ or logging (R-4)
        self._token = github_token
        self._http = http

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

    @staticmethod
    def _parse_error_message(resp: httpx.Response, default: str) -> str:
        """Parse 'message' field from JSON response or return default."""
        try:
            body = orjson.loads(resp.content)
        except (orjson.JSONDecodeError, UnicodeDecodeError):
            return default
        msg: str = body.get("message", default)
        return msg

    def _check_response(self, resp: httpx.Response, context: str) -> None:
        """Raise domain exceptions for non-2xx responses with contextual messages."""
        if resp.status_code == HTTPStatus.NOT_FOUND:
            raise CicdNotFoundError(f"Not found: {context}")
        if resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
            msg_422 = self._parse_error_message(resp, "Unprocessable Entity")
            raise CicdValidationError(f"Validation failed: {msg_422}")
        if resp.status_code in (401, 403):
            self._raise_auth_error(resp, context)
        if not resp.is_success:
            raise CicdNotFoundError(
                f"GitHub API error (status={resp.status_code}): {context}",
            )

    def _raise_auth_error(self, resp: httpx.Response, context: str) -> None:
        """Raise CicdAuthorizationError for 401/403 responses."""
        msg = self._parse_error_message(resp, "Access denied")
        if "rate limit" in msg.lower():
            reset_ts = resp.headers.get("X-RateLimit-Reset", "unknown")
            raise CicdAuthorizationError(
                f"GitHub API rate limit exceeded. Reset at epoch: {reset_ts}",
            )
        raise CicdAuthorizationError(f"Access denied: {msg}")

    @staticmethod
    def _split_repo(repo: str) -> tuple[str, str]:
        """Split 'owner/repo' slug into (owner, repo); raises ValueError on bad format."""
        parts = repo.split("/", 1)
        if len(parts) != GITHUB_REPO_PARTS_COUNT or not parts[0] or not parts[1]:
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
        if resp.status_code == HTTPStatus.NO_CONTENT:
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
