## Goal

Resolve NC-012 by removing dead method `DiagnosticStore.save_loop_guard_hint` (kind=`loop_guard_hint`, unused in production), its dedicated test, and updating all documentation sections that reference it as open.

## Scope

**In-Scope:**
- Remove `save_loop_guard_hint` method from `scripts/agent/diagnostic_store.py` (lines 212-225)
- Remove `test_save_loop_guard_hint` from `tests/test_diagnostic_store.py` (lines 290-303) and update module docstring (line 5)
- Update 4 documentation locations to remove "Needs confirmation" status and record resolution:
  - `docs/05_agent_10_05_operations-and-observability-monitoring.md:92` — remove loop_guard_hint callout paragraph
  - `docs/00_governance_07_needs-confirmation-inventory.md:203-215` — set NC-012 Status to resolved/closed
  - `docs/05_agent_04_01_state-and-persistence-state-model-part2.md:85,87` — drop table row and contradiction paragraph
  - `docs/05_agent_09_01_data-layer-session-db.md:90` — drop `loop_guard_hint` from the 5 kinds list (leaving 4)

**Out-of-Scope:**
- Any change to `ToolLoopGuard._save_guard_hint` or the `guard_hint` kind string it writes
- NC-013 (`fetch_by_kind` / `fetch_all` unused-caller question) — separate, unrelated NC item
- Modifying `scripts/agent/tool_runner.py` or any other caller of `DiagnosticStore` methods
- Making `gen_rag_reference.py` part of CI/pre-commit

## Assumptions

1. Option A (remove dead code) is the correct resolution — confirmed by inspection: `save_loop_guard_hint`'s `(reason, turn_count)` signature has no matching data source in any real call site (`check_cycle`, `check_dedup`, `check_retry` in `tool_loop_guard.py`); none track or pass a `turn_count` value.
2. No external monitoring system queries `kind="loop_guard_hint"` — repo-wide search found zero references outside `.py`/`.md` files.
3. The two `assert call_args[0][1] == "guard_hint"` assertions in `tests/test_tool_loop_guard.py` (lines 104, 152) remain valid under Option A since they test the actual production path, not the removed method.
4. After removal, `fetch_by_kind(session_id, "loop_guard_hint")` becomes unreachable dead-kind lookup, but this was already true in production (no rows with that kind were ever written).

## Unknowns & Gaps

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any deployment/monitoring config outside this git repository queries `kind="loop_guard_hint"` | No access to external monitoring systems; only repo files searchable | Resolved-by-absence: grep across all config/deploy file types returned zero matches; Option A leaves `guard_hint` kind untouched anyway | False |

No blocking unknowns remain.

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `scripts/agent/diagnostic_store.py` — remove `save_loop_guard_hint` method (lines 212-225)
  - `tests/test_diagnostic_store.py` — remove `test_save_loop_guard_hint` (lines 290-303) and update module docstring (line 5)
  - `docs/05_agent_10_05_operations-and-observability-monitoring.md` — remove NC-012 callout at line 92
  - `docs/00_governance_07_needs-confirmation-inventory.md` — resolve NC-012 entry at lines 203-215
  - `docs/05_agent_04_01_state-and-persistence-state-model-part2.md` — drop table row at line 85 and contradiction paragraph at line 87
  - `docs/05_agent_09_01_data-layer-session-db.md` — drop `loop_guard_hint` from 5 kinds list at line 90
- **Blast Radius:** Low — `save_loop_guard_hint` has exactly one caller in the entire codebase (`tests/test_diagnostic_store.py::test_save_loop_guard_hint`), confirmed via `grep -rn "save_loop_guard_hint" --include="*.py" .`. No production code path invokes it.
- **Risk Metrics:** `scripts/agent/diagnostic_store.py`: 8 commits in git history, low churn. Combined 90-day churn across both code files: 25 commits — none touch `save_loop_guard_hint` specifically since its introduction.
- **Deploy Impact:** None — pure application code + test + doc change, no service restart or config change needed.

