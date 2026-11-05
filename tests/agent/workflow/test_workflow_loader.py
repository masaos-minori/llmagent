"""tests/test_workflow_loader.py
Unit tests for agent/workflow/workflow_loader.py — load, validate, error cases.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from agent.workflow.workflow_loader import WorkflowLoader, WorkflowLoadError


def _write_json(tmp_path: Path, name: str, data: dict) -> Path:
    p = tmp_path / f"{name}.json"
    p.write_text(json.dumps(data))
    return p


_VALID = {
    "name": "default",
    "version": "1.0.0",
    "stages": [
        {"id": "plan", "timeout_sec": 30, "retryable": False},
        {"id": "execute", "timeout_sec": 120, "retryable": True},
        {"id": "verify", "timeout_sec": 10, "retryable": False},
    ],
    "retry_policy": {"max_attempts": 3, "backoff_sec": 1},
}


class TestWorkflowLoaderLoad:
    def test_load_valid(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "default", _VALID)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        wdef = loader.load()
        assert wdef.name == "default"
        assert wdef.version == "1.0.0"
        assert len(wdef.stages) == 3

    def test_load_stages_mapped(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "default", _VALID)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        wdef = loader.load()
        execute = wdef.get_stage("execute")
        assert execute is not None
        assert execute.timeout_sec == 120
        assert execute.retryable is True

    def test_load_retry_policy(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "default", _VALID)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        wdef = loader.load()
        assert wdef.retry_policy.max_attempts == 3
        assert wdef.retry_policy.backoff_sec == 1

    def test_load_custom_name(self, tmp_path: Path) -> None:
        data = dict(_VALID, name="custom")
        _write_json(tmp_path, "custom", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        wdef = loader.load("custom")
        assert wdef.name == "custom"

    def test_file_not_found(self, tmp_path: Path) -> None:
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="not found"):
            loader.load("missing")

    def test_invalid_json(self, tmp_path: Path) -> None:
        (tmp_path / "default.json").write_text("{not valid json")
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="JSON parse error"):
            loader.load()

    def test_missing_name_key(self, tmp_path: Path) -> None:
        data = {k: v for k, v in _VALID.items() if k != "name"}
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="missing required key"):
            loader.load()

    def test_missing_stages_key(self, tmp_path: Path) -> None:
        data = {k: v for k, v in _VALID.items() if k != "stages"}
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="missing required key"):
            loader.load()

    def test_empty_stages_list(self, tmp_path: Path) -> None:
        data = dict(_VALID, stages=[])
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="non-empty list"):
            loader.load()

    def test_stage_missing_required_key(self, tmp_path: Path) -> None:
        data = dict(_VALID)
        data["stages"] = [
            {"id": "plan"},
            {
                "id": "execute",
                "timeout_sec": 120,
                "retryable": True,
            },
            {"id": "verify", "timeout_sec": 10, "retryable": False},
        ]  # plan stage missing timeout_sec, retryable
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="missing keys"):
            loader.load()

    def test_missing_retry_policy(self, tmp_path: Path) -> None:
        data = {k: v for k, v in _VALID.items() if k != "retry_policy"}
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="missing required key"):
            loader.load()

    def test_duplicate_stage_ids_rejected(self, tmp_path: Path) -> None:
        data = dict(_VALID)
        data["stages"] = [
            {"id": "plan", "timeout_sec": 30, "retryable": False},
            {"id": "plan", "timeout_sec": 60, "retryable": True},
            {"id": "verify", "timeout_sec": 10, "retryable": False},
        ]
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="duplicate stage id"):
            loader.load()

    def test_missing_plan_stage_rejected(self, tmp_path: Path) -> None:
        data = dict(_VALID)
        data["stages"] = [
            {
                "id": "execute",
                "timeout_sec": 120,
                "retryable": True,
            },
            {"id": "verify", "timeout_sec": 10, "retryable": False},
        ]
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="required stages missing"):
            loader.load()

    def test_missing_execute_stage_rejected(self, tmp_path: Path) -> None:
        data = dict(_VALID)
        data["stages"] = [
            {"id": "plan", "timeout_sec": 30, "retryable": False},
            {"id": "verify", "timeout_sec": 10, "retryable": False},
        ]
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="required stages missing"):
            loader.load()

    def test_missing_verify_stage_rejected(self, tmp_path: Path) -> None:
        data = dict(_VALID)
        data["stages"] = [
            {"id": "plan", "timeout_sec": 30, "retryable": False},
            {
                "id": "execute",
                "timeout_sec": 120,
                "retryable": True,
            },
        ]
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="required stages missing"):
            loader.load()

    def test_invalid_retry_policy_rejected(self, tmp_path: Path) -> None:
        data = dict(_VALID)
        data["retry_policy"] = {"max_attempts": 0, "backoff_sec": 1}
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="max_attempts must be >= 1"):
            loader.load()

    def test_negative_backoff_sec_rejected(self, tmp_path: Path) -> None:
        data = dict(_VALID)
        data["retry_policy"] = {
            "max_attempts": 3,
            "backoff_sec": -1,
        }
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="backoff_sec must be >= 0"):
            loader.load()

    def test_default_json_has_no_retry_stage(self) -> None:
        """Real config/workflows/default.json has exactly plan/execute/verify stages."""
        import pathlib

        workflows_dir = (
            pathlib.Path(__file__).parent.parent.parent.parent / "config" / "workflows"
        )
        loader = WorkflowLoader(workflows_dir=workflows_dir)
        wdef = loader.load()
        assert {s.id for s in wdef.stages} == {"plan", "execute", "verify"}


class TestRequireApprovalKeyRejected:
    """INV-10: the workflow has no approval stage; the key is rejected at load time."""

    @pytest.mark.parametrize("value", [True, False, None, "yes", 0])
    def test_require_approval_key_rejected_for_any_value(
        self, tmp_path: Path, value: object
    ) -> None:
        data = dict(_VALID, require_approval=value)
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="require_approval"):
            loader.load()

    def test_definition_without_the_key_loads(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "default", _VALID)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        assert loader.load().name == "default"

    def test_shipped_default_workflow_has_no_require_approval_key(self) -> None:
        """Shipped config/workflows/default.json loads, so it carries no such key."""
        import pathlib

        workflows_dir = (
            pathlib.Path(__file__).parent.parent.parent.parent / "config" / "workflows"
        )
        wdef = WorkflowLoader(workflows_dir=workflows_dir).load()
        assert wdef.name


class TestWorkflowLoaderNumericValidation:
    """REQ-001/REQ-002/REQ-004: numeric fields reject non-int and out-of-range values."""

    @pytest.mark.parametrize("bad", [True, "120", 2.5, None])
    def test_non_int_timeout_sec_rejected(self, tmp_path: Path, bad: object) -> None:
        data = copy.deepcopy(_VALID)
        data["stages"][1]["timeout_sec"] = bad
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="timeout_sec"):
            loader.load()

    @pytest.mark.parametrize("bad", [0, -1])
    def test_non_positive_timeout_sec_rejected(self, tmp_path: Path, bad: int) -> None:
        data = copy.deepcopy(_VALID)
        data["stages"][1]["timeout_sec"] = bad
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="timeout_sec must be >= 1"):
            loader.load()

    @pytest.mark.parametrize("field", ["max_attempts", "backoff_sec"])
    @pytest.mark.parametrize("bad", [True, "3", 2.5, None])
    def test_non_int_policy_number_rejected(
        self, tmp_path: Path, field: str, bad: object
    ) -> None:
        data = copy.deepcopy(_VALID)
        data["retry_policy"][field] = bad
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match=field):
            loader.load()


class TestRetryOn:
    """wfretry001 AC-1 / AC-9: retry_policy.retry_on parsing and validation."""

    def test_valid_retry_on_list_loads_as_tuple(self, tmp_path: Path) -> None:
        data = dict(_VALID)
        data["retry_policy"] = {
            "max_attempts": 3,
            "backoff_sec": 1,
            "retry_on": ["exception", "timeout", "llm_failure"],
        }
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        assert loader.load().retry_policy.retry_on == (
            "exception",
            "timeout",
            "llm_failure",
        )

    def test_absent_retry_on_key_loads_default(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "default", _VALID)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        assert loader.load().retry_policy.retry_on == ("exception",)

    def test_older_format_definition_without_retry_on_loads(
        self, tmp_path: Path
    ) -> None:
        """AC-9: a pre-wfretry001 definition (no retry_on key) still loads."""
        _write_json(tmp_path, "default", _VALID)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        wdef = loader.load()
        assert wdef.name == "default"
        assert wdef.retry_policy.retry_on == ("exception",)

    def test_unknown_kind_rejected(self, tmp_path: Path) -> None:
        data = dict(_VALID)
        data["retry_policy"] = {
            "max_attempts": 3,
            "backoff_sec": 1,
            "retry_on": ["halt"],
        }
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="unknown kind 'halt'"):
            loader.load()

    def test_non_list_retry_on_rejected(self, tmp_path: Path) -> None:
        data = dict(_VALID)
        data["retry_policy"] = {
            "max_attempts": 3,
            "backoff_sec": 1,
            "retry_on": "exception",
        }
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="must be a list of strings"):
            loader.load()

    def test_non_string_element_rejected(self, tmp_path: Path) -> None:
        data = dict(_VALID)
        data["retry_policy"] = {
            "max_attempts": 3,
            "backoff_sec": 1,
            "retry_on": [3],
        }
        _write_json(tmp_path, "default", data)
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(WorkflowLoadError, match="must be a list of strings"):
            loader.load()

    def test_shipped_default_pins_retry_on_exception(self) -> None:
        """Pins procedure 04: shipped config/workflows/default.json carries retry_on."""
        wdef = WorkflowLoader().load("default")
        assert wdef.retry_policy.retry_on == ("exception",)

    def test_preflight_validate_path_loads_shipped_retry_on(self) -> None:
        """REQ-011 / AC-9: python -m agent.workflow.validate performs the same
        validation and accepts the shipped retry_on."""
        import pathlib

        from agent.workflow.validate import validate_path

        path = (
            pathlib.Path(__file__).parent.parent.parent.parent
            / "config"
            / "workflows"
            / "default.json"
        )
        wdef = validate_path(path)
        assert wdef.retry_policy.retry_on == ("exception",)


class TestWorkflowsDirResolver:
    """REQ-002: WORKFLOWS_DIR resolves through the shared resolver.

    ``WORKFLOWS_DIR`` is a module-level constant computed at import time as
    ``resolve_config_dir() / "workflows"``. Asserting its value against a fresh
    ``resolve_config_dir()`` call proves the resolver wires up correctly without
    reloading the shared module (a reload would swap the module's classes and
    leak into other suites that patch ``workflow_loader``). The env-override
    branch of ``resolve_config_dir`` itself is covered by ``test_runtime_paths``.
    """

    def test_workflows_dir_is_resolver_derived(self) -> None:
        """WORKFLOWS_DIR equals resolve_config_dir() / "workflows" (resolver-derived)."""
        from agent.workflow.workflow_loader import WORKFLOWS_DIR
        from shared.runtime_paths import resolve_config_dir

        assert WORKFLOWS_DIR == resolve_config_dir() / "workflows"
