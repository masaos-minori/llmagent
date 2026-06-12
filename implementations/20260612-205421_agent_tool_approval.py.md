# Implementation: agent/tool_approval.py — Remove BLE001 noqa, catch PolicyViolationError directly

## Goal

Replace the broad `except Exception as preflight_exc:  # noqa: BLE001` with a direct `except PolicyViolationError as preflight_exc:` in `scripts/agent/tool_approval.py`, eliminating the isinstance guard and the suppression comment.

## Scope

**In:** `scripts/agent/tool_approval.py`
**Out:** No other files change.

## Assumptions

1. `check_preflight()` only raises `PolicyViolationError` when a policy violation is detected. All other exceptions from `check_preflight()` should propagate (they indicate unexpected errors, not policy violations).
2. The current code's `isinstance` guard + re-raise already ensures only `PolicyViolationError` is handled; catching it directly expresses the same intent more clearly.
3. `PolicyViolationError` is defined in `agent.tool_exceptions`. It must be moved to the top-level imports (currently imported inside the except block).

## Implementation

### Target file

`scripts/agent/tool_approval.py`

### Procedure

1. Add `PolicyViolationError` to the top-level import from `agent.tool_exceptions`.
2. Replace the except block (lines ~118–124).

### Method

Two targeted edits: import update + except block replacement.

### Details

**Import update** (existing import line for `agent.tool_exceptions`):
```python
# Before
from agent.tool_exceptions import ApprovalPreviewError, ToolArgumentsDecodeError

# After
from agent.tool_exceptions import ApprovalPreviewError, PolicyViolationError, ToolArgumentsDecodeError
```

**Except block (lines ~116–124):**
```python
# Before
    try:
        check_preflight(ctx.cfg, tool_name, args)
    except Exception as preflight_exc:  # noqa: BLE001 — PolicyViolationError from check_preflight
        from agent.tool_exceptions import PolicyViolationError

        if not isinstance(preflight_exc, PolicyViolationError):
            raise
        audit_approval(
            ctx, tool_name, RiskLevel.HIGH, args, preflight_exc.audit_decision
        )
        emit_denied(tool_name, str(preflight_exc))
        return False

# After
    try:
        check_preflight(ctx.cfg, tool_name, args)
    except PolicyViolationError as preflight_exc:
        audit_approval(
            ctx, tool_name, RiskLevel.HIGH, args, preflight_exc.audit_decision
        )
        emit_denied(tool_name, str(preflight_exc))
        return False
```

## Validation plan

```bash
# Confirm no noqa and no except Exception in tool_approval.py
grep -n "noqa\|except Exception" scripts/agent/tool_approval.py

# Confirm PolicyViolationError is in top-level imports
grep -n "PolicyViolationError" scripts/agent/tool_approval.py

# Lint
uv run ruff check scripts/agent/tool_approval.py

# Type check
uv run mypy scripts/agent/tool_approval.py

# Tests
uv run pytest tests/test_tool_approval.py -v
uv run pytest -v --tb=no -q
```
