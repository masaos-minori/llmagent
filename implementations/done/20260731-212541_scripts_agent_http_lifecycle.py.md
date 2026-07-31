# Implementation Procedure: Warning Log for Potential Orphaned Processes

## Goal
Add a warning log in `scripts/agent/http_lifecycle.py` when `proc.terminate()` succeeds but child processes might remain because process group termination was unavailable (due to `getpgid()` failure or fallback from `os.killpg()`).

## Scope
- `scripts/agent/http_lifecycle.py`

## Assumptions
- `proc.terminate()` is used as a fallback when `os.killpg()` fails or is unavailable.
- An orphaned process exists if `proc.terminate()` kills the parent but not its descendants.

## Design decisions
- The warning should only be logged if the process actually terminates (i.e., `proc.poll()` is no longer `None`), to avoid noise during actual failures.
- The warning should indicate that children might still be running.

## Alternatives considered
- N/A

## Implementation

### Target file
- `scripts/agent/http_lifecycle.py`

### Procedure
1. In `_terminate_with_timeout`, track whether a successful process group termination was performed.
2. If `proc.terminate()` is used instead of `os.killpg()` (either because `pgid` is `None` or `os.killpg` raised an error), and the process exits successfully within the timeout, log a warning.

### Method
Modify `_terminate_with_timeout` in `scripts/agent/http_lifecycle.py`.

### Details
In `_terminate_with_timeout`:
- Initialize `used_pgid = False`.
- If `pgid` is not `None`, try `os.killpg(pgid, signal.SIGTERM)`. If successful, set `used_pgid = True`.
- If `os.killpg` fails or `pgid` is `None`, call `proc.terminate()`.
- After `await self._wait_exited(proc, timeout)`, if it returns `True` (success) and `not used_pgid`, log:
  `logger.warning("Lifecycle: %r terminated, but children may remain (no pgid available)", server_key)`

## Compatibility considerations
N/A

## Security considerations
N/A

## Rollback considerations
N/A

## Validation plan
- Unit test: Mock `os.getpgid` to return `OSError` and verify the warning is logged after `proc.terminate()` succeeds.
- Integration test: Verify that the warning appears in logs when a subprocess with `start_new_session=True` is terminated without its process group.

## Out of scope
- Implementing full process tree cleanup using `psutil`.

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260731-085048_plan.md
- Source implementation procedure: N/A
- Generated at: 20260731-212541
- Related target files: scripts/agent/http_lifecycle.py
