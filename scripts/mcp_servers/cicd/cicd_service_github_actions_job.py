#!/usr/bin/env python3
"""scripts/mcp_servers/cicd/cicd_service_github_actions_job.py

GitHubActionsJobBackend: GitHub Actions job log operations.

The jobs API call uses the injected client; each job log is downloaded through the
shared bounded helper (`mcp_servers.bounded_fetch`) under the raw and decompressed
limits, so nothing is buffered in full before the budget is known. The exact
final-output byte budget (headers, log text, and the truncation marker) is enforced
here, because the helper carries `returned_bytes` without enforcing it.

Dependency direction: service_github_actions_job -> service_defs, models,
mcp_servers.bounded_fetch, mcp_servers.address_policy
Import from here:  from mcp_servers.cicd.cicd_service_github_actions_job import GitHubActionsJobBackend
"""

from __future__ import annotations

import logging
from typing import cast
from urllib.parse import urlsplit

import httpx
from shared.json_utils import parse_http_json

from mcp_servers.address_policy import KIND_PROHIBITED_ADDRESS, AddressRejectedError
from mcp_servers.bounded_fetch import (
    FetchContentTypeError,
    FetchLimits,
    FetchRedirectError,
    FetchStatusError,
    FetchUnsupportedEncodingError,
    fetch_bounded,
)
from mcp_servers.cicd.cicd_models import (
    LOG_FETCH_TIMEOUT_S,
    MAX_DECOMPRESSED_BYTES,
    MAX_RAW_DOWNLOAD_BYTES,
    MAX_REDIRECTS,
    TRUSTED_LOG_HOSTS,
    CicdUpstreamError,
    LogFetchResult,
    LogJobResult,
    LogTotals,
)

from .cicd_service_defs import _GITHUB_API_BASE, _MAX_JOBS_FOR_LOGS, build_auth_headers

logger = logging.getLogger(__name__)

# The job log endpoint answers with plain text (Plan Assumption).
_ALLOWED_LOG_CONTENT_TYPES = frozenset({"text/plain"})


def trusted_log_host(url: str) -> str:
    """Return the hop's hostname, rejecting a host outside the trusted log hosts.

    `productionresultssa*.blob.core.windows.net` is a prefix match, not an allowlist
    wildcard (REQ-001, AC-3). The exception is `address_policy`'s own, so the helper
    propagates it unchanged.
    """
    host = (urlsplit(url).hostname or "").lower()
    if not host:
        raise AddressRejectedError("(none)", KIND_PROHIBITED_ADDRESS)
    for entry in TRUSTED_LOG_HOSTS:
        prefix, _, _ = entry.partition("*")
        if host == entry or (prefix and host.startswith(prefix)):
            return host
    raise AddressRejectedError(host, KIND_PROHIBITED_ADDRESS)


def _error_code(exc: BaseException) -> str:
    """Map a helper or transport failure to the stable per-job error code (REQ-004)."""
    if isinstance(exc, FetchStatusError):
        return "http_status"
    if isinstance(exc, AddressRejectedError):
        return "address_rejected"
    if isinstance(exc, FetchRedirectError):
        return "redirect"
    if isinstance(exc, FetchContentTypeError):
        return "content_type"
    if isinstance(exc, (FetchUnsupportedEncodingError, UnicodeDecodeError)):
        return "content_encoding"
    return "transport"


