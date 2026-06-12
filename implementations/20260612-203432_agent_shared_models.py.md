# Implementation: agent/shared/models.py — Remove dead DTOs, add audit event DTOs

## Goal

Remove the unused `CommandResult` and `ValidationErrorDetail` dataclasses and add three new frozen dataclasses (`ToolApprovalEvent`, `ApprovalDecisionEvent`, `ToolExecEvent`) that give the audit log writer in `agent/tool_audit.py` a typed structure instead of inline dicts.

## Scope

**In:** `scripts/agent/shared/models.py`
**Out:** `agent/tool_audit.py` will be updated in a separate step to use these new types. `agent/tool_models.py` is not modified.

## Assumptions

1. `CommandResult` and `ValidationErrorDetail` have zero references outside `agent/shared/models.py` (confirmed by grep).
2. The three new event DTOs are placed in `agent/shared/models.py` because `agent/shared` is importable from `agent/*` without violating import-linter contracts (`agent` → `shared` is allowed).
3. `resource_scope` stores path/branch strings only (already masked); `dict[str, str]` is accurate.
4. `args_preview` stores masked, sanitized values from `mask_args()`; typing it as `dict[str, object]` is appropriate since value types vary by tool.
5. `ts` is a `float` UNIX timestamp produced by `time.time()`.
6. The `event` field uses `Literal[...]` to make the discriminator explicit and type-safe.
7. `dataclasses.asdict()` is used in `tool_audit.py` to serialize these DTOs via `orjson`.

## Implementation

### Target file

`scripts/agent/shared/models.py`

### Procedure

1. Remove `CommandResult` and `ValidationErrorDetail` class definitions.
2. Add `from __future__ import annotations`.
3. Add imports: `dataclass, field` from `dataclasses`; `Literal` from `typing`.
4. Define `ToolApprovalEvent`, `ApprovalDecisionEvent`, `ToolExecEvent` as `@dataclass(frozen=True)`.

### Method

Full rewrite of `models.py`.

### Details

**Final file content:**
```python
"""agent/shared/models.py
Cross-cutting frozen dataclass DTOs for the agent layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ToolApprovalEvent:
    """Structured audit event for tool_approval log entries."""

    event: Literal["tool_approval"]
    task_id: str
    tool: str
    operation_type: str
    resource_scope: dict[str, str]
    risk: str
    decision: str
    args_preview: dict[str, object]
    ts: float


@dataclass(frozen=True)
class ApprovalDecisionEvent:
    """Structured audit event for approval_decision log entries."""

    event: Literal["approval_decision"]
    task_id: str
    tool: str
    risk_level: str
    decision: str
    escalation_reason: str
    ts: float


@dataclass(frozen=True)
class ToolExecEvent:
    """Structured audit event for tool_exec log entries."""

    event: Literal["tool_exec"]
    task_id: str
    tool: str
    operation_type: str
    resource_scope: dict[str, str]
    mcp_request_id: str
    is_error: bool
    args_preview: dict[str, object]
    ts: float
```

**Key design decisions:**
- `frozen=True` ensures immutability; audit events must not be mutated after creation.
- `Literal["tool_approval"]` etc. on the `event` field makes the discriminant explicit for type checkers and readers.
- No default values: all fields are required to prevent incomplete audit events.
- `dict[str, str]` for `resource_scope` (only path/branch keys) vs `dict[str, object]` for `args_preview` (arbitrary masked values).

## Validation plan

```bash
# Confirm deleted symbols have no remaining references
grep -rn "CommandResult\|ValidationErrorDetail" scripts/ | grep -v "agent/shared/models.py"

# Confirm new symbols are importable
PYTHONPATH=scripts uv run python -c "
from agent.shared.models import ToolApprovalEvent, ApprovalDecisionEvent, ToolExecEvent
print('imports OK')
"

# Lint
uv run ruff check scripts/agent/shared/models.py

# Type check
uv run mypy scripts/agent/shared/models.py

# Architecture boundaries
PYTHONPATH=scripts uv run lint-imports

# Tests (no existing tests for agent/shared; new tests added in tool_audit step)
uv run pytest -v
```
