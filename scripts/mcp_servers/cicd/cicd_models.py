#!/usr/bin/env python3
"""scripts/mcp_servers/cicd/cicd_models.py

Config loading, Pydantic models, and domain exceptions for cicd-mcp.

The request models are the single source of the published tool schemas: they
inherit the shared strict base so the contract a client discovers at `/v1/tools`
is the contract enforced at call time. `canonical_workflow_id()` is the only
identifier normalizer, used by both the request path and the allowlist comparison.

Dependency direction: models → (external: pydantic, shared) + mcp_servers.request_contract
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

from pydantic import Field
from shared.config_loader import ConfigLoader
from shared.config_utils import get_non_negative_number, get_str, get_typed
from shared.repo_identity import is_canonical_repo_key, normalize_repo_key
from shared.write_outcome import OUTCOME_UNKNOWN

from mcp_servers.request_contract import StrictRequestModel

logger = logging.getLogger(__name__)

# Hard maximums approved by the Plan on 20261126 (UNK-03); they are constants, not
# configuration values, so the config file and the docs can state them.
MAX_LOG_SIZE_KB = 1024
MAX_ALLOWLIST_SIZE = 100


# ──────────────────────────────────────────────────────────────────────────────
# Domain exceptions
# ──────────────────────────────────────────────────────────────────────────────


class CicdAuthorizationError(RuntimeError):
    """Raised when authentication/authorization fails."""


class CicdNotFoundError(ValueError):
    """Raised when a CICD resource is not found."""


class CicdValidationError(ValueError):
    """Raised on invalid input."""


class CicdUpstreamError(RuntimeError):
    """Raised on upstream service failures (e.g. GitHub API 5xx)."""


class CicdConflictError(RuntimeError):
    """Raised on a 409 conflict response (mcpci004)."""


class CicdRateLimitError(RuntimeError):
    """Raised on a 429 rate-limit response (mcpci004).

    Carries the preserved `Retry-After` and `X-RateLimit-Reset` values as structured
    fields. The backend row parses them; this class only holds them (REQ-003).
    """

    def __init__(
        self,
        message: str,
        retry_after: str | None = None,
        rate_limit_reset: str | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after
        self.rate_limit_reset = rate_limit_reset


# ──────────────────────────────────────────────────────────────────────────────
# Error-code vocabulary (mcpci004, REQ-006)
# ──────────────────────────────────────────────────────────────────────────────

# CI/CD-scoped stable lowercase-snake codes, following the style the shared helper
# recommends for new servers; `CONTROL_ERROR_CODES` is not extended.
CICD_ERROR_CODES = frozenset(
    {
        "authorization_error",
        "not_found",
        "validation_error",
        "upstream_error",
        "conflict",
        "rate_limit",
        "unexpected_error",
    }
)

EXCEPTION_ERROR_CODES: dict[type[Exception], str] = {
    CicdAuthorizationError: "authorization_error",
    CicdNotFoundError: "not_found",
    CicdValidationError: "validation_error",
    CicdUpstreamError: "upstream_error",
    CicdConflictError: "conflict",
    CicdRateLimitError: "rate_limit",
}

# Maximum length of the bounded upstream error text (UNK-04, decided at
# implementation as a module constant); the backend redaction helper applies this
# bound. The test asserts the bound rather than this specific value.
MAX_ERROR_TEXT_LENGTH = 500


# ──────────────────────────────────────────────────────────────────────────────
# Canonical identifier
# ──────────────────────────────────────────────────────────────────────────────


def canonical_workflow_id(value: str) -> str:
    """Return the canonical form of a workflow identifier.

    Accepts a workflow file name (e.g. `ci.yml`) or a positive numeric workflow ID;
    both forms are the two identifier forms the documentation names. A value that is
    already canonical is returned unchanged.

    Raises CicdValidationError for a blank value, a path separator, percent-encoding,
    a wildcard, or a numeric ID below 1, so the request path and the allowlist
    comparison cannot diverge.
    """
    if not isinstance(value, str):
        raise CicdValidationError(
            f"workflow identifier must be str, got {type(value).__name__}"
        )
    stripped = value.strip()
    if not stripped:
        raise CicdValidationError("workflow identifier is empty")
    if "/" in stripped or "\\" in stripped:
        raise CicdValidationError(
            f"workflow identifier contains a path separator and is rejected: {value!r}"
        )
    if "%" in stripped:
        raise CicdValidationError(
            f"workflow identifier contains percent-encoding and is rejected: {value!r}"
        )
    if "*" in stripped:
        raise CicdValidationError(
            f"workflow identifier contains a wildcard and is rejected: {value!r}"
        )
    canonical = stripped.lower()
    if canonical.isdigit():
        if int(canonical) < 1:
            raise CicdValidationError(
                f"numeric workflow ID must be positive: {value!r}"
            )
        return canonical
    return canonical


def canonical_repo_key(repo: str) -> str:
    """Return the canonical `owner/repo` key for a request slug.

    Raises CicdValidationError when the slug is not `owner/repo`.
    """
    parts = repo.split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise CicdValidationError(
            f"Invalid repo slug {repo!r}: expected 'owner/repo' format"
        )
    return normalize_repo_key(parts[0], parts[1])


# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────


def _validate_allowlist(key: str, entries: list[str]) -> list[str]:
    """Reject an allowlist above the hard maximum or carrying a wildcard entry.

    Entries are returned unchanged: a non-canonical entry is reported, never rewritten,
    so the guard can still detect it instead of silently matching nothing.
    """
    if len(entries) > MAX_ALLOWLIST_SIZE:
        raise ValueError(
            f"Config key {key!r} has {len(entries)} entries; the hard maximum is {MAX_ALLOWLIST_SIZE}"
        )
    for entry in entries:
        if not isinstance(entry, str):
            raise ValueError(
                f"Config key {key!r} entries must be str, got {type(entry).__name__}"
            )
        if "*" in entry:
            raise ValueError(
                f"Config key {key!r} entry {entry!r} is a wildcard and is rejected"
            )
    return entries


@dataclasses.dataclass
class CicdConfig:
    """Typed configuration for the CICD MCP server."""

    auth_token: str = ""
    repo_allowlist: list[str] = dataclasses.field(default_factory=list)
    workflow_allowlist: list[str] = dataclasses.field(default_factory=list)
    max_log_size_kb: int = 256
    github_token: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CicdConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        repo_allowlist = _validate_allowlist(
            "repo_allowlist",
            get_typed(d, "repo_allowlist", list, "a list", default=[]),
        )
        workflow_allowlist = _validate_allowlist(
            "workflow_allowlist",
            get_typed(d, "workflow_allowlist", list, "a list", default=[]),
        )
        for entry in repo_allowlist:
            if not is_canonical_repo_key(entry):
                raise ValueError(
                    f"Config key 'repo_allowlist' entry {entry!r} is not in canonical 'owner/repo' form"
                )
        for entry in workflow_allowlist:
            canonical_workflow_id(entry)

        max_log_size_kb = get_non_negative_number(
            d, "max_log_size_kb", int, "an integer", default=256
        )
        if max_log_size_kb < 1:
            raise ValueError(
                f"Config key 'max_log_size_kb' must be at least 1, got {max_log_size_kb}"
            )
        if max_log_size_kb > MAX_LOG_SIZE_KB:
            raise ValueError(
                f"Config key 'max_log_size_kb' must be at most {MAX_LOG_SIZE_KB}, got {max_log_size_kb}"
            )

        return cls(
            auth_token=get_str(d, "auth_token"),
            repo_allowlist=list(repo_allowlist),
            workflow_allowlist=list(workflow_allowlist),
            max_log_size_kb=max_log_size_kb,
            github_token=get_str(d, "github_token"),
        )

    @classmethod
    def load(cls) -> CicdConfig:
        """Load from cicd_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("cicd_mcp_server.toml"))


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions
# ──────────────────────────────────────────────────────────────────────────────

