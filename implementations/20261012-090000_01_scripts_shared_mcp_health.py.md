## Goal

Add a per-server HALF_OPEN in-flight trial flag to `McpServerHealthRegistry` so that at most one trial call is in flight while a server is HALF_OPEN (REQ-001 / ACC-001). The flag is acquired atomically at the UNAVAILABLE→HALF_OPEN transition and released on every exit path.

## Scope

Additions to `McpServerHealthRegistry` in `scripts/shared/mcp_health.py` only:

- `_half_open_trials: set[str]` initialized in `__init__`.
- `acquire_trial(server_key) -> bool` (single-shot: True for the first caller, False once a trial is in flight).
- `release_trial(server_key) -> None` (idempotent).
- `trial_in_flight(server_key) -> bool` (read-only predicate).
- A call to `acquire_trial()` inside `is_unavailable()` at the UNAVAILABLE→HALF_OPEN transition.
- Calls to `release_trial()` in `record_success()` (prev==HALF_OPEN) and `record_failure()` (was_half_open).

## Assumptions

- Dispatch runs on a single asyncio event loop, so plain `set` membership/add is atomic between awaits; the gate must therefore be established at the transition where no `await` intervenes, not in a downstream branch.
- `server_key` is the stable per-server identifier used as the dict/set key throughout the registry.
- Existing state-transition logic (failure threshold, HALF_OPEN cooldown) is unchanged.

## Design decisions

- Use a `set[str]` of in-flight trial keys rather than a per-server boolean: "no trial in flight" is the empty-membership test and each server is independent.
- Acquisition is synchronous and co-located with the state transition in `is_unavailable()`, guaranteeing no await separates setting HALF_OPEN from setting the flag.
- Release is hooked into both terminal transitions (`record_success`→HEALTHY, `record_failure`→UNAVAILABLE) and additionally backstopped by the transport layer's `try/finally` (see the `tool_transport_invoker.py` procedure doc) for cancellation/exception paths.

## Alternatives considered

- Gating only in `_check_health()`'s HALF_OPEN branch: rejected, because the first trial call enters via the transition path (`is_unavailable()`), not that branch, so it would pass uncounted and allow more than one trial.
- An `asyncio.Lock` per server: unnecessary for single-event-loop asyncio and would serialize incorrectly across the await boundary.

## Implementation

### Target file

`scripts/shared/mcp_health.py` — class `McpServerHealthRegistry`.

### Procedure

1. In `__init__`, add `self._half_open_trials: set[str] = set()` next to the other per-server dicts, with a comment that it enforces the single-trial window.
2. Add `acquire_trial(server_key) -> bool`: return `False` if `server_key in self._half_open_trials`; otherwise `add` it and return `True`. Document that it must be called synchronously (no await between the HALF_OPEN observation and this call).
3. Add `release_trial(server_key) -> None`: `self._half_open_trials.discard(server_key)` (idempotent, safe on every exit path).
4. Add `trial_in_flight(server_key) -> bool`: return `server_key in self._half_open_trials`.
5. In `is_unavailable()`, at the cooldown-expired branch, after setting the state to `HALF_OPEN`, call `self.acquire_trial(server_key)` in the same synchronous step, then `return False`.
6. In `record_success()`, after setting `HEALTHY`, if `prev == McpServerHealthState.HALF_OPEN`, call `self.release_trial(server_key)`.
7. In `record_failure()`, keep the `was_half_open` computation; when true, after setting `UNAVAILABLE`, call `self.release_trial(server_key)`.

### Method

Locate `McpServerHealthRegistry` (grep `class McpServerHealthRegistry`), then edit `__init__`, `record_failure`, `record_success`, `is_unavailable`, and append the three new methods near the existing state methods. Match module style: triple-quote docstrings, `logger.info`/`logger.warning` on the release paths.

### Details

- `_half_open_trials` holds the keys currently occupying the single HALF_OPEN trial slot.
- `acquire_trial()` is the single-shot guard: first caller gets `True`, subsequent callers get `False` until `release_trial()` runs.
- The `is_unavailable()` change is the atomic window: state set to HALF_OPEN and flag added with no await between (transition line ~95-96).
- `record_success()` releases only on a HALF_OPEN→HEALTHY transition (line ~73-75); `record_failure()` releases only when the failed probe was the HALF_OPEN trial (was_half_open, line ~48-49).
- The transport layer additionally wraps the invoke path in `try/finally` to release on cancellation/exception — see its own procedure doc.

## Compatibility considerations

- `McpServerHealthRegistry` is re-exported by `scripts/shared/mcp_config.py`; the new methods are additive, so re-export consumers are unaffected.
- Existing callers of `is_unavailable()` / `record_success()` / `record_failure()` see no signature change; only the side-effect set gains a release on the HALF_OPEN terminal transitions.

## Security considerations

- N/A: no auth/authorization or trust-boundary change. Limiting load on a recovering server introduces no new attack surface.

## Rollback considerations

- Revert the additions: remove `_half_open_trials`, the three new methods, and the two call sites. `tests/shared/test_mcp_health.py::TestHalfOpenSingleTrialFlag` fails without the flag, giving a clear regression signal.

## Validation plan

- Unit (async concurrency): extend `tests/shared/test_mcp_health.py` with `TestHalfOpenSingleTrialFlag` — two concurrent calls in HALF_OPEN, assert exactly one acquires the trial (`acquire_trial()` returns `True`) and the other gets `False`.
- Unit: assert `release_trial()` runs on the success (`record_success`) and failure (`record_failure`) paths.
- Lint/type: `ruff` and `mypy` clean.

## Completion criteria

- `_half_open_trials` present and set atomically at the UNAVAILABLE→HALF_OPEN transition; `acquire_trial()` / `release_trial()` / `trial_in_flight()` exist with the specified semantics; release hooked into both terminal transitions; concurrency test passes; `ruff`/`mypy` clean.

## Out of scope

- Breaker thresholds and cooldown timing.
- Other states (HEALTHY, DEGRADED, UNAVAILABLE entry).
- The transport-layer gate/release in `scripts/shared/tool_transport_invoker.py` (separate procedure doc).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261012-111311 | Implementation already present in commit 16e9ac35d; verified via stale_detector (not stale) and 12 passing tests. |
| 2 | Add or update tests per Validation plan | Completed | — | 20261012-111311 | Implementation already present in commit 16e9ac35d; verified via stale_detector (not stale) and 12 passing tests. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261012-111311 | Implementation already present in commit 16e9ac35d; verified via stale_detector (not stale) and 12 passing tests. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261012-111311 | Implementation already present in commit 16e9ac35d; verified via stale_detector (not stale) and 12 passing tests. |

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
- **Requirement ID**: REQ-001 / ACC-001
- **Source issue**: issues/done/20261007-154049_halfopen01_limit-half_open-trial-calls-to-one.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-163326_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-090000
- **Related target files**: scripts/shared/mcp_health.py