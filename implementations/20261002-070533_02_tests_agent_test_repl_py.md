# Implementation Procedure: test_repl.py — rewrite failure-path test for `shutdown_all()` termination

## Goal

Rewrite `TestAgentREPLRunSubprocessTermination::test_run_terminates_subprocesses_on_failure`
in `tests/agent/test_repl.py` so it verifies subprocess termination via
`Lifecycle.shutdown_all()` driven through `StartupOrchestrator.run()`, instead of asserting
`repl.py`'s own termination loop (`fake_proc.terminate.assert_called_once()`), which
`option (a)` (removing the loop from `scripts/agent/repl.py`) eliminates.

## Scope

In scope: modify `tests/agent/test_repl.py` only — rewrite the single failure-path test
(`test_run_terminates_subprocesses_on_failure`, lines 1266-1289). Leave
`test_run_does_not_terminate_subprocesses_on_success` (lines 1244-1263) byte-for-byte
unchanged.

Out of scope: modifying `scripts/agent/repl.py` (companion document, seq 01); modifying
`scripts/agent/startup.py` (reference-only); adding new files; touching any other test.

## Assumptions

- `option (a)` is the owner-decided approach (confirmed during issue-to-plan Step 8):
  `repl.py`'s termination loop is removed and termination is owned by
  `StartupOrchestrator.run()`'s internal `lifecycle.shutdown_all()`.
- `tests/agent/test_startup_rollback.py` already locks `shutdown_all()` invocation on the
  exception path; the deeper "every spawned subprocess terminated exactly once" coverage
  lives there and needs no change.
- The harness (`_make_bare_repl`) sets `ctx.services.lifecycle.shutdown_all = AsyncMock()`
  (line 48), so `shutdown_all()` is trackable.

## Design decisions

- Assert delegation, not `repl.py`-internal behavior. After seq 01 removes the loop,
  `fake_proc.terminate` will NOT be called by `repl.py`; the current line-1289 assertion
  (`assert_called_once()`) would fail. The rewritten test must therefore drive the simulated
  startup failure through `shutdown_all()` and assert that `shutdown_all()` was invoked (and
  that `repl.py` itself no longer calls `terminate` directly).
- Keep the change minimal and scoped to the one test method; do not touch the success-path
  test.
- The authoritative "each subprocess terminated exactly once" lock remains in
  `test_startup_rollback.py`; this test is a `repl.py`-level regression guard.

## Alternatives considered

Removing the test entirely and relying solely on `test_startup_rollback.py`. Rejected by the
plan row, which explicitly asks to REWRITE the test to verify `shutdown_all()` termination,
keeping a `repl.py`-level guard that `repl.py` no longer terminates processes directly.

## Implementation

### Target file

`tests/agent/test_repl.py`

### Procedure

Locate `class TestAgentREPLRunSubprocessTermination` (line 1240) and rewrite only
`test_run_terminates_subprocesses_on_failure` (lines 1266-1289). Replace the assertion
`fake_proc.terminate.assert_called_once()` (line 1289) with an assertion that termination is
performed by `Lifecycle.shutdown_all()` driven through `StartupOrchestrator.run()`. Leave
`test_run_does_not_terminate_subprocesses_on_success` (lines 1244-1263) unchanged.

Recommended rewrite (drives `shutdown_all()` via the mocked orchestrator, then asserts it ran):

```python
    @pytest.mark.asyncio
    async def test_run_terminates_subprocesses_on_failure(self) -> None:
        """When startup fails, subprocess termination is delegated to
        Lifecycle.shutdown_all() via StartupOrchestrator; repl.py no longer
        terminates processes directly."""
        import subprocess

        fake_proc = MagicMock(spec=subprocess.Popen)
        fake_proc.poll.return_value = None  # process still alive

        repl = _make_bare_repl()
        repl._orchestrator = MagicMock()
        repl._cmds = MagicMock()

        with patch("agent.repl.StartupOrchestrator") as MockStartup:
            mock_startup_instance = MagicMock()

            async def _run_then_rollback(*_args, **_kwargs) -> None:
                await repl._ctx.services_required.lifecycle.shutdown_all()
                raise RuntimeError("startup failed")

            mock_startup_instance.run = AsyncMock(side_effect=_run_then_rollback)
            MockStartup.return_value = mock_startup_instance
            repl._shutdown_event = asyncio.Event()
            repl._view.read_multiline = AsyncMock(return_value="")
            with pytest.raises(RuntimeError, match="startup failed"):
                await repl.run()

        repl._ctx.services_required.lifecycle.shutdown_all.assert_awaited_once()
```