# Descriptions are the client-visible text published by build_input_schema(); they
# live on the model fields so the published schema and the enforced contract match.
_REPO_DESC = "Repository slug in 'owner/repo' format"
_WORKFLOW_DESC = "Workflow file name (e.g. ci.yml) or numeric workflow ID"
_RUN_ID_DESC = "Workflow run ID (from get_workflow_runs output)"


class TriggerWorkflowRequest(StrictRequestModel):
    """Request body for the trigger_workflow tool."""

    repo: str = Field(..., min_length=1, description=_REPO_DESC)
    workflow: str = Field(..., min_length=1, description=_WORKFLOW_DESC)
    ref: str = Field(
        default="main",
        min_length=1,
        description="Branch name, tag, or SHA to run the workflow on",
    )
    inputs: dict[str, str] = Field(
        default_factory=dict,
        description="Input parameters for the workflow (key-value pairs)",
    )
    dry_run: bool = Field(
        default=False,
        description="Preview only; workflow dispatch is not triggered",
    )


class GetWorkflowRunsRequest(StrictRequestModel):
    """Request body for the get_workflow_runs tool."""

    repo: str = Field(..., min_length=1, description=_REPO_DESC)
    workflow: str = Field(..., min_length=1, description=_WORKFLOW_DESC)
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of runs to return",
    )


