## Goal

Resolve NC-013 by removing dead methods `DiagnosticStore.fetch_by_kind` and `DiagnosticStore.fetch_all` (no production callers found), their dedicated tests, and updating all documentation sections that reference them as open.

## Scope

**In-Scope:**
- Remove `fetch_by_kind` method from `scripts/agent/diagnostic_store.py` (lines 227-236)
- Remove `fetch_all` method from `scripts/agent/diagnostic_store.py` (lines 238-247)
- Remove `class TestDiagnosticStoreFetchAll` from `tests/test_diagnostic_store.py` (lines 181-208)
- Remove `test_fetch_by_kind_returns_empty_for_unknown_kind` and `test_fetch_by_kind_filters_by_kind` from `tests/test_diagnostic_store.py` (lines 306-334)
- Rewrite `tests/test_regression_diagnostic_persist.py::test_null_session_id_entry_stored` (lines 114-125) to verify null-`session_id` persistence via direct query against `fake_db._conn` instead of `store.fetch_all()`
- Update 4 documentation locations to remove "Needs confirmation" status and record resolution:
  - `docs/05_agent_10_05_operations-and-observability-monitoring.md:93` — replace "Needs confirmation" callout with confirmed-dead-code determination
  - `docs/00_governance_07_needs-confirmation-inventory.md:216-227` — set NC-013 Status to resolved/closed
  - `docs/05_agent_09_01_data-layer-session-db.md:92,96` — remove `fetch_by_kind`/`fetch_all` from documented read-side API list
  - `docs/05_agent_04_01_state-and-persistence-state-model-part2.md:72` — remove `fetch_all` from listed DiagnosticStore methods

**Out-of-Scope:**
- Any change to `DiagnosticStore.save()`, `fetch()`, or other convenience `save_*` methods which are confirmed live
- NC-012 (`save_loop_guard_hint` unused method) — separate, already-resolved sibling item
- Making `gen_rag_reference.py` part of CI/pre-commit

## Assumptions

1. Both `fetch_by_kind` and `fetch_all` are confirmed dead code — repo-wide grep returns zero production callers outside `diagnostic_store.py` and `tests/`.
2. The original addition of `fetch_by_kind` (commit `b0fd0671`, 2026-06-25) anticipated a possible future `/stats` integration, but that was never implemented — confirmed by absence of any `cmd_stats.py` file.
3. `fetch_all` was added as a general-purpose cross-session read API alongside `fetch()`, not tied to any specific planned feature — confirmed by original implementation doc listing it as a baseline method with no specific caller named.
4. After removal, `test_null_session_id_entry_stored` must be rewritten to use a direct SQLite query (`SELECT ... FROM session_diagnostics WHERE session_id IS NULL`) against `fake_db._conn` instead of `store.fetch_all()`, because `DiagnosticStore.fetch(session_id)` cannot be used here — passing `None` produces `WHERE session_id = NULL` which is never true in SQL (must be `IS NULL`).
5. No external system depends on these methods since they are Python-level methods on an internal class, not an exposed CLI command, HTTP route, or MCP tool.

## Unknowns & Gaps

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any current production code calls `fetch_by_kind` or `fetch_all` | Resolved — repo-wide grep returns zero matches outside `diagnostic_store.py` and `tests/` | False |
| UNK-02 | Whether a concretely planned CLI/API caller exists anywhere in `plans/`, `requires/`, `issues/`, or `docs/` | Resolved — searched all directories; only forward-looking reference is `/stats` idea in `plans/done/20260625-094407_plan.md` (already completed, closed, never wired to `fetch_by_kind`) | False |
| UNK-03 | Whether removing `fetch_all` would break `test_null_session_id_entry_stored` which uses `store.fetch_all()` as its sole verification step | Resolved — can rewrite test to use direct query against `fake_db._conn`; note `fetch(None)` cannot be used as replacement since `WHERE session_id = NULL` is always false in SQL | False |
| UNK-04 | Whether removal requires touching more documentation than the two files named in the requirement | Resolved — grep found two additional files: `docs/05_agent_09_01_data-layer-session-db.md:92,96` and `docs/05_agent_04_01_state-and-persistence-state-model-part2.md:72` | False |

No blocking unknowns remain.

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `scripts/agent/diagnostic_store.py` — remove `fetch_by_kind` (lines 227-236) and `fetch_all` (lines 238-247)
  - `tests/test_diagnostic_store.py` — remove `class TestDiagnosticStoreFetchAll` (lines 181-208); remove `test_fetch_by_kind_returns_empty_for_unknown_kind` and `test_fetch_by_kind_filters_by_kind` (lines 306-334); update module docstring (line 3)
  - `tests/test_regression_diagnostic_persist.py` — rewrite `test_null_session_id_entry_stored` (lines 114-125) to use direct SQLite query; update module docstring/comment (line 7)
  - `docs/05_agent_10_05_operations-and-observability-monitoring.md` — replace "Needs confirmation" callout at line 93
  - `docs/00_governance_07_needs-confirmation-inventory.md` — resolve NC-013 entry at lines 216-227
  - `docs/05_agent_09_01_data-layer-session-db.md` — remove `fetch_by_kind`/`fetch_all` from read-side API list at lines 92,96
  - `docs/05_agent_04_01_state-and-persistence-state-model-part2.md` — remove `fetch_all` from listed DiagnosticStore methods at line 72
