# Implementation: Create `scripts/agent/workflow_execution_policy.py`

## Goal

Create a new `WorkflowExecutionPolicy` class in `scripts/agent/workflow_execution_policy.py`
that centralizes all `workflow_mode` string comparisons. Replaces scattered
`if self._workflow_mode == "required"` / `"disabled"` / `"auto"` checks in `orchestrator.py`
and `repl_health.py` with policy method calls.

## Scope

- In-Scope: New file `scripts/agent/workflow_execution_policy.py` with `WorkflowExecutionPolicy`
  class containing 5 methods: `is_workflow_enabled()`, `requires_startup_definition()`,
  `allow_startup_fallback()`, `allow_turn_fallback()`, `fail_closed_on_creation_error()`.
- Out-of-Scope: No changes to `orchestrator.py`, `repl_health.py`, or `startup.py` in this step
  (covered by separate docs).

## Assumptions

1. Valid `workflow_mode` values are `"disabled"`, `"auto"`, `"required"`.
2. An invalid mode raises `ValueError` at construction time.
3. `agent → agent` imports are allowed (no layer violation).
4. No imports from `shared.*` or `db.*` are needed — stdlib only.

## Implementation

### Target file

`scripts/agent/workflow_execution_policy.py` (new file)

### Procedure

1. Create `scripts/agent/workflow_execution_policy.py` with the content below.
2. Run `uv run ruff check scripts/agent/workflow_execution_policy.py` — expect 0 errors.
3. Run `uv run mypy scripts/agent/workflow_execution_policy.py` — expect 0 errors.
4. Verify importable:
   ```bash
   PYTHONPATH=scripts python -c "from agent.workflow_execution_policy import WorkflowExecutionPolicy; print('OK')"
   ```

### Method

```python
#!/usr/bin/env python3
"""agent/workflow_execution_policy.py — Centralizes workflow_mode decisions."""

from __future__ import annotations


class WorkflowExecutionPolicy:
    """Centralizes workflow_mode decisions for Orchestrator and startup checks.

    mode="disabled": always use direct LLM path; no workflow definition required.
    mode="required": require workflow definition at startup; fail startup on errors.
    mode="auto":     allow startup degradation; fail-closed at turn time.
    """

    _VALID_MODES: frozenset[str] = frozenset({"disabled", "auto", "required"})

    def __init__(self, mode: str = "auto") -> None:
        if mode not in self._VALID_MODES:
            raise ValueError(
                f"Invalid workflow_mode {mode!r}. Must be one of: {sorted(self._VALID_MODES)}"
            )
        self._mode = mode

    @property
    def mode(self) -> str:
        return self._mode

    def is_workflow_enabled(self) -> bool:
        return self._mode != "disabled"

    def requires_startup_definition(self) -> bool:
        return self._mode == "required"

    def allow_startup_fallback(self) -> bool:
        return self._mode == "auto"

    def allow_turn_fallback(self, error: Exception) -> bool:
        return False  # fail-closed in all modes where workflow is used

    def fail_closed_on_creation_error(self) -> bool:
        return True  # WorkflowCreationError never triggers direct-execution fallback
```

### Details

- `allow_turn_fallback` always returns `False` — the design is fail-closed: a workflow creation
  error at turn time never silently falls back to the direct LLM path.
- `fail_closed_on_creation_error` always returns `True` for the same reason.
- The `mode` property allows `orchestrator.workflow_status()` to return the mode string for
  display without exposing the private `_mode` field directly.

## Validation plan

```bash
# Importable
PYTHONPATH=scripts python -c "from agent.workflow_execution_policy import WorkflowExecutionPolicy; print('OK')"
# Expected: OK

# Lint
uv run ruff check scripts/agent/workflow_execution_policy.py
# Expected: 0 errors

# Type check
uv run mypy scripts/agent/workflow_execution_policy.py
# Expected: 0 errors

# Architecture
PYTHONPATH=scripts uv run lint-imports
# Expected: 0 violations
```
