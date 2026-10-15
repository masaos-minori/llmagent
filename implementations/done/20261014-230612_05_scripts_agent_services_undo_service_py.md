## Goal

Rework `/undo` so deletions are gated at the compression boundary, nothing is mutated when nothing is undoable, and the DB is updated before history is touched.

## Scope

Only `scripts/agent/services/undo_service.py`: `undo_last_turn()` (lines 23-62). This document names exactly one target file.

## Assumptions

- Current `undo_last_turn()` (lines 23-62): searches the last user message anywhere in history, raises `NothingToUndoError` if none, computes `cut_idx` stripping `_memory_injected`/`_ephemeral` markers, trims `ctx.conv.history`, then calls `session.undo_last_turn()` (line 53), then evaluates a summary-warning branch (lines 55-62), returning `UndoResult(n_removed, warning)`.
- The current order trims history BEFORE the DB delete — the bug this row fixes.
- `AgentSession.undo_last_turn()` (row 03) now returns `0` when nothing is undoable (blocked by the boundary).

## Design decisions

- **DB first**: call `session.undo_last_turn()` before trimming `ctx.conv.history`, so a failed/blocked DB delete never leaves history inconsistent.
- **Floor-gated search**: search the last user message only at index `>= ctx.conv.undo_floor`; if none, block.
- **Block via `UndoResult`**: return an `UndoResult` carrying the block reason instead of raising for the boundary case; the summary-warning semantics are dropped (see row 06).

## Alternatives considered

- **Raise `NothingToUndoError` for the boundary case** — rejected: the plan routes the boundary case through `UndoResult` so `/undo` can render the compression-boundary message distinctly (rows 06/07). Keep `NothingToUndoError` only if a genuinely empty history still warrants it; reconcile with row 07.
- **Gate only in `session.undo_last_turn()`** — rejected: `undo_service` must also avoid trimming history when the DB delete is blocked (DB-first ordering).

## Implementation

### Target file

`scripts/agent/services/undo_service.py`

### Procedure

Rewrite `undo_last_turn()` (lines 23-62):

1. Search the last user message at index `>= ctx.conv.undo_floor`. If none, return a blocked `UndoResult` (reason per row 06) and change nothing.
2. Compute `cut_idx` by walking back from the user index to strip preceding `_memory_injected`/`_ephemeral` markers (as today).
3. Call `session.undo_last_turn()` **before** trimming history.
4. If it returns `0` (blocked by the boundary), return the blocked `UndoResult` and do NOT trim history.
5. Otherwise trim `ctx.conv.history` to `cut_idx`, decrement `stat_turns`, and return a success `UndoResult`.
6. Remove the summary-warning branch (lines 55-62).

### Method

```python
def undo_last_turn(ctx):
    last_user_idx = next(
        (i for i in range(len(ctx.conv.history) - 1, ctx.conv.undo_floor - 1, -1)
         if ctx.conv.history[i]["role"] == "user"),
        None,
    )
    if last_user_idx is None:
        return undo_result_blocked("Nothing to undo: at or before the compression boundary.")
    cut_idx = last_user_idx
    while cut_idx > 0 and (
        ctx.conv.history[cut_idx - 1].get("_memory_injected")
        or ctx.conv.history[cut_idx - 1].get("_ephemeral")
    ):
        cut_idx -= 1
    removed = ctx.session.undo_last_turn()   # DB first (row 03)
    if removed == 0:                          # blocked by the boundary
        return undo_result_blocked("Nothing to undo: at or before the compression boundary.")
    # trim history AFTER the DB delete succeeds
    ctx.conv.history = ctx.conv.history[:cut_idx]
    ... decrement stat_turns ...
    return UndoResult(n_removed=removed)      # no `warning` field (row 06)
```

The exact block-signaling shape (`UndoResult.block_reason` / `blocked`) is defined in row 06; the helper `undo_result_blocked(...)` is illustrative.

### Details

- The search range upper bound is `ctx.conv.undo_floor - 1` so indices `< undo_floor` are excluded. Adjust to match the intended inclusivity with row 03's DB gate.
- `removed == 0` is the block condition (a valid undo removes at least one turn). Ensure `session.undo_last_turn()` cannot legitimately return `0` for a successful undo.
- Keep `_memory_injected`/`_ephemeral` marker stripping unchanged.

## Compatibility considerations

- Return type stays `UndoResult`; the block signal is carried on the object (row 06), not an exception. `cmd_context._cmd_undo` (row 07) must inspect it.
- `NothingToUndoError` handling in `cmd_context` (row 07) must be reconciled with the new block path.

## Security considerations

N/A: strengthens integrity; no new attack surface.

## Rollback considerations

Revert the commit. Revert with rows 03 (DB gate) and 06 (`UndoResult` shape) together.

## Validation plan

```bash
uv run pytest tests/agent/commands/test_agent_cmd_context.py -p no.cacheprovider
```

Assert: undoing a normal turn deletes from the DB before trimming history and returns a success `UndoResult`; undoing when the last turn is at/before the boundary changes nothing and returns a blocked `UndoResult`; the summary-warning branch is gone.

## Completion criteria

`undo_service.undo_last_turn()` gates at the boundary, deletes from the DB before trimming history, never mutates when blocked, and returns an `UndoResult` reflecting success or block; related tests pass.

## Out of scope

The DB-layer gate (row 03), the `UndoResult` block shape (row 06), and the `/undo` display (row 07).

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
- **Related target files**: scripts/agent/services/undo_service.py