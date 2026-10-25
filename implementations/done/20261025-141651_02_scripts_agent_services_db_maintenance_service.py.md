# Implementation Procedure — scripts/agent/services/db_maintenance_service.py

## Goal

Extend `DbMaintenanceService.purge` (64-74) to accept and forward the current session
id to `purge_old_sessions`, and carry the exemption through to `DbPurgeResult`
(REQ-003, REQ-004).

## Scope

- Modify only the `purge` method of `scripts/agent/services/db_maintenance_service.py`.
- Forwarding only: no policy logic in this layer (target-table contract).
- `SQLiteHelper("session").open(write_mode=True)` context ownership stays here.

## Assumptions

- `DbMaintenanceService.purge` has exactly one production caller,
  `DbSessionOps.purge` (`db_session_ops.py:60`) — grep verified 2026-10-25.
- `raw.data` from `purge_old_sessions` contains `kept_active_session (new)` once
  procedure 01 lands; `data.get(...)` keeps this code working before that (returns
  `None`).

## Design decisions

- Keyword-only `current_session_id (new)` parameter with default `None`: existing
  positional calls `(max_sessions, max_age_days)` are unaffected.
- Map the `kept_active_session (new)` key from `data` straight into the new
  `DbPurgeResult` field (procedure 03); no interpretation in the service.

## Alternatives considered

- Returning the raw `MaintenanceResult` to the command layer: rejected — the agent
  layer's contract is its own frozen dataclasses (`agent.services.models`), and other
  `DbMaintenanceService` methods already follow that pattern.

## Implementation
### Target file
`scripts/agent/services/db_maintenance_service.py`

### Procedure

Change the `purge` method (64-74) to:

```python
def purge(
    self,
    max_sessions: int | None,
    max_age_days: int | None,
    *,
    current_session_id: int | None = None,
) -> DbPurgeResult:
    """Purge old sessions per retention config; optionally guard the active session."""
    cfg = _build_retention_config(max_sessions, max_age_days)
    with SQLiteHelper("session").open(write_mode=True) as db:
        raw = purge_old_sessions(db, cfg, keep_session_id=current_session_id)
    data = raw.data or {}
    return DbPurgeResult(
        sessions_removed=data.get("age_deleted", 0) + data.get("count_deleted", 0),
        kept_active_session=data.get("kept_active_session"),
    )
```

### Method
Changed signature and body of the existing `purge` method; new keyword
`current_session_id (new)`. The imported name `keep_session_id (new)` arrives from
procedure 01. No other method (health/checkpoint/vacuum/recover) is touched.

### Details
- `_build_retention_config` unchanged.
- The forwarding uses keyword form (`keep_session_id=...`), so the positional export
  contract of `purge_old_sessions` is never exercised differently.

## Compatibility considerations

- Existing callers passing two positional args keep working (default `None`).
- `agent.services.db_maintenance_service` import set unchanged — no new cross-layer
  imports, `lint-imports` stays 6 kept / 0 broken.

## Security considerations

N/A: no SQL built or executed in this layer.

## Rollback considerations

`git checkout -- scripts/agent/services/db_maintenance_service.py`.

## Validation plan

- Covered by procedure 04 (command test update) and procedure 06 (end-to-end purge
  test): `uv run pytest tests/agent/commands/test_agent_cmd_session.py -x -q`.
- ruff + mypy on this file.

## Completion criteria

- AC-002/AC-005 path: a guarded purge surfaces `kept_active_session (new)` on
  `DbPurgeResult`; unguarded calls return `None` there.

## Out of Scope

- Command-layer output wording (procedure 04).
- `DbPurgeResult` field addition (procedure 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the purge method change | Completed | 2026-10-25 | 2026-10-25 | keyword-only `current_session_id`; `kept_active_session` mapped from `data` |
| 2 | Run targeted validation | Completed | 2026-10-25 | 2026-10-25 | covered by procedures 04/06 runs: 119 passed; ruff/mypy clean |

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
- **Requirement ID**: REQ-003 (service layer), REQ-004
- **Source issue**: `issues/20261025-115826_sess005_purge-deletes-current-session.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-124106_sess005_purge-deletes-current-session.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-141651
- **Related target files**: scripts/agent/services/models.py (procedure 03), scripts/agent/commands/db_session_ops.py (procedure 04)