def _utf8_cut(data: bytes, limit: int) -> bytes:
    """Cut `data` at `limit` bytes on a UTF-8 character boundary (REQ-003, AC-2).

    A cut that lands inside a multi-byte character moves back to that character's
    start and drops it, so no partial character and no replacement character is left.
    """
    if limit >= len(data):
        return data
    end = limit
    start = end
    # Continuation bytes (0x80..0xBF) cannot start a character.
    while start > 0 and 0x80 <= data[start - 1] < 0xC0:
        start -= 1
    if start == 0:
        return data[:end]
    lead = data[start - 1]
    width = 1 if lead < 0x80 else (2 if lead < 0xC0 else (3 if lead < 0xF0 else 4))
    # The character that straddles the cut point is dropped.
    return data[: start - 1] if start - 1 + width > end else data[:end]


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

    def _truncation_marker(self) -> str:
        """Return the truncation marker; its bytes are inside the output budget (REQ-003)."""
        return f"\n[TRUNCATED: exceeded {self._max_log_size_kb} KB limit]\n"

    async def _fetch_job_log(
        self,
        owner: str,
        repo: str,
        job_id: int,
        room: int,
    ) -> tuple[str, str | None, bool, str | None, int]:
        """Fetch one job log under `room` bytes.

        Returns `(text to append, error code, truncated, truncation reason, decoded
        bytes handed by the helper)`. Raw transport text never reaches the output
        (REQ-004): a failure is a code.
        """
        log_url = f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
        limits = FetchLimits(
            raw_bytes=MAX_RAW_DOWNLOAD_BYTES,
            decoded_bytes=MAX_DECOMPRESSED_BYTES,
            parser_input_bytes=room,
            returned_bytes=self._max_log_size_kb * 1024,
        )
        try:
            fetched = await fetch_bounded(
                log_url,
                limits=limits,
                host_policy=trusted_log_host,
                allowed_content_types=_ALLOWED_LOG_CONTENT_TYPES,
                timeout_sec=LOG_FETCH_TIMEOUT_S,
                max_redirects=MAX_REDIRECTS,
                headers=build_auth_headers(self._token),
            )
            body = fetched.body
            helper_reason = fetched.truncated_by
            if len(body) > room:
                marker = self._truncation_marker()
                if room < len(marker.encode()):
                    # The marker must fit inside the budget, so nothing of this log can
                    # be appended: the job is recorded as skipped.
                    return "", None, True, "output_budget", len(body)
                cut = _utf8_cut(body, room - len(marker.encode()))
                return (
                    cut.decode("utf-8") + marker,
                    None,
                    True,
                    helper_reason or "output_budget",
                    len(body),
                )
            text = body.decode("utf-8")
            return (
                text + "\n",
                None,
                helper_reason is not None,
                helper_reason,
                len(body),
            )
        except Exception as exc:  # noqa: BLE001 -- per-job failure is reported as a code,
            # never as raw transport text, so the exception is not re-raised here.
            code = _error_code(exc)
            logger.warning(
                "get_workflow_logs: log fetch error job=%d code=%s",
                job_id,
                code,
            )
            return "", code, False, None, 0

    async def get_workflow_logs(
        self, owner: str, repo: str, run_id: int
    ) -> LogFetchResult:
        """Return the structured log result for a workflow run.

        Job headers and log text are assembled under the exact output budget
        (`max_log_size_kb` in bytes); per-job status, included bytes, error code, and
        truncation state are recorded instead of embedded failure text (REQ-004, REQ-005).
        """
        jobs_data = await self._fetch_jobs(owner, repo, run_id)
        jobs = jobs_data.get("jobs", [])
        max_bytes = self._max_log_size_kb * 1024

        if not jobs:
            message = f"No jobs found for run {run_id} in {owner}/{repo}."
            return _assemble((), message, 0)

        records: list[LogJobResult] = []
        parts: list[str] = []
        used = 0
        downloaded = 0
        reason: str | None = None

        for job in jobs[:_MAX_JOBS_FOR_LOGS]:
            job_id: int = job.get("id", 0)
            header = self._format_job_header(job)
            header_bytes = len(header.encode())
            room = max_bytes - used
            if header_bytes > room:
                # REQ-003: a job whose header no longer fits is not appended, and no
                # later job can fit either, so the loop stops here.
                records.append(
                    LogJobResult(
                        job_id=job_id,
                        status="skipped",
                        included_bytes=0,
                        truncated=True,
                    )
                )
                reason = "output_budget"
                break

            parts.append(header)
            used += header_bytes
            if room == header_bytes:
                # The budget is exactly the header: the job contributes no log bytes.
                records.append(
                    LogJobResult(
                        job_id=job_id,
                        status="included",
                        included_bytes=header_bytes,
                        truncated=True,
                    )
                )
                reason = "output_budget"
                break

            (
                piece,
                code,
                truncated,
                cut_reason,
                fetched_bytes,
            ) = await self._fetch_job_log(owner, repo, job_id, room - header_bytes)
            records.append(
                LogJobResult(
                    job_id=job_id,
                    status="failed" if code else "included",
                    included_bytes=header_bytes + len(piece.encode()),
                    error_code=code,
                    truncated=truncated,
                )
            )
            parts.append(piece)
            used += header_bytes + len(piece.encode())
            downloaded += fetched_bytes
            if cut_reason:
                reason = cut_reason

        return _assemble(tuple(records), "".join(parts), downloaded, reason)

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


def _assemble(
    records: tuple[LogJobResult, ...],
    output: str,
    downloaded: int,
    reason: str | None = None,
) -> LogFetchResult:
    """Build the totals from the per-job records (REQ-005)."""
    included = sum(1 for record in records if record.status == "included")
    failed = sum(1 for record in records if record.status == "failed")
    totals = LogTotals(
        jobs=len(records),
        included_jobs=included,
        failed_jobs=failed,
        downloaded_bytes=downloaded,
        visible_bytes=len(output.encode()),
        truncation_reason=reason,
    )
    return LogFetchResult(
        jobs=records,
        output=output,
        partial_success=included > 0 and failed > 0,
        totals=totals,
    )
