## Goal

Bound the cancellation unwind on the shutdown branch of the mid-turn race so a signal during a turn stops the loop instead of awaiting the cancelled dispatch forever. Wraps the existing unbounded `await dispatch_task` with `asyncio.wait_for(..., timeout=self._GRACEFUL_TIMEOUT_S)` and routes the timeout through the module's existing warning helper.

## Scope

Only `scripts/agent/repl_input_loop.py`: the shutdown branch of `_repl_loop` (`:274-281`) where the in-flight dispatch is cancelled and awaited without a limit. Keeps the race structure, the `None`-fallback read branch (`:189-194`), and `run()`'s signature byte-identical. No other source file, and no `docs/*.md` edit.

## Assumptions

- `REQ-001` (the sibling `repl.py` row) makes this branch reachable by giving `ReplInputLoop` a non-`None` event; this row only bounds the unwind once it is live.
- In Python 3.12+ `wait_for` raises `TimeoutError` when the bound expires regardless of whether the awaited task unwinds, so the bound is deterministic.
- A cancelled-but-unwinding task can outlive the loop; the boundary and the open question are recorded in UNK-03/WI-02 rather than hidden.

## Design decisions

- Bound the unwind instead of inventing a second mechanism. The reachable branch at `:274-281` already cancels `dispatch_task` and `await`s it without a limit; `asyncio.wait_for(dispatch_task, self._GRACEFUL_TIMEOUT_S)` plus `_log_graceful_shutdown_timeout()` reuses the module's existing bound and warning path. This is what REQ-003 and the issue's Acceptance Criteria ask for.
- Keep the existing `CancelledError` handling and the `break` around the bounded wait intact; the change is a local substitution inside the branch, not a restructure.
- Do not change the constant or merge the two definitions (`REQ-004`); the duplicate at `resource_shutdown_coordinator.py:29` stays untouched.

## Alternatives considered

- Adding a new sentinel or flag for the mid-turn bound: rejected — the module already has `_GRACEFUL_TIMEOUT_S` and `_log_graceful_shutdown_timeout()`, and introducing a second mechanism would make the behavioral change unattributable.
- Raising a custom exception on timeout instead of using `wait_for`: rejected — `wait_for` gives deterministic 3.12+ behavior and reuses the existing warning helper.

## Implementation
### Target file
`scripts/agent/repl_input_loop.py`

### Procedure
1. Locate the shutdown branch of `_repl_loop` via grep (line numbers shift by ±1 vs the plan — content-based grep, UNK-03): `grep -n "dispatch_task\|_GRACEFUL_TIMEOUT_S\|_log_graceful_shutdown_timeout\|_should_exit\|await dispatch_task" scripts/agent/repl_input_loop.py`.
2. Confirm the current shape: `:254` creates `dispatch_task`; `:274-281` cancels it and `await`s it with no bound; `:286-308` (the live path) already uses `timeout=self._GRACEFUL_TIMEOUT_S`.
3. Wrap the `await dispatch_task` at `:281` with `asyncio.wait_for(dispatch_task, timeout=self._GRACEFUL_TIMEOUT_S)` and catch `TimeoutError` to call `_log_graceful_shutdown_timeout()`.

### Method
- Verify `_GRACEFUL_TIMEOUT_S` is `10.0` at `:55` and `_log_graceful_shutdown_timeout` is defined at `:122-126` before editing: `grep -n "_GRACEFUL_TIMEOUT_S\|_log_graceful_shutdown_timeout" scripts/agent/repl_input_loop.py`.
- Verify the surrounding `asyncio.CancelledError` handling and the `break` are preserved after the edit.
- After editing, confirm `repl_input_loop.py` is still under the 16384 B size gate and `_repl_loop` did not gain a worse radon grade than HEAD.

### Details
- Current shutdown branch (`:274-281`):
  ```python
  if dispatch_task in pending:
      dispatch_task.cancel()
      try:
          await dispatch_task
      except _InputAborted:
          ...
  ```
  Replace the unbounded `await dispatch_task` with `await asyncio.wait_for(dispatch_task, timeout=self._GRACEFUL_TIMEOUT_S)` and add an `except asyncio.TimeoutError:` branch that calls `self._log_graceful_shutdown_timeout()`, mirroring the live path's handling at `:293-308`.
- Keep the `asyncio.CancelledError` handling and the trailing `break` exactly as they are.
- Leave `_GRACEFUL_TIMEOUT_S` (`:55`, value `10.0`), the `None`-fallback read branch (`:189-194`), and `run()`'s public signature (`:76-115`) unchanged.

## Compatibility considerations
The live path (`:286-308`) already uses this exact bound and warning helper, so the corrected branch matches existing style. `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md:43` and `docs/23_agent/agent_02_runtime-architecture.md:163-165` are corrected in their own rows to describe the now-bounded contract; this row's meaning is preserved because the public `run()` signature and the `None`-fallback path are unchanged.

## Security considerations
N/A: adding a timeout to an existing await carries no security impact.

## Rollback considerations
Revert the single commit; the await returns to its unbounded form, restoring the pre-change state exactly.

## Validation plan
- `uv run pytest tests/agent/test_repl.py::TestMidTurnSignalIsBounded -q` passes for both the non-cooperative stub (warning emitted, dispatch cancelled, loop returns within the bound) and the cooperative stub (no warning) (AC-4).
- `uv run pytest tests/agent/test_repl.py::TestReadInputShutdownRace -q` passes unchanged (AC-3, AC-4).
- `git diff --stat scripts/agent/repl_input_loop.py` lists only this file among the production rows; `resource_shutdown_coordinator.py` shows no diff (AC-5).
- `uv run python tools/check_module_size.py` exits 0 and `radon cc` shows `_repl_loop` did not worsen (Risks mitigation).

## Completion criteria
The shutdown branch of `_repl_loop` awaits the cancelled dispatch through `asyncio.wait_for(..., timeout=self._GRACEFUL_TIMEOUT_S)`, logs via `_log_graceful_shutdown_timeout()` on `TimeoutError`, keeps the existing `CancelledError` handling and `break`, and `_GRACEFUL_TIMEOUT_S` remains `10.0` at `:55`.

## Out of Scope
`scripts/agent/repl.py` (event ownership in its row), `scripts/agent/signal_handler.py` (hook deleted in its row), `scripts/agent/resource_shutdown_coordinator.py` (duplicate constant, untouched), `tests/agent/test_repl.py` fixtures (unchanged), and all `docs/*.md` — byte-identical except the rows that correct them.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Bound the cancellation unwind in `_repl_loop`'s shutdown branch with `wait_for` + `_log_graceful_shutdown_timeout` | Pending | — | — | REQ-002, REQ-003, REQ-004, REQ-006; AC-3, AC-4, AC-5 |
| 2 | Add or update tests per Validation plan | Pending | — | — | REQ-003; AC-4 (TestMidTurnSignalIsBounded) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff/mypy/radon, check_module_size, git diff --stat |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No `docs/*.md` edit in scope (REQ-008) |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-004, REQ-006, REQ-007
- **Source issue**: `issues/20261021-093421_repl001_sigint-sigterm-never-reach-repl-input-loop.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-030840_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-071921
- **Related target files**: `scripts/agent/repl_input_loop.py`
