## Goal

Add spy-based tests proving the `close_resources()` ordering on the success path and its
absence on the startup-failure path, and confirm the existing `TestAgentREPLRunSubprocess
Termination` tests still pass. Implements `REQ-004` (`AC-001`/`AC-002`/`AC-003`/`AC-004`).

## Scope

Additions to `tests/agent/test_repl.py` only. No production code is modified.

## Assumptions

- `_make_bare_repl()` builds a bare `AgentREPL` (`AgentREPL.__new__`) with a real
  `ResourceShutdownCoordinator` and a `MagicMock` ctx, as used by the existing
  `TestAgentREPLRunSubprocessTermination`.
- Module-level imports already provide `asyncio`, `AsyncMock`, `MagicMock`, `patch`,
  `pytest` (`tests/agent/test_repl.py:11,17,19`); no new imports are required.
- The existing success/failure tests already exercise the real `close_resources()` body;
  the new tests focus on ordering/spy assertions, not body behavior.

## Design decisions

- Use ordered-log spies (an `AsyncMock` with a `side_effect` that appends to a shared
  list) to assert `close_resources()` is awaited strictly after `input_loop.run()` returns
  (`REQ-001`/`REQ-002`).
- For the failure path, spy on `close_resources()` and assert `assert_not_awaited()`,
  mirroring the existing `test_run_terminates_subprocesses_on_failure` setup while adding
  the `close_resources` assertion and a `write_fatal` call assertion (`REQ-003`).

## Alternatives considered

`N/A: spy/ordering assertions are the direct verification for `AC-001`/`AC-003`; no
simpler mechanism proves call ordering or non-invocation.`

## Implementation

### Target file

`tests/agent/test_repl.py`

### Procedure

Add a new test class `TestAgentREPLRunCloseResourcesOrdering` immediately after the
existing `TestAgentREPLRunSubprocessTermination` class (which ends at line 1304). It
contains two methods:

**1. `test_run_calls_close_resources_only_after_input_loop_on_success`** (`REQ-001`/`REQ-002`,
`AC-001`/`AC-002`)

- Build `call_log: list[str] = []`.
- Define two `side_effect` helpers that append `"input_loop.run"` and `"close_resources"`
  respectively (plain sync functions capturing the shared list).
- `repl = _make_bare_repl()`; set `repl._orchestrator = MagicMock()`,
  `repl._cmds = MagicMock()`, `repl._shutdown_event = asyncio.Event()`.
- `with patch("agent.repl.StartupOrchestrator") as MockStartup:` set
  `MockStartup.return_value.run = AsyncMock(return_value=(MagicMock(), MagicMock(), []))`.
- Patch `repl._input_loop.run` and `repl._shutdown.close_resources` with
  `AsyncMock(side_effect=...)` bound to the two log helpers.
- `await repl.run()`.
- Assert `assert call_log == ["input_loop.run", "close_resources"]`.

**2. `test_run_does_not_close_resources_on_startup_failure`** (`REQ-003`, `AC-003`)

- Mirror `test_run_terminates_subprocesses_on_failure`:
  `patch("agent.repl.StartupOrchestrator")`; a rollback coroutine awaits
  `repl._ctx.services.lifecycle.shutdown_all()` then raises
  `RuntimeError("startup failed")`; set `repl._view.read_multiline = AsyncMock(return_value="")`.
- Wrap `await repl.run()` in `with pytest.raises(RuntimeError, match="startup failed"):`
  and, inside the same block, patch `repl._shutdown.close_resources` with
  `patch.object(repl._shutdown, "close_resources", new_callable=AsyncMock) as close_spy`.
- Inside the block assert:
  - `close_spy.assert_not_awaited()` (`close_resources` is NOT awaited on failure),
  - `repl._view.write_fatal.assert_called_once()` (fatal message written),
  - `repl._ctx.services.lifecycle.shutdown_all.assert_awaited()` (startup rollback ran).

### Method

Append the new class at the end of the file (after line 1304). Reuse the existing
helpers/patterns (`_make_bare_repl`, `patch`, `AsyncMock`, `MagicMock`, `pytest`).

### Details

- `write_fatal` is a sync method (called without `await` in `repl.py:127`); spy it with a
  plain `MagicMock` via `patch.object(repl._view, "write_fatal")`.
- The success-path test replaces the real `close_resources` body with a spy; body safety
  under the `MagicMock` ctx is covered by the existing
  `test_run_does_not_terminate_subprocesses_on_success` (`T-003`), which still runs the
  real body after the move.
- Keep the new class's style consistent with the surrounding class (trailing blank lines,
  docstrings).

## Compatibility considerations

`N/A: test-only additions; existing `TestAgentREPLRunSubprocessTermination` methods are
left unchanged (behavior-lock).`

## Security considerations

`N/A: test-only.`

## Rollback considerations

`N/A: revert the commit.`

## Validation plan

- `uv run pytest tests/agent/test_repl.py tests/agent/test_startup_rollback.py` → all
  pass, including `TestAgentREPLRunSubprocessTermination` (`T-003`) and the two new tests
  (`T-001` ordering, `T-002` failure-path).

## Completion criteria

- New class `TestAgentREPLRunCloseResourcesOrdering` present with both methods.
- `T-001`: `close_resources` ordering asserted via ordered log.
- `T-002`: `close_resources` `assert_not_awaited`, `write_fatal` called, exception
  propagated, `shutdown_all` awaited.
- Existing subprocess tests pass unchanged (`T-003`).

## Out of scope

- Any change to `scripts/agent/*` production code (covered by
  `implementations/20261012-140112_001_scripts_agent_repl.py.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | `tests/agent/test_repl.py` Superseded by canonical 140942 (session-wide finally, commit 9d54033be); this 133954 no-finally approach NOT implemented |
| 2 | Add or update tests per Validation plan | Completed | — | — | `T-001`/`T-002`/`T-003` Superseded by canonical 140942 (session-wide finally, commit 9d54033be); this 133954 no-finally approach NOT implemented |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | pytest (test-only module) Superseded by canonical 140942 (session-wide finally, commit 9d54033be); this 133954 no-finally approach NOT implemented |
| 4 | Update documentation | Completed | — | — | `N/A: no docs change` Superseded by canonical 140942 (session-wide finally, commit 9d54033be); this 133954 no-finally approach NOT implemented |

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
- **Requirement ID**: `REQ-004` (spy-based tests for the ordering/failure-path contract;
  preserve existing `test_repl.py` / `test_startup_rollback.py` behavior)
- **Source issue**: `issues/20261012-124806_start001_startup-failure-cleanup-handler-closes-shared-http-client-before-the-repl-session-begins.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261012-133954_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-140112
- **Related target files**: `tests/agent/test_repl.py`