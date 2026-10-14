## Goal

Make `/undo` render the compression-boundary message when it is blocked, and report the removed count on success, using the new `UndoResult.block_reason` (row 06).

## Scope

Only `scripts/agent/commands/cmd_context.py`: `_cmd_undo()` (lines 133-150). This document names exactly one target file.

## Assumptions

- Current `_cmd_undo()` (lines 133-150): lazily imports `NothingToUndoError` and `undo_last_turn`, calls `undo_last_turn()`, writes success with `result.n_removed`, writes `result.warning` if present, and catches `NothingToUndoError` → `write_no_data`.
- `undo_last_turn()` (row 05) now returns an `UndoResult` carrying `block_reason` instead of raising for the boundary case; `result.warning` no longer exists (row 06).

## Design decisions

- Inspect `result.block_reason`: when set, render it as the blocked message and change nothing; otherwise render the success message.
- Keep the success path (`result.n_removed`) unchanged.

## Alternatives considered

- **Keep catching `NothingToUndoError`** — rejected unless row 05 still raises it; the plan routes the boundary case through `UndoResult.block_reason`. Reconcile with row 05: if `NothingToUndoError` is retained for a genuinely empty history, keep a narrow catch; otherwise drop it.

## Implementation

### Target file

`scripts/agent/commands/cmd_context.py`

### Procedure

Rewrite `_cmd_undo()` (lines 133-150) to branch on `result.block_reason`.

### Method

```python
def _cmd_undo(self) -> None:
    """Roll back the last user+assistant turn, gated by the compression boundary."""
    from agent.services.undo_service import undo_last_turn

    result = undo_last_turn(self._ctx)
    if result.block_reason:                      # blocked by the boundary (rows 05/06)
        self._out.write_no_data(result.block_reason)
    else:
        self._out.write_success(
            f"Last turn undone. ({result.n_removed} messages removed)"
        )
```

Drop the `NothingToUndoError` import/catch unless row 05 still raises it (reconcile). Choose `write_no_data` vs `write_warning` for the block message consistently with the rest of `/undo` output; the plan's message text is `"Nothing to undo: ..."`.

### Details

- The block message text comes from `UndoResult.block_reason` (row 06), set by `undo_service` (row 05). Do not hard-code it here.
- Ensure `self._out` has the chosen output method available (verify `write_no_data`/`write_warning` exist on the output object).

## Compatibility considerations

- Depends on `UndoResult.block_reason` (row 06) and the block signal from `undo_service` (row 05). Must be updated together.
- If `NothingToUndoError` is removed as an import and something else still raises it, the except clause must move accordingly.

## Security considerations

N/A: display-only change.

## Rollback considerations

Revert the commit. Revert with rows 05 and 06 together.

## Validation plan

```bash
uv run pytest tests/agent/commands/test_agent_cmd_context.py -p no.cacheprovider
```

Assert: undoing a normal turn shows the success message with the removed count; undoing at/before the boundary shows the `"Nothing to undo: ..."` message and changes nothing; no reference to `result.warning` remains.

## Completion criteria

`_cmd_undo()` renders the block message when `result.block_reason` is set and the success message otherwise; no `.warning` access remains; `tests/agent/commands/test_agent_cmd_context.py` passes.

## Out of scope

The block logic (row 05), the `UndoResult` shape (row 06), and the in-memory field lifecycle (row 04).

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
- **Related target files**: scripts/agent/commands/cmd_context.py
