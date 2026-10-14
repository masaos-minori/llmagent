## Goal

Restore the `/undo` compression boundary across `/session load` by converting the stored boundary row ID (`sessions.undo_floor_message_id`) into a history index (`ctx.conv.undo_floor`).

## Scope

Only `scripts/agent/services/session_restore.py`: `restore_session()` (lines 26-53). This document names exactly one target file.

## Assumptions

- `fetch_messages()` now returns a 3-tuple `(messages, session_found, undo_floor_message_id)` (row 02); the facade `AgentSession.fetch_messages()` (row 03) passes it through.
- `restore_session()` currently unpacks `messages, session_found = ctx.session.fetch_messages(session_id)` (line 32) and rebuilds history via `ctx.conv.replace_history(...)`.
- `ctx.conv.undo_floor` is a history index (row 04); the stored boundary is a row ID (row 02).

## Design decisions

- Unpack the 3-tuple and, after rebuilding history, set `ctx.conv.undo_floor` to the index whose entry corresponds to the stored boundary row ID.
- `undo_floor_message_id == 0` means "never compressed" → set `ctx.conv.undo_floor = 0`.

## Alternatives considered

- **Re-query the boundary separately on restore** — rejected: `fetch_messages()` already returns it (row 02); use it to avoid an extra round-trip.
- **Store the boundary as a history index in the DB** — rejected: the DB stores a row ID (authoritative, stable across the message domain); the index is an in-memory view converted on restore (row 04).

## Implementation

### Target file

`scripts/agent/services/session_restore.py`

### Procedure

1. Unpack the 3-tuple from `fetch_messages()`.
2. After `ctx.conv.replace_history(...)` rebuilds history, convert the stored boundary row ID to a history index and assign `ctx.conv.undo_floor`.

### Method

```python
async def restore_session(ctx, session_id):
    messages, session_found, undo_floor_id = ctx.session.fetch_messages(session_id)
    if not session_found:
        raise SessionNotFoundError(f"Session {session_id} not found.")
    if not messages:
        raise SessionNoMessagesError(f"Session {session_id} has no messages.")
    if ctx.conv.system_prompt_content:
        system_msgs = [{"role": "system", "content": ctx.conv.system_prompt_content}]
        non_system = [m for m in messages if m["role"] != "system"]
        await ctx.conv.replace_history(system_msgs + non_system)
    else:
        await ctx.conv.replace_history(messages)
    ctx.session.session_id = session_id
    reset_session_stats(ctx)
    # convert the stored boundary row ID into a history index
    ctx.conv.undo_floor = <index of the boundary message in the rebuilt history> \
        if undo_floor_id else 0
    return SessionRestoreResult(session_id=session_id, n_messages=len(messages))
```

Replace `<index of the boundary message ...>` with the position of the boundary message in the rebuilt history.

### Details

- **Identity matching**: the conversion requires identifying which restored entry corresponds to the stored row ID. History entries built by `fetch_messages()` currently carry `role`/`content`/`tool_calls`/`tool_call_id` but NOT `message_id`. To match by row ID, the restored entries must carry a stable identity (`message_id`). Decide how to preserve it through `replace_history` (e.g., attach `message_id` to the entry dict, or identify the boundary by the summary's position). This is a design decision for the implementer; if it requires changing the history-entry shape, assess impact on other consumers of `ctx.conv.history`.
- When `undo_floor_id == 0`, set `ctx.conv.undo_floor = 0` (no boundary).
- Place the assignment AFTER `replace_history` so the index refers to the rebuilt history.

## Compatibility considerations

- Depends on the `fetch_messages()` 3-tuple contract (rows 02/03). Must be updated together.
- Preserving `message_id` on history entries (if chosen) may affect other consumers of `ctx.conv.history`; verify before committing to that approach.

## Security considerations

N/A: internal integrity restoration.

## Rollback considerations

Revert the commit. Revert with rows 02 (3-tuple) and 04 (field) together.

## Validation plan

```bash
uv run pytest tests/agent/test_session_restore.py -p no.cacheprovider
```

Assert: restoring a session that was compressed sets `ctx.conv.undo_floor` to the correct index; restoring a never-compressed session sets `undo_floor == 0`; `/undo` then blocks at/before the boundary and succeeds after it.

## Completion criteria

`restore_session()` unpacks the 3-tuple, converts the stored boundary row ID to a history index, and sets `ctx.conv.undo_floor` (0 when no boundary); `tests/agent/test_session_restore.py` passes.

## Out of scope

The 3-tuple contract (row 02), the in-memory field (row 04), and the compression entry points (rows 08/09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | |

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
- **Related target files**: scripts/agent/services/session_restore.py
