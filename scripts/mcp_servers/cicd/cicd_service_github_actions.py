#!/usr/bin/env python3
"""scripts/mcp_servers/cicd/cicd_service_github_actions.py

GitHubActionsBackend: GitHub Actions REST API client (HTTP).

Dependency direction: service_github_actions → service_defs, models
Import from here:  from mcp_servers.cicd.cicd_service_github_actions import GitHubActionsBackend
"""

from __future__ import annotations

import asyncio
import dataclasses
import datetime
import hashlib
import logging
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx
import orjson
from shared.json_utils import dumps as _json_dumps
from shared.json_utils import parse_http_json
from shared.mcp_call_state_contract import ReconcileEvidence
from shared.write_outcome import OUTCOME_UNKNOWN

from mcp_servers.cicd.cicd_models import (
    POLL_INTERVAL_S,
    POLL_TIMEOUT_S,
    CicdAuthorizationError,
    CicdNotFoundError,
    CicdValidationError,
    DispatchOutcome,
)

from .cicd_service_defs import (
    _GITHUB_API_BASE,
    GITHUB_REPO_PARTS_COUNT,
    build_auth_headers,
)

logger = logging.getLogger(__name__)


# In-process correlation record (mcpci002 REQ-002): written before the dispatch POST
# so reconcile can answer from it without I/O (sync contract, control_api.py). The
# record is not persisted: a process restart loses it and reconcile answers
# unverifiable (Plan Design decision). Only the digest is exposed through
# ReconcileEvidence, never the raw fields (REQ-006, REQ-007).
@dataclasses.dataclass
class CorrelationRecord:
    """Fallback correlation for one dispatch call: identifier, ref, actor, time."""

    workflow: str
    ref: str
    actor: str
    dispatch_time: str
    attempted: bool = False
    candidates: tuple[int, ...] = ()


_CORRELATION: dict[str, CorrelationRecord] = {}

# Call identity (session, request, call key) bound by the server's call_tool around
# the dispatch, following the github write-audit pattern; empty when no identity is
# bound. The reconciler receives the component-keyed snapshot, which carries no call
# arguments, so the key is read through this ContextVar (Plan Design decision,
# amended 20261127).
_CALL_IDENTITY: ContextVar[tuple[str, str, str]] = ContextVar(
    "cicd_call_identity", default=("", "", "")
)


@contextmanager
def bind_call_identity(
    session_id: str, request_id: str, call_id: str
) -> Iterator[None]:
    """Bind the call identity for the current context and reset it on exit."""
    token = _CALL_IDENTITY.set((session_id, request_id, call_id))
    try:
        yield
    finally:
        _CALL_IDENTITY.reset(token)


def _correlation_digest(record: CorrelationRecord) -> str:
    """Non-sensitive hex digest of the correlation fields (REQ-007)."""
    raw = f"{record.workflow}|{record.ref}|{record.actor}|{record.dispatch_time}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class DispatchReconciler:
    """Reconciler implementation for trigger_workflow (REQ-007), registered by the
    server row at the control-API seam.

    Answers from the in-process correlation record without I/O; never re-executes.
    Outcome mapping (Plan Design decision): record hit -> evidence_found, record miss
    after a process restart -> unverifiable, recorded-but-not-attempted ->
    no_evidence, multiple candidates recorded by the pre-dispatch search -> ambiguous.
    """

    def reconcile(
        self, tool_name: str, call_key: str, snapshot: Mapping[str, str]
    ) -> ReconcileEvidence:
        """Return evidence for a call whose response was lost; never re-execute."""
        if tool_name != "trigger_workflow":
            digest = hashlib.sha256(tool_name.encode("utf-8")).hexdigest()
            return ReconcileEvidence("unverifiable", digest)
        record = _CORRELATION.get(call_key)
        if record is None:
            digest = hashlib.sha256(call_key.encode("utf-8")).hexdigest()
            return ReconcileEvidence("unverifiable", digest)
        digest = _correlation_digest(record)
        if len(record.candidates) > 1:
            return ReconcileEvidence("ambiguous", digest)
        if not record.attempted:
            return ReconcileEvidence("no_evidence", digest)
        return ReconcileEvidence("evidence_found", digest)


# The instance the server row registers at the control-API seam; the correlation
# record is module-level in-process state, so one instance per process is enough.
dispatch_reconciler = DispatchReconciler()