## Implementation Steps

1. **Phase 1: Preparation / Analysis**
   - [ ] Re-confirm at implementation time that `grep -rn "save_loop_guard_hint" --include="*.py" .` still shows only the definition and the one test call site
   - [ ] Re-confirm `grep -rn '"guard_hint"\|loop_guard_hint'` across `.py`, `.md`, and config files still matches this plan's findings

2. **Phase 2: Core Logic Implementation (Option A — remove dead code)**
   - [ ] Delete `save_loop_guard_hint` method from `scripts/agent/diagnostic_store.py` (lines 212-225)
   - [ ] Delete `test_save_loop_guard_hint` from `tests/test_diagnostic_store.py` (lines 290-303) and update module docstring at line 5 (remove `save_loop_guard_hint` from the listed convenience methods)
   - [ ] Update `docs/05_agent_10_05_operations-and-observability-monitoring.md:92` — remove the loop_guard_hint callout paragraph entirely (the paragraph starting with "`DiagnosticStore` には `save_loop_guard_hint`(kind=`loop_guard_hint`)というメソッドも定義されているが...")
   - [ ] Update NC-012 in `docs/00_governance_07_needs-confirmation-inventory.md:203-215` — set Status to `resolved`, record resolution text: "`save_loop_guard_hint` method removed, `guard_hint` confirmed as the sole loop-guard kind", set Last Reviewed to today's date
   - [ ] Update `docs/05_agent_04_01_state-and-persistence-state-model-part2.md` — drop the `save_loop_guard_hint()` table row at line 85 and rewrite/remove the contradiction paragraph at line 87 (the paragraph starting with "**矛盾/未整理点:** `DiagnosticStore.save_loop_guard_hint()...`")
   - [ ] Update `docs/05_agent_09_01_data-layer-session-db.md:90` — change the 5 kinds list from `llm_transport_error, serialization_event, partial_completion, transport_failure, loop_guard_hint` to `llm_transport_error, serialization_event, partial_completion, transport_failure` (4 kinds)

3. **Phase 3: Deployment & Verification**
   - [ ] Run `uv run pytest tests/test_diagnostic_store.py tests/test_tool_loop_guard.py -v` and confirm all pass
   - [ ] Run `uv run ruff check scripts/agent/diagnostic_store.py tests/test_diagnostic_store.py` to confirm no lint regressions
   - [ ] Re-run repo-wide `grep -rn "loop_guard_hint"` to confirm zero remaining references outside the updated docs (all should be gone or updated)
   - [ ] No deploy step required

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/diagnostic_store.py` | Unit — existing suite minus removed test | `uv run pytest tests/test_diagnostic_store.py -v` | All remaining tests pass; no reference to removed method |
| `scripts/agent/tool_loop_guard.py` | Unit — existing suite, unchanged assertions | `uv run pytest tests/test_tool_loop_guard.py -v` | All tests pass; `guard_hint` kind assertions at lines 104/152 remain valid |
| Repo-wide dead-reference check | Static — grep sweep | `grep -rn "loop_guard_hint" --include="*.py" --include="*.md" .` | Zero matches after doc updates |
| `scripts/agent/diagnostic_store.py`, `tests/test_diagnostic_store.py` | Lint | `uv run ruff check scripts/agent/diagnostic_store.py tests/test_diagnostic_store.py` | 0 errors |

## Risks

- **Risk**: An external (non-repo) monitoring/dashboard system queries `kind="loop_guard_hint"` and silently continues expecting rows → **Mitigation**: No in-repo evidence of such a consumer found; Option A does not change the `guard_hint` kind or its data at all.
- **Risk**: Doc updates (4 files total) drift out of sync if only some are updated → **Mitigation**: Implementation Steps enumerate all 4 doc locations explicitly, and Phase 3 includes a final repo-wide grep sweep to catch stragglers.
