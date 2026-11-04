## Goal
Update `tests/agent/test_http_lifecycle_integration.py` so no test relies on the removed
behavior of dropping a live process from tracking on a startup-failure path (`REQ-007`), and
add the Plan's T-1..T-5 coverage for the terminate-first, outcome-gated startup-failure rule.

## Scope
**Release unit**: N/A: not part of a release unit

- Test-only file; executes after rows 01 and 02 land (`_raise_startup_failure_unconfirmed`
  and the gated poll branches exist).
- Companion verification (no edits here): `tests/agent/test_http_lifecycle_health_check.py`
  and `tests/agent/test_startup_rollback.py` must stay green unmodified.

## Assumptions
- The file's existing fixtures `_make_cfg` and the `mgr` fixture are reused as-is.
- `TerminationOutcome` is already imported in this file (`from agent.http_lifecycle_errors import
  TerminationOutcome`).
- Plan A-2 (corrected): tests drive outcomes through a patched terminator or a real child —
  never a bare fake pid against the real terminator.

## Design decisions
- Deterministic unit tests (`T-2`, `T-3`, `T-5`) patch
  `mgr._process_terminator.terminate_with_timeout` with `AsyncMock(return_value=<explicit
  TerminationOutcome>)`; no bare `AsyncMock()` left on that call path, since the new branches
  read `outcome.confirmed`.
- `T-1` is the only real-child test: `cmd=["python", "-c", "import time; time.sleep(30)"]`
  (`python` is in `_ALLOWED_COMMANDS`), shutdown_event pre-set, real terminator, guaranteed
  teardown `killpg`.

## Alternatives considered
- N/A: Plan Tests section (T-1..T-5) adopted as-is.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_integration.py`

### Procedure
Update `TestShutdownEventPollInterruption::test_shutdown_event_set_before_poll_raises_promptly`
(T-4); add `TestStartupFailureTerminateOrTrack` (new) holding `T-1`, `T-2`, `T-3`, `T-5`; pin
explicit terminator outcomes in the three existing tests that patch `terminate_with_timeout`
with a bare `AsyncMock()`.

### Method
- T-4 (update): patch the terminator with `AsyncMock(return_value=TerminationOutcome.EXITED)`;
  after `HttpStartupError`: reason is still `"shutdown requested"`, terminator awaited once,
  `_http_procs`/`_http_pgids` cleared (confirmed arm).
- T-3 (new unit): via `mgr._health_poll_until_ready` with a pre-set `shutdown_event`;
  `EXITED` outcome → assert `terminate_with_timeout` awaited with `timeout=5.0` and the
  tracking cleared.
- T-2 (new unit): readiness-timeout branch, terminator `return_value=TerminationOutcome.EXIT_UNCONFIRMED`;
  after the raise assert `_http_procs.get("test") is proc_mock`, `_http_pgids.get("test")`
  still set, `_stderr_files.get("test")` not closed; then `mgr.shutdown_all()` with the
  terminator still returning `EXIT_UNCONFIRMED` — assert the return list contains
  `("test", TerminationOutcome.EXIT_UNCONFIRMED)` (the kept-tracked survivor is named) and the
  retained-tracking error appears in `caplog`.
- T-5 (new unit): timeout branch with terminator `side_effect=OSError("boom")`; assert
  `HttpStartupError` still raised with the timeout reason and patched stderr tail, and
  tracking retained (exception classified `EXIT_UNCONFIRMED`, `REQ-005` no-masking).
- T-1 (new integration, `@pytest.mark.asyncio`): real `python -c "import time; time.sleep(30)"`
  child, `startup_timeout_sec=30`, `shutdown_event` set before `mgr.start(...)`; assert
  `HttpStartupError` reason `"shutdown requested"`, the child is gone within the terminate
  timeout (`os.killpg(pgid, 0)` raises `ProcessLookupError`), and teardown attempts
  `killpg` unconditionally with `ProcessLookupError` absorbed.
- Existing tests to pin: `test_failed_start_doesnt_block_subsequent_attempts`,
  `test_startup_failure_contains_reason_on_timeout`, `test_health_check_poll_continues_on_error`
  — change their bare `AsyncMock()` terminator patches to
  `AsyncMock(return_value=TerminationOutcome.EXITED)` so their existing
  "tracking is cleared" assertions remain exact.

### Details
- T-1 uses the real `ProcessTerminator` (no terminator patch); the poll fails fast because the
  health request against the unused port raises `httpx.HTTPError` (caught) and the
  pre-set event aborts the first poll sleep.
- Fake procs: keep `Mock(pid=..., poll=Mock(return_value=None))` with the terminator patched;
  per corrected Plan A-2 the real terminator on such a mock would take the no-pgid
  `proc.terminate()` fallback (`EXIT_UNCONFIRMED`) — patched outcomes keep intent explicit.

## Compatibility considerations
- `T-2` asserts `shutdown_all()`'s existing return contract (unconfirmed pairs), unchanged per
  `REQ-008`.

## Security considerations
- N/A: test-only change; T-1's child writes nothing and is always reaped in teardown.

## Rollback considerations
- N/A: revert the commit (test file only).

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Targeted | `uv run pytest tests/agent/test_http_lifecycle_integration.py -q` | all tests pass, including T-1..T-5 |
| Companion suites unmodified | `uv run pytest tests/agent/test_http_lifecycle_health_check.py tests/agent/test_startup_rollback.py -q` | green |
| Deterministic runtime | run the targeted file twice | identical results, no wall-clock drift beyond T-1 (~<10 s) |
| Static gates | `uv run ruff check tests/agent/test_http_lifecycle_integration.py` | clean |

## Completion criteria
- Every startup-failure test states the terminator outcome explicitly and asserts the
  terminate-or-track result for that outcome (`AC-4`).
- No test asserts that a live child is silently dropped from tracking.

## Out of Scope
- Production code (rows 01/02), the neighboring test files (verification-only here), and
  `StartupInterrupted` classification (Plan UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update T-4 and the three bare-`AsyncMock` tests | Pending | — | — | |
| 2 | Add T-1, T-2, T-3, T-5 per Validation plan | Pending | — | — | Requires rows 01 and 02 landed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation | Pending | — | — | N/A per Plan Documentation Impact |

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
- **Requirement ID**: `REQ-007` (test coverage for the terminate-or-track rule)
- **Source issue**: `issues/20261031-135416_mcporphan001_subprocess-orphaned-startup-interrupt.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-072204_mcporphan001_subprocess-orphaned-startup-interrupt.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-130912
- **Related target files**: `tests/agent/test_http_lifecycle_integration.py`
