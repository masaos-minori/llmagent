# Goal

Create the `agent/shared/` package with cross-cutting enums, exceptions, and models
used by both the command layer and the service layer, and register it in
`.importlinter` as part of the `agent` layer.

# Scope

New files only:
- `scripts/agent/shared/__init__.py`
- `scripts/agent/shared/enums.py`
- `scripts/agent/shared/exceptions.py`
- `scripts/agent/shared/models.py`
- `.importlinter` — confirm `agent.shared` is covered by the existing `agent` contract

# Assumptions

1. `.importlinter` already has a contract covering `agent` → all; `agent.shared` is
   a sub-package of `agent` and is automatically covered. No new contract entry needed.
2. `agent/shared/` may only import from `shared/` (external only) and standard
   library. It must NOT import from `agent/commands/`, `agent/services/`, or
   `agent/memory/` (those import from `agent/shared/`, not the reverse).
3. Several items listed below may already exist in other modules under different names
   (e.g. `MemoryType` is in `agent/memory/enums.py`). The `agent/shared/enums.py`
   defines NEW cross-cutting enums that are not already defined. Do not duplicate
   or move existing enums.
4. `MemoryMessage` is already defined in `agent/memory/models.py` as `HistoryMessage`.
   In `agent/shared/models.py`, define `MemoryMessage` as a new type-alias or
   re-export if appropriate, OR keep it only in `agent/memory/models.py` and skip
   it here.

# Implementation

## Target file

`scripts/agent/shared/__init__.py`,
`scripts/agent/shared/enums.py`,
`scripts/agent/shared/exceptions.py`,
`scripts/agent/shared/models.py`

## Procedure

1. Create `scripts/agent/shared/__init__.py` (empty or with `__all__`).
2. Create `scripts/agent/shared/enums.py` with the enums below.
3. Create `scripts/agent/shared/exceptions.py` with the exceptions below.
4. Create `scripts/agent/shared/models.py` with the DTOs below.
5. Run `PYTHONPATH=scripts uv run lint-imports` to confirm no new violations.
6. Run ruff + mypy on all four files.

## Method

New package — no existing code is changed. All files use `from __future__ import annotations`.

## Details

### `enums.py`

```python
from __future__ import annotations
from enum import StrEnum

class ExtractionDecision(StrEnum):
    ACCEPT = "accept"
    REJECT_TOO_SHORT = "reject_too_short"
    REJECT_NO_KEYWORDS = "reject_no_keywords"
    REJECT_DEDUP = "reject_dedup"

class RetrievalMode(StrEnum):
    FTS = "fts"
    KNN = "knn"
    HYBRID = "hybrid"

class ToolSafetyTier(StrEnum):
    READ_ONLY = "READ_ONLY"
    WRITE_SAFE = "WRITE_SAFE"
    DESTRUCTIVE = "DESTRUCTIVE"
    SHELL = "SHELL"

class WorkflowStage(StrEnum):
    CRAWL = "crawl"
    SPLIT = "split"
    INGEST = "ingest"
    DONE = "done"
```

### `exceptions.py`

```python
from __future__ import annotations

class AgentSharedError(Exception):
    """Base for all agent/shared exceptions."""

class ValidationError(AgentSharedError, ValueError):
    """Raised when input fails domain validation."""

class ConfigurationSchemaError(AgentSharedError, ValueError):
    """Raised when a config dict does not match the expected schema."""

class WorkflowStageError(AgentSharedError, RuntimeError):
    """Raised when a workflow stage fails in an unrecoverable way."""

class UnknownTierError(ValidationError):
    def __init__(self, tier: str) -> None:
        super().__init__(f"Unknown safety tier: {tier!r}")

class UnknownRoleError(ValidationError):
    def __init__(self, role: str, valid: frozenset[str]) -> None:
        super().__init__(
            f"Unknown role {role!r}. Valid: {', '.join(sorted(valid))}"
        )
```

### `models.py`

```python
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class CommandResult:
    """Structured result from a command handler."""
    success: bool
    message: str
    needs_restart: list[str] = ()  # field(default_factory=list)

@dataclass(frozen=True)
class ValidationErrorDetail:
    field: str
    message: str
    value: object = None
```

# Validation plan

- `PYTHONPATH=scripts uv run lint-imports` → 0 violations
- `uv run ruff check scripts/agent/shared/`
- `uv run mypy scripts/agent/shared/`
- `uv run pytest --ignore=tests/test_create_schema.py -q` — no regressions
