# Implementation: agent/shared/exceptions.py — Remove orphaned symbols

## Goal

Delete all exception classes in `scripts/agent/shared/exceptions.py`.
All six classes (`AgentSharedError`, `ValidationError`, `ConfigurationSchemaError`, `WorkflowStageError`, `UnknownTierError`, `UnknownRoleError`) have zero references outside the file itself and are superseded by domain-specific exceptions in their respective submodules.

## Scope

**In:** `scripts/agent/shared/exceptions.py`
**Out:** No other files change. `agent/commands/exceptions.py`, `agent/services/exceptions.py`, and submodule-specific exception hierarchies remain the canonical sources.

## Assumptions

1. `AgentSharedError`, `ValidationError`, `ConfigurationSchemaError`, `WorkflowStageError`, `UnknownRoleError` are confirmed to have zero references outside `agent/shared/exceptions.py` itself (verified by grep across `scripts/`).
2. `UnknownTierError` in `agent/shared/exceptions.py` is a duplicate of `UnknownTierError` in `agent/commands/exceptions.py`; the commands version inherits from `CommandValidationError` and is the one in active use.
3. No external plugin or test file imports from `agent.shared.exceptions`.

## Implementation

### Target file

`scripts/agent/shared/exceptions.py`

### Procedure

1. Delete all six class definitions.
2. Remove `from __future__ import annotations` since no code remains.
3. Retain the module docstring explaining canonical exception locations.

### Method

Replace the entire file content with just the module docstring.

### Details

**Before:**
```python
"""agent/shared/exceptions.py
Cross-cutting exception hierarchy for the agent layer.
"""

from __future__ import annotations


class AgentSharedError(Exception): ...
class ValidationError(AgentSharedError, ValueError): ...
class ConfigurationSchemaError(AgentSharedError, ValueError): ...
class WorkflowStageError(AgentSharedError, RuntimeError): ...
class UnknownTierError(ValidationError): ...
class UnknownRoleError(ValidationError): ...
```

**After:**
```python
"""agent/shared/exceptions.py
No public exceptions. Canonical sources:
  - command errors     -> agent.commands.exceptions
  - service errors     -> agent.services.exceptions
  - memory errors      -> agent.memory.exceptions
  - tool errors        -> agent.tool_exceptions
"""
```

## Validation plan

```bash
# Confirm zero references to the deleted symbols
grep -rn "from agent.shared.exceptions\|agent\.shared\.exceptions" scripts/
grep -rn "AgentSharedError\|WorkflowStageError\|ConfigurationSchemaError\|UnknownRoleError" scripts/ \
  | grep -v "agent/shared/exceptions.py"

# Lint
uv run ruff check scripts/agent/shared/exceptions.py

# Type check (no new errors)
uv run mypy scripts/

# Architecture boundaries
PYTHONPATH=scripts uv run lint-imports

# Tests
uv run pytest -v
```
