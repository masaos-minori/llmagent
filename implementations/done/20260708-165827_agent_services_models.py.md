# Implementation: H-9 — Remove ToolResultRow re-export from agent/services/models.py

## Goal

Remove the `ToolResultRow` import and `__all__` entry — this file only re-exported it for
agent-layer callers, and `ToolResultRow` itself is being deleted from `db/models.py` (see the
companion doc).

## Scope

**Target**: `scripts/agent/services/models.py`

**Depends on**: land together with `implementations/*_db_models.py.md` (the `ToolResultRow`
class deletion from `db/models.py`) — removing the re-export without removing the source class
is harmless (unused re-export); removing the source class without removing this re-export would
break this file's import at module load time.

**Out of scope**: `PurgeCounts`, `RagConsistencyReport`, `WalCheckpointCounts` (other db-layer
re-exports in this same import statement) — all stay, only `ToolResultRow` is removed.

## Assumptions

1. No agent-layer module imports `ToolResultRow` from `agent.services.models` (confirmed via
   `grep -rln "from agent.services.models import.*ToolResultRow" scripts/ tests/` → no matches)
   — the re-export exists but has zero actual consumers, making this a pure dead-code removal.

## Implementation

### Target file

`scripts/agent/services/models.py`

### Procedure

#### Step 1: Confirm no consumers of the re-export

```bash
grep -rln "from agent.services.models import.*ToolResultRow" scripts/ tests/
```

Expected: no matches.

#### Step 2: Remove from the import statement

Current (lines 13-18):

```python
from db.models import (
    PurgeCounts,
    RagConsistencyReport,
    ToolResultRow,
    WalCheckpointCounts,
)
```

Replace with:

```python
from db.models import (
    PurgeCounts,
    RagConsistencyReport,
    WalCheckpointCounts,
)
```

#### Step 3: Remove from `__all__`

Remove the line `"ToolResultRow",` from the `__all__` list (around line 173).

#### Step 4: Update the module docstring

Current (lines 4-6):

```
Imports only from agent.services.enums to avoid circular dependencies.
db-layer DTOs (WalCheckpointCounts, PurgeCounts, ToolResultRow) are defined in
db.models and re-exported here for agent-layer callers.
```

Replace with:

```
Imports only from agent.services.enums to avoid circular dependencies.
db-layer DTOs (WalCheckpointCounts, PurgeCounts) are defined in
db.models and re-exported here for agent-layer callers.
```

### Method

- Three small, mechanical text removals (import line, `__all__` entry, docstring mention); no
  other code in this file changes.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check scripts/agent/services/models.py` | 0 errors |
| Type check | `mypy scripts/` | no new errors |
| Grep (re-export removed) | `grep -n "ToolResultRow" scripts/agent/services/models.py` | no matches |
| Tests (full) | `uv run pytest -v` | no new failures once the companion `db/models.py` doc is applied together |
| Pre-commit | `pre-commit run --all-files` | pass |
