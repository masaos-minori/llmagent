## Goal
Wire `HealthChecker.poll_until_ready`'s two live-child failure branches — "shutdown requested"
(`REQ-001`) and readiness timeout (`REQ-002`) — through the terminate-first,
outcome-gated rule: terminate, then drop tracking only on `TerminationOutcome.confirmed`.

## Scope
**Release unit**: N/A: not part of a release unit

- Poll-branch rewiring only; the raise helpers themselves are row 01
  (`20261104-130912_01_scripts_agent_http_lifecycle.py.md`) and must land first.
- The early-exit branch is untouched (`REQ-004`).

## Assumptions
- `manager._raise_startup_failure_unconfirmed` exists from the earlier-`seq` sibling document
  (row 01) — resolved by the stale_detector sibling rule.
- `manager._stderr_log_manager` and `manager._cleanup_server_resources` are package-internal
  attributes already used by this module's call sites; extending that usage is consistent
  with the existing delegation style (module docstring lines 9-13).
- `tests/agent/test_http_lifecycle_health_check.py` patches `_cleanup_server_resources` and
  `terminate_with_timeout` with bare `AsyncMock()`s; its assertions target the confirmed path
  (client lifecycle, auth headers) and are expected to stay green — verified by running it,
  not by editing it (it is not a target row).

## Design decisions
- One shared guarded termination helper `_terminate_for_startup_failure` (new) in this module:
  a terminator exception is logged and classified `EXIT_UNCONFIRMED` so it never masks the
  original `HttpStartupError` (`REQ-005`), and both branches share one outcome path.
- Terminate runs before the stderr tail read so output written while the child is being
  signalled is captured in the failure report.
- Confirmed branch keeps the existing `_cleanup_server_resources` → `_raise_startup_failure`
  sequence (read tail + clear handles + pop tracking + raise, unchanged); the unconfirmed
  branch reads the tail via `manager._stderr_log_manager.read_tail` and calls
  `_raise_startup_failure_unconfirmed` — the two paths share no handle-clearing step
  (Plan Design "Tracking helper split").

## Alternatives considered
- Gating inside `_cleanup_server_resources`: rejected — that helper is shared with
  non-startup-failure call sites (`restart`, early-exit) and must keep clearing resources.

## Implementation
### Target file
`scripts/agent/http_lifecycle_health_checker.py`

### Procedure
1. Add module-level `async def _terminate_for_startup_failure(manager, server_key, proc, terminate_timeout_sec) -> TerminationOutcome` (new) after `_interruptible_poll_sleep`.
2. Rewrite the shutdown branch (lines 174-178) and the timeout branch (lines 180-188) of
   `poll_until_ready` to the gated flow in Method; leave everything else in the file unchanged.

### Method
- Helper: `return await manager.process_terminator.terminate_with_timeout(proc, server_key, timeout=terminate_timeout_sec)`;
  wrap in `try/except Exception` (`noqa: BLE001` with justification: a termination failure must
  not mask the startup error it is about to raise) → `logger.warning` + `return TerminationOutcome.EXIT_UNCONFIRMED`.
- Shutdown branch becomes: `outcome = await _terminate_for_startup_failure(...)`;
  if `outcome.confirmed`: `stderr_full = manager._cleanup_server_resources(server_key)` then
  `manager._raise_startup_failure(server_key, "shutdown requested", stderr_full)`;
  else: `stderr_full = manager._stderr_log_manager.read_tail(server_key).decode(errors="replace")`
  then `manager._raise_startup_failure_unconfirmed(server_key, "shutdown requested", stderr_full)`.
- Timeout branch: same shape with the existing reason string
  `f"did not become healthy within {cfg.startup_timeout_sec}s"`; replace today's
  terminate-call-then-raise (lines 180-188) with the gated sequence (terminate first, then the
  confirmed/unconfirmed split — today's pre-terminate `_cleanup_server_resources` call moves
  into the confirmed arm).