- **Blast Radius:** Low — both methods are read-only, additive convenience methods with zero production call sites confirmed via repo-wide grep. Removing them cannot change any runtime behavior of `scripts/agent/`. Only blast radius within `tests/` (2 files) and `docs/` (4 files).
- **Risk Metrics:** `scripts/agent/diagnostic_store.py`: 4 commits touching these two methods since creation — low churn, low risk to remove.
- **Deploy Impact:** None — no config keys, ports, or `deploy/deploy.sh` entries reference either method.

## Implementation Steps

1. **Phase 1: Preparation / Analysis**
   - [ ] Re-confirm at implementation time that `grep -rn "\.fetch_by_kind(\|\.fetch_all(" --include="*.py" .` still shows zero production callers outside `diagnostic_store.py` and `tests/`

2. **Phase 2: Core Logic Implementation**
   - [ ] Delete `fetch_by_kind` method from `scripts/agent/diagnostic_store.py` (lines 227-236)
   - [ ] Delete `fetch_all` method from `scripts/agent/diagnostic_store.py` (lines 238-247)
   - [ ] Delete `class TestDiagnosticStoreFetchAll` from `tests/test_diagnostic_store.py` (lines 181-208) entirely
   - [ ] Delete `test_fetch_by_kind_returns_empty_for_unknown_kind` and `test_fetch_by_kind_filters_by_kind` from `tests/test_diagnostic_store.py` (lines 306-334)
   - [ ] Rewrite `tests/test_regression_diagnostic_persist.py::test_null_session_id_entry_stored` (lines 114-125): replace `results = store.fetch_all()` with a direct query like `rows = fake_db._conn.execute("SELECT * FROM session_diagnostics WHERE session_id IS NULL").fetchall()` and assert `len(rows) == 1` and `rows[0][1] is None` (assuming `session_id` is column index 1)
   - [ ] Update module docstring in `tests/test_diagnostic_store.py` (line 3) to remove `fetch_all()` and `fetch_by_kind()` from the listed covered methods
   - [ ] Update module docstring/comment in `tests/test_regression_diagnostic_persist.py` (line 7) to match the rewritten test
   - [ ] Update `docs/05_agent_10_05_operations-and-observability-monitoring.md:93` — replace the "Needs confirmation" callout with the confirmed-dead-code determination
   - [ ] Update NC-013 in `docs/00_governance_07_needs-confirmation-inventory.md:216-227` — set Status to `resolved`, record resolution text: "`fetch_by_kind` and `fetch_all` methods removed, confirmed no production callers", set Last Reviewed to today's date
   - [ ] Update `docs/05_agent_09_01_data-layer-session-db.md:92,96` — remove `fetch_by_kind`/`fetch_all` from the documented read-side API list
   - [ ] Update `docs/05_agent_04_01_state-and-persistence-state-model-part2.md:72` — remove `fetch_all` from the listed DiagnosticStore methods

3. **Phase 3: Deployment & Verification**
   - [ ] Run `uv run pytest tests/test_diagnostic_store.py tests/test_regression_diagnostic_persist.py -q` after removal/rewrite to confirm no other code depends on the removed methods
   - [ ] Run `uv run pytest -q` (full suite) to confirm no cross-module dependency was missed
   - [ ] Run `uv run ruff check scripts/agent/diagnostic_store.py tests/test_diagnostic_store.py tests/test_regression_diagnostic_persist.py` to confirm no lint regressions
   - [ ] Re-run repo-wide `grep -rn "fetch_by_kind\|fetch_all" --include="*.py" .` to confirm zero remaining references outside historical records
   - [ ] No deploy step required

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/diagnostic_store.py` | Static — confirm zero remaining references after removal | `grep -rn "fetch_by_kind\|fetch_all" --include="*.py" .` | No matches outside historical `plans/done/`, `implementations/done/` records |
| `tests/test_diagnostic_store.py` | Unit | `uv run pytest tests/test_diagnostic_store.py -q` | All remaining tests pass; no `fetch_by_kind`/`fetch_all` test cases remain |
| `tests/test_regression_diagnostic_persist.py` | Regression | `uv run pytest tests/test_regression_diagnostic_persist.py -q` | `test_null_session_id_entry_stored` passes using rewritten direct-query assertion |
| Full suite | Integration | `uv run pytest -q` | All tests pass, confirming no hidden dependency on the removed methods |
| Import layering | Static | `lint-imports` | 0 violations (no import changes expected from a pure method removal) |

## Risks

- **Risk**: The follow-up removes `fetch_all` without first rewriting `test_null_session_id_entry_stored`'s verification, silently deleting real regression coverage for null-`session_id` persistence → **Mitigation**: This plan explicitly calls out the rewrite (direct query against `fake_db._conn`) as a required step before/alongside the method removal, not an optional cleanup; documented in UNK-03 and Implementation Steps Phase 2.
- **Risk**: Documentation drift — `docs/05_agent_09_01_data-layer-session-db.md` and `docs/05_agent_04_01_state-and-persistence-state-model-part2.md` (found via UNK-04) are not in the requirement's originally named doc list, so a future implementer following only the requirement's two named docs would miss them, leaving stale API documentation after removal → **Mitigation**: Both files are explicitly listed in this plan's Affected Files and Implementation Steps Phase 2.
- **Risk**: A hypothetical external consumer could call these methods directly via Python import, since they are public methods with no `_`-prefix → **Mitigation**: No exposed CLI/API/MCP surface calls them; this is an internal application module (`scripts/agent/`) not published as a library; residual risk accepted as consistent with sibling NC-012 precedent.
