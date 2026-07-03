# Implementation: Create `tests/test_workflow_execution_policy.py`

## Goal

Create a new test file `tests/test_workflow_execution_policy.py` with 11 unit tests for
`WorkflowExecutionPolicy`, covering all 3 modes and all public methods.

## Scope

- In-Scope: New file `tests/test_workflow_execution_policy.py` with `TestWorkflowExecutionPolicy`
  class (11 test methods).
- Out-of-Scope: No changes to production code. No changes to `test_orchestrator.py`.

## Assumptions

1. `scripts/agent/workflow_execution_policy.py` exists (prerequisite: `workflow_execution_policy_py.md`).
2. `WorkflowExecutionPolicy` is importable from `agent.workflow_execution_policy`.
3. `uv run pytest` with `asyncio_mode = "auto"` is the test runner.

## Implementation

### Target file

`tests/test_workflow_execution_policy.py` (new file)

### Procedure

1. Create `tests/test_workflow_execution_policy.py` with the content below.
2. Run `uv run ruff check tests/test_workflow_execution_policy.py` — expect 0 errors.
3. Run `uv run pytest tests/test_workflow_execution_policy.py -v` — expect 11 passed.

### Method

```python
"""tests/test_workflow_execution_policy.py
Unit tests for WorkflowExecutionPolicy covering all three modes and all public methods.
"""

from __future__ import annotations

import pytest
from agent.workflow_execution_policy import WorkflowExecutionPolicy


class TestWorkflowExecutionPolicy:
    def test_disabled_is_workflow_enabled_false(self) -> None:
        policy = WorkflowExecutionPolicy("disabled")
        assert policy.is_workflow_enabled() is False

    def test_auto_is_workflow_enabled_true(self) -> None:
        policy = WorkflowExecutionPolicy("auto")
        assert policy.is_workflow_enabled() is True

    def test_required_is_workflow_enabled_true(self) -> None:
        policy = WorkflowExecutionPolicy("required")
        assert policy.is_workflow_enabled() is True

    def test_required_requires_startup_definition_true(self) -> None:
        policy = WorkflowExecutionPolicy("required")
        assert policy.requires_startup_definition() is True

    def test_auto_requires_startup_definition_false(self) -> None:
        policy = WorkflowExecutionPolicy("auto")
        assert policy.requires_startup_definition() is False

    def test_disabled_requires_startup_definition_false(self) -> None:
        policy = WorkflowExecutionPolicy("disabled")
        assert policy.requires_startup_definition() is False

    def test_auto_allow_startup_fallback_true(self) -> None:
        policy = WorkflowExecutionPolicy("auto")
        assert policy.allow_startup_fallback() is True

    def test_disabled_allow_startup_fallback_false(self) -> None:
        policy = WorkflowExecutionPolicy("disabled")
        assert policy.allow_startup_fallback() is False

    def test_allow_turn_fallback_always_false(self) -> None:
        for mode in ("disabled", "auto", "required"):
            policy = WorkflowExecutionPolicy(mode)
            assert policy.allow_turn_fallback(RuntimeError("err")) is False

    def test_fail_closed_on_creation_error_always_true(self) -> None:
        for mode in ("disabled", "auto", "required"):
            policy = WorkflowExecutionPolicy(mode)
            assert policy.fail_closed_on_creation_error() is True

    def test_invalid_mode_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid workflow_mode"):
            WorkflowExecutionPolicy("unknown_mode")
```

### Details

- `test_allow_turn_fallback_always_false` iterates all 3 modes to confirm fail-closed behavior
  in every case — a single test covers all modes cleanly.
- `test_fail_closed_on_creation_error_always_true` follows the same pattern.
- `test_invalid_mode_raises_value_error` verifies input validation at construction time.

## Validation plan

```bash
# Lint
uv run ruff check tests/test_workflow_execution_policy.py
# Expected: 0 errors

# Run 11 tests
uv run pytest tests/test_workflow_execution_policy.py -v
# Expected: 11 passed

# Orchestrator regression
uv run pytest tests/test_orchestrator.py -q
# Expected: all pass
```