### Method

1. Confirm the breakage: after seq 01 removes `repl.py`'s loop, the current line-1289
   assertion fails. The current test wires the failure via
   `mock_startup_instance.run = AsyncMock(side_effect=RuntimeError(...))` +
   `mock_startup_instance._spawned_subprocesses = [fake_proc]` (lines 1279-1282), which only
   exercised `repl.py`'s (now-removed) `hasattr` loop — the real
   `StartupOrchestrator.run()` body never runs.
2. Replace the method body with the rewrite above: the mocked `run` first awaits
   `repl._ctx.services_required.lifecycle.shutdown_all()` (the real delegation point) then
   raises, and the final assertion checks `shutdown_all` was awaited once.
3. Do NOT add back any `fake_proc.terminate.assert_*` call — `repl.py` no longer terminates
   directly; per-proc termination is locked by `test_startup_rollback.py`.
4. Leave `test_run_does_not_terminate_subprocesses_on_success` untouched; confirm it still
   passes.

### Details

- Requirements: REQ-002 (each subprocess terminated exactly once via `shutdown_all()`),
  REQ-003 (success/failure flows behave as before).
- Evidence (verified against current source): `test_run_terminates_subprocesses_on_failure`
  at lines 1266-1289 asserts `fake_proc.terminate.assert_called_once()` at line 1289; the
  sibling success-path test at lines 1244-1263 asserts
  `fake_proc.terminate.assert_not_called()` at line 1263 and is unaffected. Harness sets
  `ctx.services.lifecycle.shutdown_all = AsyncMock()` (line 48).
- Reference files read (not modified): `tests/agent/test_startup_rollback.py` (locks
  `shutdown_all()` on the exception path — authoritative coverage for this requirement),
  `scripts/agent/startup.py` (the `except ... : await self._ctx.services_required.lifecycle
  .shutdown_all()` handler at line 81).
- Companion doc: `implementations/20261002-070533_01_scripts_agent_repl_py.md` (seq 01)
  removes the loop this test previously asserted.

## Compatibility considerations

- Success-path contract preserved; the success-path test is unchanged.
- No change to production code contracts.

## Security considerations

N/A: test-only change; no secrets, credentials, network access, or input handling introduced.

## Rollback considerations

Revert the edit to `tests/agent/test_repl.py` via `git checkout tests/agent/test_repl.py`
or by reverting the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| tests/agent/test_repl.py::TestAgentREPLRunSubprocessTermination | Regression | `uv run pytest tests/agent/test_repl.py::TestAgentREPLRunSubprocessTermination` | Both tests pass |
| tests/agent/test_startup_rollback.py | Regression (shutdown_all coverage) | `uv run pytest tests/agent/test_startup_rollback.py` | All pass |
| tests/agent/test_repl.py | Format + lint | `uv run ruff format tests/agent/test_repl.py` then `uv run ruff check tests/agent/test_repl.py` | Clean |
| tests/agent/test_repl.py | Type check | `uv run mypy tests/agent/test_repl.py` | No new type errors |

Note: mypy covers `tests/` via pre-commit; pass the explicit path so it is actually checked —
a bare `mypy` skips `tests/` (its `files` scope is `scripts/`).

## Completion criteria

- `test_run_terminates_subprocesses_on_failure` asserts `shutdown_all()`-based termination
  (not `repl.py`'s direct `terminate` call).
- `test_run_does_not_terminate_subprocesses_on_success` still passes unchanged.
- `test_startup_rollback.py` still passes (authoritative `shutdown_all` coverage intact).
- `ruff` and `mypy` are clean on the file.

## Out of scope

- Modifying `scripts/agent/repl.py` (companion document, seq 01).
- Modifying `scripts/agent/startup.py` (reference only).
- Any `docs/*.md` update.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the failure-path test to assert `shutdown_all()`-based termination | Pending | — | — | Per Implementation > Procedure/Method/Details |
| 2 | Confirm success-path test still passes | Pending | — | — | Unchanged per scope |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs in scope |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/done/20260930-161945_repl001_startup_failure_subprocess_cleanup_hasattr_introspection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-103625_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261002-070533
- **Related target files**: tests/agent/test_repl.py
