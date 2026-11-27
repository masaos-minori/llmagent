"""tests/mcp_servers/cicd/test_cicd_models.py

Contract tests for scripts/mcp_servers/cicd/cicd_models.py.

These pin the strict request contract (mcpci001): the schema shape the client
sees, the field constraints, the canonical identifier function, and the config
bounds that fail before bind. The description pins carry the wording that was
moved from `cicd_tools.py`'s property dicts to the model fields, so the published
schema and the enforced contract cannot drift.
"""

from __future__ import annotations

import pytest
from mcp_servers.cicd.cicd_models import (
    MAX_ALLOWLIST_SIZE,
    MAX_LOG_SIZE_KB,
    CicdAuthorizationError,
    CicdConfig,
    CicdNotFoundError,
    CicdUpstreamError,
    CicdValidationError,
    GetWorkflowLogsRequest,
    GetWorkflowRunsRequest,
    GetWorkflowStatusRequest,
    TriggerWorkflowRequest,
    canonical_workflow_id,
)
from pydantic import ValidationError

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
