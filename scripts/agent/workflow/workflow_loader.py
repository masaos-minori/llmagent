#!/usr/bin/env python3
"""agent/workflow/workflow_loader.py
Load and validate workflow definitions from config/workflows/*.json.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TypedDict, cast

import orjson

from agent.workflow.models import RetryPolicy, StageDefinition, WorkflowDef


class _RetryPolicyJson(TypedDict):
    max_attempts: int
    backoff: str
    backoff_sec: int


class _WorkflowJson(TypedDict):
    name: str
    version: str
    stages: list[_StageJson]
    retry_policy: _RetryPolicyJson


class _StageJson(TypedDict):
    id: str
    description: str
    timeout_sec: int
    retryable: bool


logger = logging.getLogger(__name__)

# config/workflows/ is four parent levels up from this file:
# scripts/agent/workflow/workflow_loader.py -> scripts/agent/workflow/
# -> scripts/agent/ -> scripts/ -> repo root -> config/workflows/
_WORKFLOWS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "config" / "workflows"
)

_REQUIRED_STAGE_KEYS = {"id", "description", "timeout_sec", "retryable"}
_REQUIRED_POLICY_KEYS = {"max_attempts", "backoff", "backoff_sec"}


class WorkflowLoadError(Exception):
    """Raised when a workflow JSON file cannot be loaded or fails validation."""


def _validate(data: _WorkflowJson) -> None:
    """Raise WorkflowLoadError if required keys are missing or have wrong types."""
    for key in ("name", "version", "stages", "retry_policy"):
        if key not in data:
            raise WorkflowLoadError(f"missing required key: {key!r}")
    if not isinstance(data["stages"], list) or not data["stages"]:
        raise WorkflowLoadError("'stages' must be a non-empty list")
    for i, stage in enumerate(data["stages"]):
        missing = _REQUIRED_STAGE_KEYS - stage.keys()
        if missing:
            raise WorkflowLoadError(f"stage[{i}] missing keys: {missing}")
    missing_p = _REQUIRED_POLICY_KEYS - data["retry_policy"].keys()
    if missing_p:
        raise WorkflowLoadError(f"retry_policy missing keys: {missing_p}")


class WorkflowLoader:
    """Loads a WorkflowDef from a JSON file in config/workflows/."""

    def __init__(self, workflows_dir: Path | None = None) -> None:
        self._dir = workflows_dir or _WORKFLOWS_DIR

    def load(self, name: str = "default") -> WorkflowDef:
        """Load and return the named workflow definition."""
        path = self._dir / f"{name}.json"
        if not path.exists():
            raise WorkflowLoadError(f"workflow file not found: {path}")
        try:
            raw = orjson.loads(path.read_bytes())
        except orjson.JSONDecodeError as e:
            raise WorkflowLoadError(f"JSON parse error in {path}: {e}") from e
        if not isinstance(raw, dict):
            raise WorkflowLoadError(f"expected JSON object in {path}")
        data = cast(_WorkflowJson, raw)
        _validate(data)
        stages = [
            StageDefinition(
                id=s["id"],
                description=s["description"],
                timeout_sec=int(s["timeout_sec"]),
                retryable=bool(s["retryable"]),
            )
            for s in data["stages"]
        ]
        policy_data = data["retry_policy"]
        policy = RetryPolicy(
            max_attempts=int(policy_data["max_attempts"]),
            backoff=str(policy_data["backoff"]),
            backoff_sec=int(policy_data["backoff_sec"]),
        )
        wdef = WorkflowDef(
            name=data["name"],
            version=data["version"],
            stages=stages,
            retry_policy=policy,
        )
        logger.debug(
            "Loaded workflow %r v%s (%d stages)",
            wdef.name,
            wdef.version,
            len(wdef.stages),
        )
        return wdef
