## Goal

Set the in-memory compression boundary (`ctx.conv.undo_floor`) after a history compression via the manager path, so `/undo` is gated from the moment compression persists.

## Scope

Only `scripts/agent/conversation_state_manager.py`: `handle_history_compression()` (lines 148-161). This document names exactly one target file.

## Assumptions

- Current `handle_history_compression()` (lines 148-161): compresses via `hist_mgr.compress()`, and on `compressed_count > 0` calls `ctx.session.replace_messages(ctx.conv.history)` (line 161). It does not currently set `ctx.conv.undo_floor`.
- After compression, `ctx.conv.history` is the new (compressed) history; the boundary is the position of the compression summary.
- `ctx.conv.undo_floor` is a history index (row 04); the DB boundary is a row ID (row 02). They represent the same point in different domains.

## Design decisions

- Set `ctx.conv.undo_floor` immediately after a successful `replace_messages()` so the boundary is established atomically with persistence.
- Point `undo_floor` at the summary/boundary message such that `ctx.conv.history[undo_floor:]` is the not-undoable region (summary + anything before) and turns after it are undoable.

## Alternatives considered

- **Set `undo_floor` before persisting** — rejected: if the DB write fails, the in-memory boundary would be wrong. Set it only after a successful write.
- **Derive `undo_floor` from the facade's returned row ID** — rejected: the facade returns a row ID (row 03), but `undo_floor` is a history index; the index must come from the new history position, not the row ID.

## Implementation

### Target file

`scripts/agent/conversation_state_manager.py`

### Procedure

After the successful `ctx.session.replace_messages(ctx.conv.history)` call (line 161), set `ctx.conv.undo_floor` to the boundary index in the new history.

### Method

```python
async def handle_history_compression(self) -> None:
    ctx = self._ctx
    if ctx.services_required.hist_mgr is not None:
        ctx.conv.history, result = await ctx.services_required.hist_mgr.compress(
            ctx.conv.history
        )
        if result.compressed_count > 0:
            ctx.session.replace_messages(ctx.conv.history)
            # set the in-memory boundary to the summary position in the new history
            ctx.conv.undo_floor = <index of the compression boundary message>
```

Replace `<index of the compression boundary message>` with the position of the summary message in the new `ctx.conv.history` (the point after which turns are undoable). Compute it from the compression result / new-history structure.

### Details

- The boundary index and the DB boundary row ID (row 02) must denote the same compression point. Keep them consistent.
- If compression produced no undoable post-compression turns, `undo_floor` still points at the summary; the floor-gated search (rows 03/05) will correctly block.
- This is one of two compression entry points; the other is `/compact` in `cmd_rag_export` (row 09). Both must set `undo_floor`.

## Compatibility considerations

N/A: only sets a new field after an existing call. Depends on `ctx.conv.undo_floor` (row 04) and the repo boundary write (row 02).

## Security considerations

N/A: internal integrity marker.

## Rollback considerations

Revert the commit. Revert with rows 04 (field) and 09 (other entry point) together.

## Validation plan

```bash
uv run pytest tests/agent/test_history_compression_consistency.py -p no.cacheprovider
```

Assert: after `handle_history_compression()` persists a compression, `ctx.conv.undo_floor` equals the boundary index; undoing a turn before the boundary is blocked; undoing a turn after it succeeds.

## Completion criteria

`handle_history_compression()` sets `ctx.conv.undo_floor` after a successful `replace_messages()`; the boundary matches the DB write; `tests/agent/test_history_compression_consistency.py` passes.

## Out of scope

The in-memory field lifecycle (row 04), the DB boundary write (row 02), the `/compact` entry point (row 09), and restore (row 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261015-191020 | 20261015-191020 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261015-191020 | 20261015-191020 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261015-191020 | 20261015-191020 |  |
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
- **Related target files**: scripts/agent/conversation_state_manager.py