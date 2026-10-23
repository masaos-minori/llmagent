## Goal
Re-point the 1 `asyncio.to_thread` patch site(s) in `tests/agent/test_tool_approval_repos.py` to the new private read seam `_approval_read` (new) in `scripts/agent/tool_approval.py`, without changing any assertion or case name (`plans/20261022-040200_plan.md` REQ-009; AC-6, AC-8). Added to the Plan during code-implementation: the plan-time search covered only the preflight test file.

## Scope
- Only `tests/agent/test_tool_approval_repos.py`: the patch targets. `patch("asyncio.to_thread", new=AsyncMock(return_value="yes"))` at `:120`.

## Assumptions
- `_approval_read(prompt)` is a coroutine function in `agent.tool_approval` with the same contract as `await asyncio.to_thread(input, prompt)`: it returns the answer string.
- The seam is created by the `tool_approval.py` row of this Plan, which lands first.

## Design decisions
- Patch `agent.tool_approval._approval_read` instead of `asyncio.to_thread`; an `AsyncMock(return_value=...)` keeps the same shape as before.

## Alternatives considered
- Patching `builtins.input`: rejected, the reader thread would still run; the seam is the stable, patchable boundary.

## Implementation
### Target file
`tests/agent/test_tool_approval_repos.py`

### Procedure
1. Replace each `patch("asyncio.to_thread", ...)` with a patch of `agent.tool_approval._approval_read` using the equivalent mock.
2. Swap the patch target string only.
3. Do not change any expected value, parameterization or case name.

### Method
- Enumerate sites with `grep -n to_thread` before and after; the count after must be 0.

### Details
- Evidence: `tests/agent/test_tool_approval_repos.py`: `patch("asyncio.to_thread", new=AsyncMock(return_value="yes"))` at `:120`.

## Compatibility considerations
- Test-only.

## Security considerations
- N/A: tests only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_approval_repos.py -q`, then `uv run pytest tests/agent -q`; `uv run ruff check tests/agent`.

## Completion criteria
- `grep -c "asyncio.to_thread" tests/agent/test_tool_approval_repos.py` returns 0 and the file's cases pass unchanged.

## Out of Scope
- Production code
- Other test files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the patch re-point per Implementation > Procedure (tests are this row's change) | Completed | 20261023-135531 | 20261023-135531 | implemented; full suite 9831 passed; procedures corrected (reader state machine, call-time input lookup, new-markers, nonexistent doc checkers); rows 11-13 added for three further approval test files; generated reference table regenerated |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-135531 | 20261023-135531 |  |

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
- **Requirement ID**: `REQ-009` (approval read seam), tests re-pointed
- **Source issue**: `issues/20261021-093421_repl002_cancelled_input_read_delays_process_exit.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-040200_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-074240
- **Related target files**: tests/agent/test_tool_approval_repos.py