#!/usr/bin/env python3
"""scripts/agent/workflow/workflow_loader.py

Load and validate workflow definitions from config/workflows/*.json.

Validation refuses malformed shapes before any subscript: each stage and
``retry_policy`` must be a JSON object, and ``retryable`` must be a strict JSON
bool; every failure raises ``WorkflowLoadError`` naming the offending field.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TypedDict, cast

import orjson
from shared.runtime_paths import resolve_config_dir

from agent.workflow.models import RetryPolicy, StageDefinition, WorkflowDef


class _RetryPolicyJson(TypedDict, total=False):
    """JSON representation of a workflow retry policy.

    max_attempts and backoff_sec are required at runtime, enforced by
    _REQUIRED_POLICY_KEYS in _validate; retry_on is optional (REQ-001).
    """

    max_attempts: int
    backoff_sec: int
    retry_on: list[str]


class _WorkflowJson(TypedDict, total=False):
    """JSON representation of a workflow definition."""

    name: str
    version: str
    stages: list[_StageJson]
    retry_policy: _RetryPolicyJson


class _StageJson(TypedDict):
    """JSON representation of a single workflow stage."""

    id: str
    timeout_sec: int
    retryable: bool


logger = logging.getLogger(__name__)

# config/workflows/ is four parent levels up from this file:
WORKFLOWS_DIR = resolve_config_dir() / "workflows"
_REQUIRED_STAGE_KEYS = {"id", "timeout_sec", "retryable"}
_REQUIRED_POLICY_KEYS = {"max_attempts", "backoff_sec"}
_REQUIRED_STAGES = {"plan", "execute", "verify"}


class WorkflowLoadError(Exception):
    """Raised when a workflow JSON file cannot be loaded or fails validation."""


_RETRY_KINDS = frozenset({"exception", "timeout", "llm_failure"})


def _validate_retry_on(policy: _RetryPolicyJson) -> tuple[str, ...]:
    """Validate retry_policy.retry_on and return it as a tuple of kinds.

    An absent key returns the default ("exception",). A present key must be a
    list of strings drawn from _RETRY_KINDS.
    """
    raw = policy.get("retry_on")
    if raw is None:
        return ("exception",)
    if not isinstance(raw, list) or not all(isinstance(kind, str) for kind in raw):
        raise WorkflowLoadError("retry_policy.retry_on must be a list of strings")
    for kind in raw:
        if kind not in _RETRY_KINDS:
            raise WorkflowLoadError(
                f"retry_policy.retry_on contains unknown kind {kind!r} "
                "(allowed: exception, timeout, llm_failure)"
            )
    return tuple(raw)


def _require_int(value: object, label: str, minimum: int) -> int:
    """Validate that value is a strict int (rejecting bool/float/str/None) and >= minimum.

    Raises WorkflowLoadError naming the field for a wrong type or a value below
    the minimum. ``type(value) is not int`` rejects ``bool`` even though it is a
    subclass of ``int``.
    """
    if type(value) is not int:
        raise WorkflowLoadError(
            f"{label} must be an integer, got {type(value).__name__}: {value!r}"
        )
    if value < minimum:
        raise WorkflowLoadError(f"{label} must be >= {minimum}")
    return value


def _require_dict(value: object, label: str) -> dict[str, object]:
    """Validate that value is a strict dict.

    Raises WorkflowLoadError naming the field for any other type. Mirrors
    _require_int's strictness and message shape.
    """
    if type(value) is not dict:
        raise WorkflowLoadError(
            f"{label} must be a dict, got {type(value).__name__}: {value!r}"
        )
    return value


def _validate(data: _WorkflowJson) -> None:
    """Raise WorkflowLoadError for missing keys, wrong shapes, wrong numeric types, or out-of-range values."""
    for key in ("name", "version", "stages", "retry_policy"):
        if key not in data:
            raise WorkflowLoadError(f"missing required key: {key!r}")
    stages_data = data.get("stages", [])
    if not isinstance(stages_data, list) or not stages_data:
        raise WorkflowLoadError("'stages' must be a non-empty list")
    for index, stage in enumerate(stages_data):
        _require_dict(stage, f"stage {index}")
    stage_ids = [s.get("id") for s in stages_data]
    for sid in stage_ids:
        if sid is None:
            continue
        count = sum(1 for s in stages_data if s.get("id") == sid)
        if count > 1:
            raise WorkflowLoadError(f"duplicate stage id: {sid!r}")
    found_stage_ids = set(stage_ids)
    missing_stages = _REQUIRED_STAGES - found_stage_ids
    if missing_stages:
        raise WorkflowLoadError(
            f"required stages missing: {', '.join(sorted(missing_stages))}"
        )
    for i, stage in enumerate(stages_data):
        missing = _REQUIRED_STAGE_KEYS - stage.keys()
        if missing:
            raise WorkflowLoadError(f"stage[{i}] missing keys: {missing}")
        _require_int(stage["timeout_sec"], f"stages[{i}].timeout_sec", 1)
        if type(stage["retryable"]) is not bool:
            raise WorkflowLoadError(
                f"stages[{i}].retryable must be a bool, "
                f"got {type(stage['retryable']).__name__}: {stage['retryable']!r}"
            )
    retry_policy_data = data.get("retry_policy", {})
    _require_dict(retry_policy_data, "retry_policy")
    missing_p = _REQUIRED_POLICY_KEYS - retry_policy_data.keys()
    if missing_p:
        raise WorkflowLoadError(f"retry_policy missing keys: {missing_p}")
    policy = retry_policy_data
    _require_int(policy["max_attempts"], "retry_policy.max_attempts", 1)
    _require_int(policy["backoff_sec"], "retry_policy.backoff_sec", 0)
    _validate_retry_on(policy)
    if "require_approval" in data:
        raise WorkflowLoadError(
            "require_approval is no longer supported: the workflow has no approval "
            "stage (human approval is decided before a Tool executes)"
        )


class WorkflowLoader:
    """Loads a WorkflowDef from a JSON file in config/workflows/."""

    def __init__(self, workflows_dir: Path | None = None) -> None:
        """Initialize the workflow loader with the directory containing workflow JSON definitions."""
        self._dir = workflows_dir or WORKFLOWS_DIR

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
                timeout_sec=s["timeout_sec"],
                retryable=bool(s["retryable"]),
            )
            for s in data.get("stages", [])
        ]
        policy_data = data.get("retry_policy", {})
        policy = RetryPolicy(
            max_attempts=policy_data["max_attempts"],
            backoff_sec=policy_data["backoff_sec"],
            retry_on=_validate_retry_on(policy_data),
        )
        wdef = WorkflowDef(
            name=data.get("name", ""),
            version=data.get("version", ""),
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
