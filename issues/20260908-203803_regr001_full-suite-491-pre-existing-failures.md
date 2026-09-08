# Full test suite has 491 pre-existing failures from at least 5 independent, unrelated regressions

## Priority
High

## Summary
A full `uv run pytest tests/ -q` run on current `origin/master` (as of commit `fc5e672a6`) shows 491 failed / (thousands) passed. None of these are caused by, or related to, `scripts/db/recovery.py`/`tests/db/test_db_recovery.py` (confirmed: 0 failures in `test_db_recovery.py`, which passes 20/20 in isolation). Sampling across the failing files surfaced at least 5 distinct, independent root causes, meaning the full suite currently cannot distinguish a genuine new regression from this pre-existing noise. This issue records what was found during that sampling so the individual root causes can be triaged and fixed as separate, focused follow-ups — it does not fix any of them.

## Background
Discovered while running `/git-commit-and-sync` and `code-implementation` cycles unrelated to any of these files. One root cause (unknown-top-level-config-key rejection breaking legacy test configs) is already tracked in `issues/20260908-162735_cfgval001_unknown-key-validation-breaks-legacy-test-configs.md` — do not duplicate that one here; it is referenced below only to show it is one of several concurrent causes, not the only one.

Confirmed by direct reproduction (each command run individually, not inferred from the aggregate 491 count):

