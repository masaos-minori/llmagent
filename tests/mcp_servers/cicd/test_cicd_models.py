"""tests/mcp_servers/cicd/test_cicd_models.py

Contract tests for scripts/mcp_servers/cicd/cicd_models.py.

These pin the strict request contract (mcpci001): the schema shape the client
sees, the field constraints, the canonical identifier function, and the config
bounds that fail before bind. The description pins carry the wording that was
moved from `cicd_tools.py`'s property dicts to the model fields, so the published
schema and the enforced contract cannot drift. The log response model and the
streaming-bound constants (mcpci003) are pinned here as well, so the values the
config file and the docs record cannot drift from the module constants.
"""

from __future__ import annotations

import pytest
from mcp_servers.cicd.cicd_models import (
    CICD_ERROR_CODES,
    DISPATCH_STATES,
    EXCEPTION_ERROR_CODES,
    LOG_ERROR_CODES,
    LOG_FETCH_TIMEOUT_S,
    LOG_JOB_STATUSES,
    MAX_ALLOWLIST_SIZE,
    MAX_DECOMPRESSED_BYTES,
    MAX_ERROR_TEXT_LENGTH,
    MAX_LOG_SIZE_KB,
    MAX_RAW_DOWNLOAD_BYTES,
    MAX_REDIRECTS,
    POLL_INTERVAL_S,
    POLL_TIMEOUT_S,
    TRUNCATION_REASONS,
    TRUSTED_LOG_HOSTS,
    CicdAuthorizationError,
    CicdConfig,
    CicdConflictError,
    CicdNotFoundError,
    CicdRateLimitError,
    CicdUpstreamError,
    CicdValidationError,
    DispatchOutcome,
    GetWorkflowLogsRequest,
    GetWorkflowRunsRequest,
    GetWorkflowStatusRequest,
    LogFetchResult,
    LogJobResult,
    LogTotals,
    TriggerWorkflowRequest,
    canonical_workflow_id,
)
from pydantic import ValidationError
from shared.write_outcome import OUTCOME_UNKNOWN

_REPO_DESC = "Repository slug in 'owner/repo' format"
_WORKFLOW_DESC = "Workflow file name (e.g. ci.yml) or numeric workflow ID"
_RUN_ID_DESC = "Workflow run ID (from get_workflow_runs output)"

# ──────────────────────────────────────────────────────────────────────────────
# JSON schema shape (public API surface seen by MCP clients)
# ──────────────────────────────────────────────────────────────────────────────


def test_trigger_workflow_request_schema() -> None:
    schema = TriggerWorkflowRequest.model_json_schema()
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["repo", "workflow"]
    assert schema["properties"]["repo"]["description"] == _REPO_DESC
    assert schema["properties"]["repo"]["minLength"] == 1
    assert schema["properties"]["workflow"]["description"] == _WORKFLOW_DESC
    assert schema["properties"]["workflow"]["minLength"] == 1
    assert schema["properties"]["ref"]["default"] == "main"
    assert schema["properties"]["ref"]["minLength"] == 1
    assert (
        schema["properties"]["ref"]["description"]
        == "Branch name, tag, or SHA to run the workflow on"
    )
    assert schema["properties"]["inputs"]["type"] == "object"
    assert (
        schema["properties"]["inputs"]["description"]
        == "Input parameters for the workflow (key-value pairs)"
    )
    assert schema["properties"]["dry_run"]["default"] is False
    assert (
        schema["properties"]["dry_run"]["description"]
        == "Preview only; workflow dispatch is not triggered"
    )


def test_get_workflow_runs_request_schema() -> None:
    schema = GetWorkflowRunsRequest.model_json_schema()
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["repo", "workflow"]
    assert schema["properties"]["repo"]["description"] == _REPO_DESC
    assert schema["properties"]["workflow"]["description"] == _WORKFLOW_DESC
    assert schema["properties"]["limit"]["default"] == 10
    assert schema["properties"]["limit"]["minimum"] == 1
    assert schema["properties"]["limit"]["maximum"] == 50
    assert (
        schema["properties"]["limit"]["description"]
        == "Maximum number of runs to return"
    )


