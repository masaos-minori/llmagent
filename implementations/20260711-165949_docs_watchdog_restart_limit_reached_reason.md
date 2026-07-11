# Implementation Doc: Document `restart_limit_reached` Reason

## Goal

Document the new `restart_limit_reached` degraded-reason value produced by
`record_restart_exhausted()`, including when it appears and that it does not
itself change health state.

## Scope

**In scope:**
- `docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md`: add one new
  subsection documenting the restart-exhaustion outcome and reason string.

**Out of scope:**
- Any code change — this documents the behavior implemented in Phase 1/2
  (`mcp_health.py`, `repl_health.py`).

## Assumptions

- `restart_limit_reached` is set via `record_restart_exhausted()`, called
  from `_watchdog_check_http()` when `count >= max_restarts` (Phase 1/2 of
  this plan).
- It only appears under `startup_mode=subprocess` (the only mode where the
  watchdog performs restarts and tracks `restart_counts`).
- Per plan Assumption 3, this reason does not itself change health state —
  the server is expected to already be `UNAVAILABLE` from preceding
  `record_failure()` calls; `record_restart_exhausted()` only tags the
  reason field.
- The reason can be cleared by a subsequent `record_success()` if the server
  recovers (matches `record_success()`'s existing, already-tested reset of
  `_degraded_reasons` — plan Risks table, row 3: intended behavior, not a
  new risk).

## Implementation

### Target file

`docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md`

### Procedure

1. Locate the existing enumeration/table of `get_degraded_reason()` values
   documented in this file.
2. Add a new subsection (or table row, matching the doc's existing format)
   for `restart_limit_reached`.
3. Cross-reference the new `record_restart_exhausted()` method (documented
   in the Phase 1 implementation doc) as the source of this reason string.

### Method

Not applicable (documentation-only). Reference existing method name
`record_restart_exhausted(server_key)` and the constant string value
`"restart_limit_reached"`.

### Details

New subsection content:

- **Reason value:** `restart_limit_reached`
- **Set by:** `McpServerHealthRegistry.record_restart_exhausted(server_key)`
- **Triggered when:** the watchdog's restart attempt count for a server
  reaches `mcp_watchdog_max_restarts` (i.e., `count >= max_restarts` in
  `_watchdog_check_http()`), and only when `startup_mode=subprocess`.
- **State effect:** none — this reason does not itself change
  `McpServerHealthState`; the server is expected to already be
  `UNAVAILABLE` from prior `record_failure()` calls made during the
  preceding restart attempts.
- **Operator meaning:** distinguishes "still cycling through automatic
  restarts" from "watchdog gave up; manual intervention required."
- **Clearing:** overwritten/reset like any other degraded reason on the next
  successful health check via `record_success()`.
- Cross-link to the `McpServerHealthRegistry` shared-wiring paragraph in
  `docs/04_mcp_03_03_transport-and-health.md` (Phase 4's other doc) if this
  file's format supports cross-references to other doc files.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Docs consistency | `uv run python tools/check_docs_consistency.py` | Passes |
| Docs consistency (MCP-specific) | `uv run check-mcp-docs` | Passes |
| Manual | Confirm the new subsection's claims match the final Phase 1/Phase 2 implementation (method name, string constant, trigger condition) | Matches Design |
