## Goal

Replace the dropped summary-warning semantics on `UndoResult` with a boundary-block indicator so `/undo` can report when it is blocked by the compression boundary.

## Scope

Only `scripts/agent/services/models.py`: the `UndoResult` dataclass (lines 119-124). This document names exactly one target file.

## Assumptions

- `UndoResult` (lines 119-124) is a frozen dataclass with `n_removed: int` and `warning: str | None = None`.
- It is produced ONLY by `undo_service.undo_last_turn()` (row 05) and consumed ONLY by `cmd_context._cmd_undo()` (`scripts/agent/commands/cmd_context.py:145-149`). No other producer/consumer exists in `scripts/`.
- `cmd_context` reads `result.n_removed` and `result.warning`; it must instead read the block indicator.

## Design decisions

- Drop the `warning` field and add `block_reason: str | None = None`. `None` means "not blocked" (a normal undo); a non-`None` value is the message `/undo` shows when blocked.
- Keep `n_removed: int` unchanged.

## Alternatives considered

- **Add `blocked: bool` alongside `warning`** — rejected: the plan drops warning semantics entirely; a single `block_reason` carries both the flag (non-`None`) and the message, avoiding a redundant boolean.
- **Reuse `warning` for the block message** — rejected: semantically wrong ("warning" implies a soft note about recoverability; the block is a hard gate). Rename to `block_reason`.

## Implementation

### Target file

`scripts/agent/services/models.py`

### Procedure

Change `UndoResult` (lines 119-124): remove `warning: str | None = None`, add `block_reason: str | None = None`.

### Method

```python
@dataclass(frozen=True)
class UndoResult:
    """Result of undoing a conversation action.

    `block_reason` is set when the undo was refused because the last turn is at or
    before the compression boundary; otherwise it is `None`.
    """

    n_removed: int
    block_reason: str | None = None
```

### Details

- Update the two related files in the same step:
  - `undo_service.undo_last_turn()` (row 05): return `UndoResult(n_removed=0, block_reason="...")` when blocked, `UndoResult(n_removed=<n>)` on success.
  - `cmd_context._cmd_undo()` (row 07): replace `if result.warning:` with `if result.block_reason:` and render the block message.
- Verify no test constructs `UndoResult(warning=...)` directly; update such tests under their own rows (e.g. `tests/agent/commands/test_agent_cmd_context.py`, row 15).

## Compatibility considerations

`UndoResult.warning` no longer exists. The only production consumer is `cmd_context` (row 07); update it. Any test referencing `.warning` must be updated under its own row.

## Security considerations

N/A: internal result shape only.

## Rollback considerations

Revert the commit. Revert with rows 05 (producer) and 07 (consumer) together.

## Validation plan

```bash
uv run pytest tests/agent/commands/test_agent_cmd_context.py -p no.cacheprovider
```

Assert: `UndoResult` has `block_reason` and no `warning`; a blocked undo carries a `block_reason`; a normal undo has `block_reason is None`.

## Completion criteria

`UndoResult` exposes `block_reason: str | None = None` (no `warning`); `undo_service` (row 05) and `cmd_context` (row 07) updated; related tests pass.

## Out of scope

The block logic (row 05) and the `/undo` display (row 07).

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
- **Related target files**: scripts/agent/services/models.py