def test_get_workflow_status_request_schema() -> None:
    schema = GetWorkflowStatusRequest.model_json_schema()
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["repo", "run_id"]
    assert schema["properties"]["repo"]["description"] == _REPO_DESC
    assert schema["properties"]["run_id"]["exclusiveMinimum"] == 0
    assert schema["properties"]["run_id"]["description"] == _RUN_ID_DESC


def test_get_workflow_logs_request_schema() -> None:
    schema = GetWorkflowLogsRequest.model_json_schema()
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["repo", "run_id"]
    assert schema["properties"]["repo"]["description"] == _REPO_DESC
    assert schema["properties"]["run_id"]["exclusiveMinimum"] == 0
    assert schema["properties"]["run_id"]["description"] == _RUN_ID_DESC


# ──────────────────────────────────────────────────────────────────────────────
# Field validation / boundary behavior
# ──────────────────────────────────────────────────────────────────────────────


def test_trigger_workflow_request_requires_repo_and_workflow() -> None:
    with pytest.raises(ValidationError):
        TriggerWorkflowRequest.model_validate({})


def test_trigger_workflow_request_applies_defaults() -> None:
    req = TriggerWorkflowRequest(repo="o/r", workflow="ci.yml")
    assert req.ref == "main"
    assert req.inputs == {}
    assert req.dry_run is False


def test_trigger_workflow_request_rejects_extra_field() -> None:
    with pytest.raises(ValidationError):
        TriggerWorkflowRequest(repo="o/r", workflow="ci.yml", unexpected="x")


@pytest.mark.parametrize("field", ["repo", "workflow", "ref"])
def test_request_models_reject_blank_string(field: str) -> None:
    with pytest.raises(ValidationError):
        TriggerWorkflowRequest.model_validate(
            {"repo": "o/r", "workflow": "ci.yml", field: ""}
        )


@pytest.mark.parametrize("limit", [0, 51])
def test_get_workflow_runs_request_rejects_out_of_range_limit(limit: int) -> None:
    with pytest.raises(ValidationError):
        GetWorkflowRunsRequest(repo="o/r", workflow="ci.yml", limit=limit)


@pytest.mark.parametrize("limit", [1, 50])
def test_get_workflow_runs_request_accepts_boundary_limit(limit: int) -> None:
    req = GetWorkflowRunsRequest(repo="o/r", workflow="ci.yml", limit=limit)
    assert req.limit == limit


def test_get_workflow_runs_request_default_limit() -> None:
    req = GetWorkflowRunsRequest(repo="o/r", workflow="ci.yml")
    assert req.limit == 10


@pytest.mark.parametrize("run_id", [0, -1])
def test_get_workflow_status_request_rejects_non_positive_run_id(run_id: int) -> None:
    with pytest.raises(ValidationError):
        GetWorkflowStatusRequest(repo="o/r", run_id=run_id)


def test_get_workflow_logs_request_rejects_non_positive_run_id() -> None:
    with pytest.raises(ValidationError):
        GetWorkflowLogsRequest(repo="o/r", run_id=0)


def test_get_workflow_status_request_accepts_positive_run_id() -> None:
    req = GetWorkflowStatusRequest(repo="o/r", run_id=123)
    assert req.run_id == 123


# ──────────────────────────────────────────────────────────────────────────────
# Canonical workflow identifier
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("ci.yml", "ci.yml"),
        ("CI.yml", "ci.yml"),
        ("  ci.yml  ", "ci.yml"),
        ("123", "123"),
    ],
)
def test_canonical_workflow_id_accepts_both_forms(value: str, expected: str) -> None:
    assert canonical_workflow_id(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "workflows/build.yml",
        "build\\release",
        "%63i.yml",
        "*",
        "ci.*.yml",
        "0",
    ],
)
def test_canonical_workflow_id_rejects_unusable_forms(value: str) -> None:
    with pytest.raises(CicdValidationError):
        canonical_workflow_id(value)


