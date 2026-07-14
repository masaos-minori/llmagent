## Goal

Add test coverage for the two new diagnosable failure classes introduced by Phases
1-3: malformed-JSON probes routed to `record_degraded(reason="malformed_health_response")`,
and distinct log text between the unreachable / malformed / degraded-restart-true
cases, plus a direct unit test of the new `_classify_health_failure()` helper across
all 5 classification outcomes. Then run the full validation plan for this requirement.

## Scope

**In-Scope:**
- `tests/test_mcp_health_degraded.py` (existing watchdog-integration section): add 4
  new test functions:
  1. `test_watchdog_malformed_json_calls_record_degraded_with_reason`
  2. `test_watchdog_degraded_with_restart_recommended_true_logs_distinctly`
  3. `test_watchdog_unreachable_logs_distinctly_from_degraded`
  4. `test_classify_health_failure_all_five_cases`
- Running the full Validation plan (lint, type check, architecture, complexity, tests,
  regression, docs) after tests are added and Phases 1-3 are implemented.

**Out-of-Scope:**
- Any change to production code (`health_models.py`, `repl_health.py`) — this phase is
  test-only, per the plan's Affected areas table ("Blast radius: None (test-only)").
- Any change to the existing `test_watchdog_reachable_restart_does_not_call_record_degraded`
  test beyond what test 2 below extends via additional assertions.

## Assumptions

- Depends on Phase 1 (`health_models.py`), Phase 2 (`_probe_mcp_health_detail()` +
  `_classify_health_failure()` + fully-healthy condition fix), and Phase 3
  (`_watchdog_check_http()` logging + `record_degraded` reason routing) all being
  implemented before these tests can pass.
- `tests/test_mcp_health_degraded.py` already has a "watchdog-integration section"
  containing at least `test_watchdog_reachable_restart_does_not_call_record_degraded`
  — confirmed by the plan's Design section referencing this existing test by name.
- `caplog` (pytest's built-in log-capture fixture) is the appropriate mechanism for
  asserting on log message content, consistent with existing patterns in this test
  file's watchdog-integration section.
- Log-text assertions should check distinguishing substrings (e.g. `"unreachable"` vs
  `"malformed"` vs `"non-200"`) rather than full message equality, per the plan's Risks
  table guidance on brittleness — this keeps tests resilient to minor wording changes
  while still catching regressions in classification.
- `McpHealthProbeResult` construction in new tests must use keyword arguments (matching
  existing test style) and must set `parse_failed=True`/`parse_error=...` explicitly
  where relevant, since these fields default to `False`/`None` otherwise.

## Implementation

### Target file

`tests/test_mcp_health_degraded.py`

### Procedure

1. Open `tests/test_mcp_health_degraded.py` and locate the watchdog-integration test
   section (containing `test_watchdog_reachable_restart_does_not_call_record_degraded`).
2. Add `test_watchdog_malformed_json_calls_record_degraded_with_reason`:
   - Construct an `McpHealthProbeResult` with `reachable=True`, `status_code=200`,
     `restart_recommended=False`, `operator_action_required=False`, `body={}`,
     `parse_failed=True`, `parse_error="<some diagnostic string>"`.
   - Invoke `_watchdog_check_http()` (or whatever entry point the existing watchdog
     tests use — mirror the existing test's setup/mocking pattern) with this probe
     result injected (via mock/monkeypatch, matching existing test conventions).
   - Assert the mocked `health_registry.record_degraded` was called with
     `reason="malformed_health_response"` for the relevant `key`.
   - Assert (via `caplog`) that a `WARNING`-level log record was emitted containing a
     substring indicating "malformed" (e.g. `"malformed"` in the message text).
3. Add `test_watchdog_degraded_with_restart_recommended_true_logs_distinctly`:
   - Extend the existing `test_watchdog_reachable_restart_does_not_call_record_degraded`
     case (construct a probe with `restart_recommended=True`, reachable, 200 status).
   - In addition to existing assertions, assert (via `caplog`) that the log message
     text differs from the unreachable case's message text — specifically check for a
     distinguishing substring like `"restart_recommended=true"` or similar, matching
     whatever `_classify_health_failure()` actually returns for this case.
4. Add `test_watchdog_unreachable_logs_distinctly_from_degraded`:
   - Construct an unreachable probe (`reachable=False`, `status_code=None`).
   - Invoke the watchdog path, capture logs via `caplog`.
   - Assert the log text contains a substring identifying "unreachable" and does NOT
     contain substrings used by the degraded/malformed cases (regression guard for
     "operators can identify the exact health failure class from logs").
5. Add `test_classify_health_failure_all_five_cases`:
   - Import `_classify_health_failure` directly from `scripts.agent.repl_health` (or
     the project's actual import path for that module).
   - Construct 5 `McpHealthProbeResult` instances, one per classification branch:
     unreachable, non-200, malformed (parse_failed=True), degraded-no-restart
     (reachable, 200, restart_recommended=False), degraded-restart-true (reachable,
     200, restart_recommended=True).
   - Call `_classify_health_failure()` on each and assert the returned string matches
     the expected distinguishing substring for each case (per the priority order
     defined in Phase 2's Method section: unreachable checked first, then
     parse_failed, then status_code, then restart_recommended).
6. Run the full Validation plan below.

### Method

Follow existing test file conventions: reuse whatever fixture/mock setup the existing
`test_watchdog_reachable_restart_does_not_call_record_degraded` test uses for
constructing a fake `srv_cfg`, `health_registry` mock, and invoking the watchdog check
function, to keep the 3 integration-style tests consistent with the file's established
patterns. The 4th test (`test_classify_health_failure_all_five_cases`) is a pure unit
test with no mocking required, since `_classify_health_failure()` takes only a
`McpHealthProbeResult` and returns a `str`.

### Details

- Use `caplog.set_level(logging.WARNING)` (or equivalent existing pattern in the file)
  to ensure `WARNING`-level watchdog log messages are captured.
- Prefer `assert "malformed" in caplog.text.lower()` style substring checks over exact
  string equality, per the plan's Risks table (`caplog`-based assertions on log message
  text are more brittle than state-based assertions — mitigated by checking
  distinguishing substrings only).
- For `test_classify_health_failure_all_five_cases`, assert on substrings too (not
  exact equality), for consistency with the rest of the file and to avoid tight
  coupling to exact wording chosen during Phase 2 implementation.
- Confirm the mocked `health_registry.record_degraded` call's `reason` kwarg is
  asserted with an exact string match (`"malformed_health_response"`), since this
  value is a fixed literal contract (not free-form log text) and should be pinned
  precisely.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/repl_health.py scripts/agent/shared/health_models.py tests/test_mcp_health_degraded.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/repl_health.py scripts/agent/shared/health_models.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Complexity | `uv run radon cc scripts/agent/repl_health.py -s` | `_watchdog_check_http` CC does not increase beyond its current 18 |
| Tests | `uv run pytest tests/test_mcp_health_degraded.py -v` | All pass, including the 4 new tests |
| Regression | `uv run pytest tests/test_watchdog.py tests/test_repl_health.py -q` | No new failures — confirms restart decisions unchanged for every existing fixture |
| Docs | `uv run python tools/check_docs_consistency.py` | Passes (no doc claims contradicted; only logging behavior changes) |
