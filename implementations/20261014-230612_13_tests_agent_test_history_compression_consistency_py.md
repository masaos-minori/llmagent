## Goal

Verify end-to-end that a history compression establishes `ctx.conv.undo_floor` and that `/undo` is gated by it: turns at/before the boundary cannot be undone, turns after it can.

## Scope

Only `tests/agent/test_history_compression_consistency.py`. This document names exactly one target file.

## Assumptions

- Tests build an `AgentContext` with a real (temp) `session` DB, a history, and a stubbed `hist_mgr`.
- The two compression entry points are `handle_history_compression()` (row 08) and `/compact` (row 09); both set `ctx.conv.undo_floor`.

## Design decisions

- Add tests that drive each compression entry point and assert `ctx.conv.undo_floor` matches the persisted boundary.
- Add tests that undo a turn before the boundary (blocked) and after the boundary (success), checking both history and DB.

## Alternatives considered

- **Stub `hist_mgr` vs. a real history manager** — a stubbed `hist_mgr` isolates the compression -> boundary -> undo flow without depending on the summarizer; both entry points (manager and `/compact`) are driven this way.
- **In-memory index vs. DB row ID assertions** — the tests assert both domains denote the same point, since they are different representations of one boundary.

## Implementation

### Target file

`tests/agent/test_history_compression_consistency.py`

### Procedure

1. Add a test: after `handle_history_compression()` persists a compression, `ctx.conv.undo_floor` is set and equals the boundary position; the DB `sessions.undo_floor_message_id` matches.
2. Add a test: after `/compact` (`_cmd_compact`) persists a compression, `ctx.conv.undo_floor` is set consistently.
3. Add a test: undoing a turn whose last user message is at/before `undo_floor` changes neither history nor DB (block signal).
4. Add a test: undoing a turn after the boundary removes it from history and DB.

### Method

- For each entry point, seed enough turns to trigger compression, run compression, then assert `ctx.conv.undo_floor` and the DB boundary denote the same point.
- For the gate tests, call `undo_service.undo_last_turn(ctx)` and assert the returned `UndoResult.block_reason` is set when blocked and `None` when a valid undo occurs; assert DB row counts accordingly.

### Details

- Keep the in-memory index (`ctx.conv.undo_floor`) and the DB row ID (`undo_floor_message_id`) consistent in assertions — they are different domains representing the same point.
- Ensure the stubbed `hist_mgr.compress()`/`force_compress()` returns `(new_history, result)` with `compressed_count > 0`.

## Compatibility considerations

Depends on `ctx.conv.undo_floor` (row 04), the compression setters (rows 08/09), and the block signal (rows 05/06). Coordinate.

## Security considerations

N/A: test-only.

## Rollback considerations

Revert the commit. Revert with rows 04/08/09/05/06 together.

## Validation plan

```bash
uv run pytest tests/agent/test_history_compression_consistency.py -p no.cacheprovider
```

Assert: compression sets the boundary; undo gates correctly on both entry points; suite passes.

## Completion criteria

`test_history_compression_consistency.py` covers boundary establishment on both compression paths and `/undo` gating; the test passes.

## Out of scope

The repo/facade contract tests (rows 11/12) and the restore conversion (row 14).

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
- **Related target files**: tests/agent/test_history_compression_consistency.py
