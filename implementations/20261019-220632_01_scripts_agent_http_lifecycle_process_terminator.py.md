## Goal
- Make the SIGTERM wait in the process terminator detect a child that has already exited, so a server that exits promptly on SIGTERM is not waited on until the SIGKILL escalation (`REQ-001` (reap the child while waiting), `REQ-004` (keep the SIGKILL backstop and failure behavior)).

## Scope
- In scope: `scripts/agent/http_lifecycle_process_terminator.py` only.
- Out of scope: the shutdown coordinator, the callers of the terminator, the MCP server, tests, and docs (each has its own procedure document).

## Assumptions
- `Popen.poll()` is idempotent and reaps an exited child, so calling it on every wait iteration is safe even when another code path also polls the same object.
- A process group whose leader has been reaped but which still has live members keeps `os.killpg(pgid, 0)` succeeding, so waiting for the whole group (launcher and child) stays correct.

## Design decisions
- Reap first, then probe: in each iteration call the process's `poll()` (through the same safe access the module already uses) and then run the existing `os.killpg(pgid, 0)` probe; the probe is unchanged, so the group-wide wait semantics and the SIGKILL escalation are preserved.
- Apply the same reap to `wait_exited`, which uses the identical probe and has the same flaw.

## Alternatives considered
- Replace the group probe with `proc.poll()` alone: rejected, because it would stop waiting while other members of the group (for example the onefile child) are still alive.
- Use `os.waitpid`: rejected, because `Popen` already owns the wait status and a second reaper would race it.

## Implementation
### Target file

`scripts/agent/http_lifecycle_process_terminator.py`

### Procedure
1. In `ProcessTerminator.terminate_with_timeout`, inside the loop that waits up to `timeout` seconds after SIGTERM, reap the child at the start of every iteration before the `os.killpg(pgid, 0)` probe.
2. In `ProcessTerminator.wait_exited`, reap the child at the start of every iteration in the same way.
3. Add one small module-level helper `_reap` (new) that calls the process's `poll()` when it exists and swallows `OSError`, `AttributeError`, and `TypeError` exactly like `_already_exited` does; use it from both loops.
### Method
- The helper takes `proc: object`, uses `getattr(proc, "poll", None)` like `_already_exited`, and returns nothing; the loops keep their current structure, `ProcessLookupError` handling, and the final SIGKILL branch.
- Do not change the early `_already_exited` checks, the SIGTERM send, the SIGKILL escalation, return values, or log messages.
### Details
- Evidence: the wait loops contain only the `os.killpg(pgid, 0)` probe and `poll()` appears only in `_already_exited`; an experiment with a plain child showed the probe still succeeded for an exited, unreaped child and raised `ProcessLookupError` only after `poll()`.
- With a mocked `poll` that returns `None` (the current tests), the new call changes nothing, so existing mock-based tests are unaffected.

## Compatibility considerations
- Return values, exceptions, log lines, and the escalation timing for a server that ignores SIGTERM are unchanged; only the detection time of an exited child changes. Other callers (startup-failure, restart) benefit from the same detection.

## Security considerations
- N/A: no new input, no new signal target; process-group signalling is unchanged.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_process_terminator.py tests/agent/test_http_lifecycle_health_check.py tests/agent/test_http_lifecycle_warning.py tests/agent/test_http_lifecycle_integration.py tests/integration/test_mcp_transport_crash.py -q`
- `uv run ruff format` and `uv run ruff check` on the file, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, and `uv run bandit scripts/agent/http_lifecycle_process_terminator.py` per `rules/toolchain.md`.

## Completion criteria
- A child that exits on SIGTERM is reported terminated well before the timeout (the regression test of the tests procedure passes).
- The existing terminator and caller tests pass unchanged.
- Cyclomatic complexity of `terminate_with_timeout` does not increase.

## Out of Scope
- Modifying any file other than the target file; changing `_SHUTDOWN_TIMEOUT_SEC`; changing the uvicorn configuration; `issues/done/`, `plans/done/`, `implementations/done/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `_reap` (new) helper and use it in `terminate_with_timeout` and `wait_exited` | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) including the caller regression tests | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (reap the child while waiting), `REQ-004` (keep the SIGKILL backstop)
- **Source issue**: issues/done/20261019-215906_mcpshut001_make-mcp-server-shutdown-bounded-and-complete.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-220318_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-220632
- **Related target files**: scripts/agent/http_lifecycle_process_terminator.py