# ──────────────────────────────────────────────────────────────────────────────
# CicdConfig
# ──────────────────────────────────────────────────────────────────────────────


def test_cicd_config_from_dict_defaults() -> None:
    config = CicdConfig.from_dict({})
    assert config.auth_token == ""
    assert config.repo_allowlist == []
    assert config.workflow_allowlist == []
    assert config.max_log_size_kb == 256
    assert config.github_token == ""


def test_cicd_config_from_dict_populated() -> None:
    config = CicdConfig.from_dict(
        {
            "auth_token": "tok",
            "repo_allowlist": ["o/r"],
            "workflow_allowlist": ["ci.yml"],
            "max_log_size_kb": 512,
            "github_token": "ghtok",
        }
    )
    assert config.auth_token == "tok"
    assert config.repo_allowlist == ["o/r"]
    assert config.workflow_allowlist == ["ci.yml"]
    assert config.max_log_size_kb == 512
    assert config.github_token == "ghtok"


def test_cicd_config_from_dict_rejects_non_integer_max_log_size_kb() -> None:
    with pytest.raises(ValueError):
        CicdConfig.from_dict({"max_log_size_kb": 1.5})


def test_cicd_config_from_dict_rejects_bool_max_log_size_kb() -> None:
    with pytest.raises(ValueError):
        CicdConfig.from_dict({"max_log_size_kb": True})


@pytest.mark.parametrize("max_log_size_kb", [0, -1, MAX_LOG_SIZE_KB + 1])
def test_cicd_config_from_dict_rejects_max_log_size_kb_outside_bounds(
    max_log_size_kb: int,
) -> None:
    with pytest.raises(ValueError):
        CicdConfig.from_dict({"max_log_size_kb": max_log_size_kb})


@pytest.mark.parametrize("max_log_size_kb", [1, MAX_LOG_SIZE_KB])
def test_cicd_config_from_dict_accepts_boundary_max_log_size_kb(
    max_log_size_kb: int,
) -> None:
    config = CicdConfig.from_dict({"max_log_size_kb": max_log_size_kb})
    assert config.max_log_size_kb == max_log_size_kb


def test_cicd_config_from_dict_rejects_non_list_repo_allowlist() -> None:
    with pytest.raises(ValueError):
        CicdConfig.from_dict({"repo_allowlist": "o/r"})


def test_cicd_config_from_dict_rejects_wildcard_allowlist_entry() -> None:
    with pytest.raises(ValueError):
        CicdConfig.from_dict({"repo_allowlist": ["*"]})


def test_cicd_config_from_dict_rejects_wildcard_workflow_entry() -> None:
    with pytest.raises(ValueError):
        CicdConfig.from_dict({"workflow_allowlist": ["*.yml"]})


def test_cicd_config_from_dict_rejects_oversized_allowlist() -> None:
    entries = [f"o/r{i}" for i in range(MAX_ALLOWLIST_SIZE + 1)]
    with pytest.raises(ValueError):
        CicdConfig.from_dict({"repo_allowlist": entries})


def test_cicd_config_from_dict_accepts_boundary_allowlist_size() -> None:
    entries = [f"o/r{i}" for i in range(MAX_ALLOWLIST_SIZE)]
    config = CicdConfig.from_dict({"repo_allowlist": entries})
    assert len(config.repo_allowlist) == MAX_ALLOWLIST_SIZE


def test_cicd_config_from_dict_rejects_non_canonical_repo_entry() -> None:
    with pytest.raises(ValueError):
        CicdConfig.from_dict({"repo_allowlist": ["Owner/Repo"]})


def test_cicd_config_from_dict_rejects_workflow_entry_with_separator() -> None:
    with pytest.raises(ValueError):
        CicdConfig.from_dict({"workflow_allowlist": ["workflows/build.yml"]})


# ──────────────────────────────────────────────────────────────────────────────
# Domain exceptions — type hierarchy relied upon by callers
# ──────────────────────────────────────────────────────────────────────────────