class GitHubActionsBackend:
    """GitHub Actions REST API client for workflow dispatch/status operations.

    NEVER log build_auth_headers() return value — it contains the Bearer token.
    """

    def __init__(
        self,
        github_token: str,
        http: httpx.AsyncClient,
    ) -> None:
        """Store credentials and HTTP client for GitHub Actions API calls."""
        # Store token privately; never expose via __repr__ or logging (R-4)
        self._token = github_token
        self._http = http

    def __repr__(self) -> str:
        """Return a safe string representation that masks the authentication token."""
        # Mask token value to prevent accidental log exposure (R-4)
        token_status = "set" if self._token else "not set"
        return f"GitHubActionsBackend(token={token_status!r})"

    @staticmethod
    def _parse_error_message(resp: httpx.Response, default: str) -> str:
        """Parse 'message' field from JSON response or return default."""
        try:
            body = parse_http_json(resp)
        except (ValueError, UnicodeDecodeError):
            return default
        msg = cast(str, body.get("message", default))
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
    ) -> DispatchOutcome:
        """Trigger a workflow dispatch event and return the structured outcome.

        A 2xx response never becomes confirmed without a matched run (REQ-001). The
        correlation record is written before the dispatch POST (REQ-002); a repeat of
        the same logical call searches for the run before dispatching (REQ-004).
        """
        session_id, _request_id, call_key = _CALL_IDENTITY.get()
        record = CorrelationRecord(
            workflow=workflow,
            ref=ref,
            actor=session_id,
            dispatch_time=datetime.datetime.now(datetime.UTC).isoformat(),
        )
        if call_key:
            _CORRELATION[call_key] = record

        # Pre-dispatch run search for a repeat of the same logical call (REQ-004,
        # AC-3), keyed by the fallback correlation because a marker in `inputs`
        # would change the args hash and the dedup key (Plan Risk).
        prior = self._prior_record(record)
        if prior is not None:
            found = await self._search_runs(owner, repo, workflow, prior.dispatch_time)
            if found is None:
                return DispatchOutcome(
                    state=OUTCOME_UNKNOWN, workflow=workflow, ref=ref
                )
            if len(found) > 1:
                record.candidates = tuple(r["id"] for r in found)
                return DispatchOutcome(
                    state="reconciliation_required", workflow=workflow, ref=ref
                )
            if found:
                run = found[0]
                record.candidates = (run["id"],)
                return self._confirmed(run, workflow, ref)

        # The canonical identifier is encoded as one path segment, so a separator or a
        # percent-encoded segment cannot alter the dispatch path (AC-4).
        segment = quote(workflow, safe="")
        url = f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/actions/workflows/{segment}/dispatches"
        body = orjson.dumps({"ref": ref, "inputs": inputs})
        record.attempted = True
        try:
            resp = await self._http.post(
                url,
                headers={
                    **build_auth_headers(self._token),
                    "Content-Type": "application/json",
                },
                content=body,
            )
        except httpx.HTTPError:
            # Response loss: no retry, the outcome stays unknown (REQ-003).
            return DispatchOutcome(state=OUTCOME_UNKNOWN, workflow=workflow, ref=ref)
        self._check_response(resp, f"trigger_workflow {owner}/{repo}/{workflow}")
        logger.info(
            "trigger_workflow: dispatched repo=%s/%s workflow=%s ref=%s",
            owner,
            repo,
            workflow,
            ref,
        )
        # Bounded polling for the matching run (REQ-003); a timeout produces
        # outcome_unknown, never a retry.
        found = await self._poll_runs(owner, repo, workflow, record.dispatch_time)
        if found is None:
            return DispatchOutcome(state=OUTCOME_UNKNOWN, workflow=workflow, ref=ref)
        if len(found) > 1:
            record.candidates = tuple(r["id"] for r in found)
            return DispatchOutcome(
                state="reconciliation_required", workflow=workflow, ref=ref
            )
        if found:
            return self._confirmed(found[0], workflow, ref)
        return DispatchOutcome(state="accepted_unconfirmed", workflow=workflow, ref=ref)

    def _prior_record(self, record: CorrelationRecord) -> CorrelationRecord | None:
        """Return the earlier correlation for the same logical call, if recorded."""
        for key, prior in _CORRELATION.items():
            if (
                key != _CALL_IDENTITY.get()[2]
                and prior.workflow == record.workflow
                and prior.ref == record.ref
                and prior.actor == record.actor
            ):
                return prior
        return None

    async def _search_runs(
        self, owner: str, repo: str, workflow: str, since_iso: str
    ) -> list[dict[str, Any]] | None:
        """Return runs created at or after the correlation time; None on response loss."""
        segment = quote(workflow, safe="")
        url = (
            f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/actions/workflows/{segment}/runs"
        )
        try:
            resp = await self._http.get(
                url,
                headers=build_auth_headers(self._token),
                params={"per_page": 50},
            )
        except httpx.HTTPError:
            return None
        self._check_response(resp, f"get_workflow_runs {owner}/{repo}/{workflow}")
        data = parse_http_json(resp)
        runs = cast(list[dict[str, Any]], data.get("workflow_runs", []))
        since = datetime.datetime.fromisoformat(since_iso)
        return [r for r in runs if self._created_at(r) >= since]

    async def _poll_runs(
        self, owner: str, repo: str, workflow: str, since_iso: str
    ) -> list[dict[str, Any]] | None:
        """Poll for matching runs bounded by the models-row constants (REQ-003)."""
        deadline = time.monotonic() + POLL_TIMEOUT_S
        while True:
            found = await self._search_runs(owner, repo, workflow, since_iso)
            if found is None:
                return None
            if found:
                return found
            if time.monotonic() >= deadline:
                return []
            await asyncio.sleep(POLL_INTERVAL_S)

    @staticmethod
    def _created_at(run: Mapping[str, Any]) -> datetime.datetime:
        """Parse a run's created_at; a missing or malformed value sorts before `since`."""
        raw = run.get("created_at")
        if not raw:
            return datetime.datetime.min
        try:
            return datetime.datetime.fromisoformat(str(raw))
        except ValueError:
            return datetime.datetime.min

    @staticmethod
    def _confirmed(run: Mapping[str, Any], workflow: str, ref: str) -> DispatchOutcome:
        """Build the confirmed outcome from a unique matched run (REQ-001)."""
        return DispatchOutcome(
            state="confirmed",
            run_id=cast(int, run.get("id")),
            run_url=cast(str | None, run.get("html_url")),
            run_status=cast(str | None, run.get("status")),
            workflow=workflow,
            ref=ref,
        )

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
            headers=build_auth_headers(self._token),
            params={"per_page": min(limit, 50)},
        )
        self._check_response(resp, f"get_workflow_runs {owner}/{repo}/{workflow}")
        data = parse_http_json(resp)
        runs = cast(list[dict[str, Any]], data.get("workflow_runs", []))[:limit]
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
                "head_sha": (_sha := r.get("head_sha")) and str(_sha)[:8] or "",
            }
            for r in runs
        ]
        result = {
            "repo": f"{owner}/{repo}",
            "workflow": workflow,
            "total_count": data.get("total_count", len(runs)),
            "runs": formatted,
        }
        encoded: str = _json_dumps(result, option=orjson.OPT_INDENT_2)
        return encoded

    async def get_workflow_status(self, owner: str, repo: str, run_id: int) -> str:
        """Return details for a single workflow run."""
        url = f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/actions/runs/{run_id}"
        resp = await self._http.get(url, headers=build_auth_headers(self._token))
        self._check_response(resp, f"get_workflow_status {owner}/{repo} run={run_id}")
        r = parse_http_json(resp)
        head_sha_raw = r.get("head_sha")
        head_sha = str(head_sha_raw)[:8] if head_sha_raw else ""
        result = {
            "id": cast(int | None, r.get("id")),
            "name": cast(str | None, r.get("name")),
            "status": cast(str | None, r.get("status")),
            "conclusion": cast(str | None, r.get("conclusion")),
            "workflow_id": r.get("workflow_id"),
            "created_at": r.get("created_at"),
            "updated_at": r.get("updated_at"),
            "run_started_at": r.get("run_started_at"),
            "html_url": r.get("html_url"),
            "head_branch": r.get("head_branch"),
            "head_sha": head_sha,
            "event": r.get("event"),
            "run_attempt": r.get("run_attempt"),
        }
        encoded2: str = _json_dumps(result, option=orjson.OPT_INDENT_2)
        return encoded2
