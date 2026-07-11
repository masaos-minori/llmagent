## Goal

Add direct unit tests for every `McpServerHealthRegistry` state transition named in the plan,
including the new `record_degraded()` guard against overwriting `UNAVAILABLE`/`HALF_OPEN`, so the
state machine's behavior is deterministic and fully covered.

## Scope

**In scope:**
- `tests/test_mcp_health_degraded.py`: add 8 new unit tests (per the plan's Design section) that
  exercise `HEALTHY→DEGRADED`, `DEGRADED→UNAVAILABLE`, `UNAVAILABLE→HALF_OPEN` (via
  `is_unavailable()`'s cooldown side effect), `HALF_OPEN→HEALTHY`, `HALF_OPEN→UNAVAILABLE`, the new
  guard for `UNAVAILABLE`, the new guard for `HALF_OPEN`, and `record_success()`'s reset of failure
  count/unavailable timestamp.
- Confirm the existing `test_record_degraded_idempotent()` test still passes unmodified.

**Out of scope:**
- `scripts/shared/mcp_health.py` production code changes — covered by a separate implementation doc
  (Phase 1).
- `docs/04_mcp_03_03_transport-and-health.md` — covered by a separate implementation doc (Phase 3).
- Any test of watchdog probe parsing, `ToolExecutor`, or `HttpTransport` retry logic.

## Assumptions

1. This test file already exists with a `McpServerHealthRegistry` unit-test section (added by prior
   implementation work); new tests are appended there, not created as a new file.
2. `McpServerHealthRegistry` is importable from `shared.mcp_health` as in the existing tests.
3. Phase 1 (the `record_degraded()` guard) is implemented before or alongside these tests, since two
   of the new tests assert the guard's behavior directly.
4. The existing `test_record_degraded_idempotent()` test calls `record_degraded()` twice while state
   is `HEALTHY`→`DEGRADED`, so the new guard does not change its outcome — it must be left
   unmodified and still pass.
5. `half_open_cooldown_sec` (or equivalent) is a constructor parameter of `McpServerHealthRegistry`
   that can be set to `0.0`, or `time.monotonic` can be monkeypatched, to make the
   `UNAVAILABLE→HALF_OPEN` cooldown test deterministic without real sleeps.
6. No existing test in this file already covers `record_failure()`'s own transitions or
   `is_unavailable()`'s cooldown-elapsed side effect directly against the registry (confirmed in the
   plan by reading the file in full and grepping `tests/test_tool_executor*.py`).

## Implementation

### Target file

`tests/test_mcp_health_degraded.py`

### Procedure

1. Add `test_record_failure_below_threshold_sets_degraded`: create a registry, call
   `record_failure()` fewer times than the `UNAVAILABLE` threshold, assert `get_state() ==
   DEGRADED`.
2. Add `test_record_failure_reaches_threshold_sets_unavailable`: call `record_failure()` enough
   times to reach the threshold, assert `get_state() == UNAVAILABLE`.
3. Add `test_is_unavailable_transitions_to_half_open_after_cooldown`: drive a registry to
   `UNAVAILABLE`, use a zero/short cooldown (or monkeypatch `time.monotonic`), call
   `is_unavailable()`, assert it returns `False` (or the expected trial-dispatch semantics) and
   `get_state() == HALF_OPEN` afterward.
4. Add `test_record_success_from_half_open_sets_healthy`: drive a registry into `HALF_OPEN`, call
   `record_success()`, assert `get_state() == HEALTHY`.
5. Add `test_record_failure_from_half_open_sets_unavailable_and_resets_cooldown`: drive a registry
   into `HALF_OPEN`, call `record_failure()`, assert `get_state() == UNAVAILABLE`.
6. Add `test_record_degraded_does_not_overwrite_unavailable`: drive a registry to `UNAVAILABLE`,
   call `record_degraded()`, assert `get_state()` is still `UNAVAILABLE` (not `DEGRADED`).
7. Add `test_record_degraded_does_not_overwrite_half_open`: drive a registry to `HALF_OPEN`, call
   `record_degraded()`, assert `get_state()` is still `HALF_OPEN` (not `DEGRADED`).
8. Add `test_record_success_resets_failure_count_and_unavailable_timestamp`: drive a registry
   partway toward `UNAVAILABLE` (below threshold), call `record_success()`, then call
   `record_failure()` once and assert the state is `DEGRADED` (not `UNAVAILABLE`) — proving the
   failure count was reset to 0, not merely that the visible state changed.
9. Re-run the existing `test_record_degraded_idempotent()` test unmodified; confirm it still passes.

### Method

Use `pytest` plain functions (no new fixtures required unless the existing file already defines a
`registry` fixture — reuse it if present). Each test should:
- Construct a fresh `McpServerHealthRegistry()` (or use the existing fixture) to avoid cross-test
  state leakage.
- Drive the registry to the required starting state using the registry's own public methods
  (`record_failure()`, `record_success()`, `is_unavailable()`) rather than reaching into private
  attributes, except where asserting internal counters is the explicit point of the test (test 8),
  in which case prefer asserting through observable behavior (a subsequent `record_failure()` call)
  over touching `_failure_counts` directly.
- Use `monkeypatch` (pytest builtin) for `time.monotonic` or construct the registry with a
  zero-length cooldown parameter — do not use real `time.sleep()`.

### Details

- Follow existing test naming/style conventions already present in
  `tests/test_mcp_health_degraded.py`.
- Each new test is independent and order-independent (no shared mutable module-level registry).
- No new test file, no new fixture file.
- English-only test names, docstrings, and assertion messages per `rules/coding.md`.

## Validation plan

Checks from the plan's Validation plan table that are relevant to this target file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_mcp_health_degraded.py` | 0 errors |
| Tests | `uv run pytest tests/test_mcp_health_degraded.py -v` | All pass, including the 8 new tests and the unmodified idempotent test |
| Regression | `uv run pytest tests/test_tool_executor.py tests/test_tool_executor_order.py tests/test_tool_executor_routing.py tests/test_watchdog.py -q` | No new failures |
| Coverage | `uv run coverage run -m pytest tests/test_mcp_health_degraded.py && uv run coverage report --include="*/mcp_health.py"` | `record_degraded()`'s new guard branch covered |
