# ProcessTerminator treats proc.pid as the process-group id and ignores the stored pgid, risking a wrong-group kill

## Priority
Medium

## Summary
`ProcessTerminator.terminate_with_timeout` derives the process-group id from `proc.pid` and passes it to `os.killpg`. That value is only a valid process-group id when the process is a group leader (started with `start_new_session=True`). The manager already stores the authoritative pgid via `os.getpgid(proc.pid)`, but the terminator never reads it, and `cfg.fields` can override `start_new_session` to `False`. Make termination use the true pgid so `os.killpg` always targets the intended group.

## Background
HTTP subprocess MCP servers are started with `start_new_session=True` (`scripts/agent/http_lifecycle.py::_create_and_validate_proc`), which makes the child a session/group leader, so `proc.pid == os.getpgid(proc.pid)` in practice. The manager records the real pgid in `self._http_pgids[server_key]` immediately after launch. Termination flows through `ProcessTerminator.terminate_with_timeout` (`scripts/agent/http_lifecycle_process_terminator.py`), which recomputes the pgid from `proc.pid` rather than reading the stored value.

## Problem
Verified against the code on 2026-10-16:
- `terminate_with_timeout` line 84: `pgid = getattr(proc, "pid", None)` followed by `os.killpg(pgid, signal.SIGTERM/KILL)`. `os.killpg` requires a process-group id, not a pid.
- The invariant `proc.pid == pgid` holds only for group leaders. `http_lifecycle.py` lines 302-316 build `popen_kwargs` with `"start_new_session": True` but then apply `if cfg.fields: popen_kwargs.update(cfg.fields)`, so an admin config can set `fields: {start_new_session: false}`. If set, the child is NOT a group leader and `os.killpg(proc.pid)` targets an unrelated process group, potentially signaling unrelated processes.
- The authoritative pgid in `self._http_pgids` (computed correctly at line 323) is ignored by the terminator.
- Inconsistency: `scripts/agent/http_lifecycle_shutdown_coordinator.py::_get_pgid` correctly falls back to `os.getpgid(proc.pid)`, showing the correct approach exists but is not used by the terminator.
- Impact is currently latent because the default config uses `start_new_session=True`; the defect activates on config override or any non-leader process.

## Reason for Change
The termination path silently assumes an invariant (`proc.pid == pgid`) that is not enforced or documented at the call site, and that config can break. Correctness of process-group termination should not depend on an undocumented assumption.

## Implementation Intent
Pass the authoritative pgid into termination (read `self._http_pgids[server_key]` from the manager, or compute via `os.getpgid(proc.pid)` like `_get_pgid`), and have `terminate_with_timeout` prefer that value over `proc.pid`. Keep the `proc.terminate()` fallback for the no-pgid case. Document the group-leader requirement at the subprocess-launch site.

## Target Files or Areas
- `scripts/agent/http_lifecycle_process_terminator.py` (Phase 4 primary)
- `scripts/agent/http_lifecycle.py` (pass/store authoritative pgid; document `start_new_session`)
- `scripts/agent/http_lifecycle_shutdown_coordinator.py` (reuse `_get_pgid` consistently)
- `tests/agent/test_http_lifecycle_process_terminator.py`

## Required Changes
- Terminate using the true process-group id, not `proc.pid` directly.
- Retain the graceful `proc.terminate()` fallback when no pgid is available.
- Document that subprocesses must be group leaders (`start_new_session=True`) for group termination.
- Add a test asserting termination calls `os.killpg` with the group id even when `proc.pid` differs from the pgid (via a fake proc whose `pid` and pgid differ).

## Constraints
- Do not change the SIGTERM-then-SIGKILL escalation order or timeouts.
- Preserve the existing warnings about orphaned children when no pgid is available.
- No behavior change for the default `start_new_session=True` case (where `proc.pid == pgid`).

## Acceptance Criteria
- Termination sends signals to the actual process group, verified by a test where the fake proc's `pid` differs from its pgid.
- The no-pgid fallback still calls `proc.terminate()`.
- Existing terminator tests pass unchanged for the default case.

## Testing Expectations
- Unit tests for `terminate_with_timeout` and `wait_exited` with a fake proc whose `pid != pgid`.
- `ruff`, `mypy --no-namespace-packages scripts/`, bandit, full `pytest` with sandbox config.

## Documentation Impact
Add an operational note that group termination requires `start_new_session=True` and that overriding it via `cfg.fields` disables safe group termination.

## Out of Scope
- Changes to the escalation policy, timeout values, or shutdown coordinator iteration order.
- Any change to which servers are configured with `start_new_session`.

## Dependencies
- `N/A: none`

## Unresolved Questions
- Whether any production config sets `fields.start_new_session=false`; confirm by inspecting `config/*_mcp_server.toml` before deciding whether this is a latent-only defect or actively exposed.

## AI Implementation Instruction
Fix only the pgid derivation in the terminator. Do not alter escalation, timeouts, or the shutdown coordinator loop. Confirm production config does not rely on `start_new_session=false`. Add a fake-proc test where `pid != pgid`. No compatibility shims.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261016-092918
- **Related target files**: scripts/agent/http_lifecycle_process_terminator.py, scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_shutdown_coordinator.py
