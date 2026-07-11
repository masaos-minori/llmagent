## Goal

Make `_probe_mcp_health_detail()` populate the new `parse_failed`/`parse_error` fields
when JSON parsing of a `/health` response body fails, and introduce a small,
independently-testable `_classify_health_failure()` helper that turns any non-fully-
-healthy `McpHealthProbeResult` into a short, log-friendly label — without changing
any restart/degrade decision logic (that is Phase 3's concern).

## Scope

**In-Scope:**
- `scripts/agent/repl_health.py`: update `_probe_mcp_health_detail()`'s JSON-parse
  exception branch to construct `McpHealthProbeResult` with `parse_failed=True` and a
  populated `parse_error`.
- Add a new module-level helper function `_classify_health_failure(probe:
  McpHealthProbeResult) -> str` in `repl_health.py`.
- Add `and not probe.parse_failed` to the existing "fully healthy" branch condition
  (wherever `_watchdog_check_http()` or related code currently treats
  `reachable and status_code == 200` alone as fully healthy) so a 200-status response
  with a malformed body is no longer misclassified as fully healthy.

**Out-of-Scope:**
- Any change to `_watchdog_check_http()`'s logging calls or its call to
  `record_degraded()` — that is Phase 3 (separate implementation doc).
- Any change to which of the 3 existing restart/no-restart decision branches fires.
- `scripts/agent/shared/health_models.py` field definitions — covered by the prior
  Phase 1 doc (`implementations/20260711-165739_health_models_parse_failed_fields.md`).

## Assumptions

- `_probe_mcp_health_detail()` (around line 40 of `repl_health.py`) currently swallows
  any JSON-parse exception into `body = {}` via a bare-ish `except Exception` already
  justified with `# noqa: BLE001` — confirmed by direct read of the plan's Design
  section quoting this code.
- The exception branch currently constructs `McpHealthProbeResult` with
  `restart_recommended=False`, `operator_action_required=False`, `body={}`; this
  behavior must be preserved unchanged — only `parse_failed`/`parse_error` are newly
  populated on that same construction call.
- `_classify_health_failure()` must not read or write any state, must not call
  `record_degraded()` or perform any I/O — it is a pure function used only to produce a
  log-friendly string. This keeps it trivially unit-testable in isolation (see Phase 4
  tests) and keeps it out of `_watchdog_check_http()`'s cyclomatic complexity budget
  (that function is already at CC 18 per `radon cc`).
- Depends on Phase 1 (`health_models.py`) having already added the `parse_failed` /
  `parse_error` fields before this phase's code compiles/type-checks correctly.

## Implementation

### Target file

`scripts/agent/repl_health.py`

### Procedure

1. Confirm Phase 1's `health_models.py` change (new `parse_failed`/`parse_error`
   fields) is present before starting, since this phase's code references them.
2. In `_probe_mcp_health_detail()`, locate the `try: body = resp.json()` /
   `except Exception as exc:` block.
3. In the `except` branch's `return McpHealthProbeResult(...)` call, add:
   - `parse_failed=True`
   - `parse_error=f"{exc} (raw={resp.text[:200]!r})"`
   Leave `reachable=True`, `status_code=resp.status_code`,
   `restart_recommended=False`, `operator_action_required=False`, `body={}` unchanged.
4. Add a new function `_classify_health_failure(probe: McpHealthProbeResult) -> str`
   near the other health-probe helper functions in the same module (see Method for the
   exact branch order and return strings).
5. Locate the branch condition in `_watchdog_check_http()` (or its helper) that
   currently treats a probe as "fully healthy" when
   `probe.reachable and probe.status_code == HTTPStatus.OK`. Add `and not
   probe.parse_failed` to that condition so a malformed-but-200 response is no longer
   classified as fully healthy.
6. Do not add any new log statements or `record_degraded()` calls in this phase — that
   is Phase 3.

### Method

`_classify_health_failure()` is a straight sequential-`if` classifier, evaluated in
this fixed priority order (first match wins):

1. `not probe.reachable` → `"unreachable"`
2. `probe.parse_failed` → `f"malformed JSON ({probe.parse_error})"`
3. `probe.status_code != HTTPStatus.OK` → `f"non-200 (status={probe.status_code})"`
4. `probe.restart_recommended` → `"degraded (restart_recommended=true)"`
5. else → `"degraded (restart_recommended=false)"`

This ordering matters: unreachable is checked first (no status code available),
parse failure is checked before status-code comparison (a malformed body can still
arrive with `status_code == 200`), and the two remaining "reachable, 200, no parse
failure" outcomes are split on `restart_recommended` last.

### Details

- Function signature: `def _classify_health_failure(probe: McpHealthProbeResult) ->
  str:` — module-level, not a method, since it only reads its single argument.
- Include a docstring stating explicitly that this function does not affect any
  restart/degrade decision and is for diagnostic logging only (mirrors the plan's
  Design section wording), to prevent future readers from assuming it drives control
  flow.
- `HTTPStatus.OK` should be used for the status comparison (matches existing style in
  this module) rather than a bare `200` literal — check existing imports in
  `repl_health.py` for `from http import HTTPStatus` and reuse it; add the import only
  if not already present.
- Do not call this function from anywhere yet in this phase except where Phase 3 will
  wire it in — but since Phase 3 is a distinct doc/phase, this phase should leave the
  function defined but only reference it in the "fully healthy" condition update
  (`and not probe.parse_failed`, which does not require calling the classifier).
- Keep the parse-error string bounded: `resp.text[:200]` truncation prevents huge
  bodies from bloating log lines.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/repl_health.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/repl_health.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Complexity | `uv run radon cc scripts/agent/repl_health.py -s` | `_classify_health_failure` graded independently (expected A/B, simple sequential ifs); `_watchdog_check_http` unaffected by this phase alone |
| Tests | `uv run pytest tests/test_mcp_health_degraded.py tests/test_repl_health.py -q` | No new failures (classifier not yet wired into logging, so behavior is unchanged at this phase) |
