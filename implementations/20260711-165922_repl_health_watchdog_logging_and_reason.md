## Goal

Make `_watchdog_check_http()` emit 5 explicitly distinct, diagnosable log messages
(one per failure class: unreachable, malformed JSON, non-200, degraded-no-restart,
degraded-restart-true) instead of today's 2 generic ones, and route malformed-JSON
probes to `record_degraded(key, reason="malformed_health_response")` — all without
changing which of the 3 existing restart/no-restart decision branches fires for any
given probe result.

## Scope

**In-Scope:**
- `scripts/agent/repl_health.py`: `_watchdog_check_http()`'s two failure-handling
  branches (the "reachable, not restart_recommended" branch and the "unreachable or
  restart_recommended" branch):
  - Add a call to `_classify_health_failure(probe)` (introduced in Phase 2) and log its
    result via `logger.warning(...)` with `key` and `srv_cfg.url` included in every
    message.
  - In the "reachable, not restart_recommended" branch: when `probe.parse_failed` is
    `True`, call `health_registry.record_degraded(key, reason="malformed_health_response")`
    instead of the existing `body.get("reason")`/`body.get("message")` extraction
    (which is meaningless on an empty body).

**Out-of-Scope:**
- `McpServerHealthRegistry.record_degraded()`'s own internal state-transition logic
  (`UNAVAILABLE`/`HALF_OPEN` guard) — covered by the sibling plan
  `plans/20260711-134244_plan.md`; this phase only changes the `reason` string value
  passed *into* `record_degraded()`, not its internal behavior.
- Which of the 3 existing decision branches fires (healthy / degraded-no-restart /
  restart-or-give-up) for any given probe result — must remain unchanged.
- Auto-restarting solely because of malformed JSON — explicitly excluded.
- `_probe_mcp_health_detail()` and `_classify_health_failure()` definitions —
  covered by Phase 2 (`implementations/20260711-165855_repl_health_probe_and_classification.md`).

## Assumptions

- Depends on Phase 1 (`health_models.py` new fields) and Phase 2
  (`_probe_mcp_health_detail()` populating those fields, `_classify_health_failure()`
  helper, and the `and not probe.parse_failed` fully-healthy condition update) having
  already landed.
- A parse-failure probe already defaults to `restart_recommended=False` (since `body =
  {}` on parse failure), so it already falls into the "reachable, not
  restart_recommended" (degraded, no-restart) branch today — this phase only makes
  that existing, correct routing *explicit and diagnosable* via logging and the new
  `reason` string; it is not a decision-routing change.
- `_watchdog_check_http()` already has cyclomatic complexity C (18) per `radon cc`,
  near this codebase's stated review threshold (CC >= 15 flags "additional test
  coverage before changes"). This phase must not add new `if`/`elif` branch structure
  beyond what already exists — only a single added log line plus a single conditional
  `record_degraded()` call per modified branch, reusing `_classify_health_failure()`
  (already extracted in Phase 2) to keep classification logic out of this function.
- Malformed JSON must not be treated as `operator_action_required=True` on the
  `McpHealthProbeResult` model itself (there is no body to read that flag from during a
  parse failure, and forcing it to `True` would fabricate data the probe never
  received). Instead, the watchdog's own logging decision (via `_classify_health_failure`
  output at `WARNING` level) provides operator visibility, satisfying "operators can
  identify the exact health failure class" without inventing model data.

## Implementation

### Target file

`scripts/agent/repl_health.py`

### Procedure

1. Locate `_watchdog_check_http()`'s "reachable and not restart_recommended" branch
   (the degraded-no-restart path).
   - Before the existing `operator_action_required` check, add:
     `logger.warning("Watchdog: %r (%s) — %s", key, srv_cfg.url,
     _classify_health_failure(probe))`.
   - Add a conditional: when `probe.parse_failed` is `True`, call
     `health_registry.record_degraded(key, reason="malformed_health_response")` instead
     of the existing `body.get("reason")`/`body.get("message")`-derived reason
     extraction. When `probe.parse_failed` is `False`, keep the existing
     `body.get(...)`-derived reason extraction unchanged.
2. Locate `_watchdog_check_http()`'s "unreachable or restart_recommended" branch (the
   restart-or-give-up path).
   - Replace the single generic `"health check failed, restarting"` log message with
     one that includes `_classify_health_failure(probe)`, e.g.:
     `logger.warning("Watchdog: %r (%s) restarting — %s", key, srv_cfg.url,
     _classify_health_failure(probe))`.
   - Do not change the restart-decision logic itself (`count >= max_restarts` /
     `lifecycle.restart()` calls) — only the log message content changes.
3. Do not modify the "fully healthy" branch's logging (already updated in Phase 2's
   condition change; no additional logging needed there).
4. Verify no new conditional branches were introduced beyond the single `if
   probe.parse_failed` check per modified branch (keep CC flat).

### Method

Both changes are additive at the log-statement level: one `logger.warning(...)` call
added per branch, reusing the already-defined `_classify_health_failure()` from Phase
2 to avoid inline classification logic. The `record_degraded()` reason routing uses a
simple `if probe.parse_failed: ... else: ...` ternary-style branch, not a new nested
`if` structure, to keep `_watchdog_check_http()`'s complexity from increasing.

### Details

- Every new log message must include both `key` (the MCP server's config key) and
  `srv_cfg.url` (the health endpoint URL) so operators can identify *which* server
  triggered the message — matching the existing log statements' style in this
  function.
- Use `%r`/`%s`-style lazy logging arguments (not f-strings) for the `logger.warning`
  calls, consistent with `rules/coding.md`'s "comments and log output: English only"
  and this module's existing logging pattern (`logger.error("... key=value key2=%s",
  val)` per `skills/python-design/workflow.md` Step 6 convention).
- The `reason="malformed_health_response"` string is a fixed literal — do not derive it
  from `body.get(...)` for the parse-failure case, since `body` is `{}` and any such
  extraction would silently produce `None`/garbage.
- Confirm `record_degraded()`'s signature accepts a `reason: str` keyword argument
  before wiring this call (read `McpServerHealthRegistry.record_degraded()` in
  whichever module defines it, likely alongside `health_models.py` or a registry
  module) — this phase does not change that method's signature or internals, only
  supplies a value to its existing `reason` parameter.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/repl_health.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/repl_health.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Complexity | `uv run radon cc scripts/agent/repl_health.py -s` | `_watchdog_check_http` CC does not increase beyond its current 18 |
| Tests | `uv run pytest tests/test_mcp_health_degraded.py -v` | All pass (new tests added in Phase 4) |
| Regression | `uv run pytest tests/test_watchdog.py tests/test_repl_health.py -q` | No new failures — confirms restart decisions (which of the 3 branches fires) are unchanged for every existing fixture |
| Docs | `uv run python tools/check_docs_consistency.py` | Passes — this phase changes only logging, not documented state-machine behavior |
