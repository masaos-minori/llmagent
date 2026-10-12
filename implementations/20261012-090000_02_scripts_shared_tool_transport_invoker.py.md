## Goal

Gate HALF_OPEN dispatch on the single-trial flag and release it on every exit path, so concurrent calls in HALF_OPEN yield exactly one dispatched trial and the rest are rejected (REQ-002 / REQ-003 / ACC-002, ACC-003).

## Scope

`scripts/shared/tool_transport_invoker.py` only:

- `_check_health()` returns `(error_result_or_None, owns_half_open_trial)`.
- In the HALF_OPEN branch, call `acquire_trial()`; on success return `(None, True)`, on failure return an "unavailable"/"trial in progress" error result with `False`.
- `_run_precall_gates()` wraps its body in `try/finally` that calls `release_trial()` when this call `owns_half_open_trial`.

## Assumptions

- `_check_health()` is invoked on the synchronous path before any `await`, so `acquire_trial()` runs with no await between observing HALF_OPEN and setting the flag.
- `record_success()` / `record_failure()` in the registry also release on the terminal transitions; the `try/finally` here is a backstop for cancellation, exception, and early-return paths.

## Design decisions

- Return a 2-tuple `(result, owns_half_open_trial)` so the caller knows whether it claimed the trial and must release it.
- Reject concurrent HALF_OPEN calls with a normalized tool error result whose message indicates the reason ("HALF_OPEN trial already in progress").
- Release via `try/finally` in `_run_precall_gates()` so cancellation/exceptions never leak the slot; release is idempotent (`discard`), so it coexists safely with the `record_success`/`record_failure` releases.

## Alternatives considered

- Returning only the error result (dropping the bool): rejected, because the caller needs to know whether to release the slot it acquired.
- Releasing only in `record_*`/`finally` without a shared idempotent release: risk of double-release bugs; `release_trial()`'s `discard` makes either release order safe.

## Implementation

### Target file

`scripts/shared/tool_transport_invoker.py`.

### Procedure

1. Change `_check_health()` return type to `tuple[ToolCallResult | None, bool]` and document that the bool is `owns_half_open_trial` (True when this call became the HALF_OPEN trial owner and must release on every exit path).
2. In the `state == McpServerHealthState.HALF_OPEN` branch: call `self._health_registry.acquire_trial(server_key)`. If True, log and return `(None, True)`. Else build an error result whose message contains "HALF_OPEN trial already in progress" via `_error_result(...)` and return `(error_result, False)`.
3. Preserve post-transition ownership detection: after `is_unavailable()`, compute `owns_trial = self._health_registry.trial_in_flight(server_key) and not before_flight` and return `(None, owns_trial)`.
4. In `_run_precall_gates()`, capture `health_err, owns_half_open_trial = self._check_health(server_key)`; wrap the existing gate body in `try/finally`; in `finally`, if `owns_half_open_trial and self._health_registry is not None`, call `self._health_registry.release_trial(server_key)`.

### Method

Grep `_check_health` and `_run_precall_gates`; edit the return typing, the HALF_OPEN branch, and add the `try/finally` around the existing disabled-server / lifecycle / transport checks. Keep the existing check ordering inside the try.

### Details

- The HALF_OPEN branch is the reject-path: concurrent calls observe HALF_OPEN and find the flag already set, so `acquire_trial()` returns `False` and they receive an "unavailable" error.
- The transition path (the call that triggered UNAVAILABLE→HALF_OPEN) sets the flag inside `is_unavailable()` (see the `mcp_health.py` procedure doc) and reports ownership here via the `trial_in_flight` diff.
- `try/finally` covers early returns (disabled server, missing transport) and exceptions — the backstop for REQ-003's cancellation path.
- Release is idempotent (`discard`), so it does not conflict with `record_success`/`record_failure` releases.

## Compatibility considerations

- `_check_health()` is internal; its return type changed from `ToolCallResult | None` to a 2-tuple. Update only its single caller `_run_precall_gates()`.
- `_run_precall_gates()` is called by `invoke()` and `ToolExecutor._raw_execute(); their signatures are unchanged.

## Security considerations

- N/A: no trust-boundary change. The normalized error message must not leak internals beyond the server key and trial status — use the existing `_error_result` helper.

## Rollback considerations

- Restore `_check_health()` to return a single result and remove the `try/finally` release in `_run_precall_gates()`. Failing tests: `tests/shared/test_tool_transport_invoker.py::TestHalfOpenSingleTrialGate` and `tests/shared/test_tool_executor_routing.py::TestToolExecutorHealthGate::test_half_open_allows_trial_dispatch`.

## Validation plan

- Integration: verify exactly one HALF_OPEN call dispatches and concurrent calls get the "trial in progress" error (`TestHalfOpenSingleTrialGate`).
- Integration: verify the flag is released on success, failure, and cancellation (`test_tool_executor_routing.py::TestToolExecutorHealthGate::test_half_open_allows_trial_dispatch` plus a cancellation case).
- Lint/type: `ruff` and `mypy` clean.

## Completion criteria

- `_check_health()` returns the ownership tuple; HALF_OPEN dispatch is gated on `acquire_trial()`; `_run_precall_gates()` releases in `finally` when the call owns the trial; concurrency + release tests pass; `ruff`/`mypy` clean.

## Out of scope

- The registry-side flag in `scripts/shared/mcp_health.py` (separate procedure doc).
- Breaker thresholds and cooldown timing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261012-111324 | Implementation already present in commit 16e9ac35d; verified via stale_detector (not stale) and 12 passing tests. |
| 2 | Add or update tests per Validation plan | Completed | — | 20261012-111324 | Implementation already present in commit 16e9ac35d; verified via stale_detector (not stale) and 12 passing tests. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261012-111324 | Implementation already present in commit 16e9ac35d; verified via stale_detector (not stale) and 12 passing tests. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261012-111324 | Implementation already present in commit 16e9ac35d; verified via stale_detector (not stale) and 12 passing tests. |

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
- **Requirement ID**: REQ-002 / REQ-003 / ACC-002, ACC-003
- **Source issue**: issues/done/20261007-154049_halfopen01_limit-half_open-trial-calls-to-one.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-163326_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-090000
- **Related target files**: scripts/shared/tool_transport_invoker.py