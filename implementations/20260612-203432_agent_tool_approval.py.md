# Implementation: agent/tool_approval.py — Remove deprecated ApprovalDecision TypedDict

## Goal

Delete the `ApprovalDecision` TypedDict class from `scripts/agent/tool_approval.py`.
The class was marked deprecated in a previous refactor and has no callers; `ApprovalOutcome` in `agent/tool_models.py` is the active replacement.

## Scope

**In:** `scripts/agent/tool_approval.py` — remove `ApprovalDecision` class definition and its import dependency (`TypedDict` from `typing`).
**Out:** No other files change. `ApprovalOutcome` in `agent/tool_models.py` is not modified.

## Assumptions

1. `ApprovalDecision` is imported nowhere outside `agent/tool_approval.py` (confirmed by grep: zero external references).
2. After removing `ApprovalDecision`, the `TypedDict` import from `typing` becomes unused and must be removed.
3. Removing the class has no runtime effect since nothing constructs or references it.

## Implementation

### Target file

`scripts/agent/tool_approval.py`

### Procedure

1. Delete the `ApprovalDecision` class definition (including its docstring).
2. Remove `TypedDict` from the `from typing import ...` line.
3. If `Any` is still used elsewhere in the file, retain it; otherwise remove it too.

### Method

Targeted deletion: remove the class block and update the import line.

### Details

**Lines to delete (class definition):**
```python
class ApprovalDecision(TypedDict, total=False):
    """Deprecated: use ApprovalOutcome DTO instead.

    Retained for backward compatibility with existing callers.
    """

    tool_name: str
    risk_level: str
    decision: str
    escalation_reason: str
    preview: str
```

**Import line before:**
```python
from typing import TYPE_CHECKING, Any, TypedDict
```

**Import line after:**
```python
from typing import TYPE_CHECKING, Any
```

Note: `Any` is still used in `_build_preview_with_dry_run` and `run_approval_checks` as `dict[str, Any]`, so it must be retained.

## Validation plan

```bash
# Confirm the class is gone
grep -n "ApprovalDecision\|TypedDict" scripts/agent/tool_approval.py

# Confirm no external references exist
grep -rn "ApprovalDecision" scripts/ | grep -v "tool_approval.py"

# Lint
uv run ruff check scripts/agent/tool_approval.py

# Type check
uv run mypy scripts/agent/tool_approval.py

# Tests (tool_approval is covered by test_tool_approval.py)
uv run pytest tests/test_tool_approval.py -v
uv run pytest -v
```
