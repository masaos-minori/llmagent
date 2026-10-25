# Implementation Procedure — scripts/agent/services/models.py

## Goal

Give `DbPurgeResult` (187-191) one additive optional field
`kept_active_session (new)` so the purge exemption can reach the command layer —
without it REQ-003 surfacing is impossible (the frozen dataclass carries only
`sessions_removed` and the service discards `raw.data`), as recorded by the plan's
2026-10-25 re-verification.

## Scope

- Modify only the `DbPurgeResult` dataclass in `scripts/agent/services/models.py`.
- No other result dataclass, key, or default changes.

## Assumptions

- `DbPurgeResult` is constructed only in `db_maintenance_service.py:72` and in tests
  (`test_agent_cmd_session.py` mock `return_value` constructions at 526/541/555) —
  a defaulted field keeps every existing construction valid (grep verified 2026-10-25).
- The dataclass is `frozen=True`; adding a defaulted field is legal and does not
  change equality semantics of existing constructions (`kept_active_session=None`).

## Design decisions

- `kept_active_session: int | None = None` placed after `sessions_removed` so the
  positional construction form is unchanged.
- Type `int | None` mirrors the `MaintenanceResult` data key
  `kept_active_session (new)` (procedure 01) exactly; no conversion in the models
  layer.

## Alternatives considered

- Passing `MaintenanceResult` through the service: rejected (procedure 02 Alternatives).
- Encoding the note in a free-text message field: rejected — REQ-003 asks for a
  structured result surfaced by the command.

## Implementation
### Target file
`scripts/agent/services/models.py`

### Procedure

Extend the dataclass body (187-191):

```python
@dataclass(frozen=True)
class DbPurgeResult:
    """Result of purging old sessions from the database."""

    sessions_removed: int
    kept_active_session: int | None = None  # (new) id exempted from retention, None otherwise
```

### Method
One new field `kept_active_session (new)` on the existing `DbPurgeResult`; no new
symbols, no import changes (the module already imports `dataclass`).

### Details
- Docstring left as-is or extended by one sentence describing the new field; either
  is acceptable, no behavior implication.

## Compatibility considerations

- All existing `DbPurgeResult(sessions_removed=...)` constructions (service + tests)
  compile and behave identically (`kept_active_session (new)` defaults to `None`).
- Frozen-dataclass equality for old constructions is unchanged (new field equals
  `None` on both sides).

## Security considerations

N/A: data-only change.

## Rollback considerations

Remove the one field line; nothing else references it before procedures 02/04 land.

## Validation plan

- Import/type check: ruff + mypy on this file.
- Existing tests constructing `DbPurgeResult` pass unmodified:
  `uv run pytest tests/agent/commands/test_agent_cmd_session.py -x -q`.

## Completion criteria

- `DbPurgeResult(sessions_removed=8)` still constructs with `kept_active_session is None`.
- Procedure 02 can construct the dataclass with the new keyword (mypy clean).

## Out of Scope

- Any other `agent.services.models` dataclass.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the field | Completed | 2026-10-25 | 2026-10-25 | `kept_active_session: int \| None = None` after `sessions_removed` |
| 2 | Run targeted validation | Completed | 2026-10-25 | 2026-10-25 | ruff/mypy clean; existing `DbPurgeResult` constructions pass unmodified |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 (result carrier), added by plan re-verification
- **Source issue**: `issues/20261025-115826_sess005_purge-deletes-current-session.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-124106_sess005_purge-deletes-current-session.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-141651
- **Related target files**: scripts/agent/services/db_maintenance_service.py (procedure 02), scripts/agent/commands/db_session_ops.py (procedure 04)