def test_exception_hierarchy() -> None:
    assert issubclass(CicdAuthorizationError, RuntimeError)
    assert issubclass(CicdNotFoundError, ValueError)
    assert issubclass(CicdValidationError, ValueError)
    assert issubclass(CicdUpstreamError, RuntimeError)
    # mcpci004: the two new types keep the RuntimeError base the callers rely on.
    assert issubclass(CicdConflictError, RuntimeError)
    assert issubclass(CicdRateLimitError, RuntimeError)


def test_error_code_vocabulary_is_the_ci_cd_frozenset() -> None:
    assert CICD_ERROR_CODES == frozenset(
        {
            "authorization_error",
            "not_found",
            "validation_error",
            "upstream_error",
            "conflict",
            "rate_limit",
            # The audit category for an unexpected failure has no exception class, so
            # it is a vocabulary code with no mapping entry.
            "unexpected_error",
        }
    )


def test_exception_error_codes_map_into_the_vocabulary() -> None:
    # `unexpected_error` is the only code with no exception mapping.
    assert set(EXCEPTION_ERROR_CODES.values()) < CICD_ERROR_CODES
    assert EXCEPTION_ERROR_CODES[CicdConflictError] == "conflict"
    assert EXCEPTION_ERROR_CODES[CicdRateLimitError] == "rate_limit"


def test_rate_limit_error_carries_the_preserved_metadata_fields() -> None:
    exc = CicdRateLimitError(
        "Too many requests", retry_after="30", rate_limit_reset="1714000000"
    )
    assert exc.retry_after == "30"
    assert exc.rate_limit_reset == "1714000000"


def test_max_error_text_length_is_a_positive_bound() -> None:
    # The bound is pinned as a bound; the backend test asserts the behavior rather
    # than this specific value (UNK-04).
    assert MAX_ERROR_TEXT_LENGTH > 0


# ──────────────────────────────────────────────────────────────────────────────
# Dispatch outcome (mcpci002 response model)
# ──────────────────────────────────────────────────────────────────────────────


def test_dispatch_states_are_the_five_states() -> None:
    assert DISPATCH_STATES == frozenset(
        {
            "accepted",
            "confirmed",
            "accepted_unconfirmed",
            OUTCOME_UNKNOWN,
            "reconciliation_required",
        }
    )
    # outcome_unknown is the shared write-outcome vocabulary value, not a redefinition.
    assert OUTCOME_UNKNOWN in DISPATCH_STATES


def test_polling_constants_are_the_decided_bounds() -> None:
    assert POLL_TIMEOUT_S == 10
    assert POLL_INTERVAL_S == 2


def test_dispatch_outcome_shape() -> None:
    outcome = DispatchOutcome(state="accepted")
    assert outcome.state == "accepted"
    assert outcome.run_id is None
    assert outcome.run_url is None
    assert outcome.run_status is None
    assert outcome.workflow is None
    assert outcome.ref is None


def test_confirmed_requires_a_matched_run() -> None:
    with pytest.raises(ValueError):
        DispatchOutcome(state="confirmed")
    outcome = DispatchOutcome(
        state="confirmed",
        run_id=42,
        run_url="https://github.com/o/r/actions/runs/42",
        run_status="completed",
        workflow="ci.yml",
        ref="main",
    )
    assert outcome.run_id == 42
    assert outcome.run_url == "https://github.com/o/r/actions/runs/42"
    assert outcome.run_status == "completed"
    assert outcome.workflow == "ci.yml"
    assert outcome.ref == "main"


@pytest.mark.parametrize("state", sorted(DISPATCH_STATES - {"confirmed"}))
def test_states_without_matched_run_are_constructible(state: str) -> None:
    assert DispatchOutcome(state=state).state == state


def test_dispatch_outcome_rejects_unknown_state() -> None:
    with pytest.raises(ValueError):
        DispatchOutcome(state="applied")


# ──────────────────────────────────────────────────────────────────────────────
# Log streaming bounds and response model (mcpci003)
# ──────────────────────────────────────────────────────────────────────────────


