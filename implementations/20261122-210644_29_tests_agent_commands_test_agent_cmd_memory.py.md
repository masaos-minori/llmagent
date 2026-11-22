## Goal

Await the now-async `_cmd_memory` in this test module (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: this test file only.

## Assumptions

- Verified: the file calls `cmd._cmd_memory(...)` synchronously (for example lines 462 and 471).

## Design decisions

- Mark affected tests async (the repository's pytest asyncio mode) and await each call.

## Alternatives considered

N/A: mechanical update.

## Implementation
### Target file
`tests/agent/commands/test_agent_cmd_memory.py`

### Procedure
1. Find every `_cmd_memory` call with `rg` and convert each to `await`, making the test functions `async def` where needed.

### Method
Mechanical edit; no assertion changes.

### Details
- Keep patches of the data-ops methods compatible with awaiting (use `AsyncMock` for delete and prune).

## Compatibility considerations

N/A: test-only.

## Security considerations

N/A: test-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/commands/test_agent_cmd_memory.py -q`
- `uv run ruff check tests/agent/commands/test_agent_cmd_memory.py`

## Completion criteria

- No synchronous `_cmd_memory` call remains; the file passes.

## Out of Scope

Other Memory test files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (awaited async `_cmd_memory`)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `tests/agent/commands/test_agent_cmd_memory.py`
