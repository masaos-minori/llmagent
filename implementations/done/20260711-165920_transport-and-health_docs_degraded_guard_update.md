## Goal

Update `docs/04_mcp_03_03_transport-and-health.md` to document the new `record_degraded()` guard
(cannot overwrite `UNAVAILABLE`/`HALF_OPEN`), and run the plan's full validation sequence to confirm
Phase 1 and Phase 2 changes are correct and consistent.

## Scope

**In scope:**
- `docs/04_mcp_03_03_transport-and-health.md`: update the `record_degraded()` method-table row
  (around line 65) and the state-transition diagram section to reflect the new guard; document
  `is_unavailable()`'s state-changing side effect explicitly.
- Run the plan's Validation plan checks (lint, type check, architecture, security, tests,
  regression, docs consistency, coverage) after Phase 1 and Phase 2 are implemented.

**Out of scope:**
- `docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md` / `-part2.md` — these document
  watchdog reason strings, not `HealthRegistry` state-machine internals; only touch if they are
  found to describe the now-fixed `record_degraded()` behavior incorrectly (verify during this
  phase, but do not modify speculatively).
- Any change to `scripts/shared/mcp_health.py` or `tests/test_mcp_health_degraded.py` — those are
  covered by Phase 1 and Phase 2's own implementation docs; this phase only verifies them via the
  validation commands.

## Assumptions

1. `docs/04_mcp_03_03_transport-and-health.md` currently has a method table that includes a
   `record_degraded` row around line 65, and a separate state-transition diagram section, per the
   plan's Design section.
2. The doc's existing description of `record_degraded()` does not yet mention the
   `UNAVAILABLE`/`HALF_OPEN` guard (that is the entire point of this update).
3. `is_unavailable()`'s state-changing side effect (transitioning `UNAVAILABLE` to `HALF_OPEN` after
   cooldown) is not yet explicitly called out in this doc and needs a new sentence.
4. Phase 1 (`scripts/shared/mcp_health.py` guard) and Phase 2 (new tests) are implemented before
   this phase's validation commands are run, since several checks (tests, coverage) depend on both.
5. `uv run check-mcp-docs` / `uv run python tools/check_docs_consistency.py` are the doc-consistency
   entry points referenced by `rules/toolchain.md` and the plan's Validation plan table
   respectively; run whichever is confirmed present in `tools/` at implementation time.
6. No `deploy.sh` change is needed: no new module, config key, DB schema, or MCP server was added by
   this plan.

## Implementation

### Target file

`docs/04_mcp_03_03_transport-and-health.md`

### Procedure

1. Open the method table and locate the `record_degraded` row (around line 65).
2. Update the row's description to state: "Sets state to `DEGRADED` unless the current state is
   `UNAVAILABLE` or `HALF_OPEN`, in which case the call is a no-op (logged at debug level) — a
   degraded-but-reachable probe must not clear circuit-breaker state."
3. Locate the state-transition diagram section (or the prose immediately following it).
4. Add one sentence noting that `record_degraded()` cannot move a server out of `UNAVAILABLE` or
   `HALF_OPEN` — i.e., there is no `UNAVAILABLE → DEGRADED` or `HALF_OPEN → DEGRADED` edge via this
   method.
5. Add or update documentation of `is_unavailable()` to note explicitly that it is not a pure query:
   it can transition `UNAVAILABLE` to `HALF_OPEN` as a side effect once the cooldown window has
   elapsed.
6. Cross-check `docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md` and `-part2.md` for
   any prose that describes `record_degraded()` as able to clear `UNAVAILABLE`/`HALF_OPEN`; if found
   incorrect, note it for a follow-up (do not edit speculatively beyond what the plan authorizes).
7. Run the full Validation plan command list (see below) and record pass/fail results.

### Method

- Docs-only edit: locate exact lines via `grep -n "record_degraded" docs/04_mcp_03_03_transport-and-health.md`
  before editing, to target the correct table row and diagram section precisely.
- Keep the added sentences concise and consistent with the doc's existing tone/format (method table
  row style, diagram caption style).
- English-only, per `rules/coding.md`.

### Details

- No production code or test code is touched in this phase.
- This phase's "verification" sub-step is a validation run, not new implementation — if any check
  fails, the fix belongs in Phase 1 or Phase 2's target file, not here.
- No new file created; only the existing docs file is modified.

## Validation plan

Full validation sequence from the plan (all rows apply since this phase performs the final
verification pass across all three target files):

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/shared/mcp_health.py tests/test_mcp_health_degraded.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/mcp_health.py` | No new errors (baseline: 0 today) |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no import changes) |
| Security | `uv run bandit -r scripts/shared/mcp_health.py -c pyproject.toml` | 0 findings (baseline: 0 today) |
| Tests | `uv run pytest tests/test_mcp_health_degraded.py -v` | All pass, including the 8 new tests |
| Regression | `uv run pytest tests/test_tool_executor.py tests/test_tool_executor_order.py tests/test_tool_executor_routing.py tests/test_watchdog.py -q` | No new failures |
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
| Coverage | `uv run coverage run -m pytest tests/test_mcp_health_degraded.py && uv run coverage report --include="*/mcp_health.py"` | `record_degraded()`'s new guard branch covered |
