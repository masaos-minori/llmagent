# Implementation: agent/shared/enums.py — Remove orphaned symbols

## Goal

Delete all symbols in `scripts/agent/shared/enums.py` that have zero references in the codebase.
The file's defined symbols (`ExtractionDecision`, `RetrievalMode`, `ToolSafetyTier`, `WorkflowStage`) are duplicated or superseded by symbols in other modules and are not imported by any file.

## Scope

**In:** `scripts/agent/shared/enums.py`
**Out:** No other files change. `agent/memory/enums.py` and `agent/tool_enums.py` are the canonical sources and are not modified.

## Assumptions

1. `ExtractionDecision` and `RetrievalMode` in `agent/shared/enums.py` are confirmed duplicates of the same classes in `agent/memory/enums.py`.
2. `ToolSafetyTier` has no equivalent import anywhere; `agent/tool_enums.py` provides `RiskLevel` which serves the same purpose.
3. `WorkflowStage` has zero references across `scripts/` (confirmed by grep).
4. No dynamic import (`importlib`, `__import__`) references these symbols (confirmed absent).

## Implementation

### Target file

`scripts/agent/shared/enums.py`

### Procedure

1. Delete all class definitions: `ExtractionDecision`, `RetrievalMode`, `ToolSafetyTier`, `WorkflowStage`.
2. Remove the `from __future__ import annotations` line if no longer needed.
3. Remove the `from enum import StrEnum` import line since no StrEnum subclasses remain.
4. Retain the module docstring to document why the file is empty (no re-exports needed from this path).

### Method

Replace the entire file content with just the module docstring.

### Details

**Before:**
```python
"""agent/shared/enums.py
Cross-cutting StrEnum definitions for the agent layer.
"""

from __future__ import annotations

from enum import StrEnum


class ExtractionDecision(StrEnum):
    ...

class RetrievalMode(StrEnum):
    ...

class ToolSafetyTier(StrEnum):
    ...

class WorkflowStage(StrEnum):
    ...
```

**After:**
```python
"""agent/shared/enums.py
No public enums. Canonical sources:
  - ExtractionDecision, RetrievalMode -> agent.memory.enums
  - RiskLevel, ApprovalDecisionType   -> agent.tool_enums
"""
```

The file remains as a documentation stub to prevent future re-introduction of duplicates.

## Validation plan

```bash
# Confirm zero references to the deleted symbols
grep -rn "from agent.shared.enums\|agent\.shared\.enums" scripts/

# Lint
uv run ruff check scripts/agent/shared/enums.py

# Type check (no new errors)
uv run mypy scripts/

# Architecture boundaries
PYTHONPATH=scripts uv run lint-imports

# Tests
uv run pytest -v
```