def test_log_limits_are_the_decided_values() -> None:
    # These are the values recorded in config/cicd_mcp_server.toml and the docs.
    assert MAX_RAW_DOWNLOAD_BYTES == 1_048_576
    assert MAX_DECOMPRESSED_BYTES == 1_048_576
    assert MAX_REDIRECTS == 3
    assert LOG_FETCH_TIMEOUT_S == 10


def test_trusted_log_hosts_are_the_github_controlled_hosts() -> None:
    assert TRUSTED_LOG_HOSTS == frozenset(
        {
            "api.github.com",
            "results-receiver.actions.githubusercontent.com",
            "productionresultssa*.blob.core.windows.net",
        }
    )


def test_log_vocabulary_is_the_stable_contract() -> None:
    assert LOG_JOB_STATUSES == frozenset({"included", "failed", "skipped"})
    assert LOG_ERROR_CODES == frozenset(
        {
            "http_status",
            "address_rejected",
            "redirect",
            "content_type",
            "content_encoding",
            "transport",
        }
    )
    # The first three are bounded_fetch's TRUNCATED_BY_* values passed through unchanged.
    assert TRUNCATION_REASONS == frozenset(
        {"raw", "decoded", "parser_input", "output_budget"}
    )


def test_log_job_result_shape() -> None:
    job = LogJobResult(
        job_id=7, status="failed", included_bytes=0, error_code="http_status"
    )
    assert job.job_id == 7
    assert job.status == "failed"
    assert job.included_bytes == 0
    assert job.error_code == "http_status"
    assert job.truncated is False


def test_log_job_result_rejects_a_code_on_a_non_failed_job() -> None:
    with pytest.raises(ValueError):
        LogJobResult(
            job_id=1, status="included", included_bytes=4, error_code="transport"
        )
    with pytest.raises(ValueError):
        LogJobResult(job_id=1, status="failed", included_bytes=0, error_code="unknown")
    with pytest.raises(ValueError):
        LogJobResult(job_id=1, status="unknown", included_bytes=0)
    with pytest.raises(ValueError):
        LogJobResult(job_id=1, status="skipped", included_bytes=-1)


def test_log_totals_shape() -> None:
    totals = LogTotals(
        jobs=2,
        included_jobs=1,
        failed_jobs=1,
        downloaded_bytes=4,
        visible_bytes=19,
        truncation_reason="raw",
    )
    assert totals.truncation_reason == "raw"
    with pytest.raises(ValueError):
        LogTotals(
            jobs=1,
            included_jobs=0,
            failed_jobs=1,
            downloaded_bytes=0,
            visible_bytes=0,
            truncation_reason="memory",
        )


def test_log_fetch_result_shape() -> None:
    output = "=== Job: build ===\nlog\n"
    result = LogFetchResult(
        jobs=(
            LogJobResult(job_id=1, status="included", included_bytes=23),
            LogJobResult(
                job_id=2, status="failed", included_bytes=0, error_code="http_status"
            ),
        ),
        output=output,
        partial_success=True,
        totals=LogTotals(
            jobs=2,
            included_jobs=1,
            failed_jobs=1,
            downloaded_bytes=4,
            visible_bytes=len(output.encode()),
        ),
    )
    assert result.partial_success is True
    assert result.totals.visible_bytes == len(result.output.encode())
    assert result.jobs[1].error_code == "http_status"


def test_log_fetch_result_rejects_a_counts_or_partial_mismatch() -> None:
    job = LogJobResult(
        job_id=1, status="failed", included_bytes=0, error_code="transport"
    )
    totals = LogTotals(
        jobs=1,
        included_jobs=0,
        failed_jobs=1,
        downloaded_bytes=0,
        visible_bytes=0,
    )
    with pytest.raises(ValueError):
        LogFetchResult(jobs=(job,), output="x", partial_success=False, totals=totals)
    with pytest.raises(ValueError):
        LogFetchResult(
            jobs=(job,),
            output="",
            partial_success=True,
            totals=LogTotals(
                jobs=1,
                included_jobs=1,
                failed_jobs=0,
                downloaded_bytes=0,
                visible_bytes=0,
            ),
        )
