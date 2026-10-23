## Goal

Add `tests/agent/test_stdin_reader.py` proving the primitive's thread mechanism and exit property: request-driven delivery, the one-request guard, cancelled-request delivery, the closed-loop no-op, worker survival after exceptions, the daemon-thread-only assertion, and one `@pytest.mark.integration` subprocess case measuring process exit while a read is abandoned (`plans/20261022-040200_plan.md`, REQ-001, REQ-002, REQ-003, REQ-004, REQ-005; AC-1, AC-3, AC-4).

## Scope

Create one new test file `tests/agent/test_stdin_reader.py`. No existing test file is modified by this row.

## Assumptions

- The primitive exposes an injection point for the read callable (a constructor argument defaulting to builtin `input`, or a settable attribute) so unit tests can drive it deterministically without a TTY.
- The suite runs under `asyncio_mode = "auto"` (`pyproject.toml`); the `integration` marker is already registered (`pyproject.toml:131-137`).

## Design decisions

- Unit tests inject a counting fake read function and assert the call count equals the request count (no speculative pre-read, one read per request).
- The subprocess case keeps the child's stdin pipe open, never writes to it, cancels the read after 100 ms, and asserts the parent sees the child exit within 2.0 s of `time.monotonic()` while the stubbed read would block for 30 s. The 30 s/2 s separation keeps it far from any production timeout constant.

## Alternatives considered

N/A: the Plan's test list is fixed; this row implements them.

## Implementation

### Target file

`tests/agent/test_stdin_reader.py` (new)

### Procedure

1. Write four unit test classes and one integration test as described below.
2. Confirm the cases fail against HEAD (the read is a pool worker and the process waits for it) before implementing the primitive — the mutation guard.

### Method

- `TestRequestDrivenRead` (new): inject a counting fake; assert (a) no line is consumed before a request exists, (b) one read per request, (c) a second concurrent `read()` on the same instance raises `RuntimeError`.
- `TestCancelledRequestDelivery` (new): cancel a request, then complete the read; assert the line is delivered to the newest pending request, discarded when none exists, and that a delivery to a closed loop produces no exception and no log.
- `TestWorkerSurvivesReadErrors` (new): inject a fake that raises `EOFError`, then `KeyboardInterrupt`, then `SystemExit`, then `RuntimeError`; assert each arrives at the awaiting call site as a stored future exception and that the same instance serves the next request.
- `TestReaderUsesNoExecutorAndNoNonDaemonThread` (new): assert `threading.enumerate()` shows the worker is a daemon thread and no non-daemon thread is created by a read; spy on the running loop's `run_in_executor` during a read and assert it is never called.
- `TestAbandonedReadDoesNotDelayProcessExit` (new) (`@pytest.mark.integration`): run `sys.executable -c` with the primitive, keep the child's stdin pipe open and never write to it, start a read, cancel it after 100 ms, let the child's main coroutine return, and assert the child exits within 2.0 s of `time.monotonic()`.

### Details

- Ground the subprocess pattern in `tests/integration/conftest.py:17-35` and the `integration` marker precedent in `tests/agent/test_lifecycle.py:731-795`.
- Each test must fail if its invariant is removed (daemon flag, one-request guard, done-future guard, exception delivery) — this is the mutation guard.

## Compatibility considerations

N/A: new file; does not affect existing tests.

## Security considerations

N/A: tests only.

## Rollback considerations

N/A: delete the file.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/stdin_reader.py` | Unit: injected fake read function; request counting, concurrency guard, cancelled-request delivery, closed-loop no-op, worker survival; plus the `integration` subprocess exit measurement. | `uv run pytest tests/agent/test_stdin_reader.py -v` ; `uv run pytest tests/agent/test_stdin_reader.py -m integration -v` | All cases pass; child exits within 2.0 s while its read is still blocked; no non-daemon thread created (AC-1, AC-3, AC-4). |

## Completion criteria

- All five test classes/cases pass against the implemented primitive.
- The integration case exits within 2.0 s while its read is still blocked.
- The mutation guard holds (each test fails when its invariant is removed).

## Out of Scope

Modifying any existing test file (rows 6, 7, 8).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `tests/agent/test_stdin_reader.py` with the four unit classes and the integration subprocess case | Completed | 20261023-135522 | 20261023-135522 | REQ-001..REQ-005; AC-1, AC-3, AC-4 implemented; full suite 9831 passed; procedures corrected (reader state machine, call-time input lookup, new-markers, nonexistent doc checkers); rows 11-13 added for three further approval test files; generated reference table regenerated |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-135522 | 20261023-135522 |  |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: `issues/20261021-093421_repl002_cancelled_input_read_delays_process_exit.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-040200_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-074240
- **Related target files**: `tests/agent/test_stdin_reader.py`