## Goal

In `SessionMessageRepository.replace_messages`, skip messages carrying the ephemeral keys `_ephemeral` or `_memory_injected` when building the rows to insert, so the compressed snapshot no longer persists ephemeral memory/hint rows; keep the boundary as the maximum persisted `message_id` and preserve the "nothing persisted" behavior when every message is ephemeral or invalid (REQ-004; AC-5).

## Scope
**Release unit**: summary-persist-restore (Phase 3; released with the restore change in Row 02 so the stored set and the rebuilt history agree).

## Assumptions

- `replace_messages` (`scripts/agent/session_message_repo.py`, lines ~155–163) iterates `messages`, keeps only role-valid rows, and appends `(session_id, role, content, tc_json, tool_call_id)` tuples; it filters by role alone today, so a marked row is stored without its marker.
- `_ephemeral` / `_memory_injected` are top-level keys of the `LLMMessage` dict (`scripts/shared/types.py`); a persisted row read back by `fetch_messages` carries only `role`/`content`, so the marker never survives round-trip anyway, but the row itself is what must not be written.
- The filter belongs here (not on restore) because `replace_messages` is the single place that turns history rows into persisted rows for both the turn path and `/compact` (Plan Point 5).

## Design decisions

- Add one skip in the build loop: `if msg.get("_memory_injected") or "_ephemeral" in msg: continue`, placed after the role check, so ephemeral rows never enter `rows`.
- Add `if not rows: return None` after the loop and before the `DELETE`+`executemany`, matching `save_many`'s guard, so an all-ephemeral snapshot clears nothing and returns `None` instead of deleting every row (correctness + the documented "nothing persisted" contract).

## Alternatives considered

- Filter on restore by a prefix rule: rejected; the Plan puts the filter in `replace_messages` so both writers stop persisting with one change, and the dropped marker is unavailable on restore anyway.
- Drop ephemeral rows in `HistoryManager.compress` or `TurnPersistence`: rejected; `replace_messages` is the convergence point and the single tested boundary.

## Implementation
### Target file
`scripts/agent/session_message_repo.py`

### Procedure
1. In `replace_messages`, add an ephemeral-key skip inside the `for msg in messages:` loop, after the invalid-role check.
2. Add the `if not rows: return None` guard before the DB transaction block.

### Method
```python
def replace_messages(self, session_id, messages):
    if not messages:
        return None
    rows = []
    for msg in messages:
        role = msg.get("role", "user")
        if role not in self._valid_roles:
            logger.warning("replace_messages: skipping invalid role %r", role)
            continue
        if msg.get("_memory_injected") or "_ephemeral" in msg:
            continue
        content = msg.get("content") or ""
        tc_json = _tool_calls_json(msg.get("tool_calls"))
        tool_call_id = msg.get("tool_call_id")
        rows.append((session_id, role, content, tc_json, tool_call_id))
    if not rows:
        return None
    with SQLiteHelper("session").open(write_mode=True) as db:
        ...
```

### Details
- The guard returns `None` (matching the docstring) when no row survives, so `undo_floor` is left untouched rather than reset to `0`.
- No new import: the two ephemeral keys are checked directly, avoiding a dependency on the private `LLMMessage` definition.
- Stale-reference marks: none created here; the keys `_ephemeral` / `_memory_injected` are existing message fields.

## Compatibility considerations

- Both the turn path and `/compact` now omit ephemeral system rows from the persisted set; the persisted schema is unchanged (no column/schema change, per Constraints).
- Overlap with the compression-compensation Plan (shared `session_message_repo.py`): different method (`replace_messages` vs `delete_messages_from`/`turn_start_marker`); the shared rule "ephemeral system rows are never persisted" is stated in the Plan Scope.

## Security considerations

- Persisting fewer rows shrinks the surface of what a local actor could leave behind indefinitely; the ephemeral memory block is no longer stored, so it cannot accumulate across sessions.

## Rollback considerations

- Remove the ephemeral skip and the `if not rows` guard.

## Validation plan

- `uv run pytest tests/agent/test_session_message_repo.py tests/agent/test_history_compression_consistency.py -v` — ephemeral-filter and boundary tests (Row 05, Row 06) fail before and pass after; existing `replace_messages` tests pass unchanged.
- Static: `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria

- After a compression the persisted rows contain no `_ephemeral`/`_memory_injected` row; the persisted boundary equals the maximum persisted `message_id`; with all-ephemeral or all-invalid input the method returns `None` and persists nothing.

## Out of Scope

- The shared constant/predicate (Row 01), restore (Row 02), the persistence tests (Row 05), the round-trip test (Row 06), and the docs (Rows 08–10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | release unit summary-persist-restore |
| 2 | Add or update tests per Validation plan | Pending | — | — | covered by Row 05/06 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | persistence model in Row 09 |

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
- **Requirement ID**: `REQ-004` (do not persist ephemeral system rows), `AC-5`
- **Source issue**: issues/done/20261031-180437_restoresummary001_session-load-drops-summary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115505_restoresummary001_session-load-drops-summary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-072108
- **Related target files**: scripts/agent/session_message_repo.py
