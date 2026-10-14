## Goal

Set the in-memory compression boundary (`ctx.conv.undo_floor`) after a forced compression via `/compact`, matching the manager path (row 08).

## Scope

Only `scripts/agent/commands/cmd_rag_export.py`: `_cmd_compact()` (lines 26-55). This document names exactly one target file.

## Assumptions

- Current `_cmd_compact()` (lines 26-55): force-compresses via `hist_mgr.force_compress()`, and on success calls `ctx.session.replace_messages(ctx.conv.history)` (line 52). It does not set `ctx.conv.undo_floor`.
- After force-compression, `ctx.conv.history` is the new history; the boundary is the summary position.

## Design decisions

- Set `ctx.conv.undo_floor` immediately after the successful `replace_messages()` (line 52), mirroring row 08.
- Point `undo_floor` at the summary/boundary message so post-summary turns are undoable and earlier turns are blocked.

## Alternatives considered

- **Set `undo_floor` only in the manager path** — rejected: `/compact` is an independent entry point that also persists a snapshot; it must establish the boundary too, or `/undo` would be ungated after a forced compact.

## Implementation

### Target file

`scripts/agent/commands/cmd_rag_export.py`

### Procedure

After the successful `ctx.session.replace_messages(ctx.conv.history)` call (line 52), set `ctx.conv.undo_floor` to the boundary index in the new history.

### Method

```python
# inside the try, after:
    ctx.session.replace_messages(ctx.conv.history)
    # set the in-memory boundary to the summary position in the new history
    ctx.conv.undo_floor = <index of the compression boundary message>
```

Reuse the same index computation as row 08 (position of the summary message in the new `ctx.conv.history`).

### Details

- Consistency: `/compact` (this file) and `handle_history_compression()` (row 08) are the two compression entry points; both must set `undo_floor` identically.
- The boundary index denotes the same point as the DB boundary row ID (row 02).

## Compatibility considerations

N/A: only sets a new field after an existing call. Depends on `ctx.conv.undo_floor` (row 04).

## Security considerations

N/A: internal integrity marker.

## Rollback considerations

Revert the commit. Revert with rows 04 (field) and 08 (manager path) together.

## Validation plan

```bash
uv run pytest tests/agent/test_history_compression_consistency.py -p no.cacheprovider
```

Assert: after `/compact` persists a compression, `ctx.conv.undo_floor` equals the boundary index; `/undo` blocks at/before the boundary and succeeds after it.

## Completion criteria

`_cmd_compact()` sets `ctx.conv.undo_floor` after a successful `replace_messages()`; matches the manager path (row 08); `tests/agent/test_history_compression_consistency.py` passes.

## Out of scope

The in-memory field lifecycle (row 04), the DB boundary write (row 02), the manager compression path (row 08), and restore (row 10).

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
- **Related target files**: scripts/agent/commands/cmd_rag_export.py
