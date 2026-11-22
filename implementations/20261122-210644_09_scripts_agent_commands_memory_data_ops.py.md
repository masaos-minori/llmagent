## Goal

Remove the blocking `input()` confirmation from Memory delete and prune and route it through the controller as a request-bound, destructive prompt (REQ-001, REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `scripts/agent/commands/memory_data_ops.py` and `tests/agent/commands/test_memory_data_ops.py`. The async dispatch is the `cmd_memory.py` row.

## Assumptions

- Verified: `_confirm` calls `input()` (`scripts/agent/commands/memory_data_ops.py:50`) from sync handlers `memory_delete` (line 321) and `memory_prune` (line 363) that run on the event loop.
- The open maintenance-job Issue also names this file; this procedure changes only the two handlers and `_confirm`.

## Design decisions

- `_confirm` becomes `async` and submits a destructive request of kind memory_delete or memory_prune; only a completed outcome with `y` or `yes` returns True; `InputBusyError` prints a cancelled message and returns False.
- Operation id: the resolved memory id for delete, and `prune:` plus the day count for prune.

## Alternatives considered

Rejected: keeping a sync `input()` guarded by a flag (still a second reader and an event-loop block).

## Implementation
### Target file
`scripts/agent/commands/memory_data_ops.py`

### Procedure
1. Rewrite `_confirm(prompt)` as an async function taking the prompt kind and operation id, using `get_input_controller` from the controller module.
2. Make `memory_delete` and `memory_prune` `async def` and `await` the confirmation; keep the dry-run branches and audit calls as they are.
3. Print `[memory] Cancelled: nothing was deleted` for every non-confirmed outcome, with a distinct line when the controller refuses because a read is unresolved.

### Method
Two function signatures and one helper change; no change to `write_delete` or `prune_old_memories` calls.

### Details
- Remove `input` use entirely; no `builtins.input` reference remains in `scripts/` after this row (Acceptance criterion AC-2).

### Companion test files
- `tests/agent/commands/test_memory_data_ops.py`
  - Procedure: Replace `patch("builtins.input")` at lines 233, 391, and 560 with a patched controller returning completed results; add tests for refusal while a read is orphaned, cancelled and timed-out outcomes, and await of the async handlers.
  - Validation: `uv run pytest tests/agent/commands/test_memory_data_ops.py -q`

## Compatibility considerations

`memory_delete` and `memory_prune` become coroutines; their only production caller is updated by the `cmd_memory.py` row in the same phase.

## Security considerations

A stale line cannot confirm a deletion; confirmation is bound to the memory id or prune operation.

## Rollback considerations

N/A: revert the commit together with the `cmd_memory.py` change.

## Validation plan

- `uv run pytest tests/agent/commands -q`
- `uv run ruff check scripts/agent/commands/memory_data_ops.py && uv run mypy scripts/agent/commands/memory_data_ops.py`

## Completion criteria

- No direct `input()` remains; confirmation goes through the controller; destructive confirmation is refused while a read is unresolved; tests pass.

## Out of Scope

Maintenance-job framework changes to these handlers, rebuild and reindex confirmations.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (companion test files included) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (no second stdin reader), `REQ-004` (request-bound async confirmation)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `scripts/agent/commands/memory_data_ops.py`, `tests/agent/commands/test_memory_data_ops.py`
