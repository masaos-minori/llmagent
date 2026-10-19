## Goal
- Add a regression test with a real subprocess that exits on SIGTERM, proving the terminator detects the exit promptly (`REQ-005` (tests for the terminator behavior), covering `REQ-001` and `REQ-004`).

## Scope
- In scope: `tests/agent/test_http_lifecycle_process_terminator.py` only.
- Out of scope: the terminator source, the coordinator tests, and every other file (each has its own procedure document).

## Assumptions
- The terminator source change (reap in the wait loop) is applied before this test is expected to pass; write the test first and observe it fail against the current terminator.
- A short-lived real child (`sleep`-based) started with `start_new_session=True` behaves like an MCP server group for this purpose.

## Design decisions
- Use a real `subprocess.Popen` instead of mocks, because the bug is invisible to a mocked `os.killpg`.
- Assert on outcome (the call returns `True`, the child has an exit status, and the elapsed time is far below the timeout) rather than on tight wall-clock values, to stay deterministic.

## Alternatives considered
- Extend the mock-based tests only: rejected, because they patch `os.killpg` and never create an unreaped child.

## Implementation
### Target file

`tests/agent/test_http_lifecycle_process_terminator.py`

### Procedure
1. Add a test that starts `sleep 60` with `start_new_session=True`, calls `ProcessTerminator().terminate_with_timeout(proc, "k", timeout=10.0)`, and asserts it returns `True`, that `proc.poll()` is not `None`, and that the elapsed time is below 5 seconds.
2. Add a test that does the same through `ProcessTerminator().wait_exited(proc, "k", timeout=5.0)` after sending SIGTERM to the group, asserting `True`.
3. Add a test that starts a child ignoring SIGTERM (a Python one-liner with `signal.signal(signal.SIGTERM, signal.SIG_IGN)` that sleeps) and asserts `terminate_with_timeout(proc, "k", timeout=1.0)` returns `True` after the SIGKILL escalation and the child ends with a SIGKILL exit status.
### Method
- Place the tests in the existing test class or a new class in the same file, using the file's existing `pytest.mark.asyncio` style; clean up any leftover child in a `finally`.
- Run the first two tests before the source change to see them fail (they wait for the full timeout and escalate).
### Details
- The ignore-SIGTERM child needs a short startup wait so the handler is installed before the signal is sent; poll for a readiness marker (for example a line written to stdout) instead of a fixed sleep.

## Compatibility considerations
- N/A: test-only change.

## Security considerations
- N/A: no security impact; children are local, short-lived, and killed in cleanup.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_process_terminator.py -q` (new tests fail before the terminator change, pass after).
- `uv run ruff format --check`, `uv run ruff check`, and `uv run mypy` on the file per `rules/toolchain.md`.

## Completion criteria
- The first two tests fail on the current terminator and pass after the fix; the third passes before and after.
- No leftover child process after the tests.

## Out of Scope
- Modifying any file other than the target file; `issues/done/`, `plans/done/`, `implementations/done/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the real-subprocess tests and observe the first two fail against the current terminator | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) after the terminator change | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (tests for the terminator behavior)
- **Source issue**: issues/done/20261019-215906_mcpshut001_make-mcp-server-shutdown-bounded-and-complete.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-220318_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-220632
- **Related target files**: tests/agent/test_http_lifecycle_process_terminator.py