- Add `from agent.http_lifecycle_errors import TerminationOutcome` at the import block; update
  `poll_until_ready`'s docstring Raises/Note lines to state: on a live-child failure the child
  is terminated first and tracking is dropped only on a confirmed exit.

### Details
- The `_interruptible_poll_sleep` race, poll loop, degraded-but-live predicate, and per-call-site
  `AsyncClient` note stay untouched.
- `terminate_timeout_sec` is already a parameter (`TERMINATE_TIMEOUT_SEC = 5.0` supplied by
  `_health_poll_until_ready`) — bounded termination is reused, not redefined (`REQ-008`).

## Compatibility considerations
- `poll_until_ready`'s signature is unchanged; `manager` protocol gains one method call that
  row 01 adds to the real manager. Tests that inject fake managers must provide it.

## Security considerations
- N/A: no new data handling; stderr tail flows through the existing masked report sites
  (`StartupFailure` payload unchanged).

## Rollback considerations
- N/A: revert the commit (one helper function plus two branch rewrites).

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Row-03 tests | `uv run pytest tests/agent/test_http_lifecycle_integration.py -q` | T-1..T-5 pass |
| Neighboring suite | `uv run pytest tests/agent/test_http_lifecycle_health_check.py tests/agent/test_http_lifecycle_shutdown_coordinator.py tests/agent/test_http_lifecycle_process_terminator.py -q` | Green without editing these files |
| Static gates | `uv run ruff check scripts/agent/http_lifecycle_health_checker.py` ; `uv run mypy --no-namespace-packages scripts/agent/http_lifecycle_health_checker.py` | Clean |
| Complexity | `radon cc -nc scripts/agent/http_lifecycle_health_checker.py` | `poll_until_ready` stays at grade A/B — no new B+ block above the current grade |

## Completion criteria
- After a shutdown request or timeout with a confirmed exit: tracking is fully cleared and
  `HttpStartupError` carries the reason + stderr tail (`AC-1` confirmed arm).
- After an unconfirmed termination: `_http_procs`/`_http_pgids`/stderr handle stay populated,
  the retained-tracking error is logged, and `shutdown_all()` names the server key (`AC-1`/`AC-2`).
- Early-exit behavior unchanged (`AC-3`); static gates clean.

## Out of Scope
- The raise helpers themselves (row 01), the tests (row 03), the terminator/coordinator
  internals (`REQ-008`), and the `StartupInterrupted` classification (Plan UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261104-180947 | 20261104-181102 | `_terminate_for_startup_failure` added after `_interruptible_poll_sleep`; shutdown and timeout branches rewritten to the gated split; docstring Raises/Note updated; `TerminationOutcome` import added |
| 2 | Add or update tests per Validation plan | Completed | 20261104-181102 | 20261104-181215 | See Blocker Log: 5 terminator patches in the companion file adapted to the `TerminationOutcome` contract (deviation from the no-edit assumption) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261104-181215 | 20261104-181251 | ruff/format/mypy clean; radon -nc empty; neighboring suites 100 passed |
| 4 | Update documentation | Completed | — | 20261104-181251 | N/A per Plan Documentation Impact |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | The Assumptions section states the companion file patches `terminate_with_timeout` with bare `AsyncMock()`s; in fact 5 patches use `AsyncMock(return_value=True)` (pre-`TerminationOutcome` bool leftover). The new `outcome.confirmed` read broke 4 tests (AttributeError on bool). Fix: patched all 5 sites with `AsyncMock(return_value=TerminationOutcome.EXITED)`, which preserves each test's confirmed-path intent; verified by re-running the suite green | Yes | 20261104-181215 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (terminate on shutdown-requested branch), `REQ-002` (consume the outcome on timeout), `REQ-004` (early exit untouched)
- **Source issue**: `issues/20261031-135416_mcporphan001_subprocess-orphaned-startup-interrupt.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-072204_mcporphan001_subprocess-orphaned-startup-interrupt.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-130912
- **Related target files**: `scripts/agent/http_lifecycle_health_checker.py`
