## Goal

Make `_cmd_memory` async so it can await the async delete and prune handlers (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `scripts/agent/commands/cmd_memory.py` and `tests/agent/commands/test_cmd_memory.py`; `test_agent_cmd_memory.py` is its own row.

## Assumptions

- Verified: `_cmd_memory` builds a dict of lambdas and calls `handler()` synchronously (`scripts/agent/commands/cmd_memory.py:80-124`); the registry awaits a handler only when `CommandDef.is_async` is true and rejects a mismatch at construction (`scripts/agent/commands/registry.py:80-90,130-137`); the `/memory` flag is changed by the `command_defs_list.py` procedure (seq 31), which must land with this one (Step 3b correction).

## Design decisions

- Make `_cmd_memory` `async def`; after calling a dispatch lambda, await the result when it is awaitable (`inspect.isawaitable`), so sync handlers stay unchanged.

## Alternatives considered

Rejected: making every Memory handler async (out of scope; only delete and prune need the controller).

## Implementation
### Target file
`scripts/agent/commands/cmd_memory.py`

### Procedure
1. Change the signature to `async def _cmd_memory`; keep the `status`, no-args, and disabled-memory branches.
2. Await the handler result when awaitable; keep the `UnknownSubcommandError` path.

### Method
Local edit in one method; add the `inspect` import.

### Details
- Confirm `CommandRegistry` binds `_cmd_memory` through the same path as other async commands (it awaits through `_invoke_handler`).

### Companion test files
- `tests/agent/commands/test_cmd_memory.py`
  - Procedure: Await every call of `_cmd_memory`; add a case where delete returns a coroutine that is awaited.
  - Validation: `uv run pytest tests/agent/commands/test_cmd_memory.py -q`

## Compatibility considerations

`_cmd_memory` callers must await; production dispatch already does, tests are updated by companions and the next row.

## Security considerations

N/A: dispatch plumbing only.

## Rollback considerations

N/A: revert the commit together with the `memory_data_ops.py` change.

## Validation plan

- `uv run pytest tests/agent/commands -q`
- `uv run ruff check scripts/agent/commands/cmd_memory.py && uv run mypy scripts/agent/commands/cmd_memory.py`

## Completion criteria

- `_cmd_memory` is a coroutine function and awaits async handlers; the command registry dispatch tests pass.

## Out of Scope

Other `/memory` subcommands' behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-213733 | 20261122-213733 | Changed: scripts/agent/commands/cmd_memory.py (and companions) |
| 2 | Add or update tests per Validation plan (companion test files included) | Completed | 20261122-213733 | 20261122-213733 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261122-213733 | 20261122-213733 | ruff, mypy, lint-imports, bandit clean; full suite 13377 passed; diff-cover 91% |

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
- **Requirement ID**: `REQ-004` (async Memory handlers awaited at dispatch)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `scripts/agent/commands/cmd_memory.py`, `tests/agent/commands/test_cmd_memory.py`
