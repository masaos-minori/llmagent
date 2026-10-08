# Move git-mcp blocking operations off the event loop

## Priority
Medium

## Summary
Run GitPython's synchronous operations outside the event loop and use a lock that is safe in async code, so `/health` and other requests stay responsive during push and pull.

## Background
Source: local investigation notes (memo1.md, ISSUE-09), from an earlier review finding.

## Problem
- Async handlers run GitPython synchronous operations (`push`, `pull`, `fetch`, `snapshot`) directly (per investigation notes, not re-verified).
- `_get_repo_lock()` returns a `threading.Lock` that is awaited from async code (Explicit in code — `scripts/mcp_servers/git/repository_state.py` defines `threading.Lock` based per-repo locks).

## Reason for Change
- A network push or pull blocks the whole server event loop, so `/health` stops responding; the Agent then sees timeouts and health failures and may mark the server unavailable.
- Waiting on a synchronous lock in the event-loop thread risks deadlock or total stall.

## Implementation Intent
- Keep long-running git operations off the event loop so health checks and read operations remain responsive.

## Target Files or Areas
- `scripts/mcp_servers/git/git_service.py`, `scripts/mcp_servers/git/repository_state.py`

## Required Changes
- Run the op in `_run_tool()` via `asyncio.to_thread()`.
- Replace the per-repo lock with an `asyncio.Lock`, or acquire the lock inside the worker thread.
- Add timeouts to push and pull.

## Constraints
- Preserve per-repository mutual exclusion; no behavior change in outcomes.

## Acceptance Criteria
- `/health` responds while a push is running (test).

## Testing Expectations
- Async test with a slow fake git operation; ruff, mypy, targeted pytest.

## Documentation Impact
Update the git-mcp documentation only where locking or timeout behavior is described.

## Out of Scope
- Ref validation, audit, and error-path changes.

## Dependencies
- Implement after the git-mcp ref-validation and audit issues (same files).

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Do not change operation results or protection logic. Keep the diff limited to execution and locking.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-154016
- **Related target files**: `scripts/mcp_servers/git/git_service.py`, `scripts/mcp_servers/git/repository_state.py`