1. **`SystemExit: 1` from `ProductionConfigValidator`'s unknown-key rejection** (same root cause as `cfgval001`) — reproduces in `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_approval_preflight.py`, `tests/agent/test_tool_loop_guard.py` (at minimum).
2. **`AttributeError: <module 'agent.startup' ...> does not have the attribute 'find_all_pending_approvals'`** — reproduces in `tests/agent/test_startup.py`. `scripts/agent/startup.py` does not currently define (or no longer defines) a `find_all_pending_approvals` function that the test expects.
3. **`AttributeError: 'Orchestrator' object has no attribute '_llm_turn_executor'. Did you mean: '_llm_executor'?`** — reproduces in `tests/agent/test_orchestrator.py` (78 failures in this file alone, the largest single contributor to the 491 total). The attribute was apparently renamed from `_llm_turn_executor` to `_llm_executor` on `Orchestrator` without updating the tests that construct/patch it.
4. **Diagnostic store tests observe hundreds of pre-existing rows instead of the 1 row they just inserted** — reproduces in `tests/agent/test_diagnostic_store.py` (e.g. `test_save_transport_failure`: `assert len(rows) == 1` fails with `assert 801 == 1`, i.e. 801 rows already present). This reproduces even running the file in isolation (24 failed / 13 passed), so it is not pytest-random-order test pollution between files — the test fixture appears to be reading/writing a shared, persistent diagnostics database rather than an isolated one per test.
5. **Assertion failure comparing to an empty string** — reproduces in `tests/agent/commands/test_agent_cmd_session.py` (`assert 'usage' in ''` — the tested command's output is unexpectedly empty). Not yet root-caused; recorded here as a distinct symptom from 1-4, not yet confirmed as its own independent cause or a downstream effect of one of the others.

## Problem
With 491 tests failing for at least 5 unrelated reasons, the full test suite currently cannot serve its intended purpose of catching a genuine regression introduced by an unrelated change — a real new failure is indistinguishable from this existing noise without manually re-deriving which of these (or another, undiscovered) cause is responsible each time. Item 4 in particular (a test observing hundreds of persisted rows) suggests a test isolation problem serious enough to also risk corrupting or growing a real, non-test diagnostics database if the same code path is ever reached outside tests.

## Reason for Change
This blocks confident use of `uv run pytest tests/ -q` as a merge gate — every unrelated change currently must manually verify "did my change add to this list" rather than relying on a clean full-suite run. Item 4's data-isolation question also carries a correctness/data-integrity risk that should not sit untriaged.

## Implementation Intent
This issue is a triage record, not a fix. Recommended next step: split this into (at least) 4 separate follow-up issues — one per root cause below — each independently investigated and fixed:
1. `find_all_pending_approvals` missing from `scripts/agent/startup.py` (or renamed) — reconcile `tests/agent/test_startup.py` with current `startup.py`.
2. `Orchestrator._llm_turn_executor` → `_llm_executor` rename not propagated to `tests/agent/test_orchestrator.py` (and likely other files constructing/patching this attribute — a full `rg -n "_llm_turn_executor" tests/` pass is needed to find all affected call sites, not just `test_orchestrator.py`).
3. `tests/agent/test_diagnostic_store.py`'s apparent shared/persistent-DB test isolation failure — needs investigation into what fixture (or lack of one) controls the diagnostics DB path/lifecycle for this test file, and whether this is unique to this file or a broader `conftest.py`-level gap.
4. `tests/agent/commands/test_agent_cmd_session.py`'s empty-output assertion failure — needs its own root-cause investigation; not yet confirmed related to any of 1-3.

The already-tracked `cfgval001` issue does not need re-filing; note its existence when scoping the split so its affected test files aren't re-investigated as if new.

## Target Files or Areas
- `scripts/agent/startup.py`, `tests/agent/test_startup.py`
- `scripts/agent/orchestrator.py` (or wherever `_llm_executor` is defined), `tests/agent/test_orchestrator.py`, and any other test file referencing `_llm_turn_executor` (unconfirmed full list — see Implementation Intent #2)
- `scripts/agent/diagnostic_store.py` (or equivalent), `tests/agent/test_diagnostic_store.py`, relevant `conftest.py` fixtures
- `tests/agent/commands/test_agent_cmd_session.py` and whatever command it exercises
- `issues/20260908-162735_cfgval001_unknown-key-validation-breaks-legacy-test-configs.md` (already-filed, related but separate)

## Required Changes
- Split this issue into per-root-cause follow-ups once each is scoped (see Implementation Intent).
- For item 4 specifically: confirm as a priority whether the observed shared-row behavior can affect any non-test/production diagnostics data path, given the correctness/data-integrity concern noted above — this determination alone (independent of a full fix) is worth doing quickly.
- Re-run a full `uv run pytest tests/ -q` after each follow-up lands, to confirm the failure count drops and no new unrelated cause was masked by the ones already fixed.

## Constraints
Do not attempt to fix all 5+ causes in one combined change — they affect unrelated modules (`agent/startup.py`, `agent/orchestrator.py`, diagnostic store, a REPL command) and mixing them into one diff would make review and rollback harder than necessary, per the same reasoning `cfgval001` already applied to its own scope.

## Acceptance Criteria
- [ ] Each of the 4 unconfirmed root causes above (items 2-5; item 1/`SystemExit` is already covered by `cfgval001`) is either filed as its own follow-up issue or otherwise formally tracked
- [ ] Item 4's data-isolation question (whether production diagnostics data could be affected) is explicitly answered, not left open
- [ ] A full `uv run pytest tests/ -q` re-run after all follow-ups land shows a failure count of 0 attributable to any of the 5 causes recorded here (a residual, still-undiscovered 6th cause would be a new, separate finding, not a failure of this issue)

## Testing Expectations
- `uv run pytest tests/agent/test_tool_policy.py tests/agent/test_tool_approval_preflight.py tests/agent/test_tool_loop_guard.py` — should pass once `cfgval001` is resolved (not this issue's own scope)
- `uv run pytest tests/agent/test_startup.py` — should pass once item 2 is resolved
- `uv run pytest tests/agent/test_orchestrator.py` — should pass once item 3 is resolved
- `uv run pytest tests/agent/test_diagnostic_store.py` (run in isolation, not just as part of the full suite) — should pass once item 4 is resolved
- `uv run pytest tests/agent/commands/test_agent_cmd_session.py` — should pass once item 5 is resolved
- Full `uv run pytest tests/ -q` — failure count should drop to (ideally) 0, or to a count fully explained by causes not yet discovered

## Documentation Impact
N/A: this issue is a triage record; documentation impact, if any, belongs to each individual follow-up issue once root-caused.

## Out of Scope
- Fixing any of the 5 root causes as part of this issue itself.
- Any change to `scripts/db/recovery.py`, `tests/db/test_db_recovery.py`, or the `cfgval001` issue's own scope.
- Discovering every one of the 491 individual failing test names — this issue records the sampled root causes, not an exhaustive per-test catalog.

## Dependencies
Related to, but does not duplicate, `issues/20260908-162735_cfgval001_unknown-key-validation-breaks-legacy-test-configs.md` (one of the 5+ causes contributing to the same 491-failure count).

## Unresolved Questions
- Full scope of item 3 (`_llm_turn_executor`/`_llm_executor`): whether `tests/agent/test_orchestrator.py` is the only affected file, or whether other test files also reference the old attribute name.
- Root cause of item 4 (diagnostic store): whether this is specific to `tests/agent/test_diagnostic_store.py`'s own fixtures, a `conftest.py`-level gap affecting other test files too, or an actual defect in the underlying `DiagnosticStore`/DB-path resolution code reachable outside tests.
- Whether item 5 (`test_agent_cmd_session.py`) is an independent 5th cause or a downstream symptom of one of items 1-4 (e.g. if the exercised command itself depends on `ProductionConfigValidator` or `Orchestrator`).
- Whether the 491 count fully decomposes into these 5 causes, or whether a 6th (or more) undiscovered cause remains — this issue's sampling was not exhaustive across all 39 distinct failing test files.

## AI Implementation Instruction
Do not attempt a combined fix across multiple root causes. When this issue is picked up, first re-run a full `uv run pytest tests/ -q` to confirm the current failure count and set of failing files (this repository changes quickly; the 491 figure and file list here are a snapshot, not a guarantee of current state). Split into separate, single-cause issues before implementing any fix — do not scope-creep one follow-up into fixing an unrelated cause encountered along the way.
