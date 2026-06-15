"""tests/test_workflow_loader.py
Unit tests for agent/workflow/workflow_loader.py — load, validate, error cases.
"""

from __future__ import annotations

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
        {"id": "plan", "description": "d", "timeout_sec": 30, "retryable": False},
        {"id": "execute", "description": "d", "timeout_sec": 120, "retryable": True},
        {"id": "verify", "description": "d", "timeout_sec": 10, "retryable": False},
    ],
    "retry_policy": {"max_attempts": 3, "backoff": "fixed", "backoff_sec": 1},
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
        assert wdef.retry_policy.backoff == "fixed"
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
            {"id": "plan", "description": "d"}
        ]  # missing timeout_sec, retryable
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