class GetWorkflowStatusRequest(StrictRequestModel):
    """Request body for the get_workflow_status tool."""

    repo: str = Field(..., min_length=1, description=_REPO_DESC)
    run_id: int = Field(..., gt=0, description=_RUN_ID_DESC)


class GetWorkflowLogsRequest(StrictRequestModel):
    """Request body for the get_workflow_logs tool."""

    repo: str = Field(..., min_length=1, description=_REPO_DESC)
    run_id: int = Field(..., gt=0, description=_RUN_ID_DESC)


# ──────────────────────────────────────────────────────────────────────────────
# Dispatch outcome (response side of the trigger_workflow contract, mcpci002)
# ──────────────────────────────────────────────────────────────────────────────

# Bounded polling window (REQ-003); constants, not configuration (Plan Assumption,
# UNK-02 decided 20261127): the window stays inside the lifespan-owned shared HTTP
# client timeout of 30.0 s.
POLL_TIMEOUT_S = 10
POLL_INTERVAL_S = 2

# The five dispatch states (REQ-001). `outcome_unknown` is reused from the shared
# write-outcome vocabulary rather than redefined; the shared RECONCILE_OUTCOMES set
# is not extended (Plan Design decision, mcpdl004 ownership).
DISPATCH_STATES = frozenset(
    {
        "accepted",
        "confirmed",
        "accepted_unconfirmed",
        OUTCOME_UNKNOWN,
        "reconciliation_required",
    }
)


@dataclasses.dataclass(frozen=True)
class DispatchOutcome:
    """Structured dispatch outcome for trigger_workflow (REQ-001, REQ-003).

    The state is set by the backend row, not by the model; a 2xx response never
    becomes confirmed without a matched run (REQ-001).
    """

    state: str
    run_id: int | None = None
    run_url: str | None = None
    run_status: str | None = None
    workflow: str | None = None
    ref: str | None = None

    def __post_init__(self) -> None:
        if self.state not in DISPATCH_STATES:
            raise ValueError(f"DispatchOutcome: unknown state {self.state!r}")
        if self.state == "confirmed" and self.run_id is None:
            raise ValueError("DispatchOutcome: confirmed requires a matched run")


# ──────────────────────────────────────────────────────────────────────────────
# Log streaming bounds and response contract (mcpci003)
# ──────────────────────────────────────────────────────────────────────────────

# Independent byte limits decided 20261127 (UNK-02); constants, not configuration, so
# `config/cicd_mcp_server.toml` and the docs can state them. `returned_bytes` is the
# caller's own output budget and is enforced by the job backend, not by the helper.
MAX_RAW_DOWNLOAD_BYTES = 1_048_576
MAX_DECOMPRESSED_BYTES = 1_048_576
MAX_REDIRECTS = 3
LOG_FETCH_TIMEOUT_S = 10

# Trusted GitHub-controlled log hosts (UNK-01, resolved 20261127 from GitHub
# documentation and observed 302 targets). The blob entry is a prefix match, not an
# allowlist wildcard, so the config wildcard-rejection rule does not apply here.
TRUSTED_LOG_HOSTS = frozenset(
    {
        "api.github.com",
        "results-receiver.actions.githubusercontent.com",
        "productionresultssa*.blob.core.windows.net",
    }
)

