## Goal

Surface the persisted compression boundary through `AgentSession`, enforce the boundary at the DB layer during undo, and remove the obsolete turn-deletion helper.

## Scope

Only `scripts/agent/session.py`: `replace_messages()` (facade, line 70), `undo_last_turn()` (line 216), `delete_last_turn()` (line 187, removal), and `fetch_messages()` (facade, line 103). This document names exactly one target file.

## Assumptions

- `replace_messages()` facade (lines 70-80) currently returns `None`; `SessionMessageRepository.replace_messages()` (row 02) will return the boundary `int | None`.
- `undo_last_turn()` (lines 216-253) deletes `message_id >= last_user_id`; the boundary must tighten this to `message_id > undo_floor_message_id`.
- `fetch_messages()` facade (lines 103-110) returns the repo's tuple; the repo now returns a 3-tuple (row 02).
- `delete_last_turn()` may have external callers; verify before removing.

## Design decisions

- The facade returns the boundary the repo computes, so callers set `ctx.conv.undo_floor` from a single return value after a successful write.
- Enforce the boundary at the DB layer (read `undo_floor_message_id` from `sessions`) so undo cannot delete the boundary row or anything before it, independent of in-memory state.
- Delete `delete_last_turn()` only after a zero-caller `rg` re-check confirms no references remain (per `rules/coding.md` deprecation policy).

## Alternatives considered

- **Gate undo only in `undo_service` (history index)** — rejected: the DB is the source of truth; an in-memory-only gate can be bypassed or desynced. The DB-layer gate (this file) is authoritative.
- **Return a richer object from `undo_last_turn()`** — rejected: the plan keeps an `int` return (count deleted); "nothing undoable" is signaled by `0`, and the higher-level block signal lives in `UndoResult` (row 06).

## Implementation

### Target file

`scripts/agent/session.py`

### Procedure

1. `replace_messages()` facade (lines 70-80): return the boundary from the repo call.
2. `undo_last_turn()` (lines 216-253): read the boundary and gate deletion at `message_id > undo_floor_message_id`.
3. `fetch_messages()` facade (lines 103-110): unpack the repo's 3-tuple and return it.
4. Remove `delete_last_turn()` (lines 187-214) after confirming zero callers.

### Method

**`replace_messages()`** — change the body to return the repo's result:

```python
def replace_messages(self, messages):
    if self.session_id is None:
        logger.warning("replace_messages called before session.start(); skipping persist")
        return None
    return self._message_repo.replace_messages(self.session_id, messages)
```

The repo's `replace_messages()` (row 02) returns `int | None` (the boundary).

**`undo_last_turn()`** — read the boundary and gate:

```python
# read floor
floor_row = db.execute(
    "SELECT undo_floor_message_id FROM sessions WHERE session_id = ?",
    (self.session_id,),
).fetchone()
undo_floor = floor_row[0] if floor_row else 0
# find last user id (walk back) ...
if last_user_id is None or last_user_id <= undo_floor:
    return 0  # nothing undoable beyond the boundary
deleted = db.execute(
    "SELECT COUNT(*) FROM messages WHERE session_id = ? AND message_id > ?",
    (self.session_id, undo_floor),
).fetchone()[0]
db.execute(
    "DELETE FROM messages WHERE session_id = ? AND message_id > ?",
    (self.session_id, undo_floor),
)
```

Keep the early `return 0` when `session_id is None` or no rows. The key change: replace both `message_id >= last_user_id` predicates with `message_id > undo_floor_message_id`, and add the `last_user_id <= undo_floor` block guard.

**`fetch_messages()`** — unpack the 3-tuple:

```python
def fetch_messages(self, session_id):
    return self._message_repo.fetch_messages(session_id)
```

Update the return annotation to `tuple[list[LLMMessage], bool, int]` and the docstring to document the third element.

**`delete_last_turn()`** — remove the method (lines 187-214). First run `rg 'delete_last_turn'` across `scripts/` and `tests/`; if any caller exists, report it as a Plan Gap (do not remove).

### Details

- `undo_last_turn()` returns `0` when nothing is undoable (blocked by the boundary). `undo_service` (row 05) treats `0` as the block condition and raises the block signal.
- The DB-layer floor (`undo_floor_message_id`) and the history-index floor (`ctx.conv.undo_floor`, row 04) are different domains but must agree on what is undoable; `undo_service` coordinates them.

## Compatibility considerations

- `undo_last_turn()` still returns `int`; `0` now also means "blocked by boundary" (previously it meant "no user message"). Callers must treat `0` as blocked.
- `fetch_messages()` facade now returns a 3-tuple — matches the repo change (row 02). Update `restore_session()` (row 10).
- Removing `delete_last_turn()` changes its public surface; confirm zero callers first.

## Security considerations

N/A: the boundary gate strengthens integrity; no new attack surface.

## Rollback considerations

Revert the commit. Reverting this row alone against the repo change (row 02) would leave `fetch_messages()` returning a 2-tuple while callers expect 3 — revert together.

## Validation plan

```bash
uv run pytest tests/agent/test_agent_session.py -p no.cacheprovider
```

Assert: `replace_messages()` returns the boundary after a rewrite; `undo_last_turn()` deletes only `message_id > floor` and returns `0` when the last user turn is at/before the floor; `fetch_messages()` returns a 3-tuple; `delete_last_turn()` no longer exists and nothing references it.

## Completion criteria

`AgentSession.replace_messages()` returns the boundary; `undo_last_turn()` gates at `message_id > undo_floor_message_id` and returns `0` when blocked; `delete_last_turn()` removed with zero residual callers; `fetch_messages()` returns a 3-tuple; `tests/agent/test_agent_session.py` passes.

## Out of scope

The repo boundary write (row 02), the in-memory field (row 04), the service-level gating/block signal (rows 05/06), and the `/undo` display (row 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261015-200906 | 20261015-200906 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261015-200906 | 20261015-200906 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261015-200906 | 20261015-200906 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — |  |

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
- **Source issue**: N/A
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-214826_plan.md
- **Source implementation procedure**: N/A
- **Generated at**: 20261014-230612
- **Related target files**: scripts/agent/session.py