# Per-job statuses and error codes (REQ-004): stable values, never raw exception text.
LOG_JOB_STATUSES = frozenset({"included", "failed", "skipped"})
LOG_ERROR_CODES = frozenset(
    {
        "http_status",
        "address_rejected",
        "redirect",
        "content_type",
        "content_encoding",
        "transport",
    }
)

# Truncation reasons. The first three match `bounded_fetch`'s `TRUNCATED_BY_*` values,
# which the job backend passes through unchanged; `output_budget` is the job backend's
# own final-output limit (REQ-003).
TRUNCATION_REASONS = frozenset({"raw", "decoded", "parser_input", "output_budget"})


@dataclasses.dataclass(frozen=True)
class LogJobResult:
    """Per-job log outcome (REQ-004): failure is a code, not output text.

    `included_bytes` is what this job contributed to the final output — its header,
    its log text, and the truncation marker when one was added. A skipped job
    contributed nothing, so it is 0.
    """

    job_id: int
    status: str
    included_bytes: int
    error_code: str | None = None
    truncated: bool = False

    def __post_init__(self) -> None:
        if self.status not in LOG_JOB_STATUSES:
            raise ValueError(f"LogJobResult: unknown status {self.status!r}")
        if self.status == "failed":
            if self.error_code not in LOG_ERROR_CODES:
                raise ValueError(
                    f"LogJobResult: unknown error code {self.error_code!r}"
                )
        elif self.error_code is not None:
            raise ValueError("LogJobResult: error_code is set only for a failed job")
        if isinstance(self.included_bytes, bool) or self.included_bytes < 0:
            raise ValueError(
                f"LogJobResult: included_bytes must be non-negative: {self.included_bytes!r}"
            )
        if not isinstance(self.truncated, bool):
            raise ValueError("LogJobResult: truncated must be bool")


@dataclasses.dataclass(frozen=True)
class LogTotals:
    """Totals of one log retrieval (REQ-005)."""

    jobs: int
    included_jobs: int
    failed_jobs: int
    downloaded_bytes: int
    visible_bytes: int
    truncation_reason: str | None = None

    def __post_init__(self) -> None:
        if self.truncation_reason not in TRUNCATION_REASONS | {None}:
            raise ValueError(
                f"LogTotals: unknown truncation reason {self.truncation_reason!r}"
            )
        for name in (
            "jobs",
            "included_jobs",
            "failed_jobs",
            "downloaded_bytes",
            "visible_bytes",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"LogTotals: {name} must be a non-negative integer")


@dataclasses.dataclass(frozen=True)
class LogFetchResult:
    """The structured log result: jobs, the assembled output, `partial_success`, and the totals.

    `output` is the final assembled text (job headers, log text, and the truncation marker)
    that the job backend kept inside the byte budget; `totals.visible_bytes` is its byte
    count (user decision 20261127: the text carrier is the result, not a per-job field).
    """

    jobs: tuple[LogJobResult, ...]
    output: str
    partial_success: bool
    totals: LogTotals

    def __post_init__(self) -> None:
        if not isinstance(self.output, str):
            raise ValueError("LogFetchResult: output must be str")
        if not isinstance(self.partial_success, bool):
            raise ValueError("LogFetchResult: partial_success must be bool")
        if len(self.output.encode()) != self.totals.visible_bytes:
            raise ValueError(
                "LogFetchResult: visible_bytes must match the output length"
            )
        included = sum(1 for job in self.jobs if job.status == "included")
        failed = sum(1 for job in self.jobs if job.status == "failed")
        if self.partial_success != (included > 0 and failed > 0):
            raise ValueError(
                "LogFetchResult: partial_success must match the per-job statuses"
            )
        if self.totals.jobs != len(self.jobs):
            raise ValueError("LogFetchResult: totals.jobs must match the job list")
        if self.totals.included_jobs != included or self.totals.failed_jobs != failed:
            raise ValueError("LogFetchResult: totals counts must match the job list")
