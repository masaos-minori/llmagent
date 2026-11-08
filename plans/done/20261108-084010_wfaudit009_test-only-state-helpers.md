## Goal
Collapse the duplicated workflow persistence API surface: delete the test-only helpers (`attempt_ops.start_attempt`, `attempt_ops.count_attempts`, `StateStore.find_stale_running_attempts`, `StateStore.pending_tool_calls`) and move their tests onto the production helpers that already do the same jobs.

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/agent/workflow/attempt_ops.py` — delete `start_attempt` (L42-77) and `count_attempts` (L104-110).
  - `scripts/agent/workflow/state_store.py` — delete `find_stale_running_attempts` (L174-187) and `pending_tool_calls` (L122-124).
  - `scripts/agent/workflow/idempotency_ops.py` — remove the now-obsolete "not attempt_ops.start_attempt ... change together" comment (L57-59) since the near-duplicate insert path disappears.
  - Tests: retarget every caller test file onto production paths (`begin_stage_if_new`, `recover_stale_attempts`/`_classify_running_attempts`, `tool_call_state_ops.pending_tool_calls` directly, inline COUNT query): `tests/agent/workflow/test_workflow_state_store.py` (import L20; `TestAttempts` block L151-162 plus call sites L166, L182, L252-254; `test_find_stale_returns_only_old_attempts` L517-534; pending-listing sites L719-812), `tests/agent/workflow/test_state_store.py` (`test_find_stale_running_attempts_exposes_lease_keys` L256-269), `tests/agent/workflow/test_workflow_engine.py` (import L15; count asserts L221, L378, L405, L462, L622, L643, L683; pending assert L735), `tests/agent/workflow/test_workflow_stage_persistence.py` (import L11; L42, L61, L73), `tests/agent/workflow/test_workflow_status_vocabulary.py` (import L21; L115).
- **Out-of-Scope**:
  - Wiring the helpers into production instead of deleting (rejected in Design: production already has the executing paths; wiring would create a second API for the same job).
  - `wfaudit015` facade routing (separate plan; this deletion shrinks what 015 must route).
- **Dependencies**: Land after `wfaudit001`/`wfaudit007` (they extend `recover_stale_attempts`, the production path the tests move onto) and coordinate with `wfaudit008` (overlapping test-suite edits).

## Background
Caller census re-verified at HEAD `ad48bfa28` (corrections recorded in Notes): `attempt_ops.start_attempt` — callers are `tests/agent/workflow/test_workflow_state_store.py` (import L20; L153, L160-161, L166, L182, L252-254), `tests/agent/workflow/test_workflow_stage_persistence.py` (import L11; L42, L61, L73) and `tests/agent/workflow/test_workflow_status_vocabulary.py` (import L21; L115); zero production callers in `scripts/` (only a naming mention in `idempotency_ops.py`'s comment). Production creates attempts only through `begin_stage_if_new` (`idempotency_ops.py`), whose comment at L57-59 warns its insert is a near-duplicate of `start_attempt` that "must change together". `attempt_ops.count_attempts` — callers are `tests/agent/workflow/test_workflow_engine.py` (import L15; asserts L221, L378, L405, L462, L622, L643, L683) and `test_workflow_state_store.py` (L162); zero production. `StateStore.find_stale_running_attempts` — called only from `test_state_store.py:267` and `test_workflow_state_store.py:528`; production recovery uses `recover_stale_attempts` (L189-254) over the private `_classify_running_attempts` (L257). `StateStore.pending_tool_calls` (L122-124) — ten test call sites (`test_workflow_state_store.py` L719-812, `test_workflow_engine.py:735`), zero production; the engine calls `tool_call_state_ops` functions directly.

## Problem
Two near-duplicate insert paths (start_attempt vs begin_stage_if_new) invite drift, and four public helpers advertise API that nothing uses while tests exercise code paths production never runs — the suite measures the wrong surface.

## Reason for Change
Precedent: wfreview006 already deleted the StateStore facade-level twins of these methods (`cbb58b12a`); this plan finishes the job at the ops level. Deleting removes the drift hazard and aligns tests with production call paths.

## Implementation Intent
Delete, not wire: every deletion target has a production path already used by the engine (attempt creation via `begin_stage_if_new`, stale detection via `recover_stale_attempts`/`_classify_running_attempts`, pending listing via `tool_call_state_ops.pending_tool_calls`). Tests move to those production entry points, keeping each assertion's observable meaning.

## Requirements
- `REQ-001`: The four helpers no longer exist (`grep` clean in `scripts/` and `tests/`, apart from the surviving `tool_call_state_ops.pending_tool_calls` and its retargeted test callers).
- `REQ-002`: Attempt-creation tests now exercise `begin_stage_if_new` (including its lease/owner stamping branch, which `start_attempt` provided but no test ever exercised) with identical observable assertions.
- `REQ-003`: Stale-detection tests now exercise `recover_stale_attempts` (and its classification report) instead of the deleted finder.
- `REQ-004`: Pending-tool-call tests now call `tool_call_state_ops.pending_tool_calls(store._db, task_id)` (or the facade path kept alive via `wfaudit015`, whichever exists at implementation time).
- `REQ-005`: The `idempotency_ops.py` near-duplicate comment is replaced by a single-source statement (the insert lives here only).

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/attempt_ops.py` | Modify | Delete `start_attempt` (L42-77), `count_attempts` (L104-110); drop the imports they alone used (`uuid`, `AttemptRecord`) | `REQ-001` | Test-only callers (census re-verified at `ad48bfa28`) | `test_workflow_state_store.py`, `test_workflow_engine.py`, `test_workflow_stage_persistence.py`, `test_workflow_status_vocabulary.py` | `Verified` |
| `scripts/agent/workflow/state_store.py` | Modify | Delete `find_stale_running_attempts` (L174-187), `pending_tool_calls` (L122-124) | `REQ-001` | Test-only callers (census re-verified at `ad48bfa28`) | `test_state_store.py`, `test_workflow_state_store.py` | `Verified` |
| `scripts/agent/workflow/idempotency_ops.py` | Modify | Replace near-duplicate warning comment (L57-59) | `REQ-005` | Comment verified verbatim | n/a | `Verified` |
| `tests/agent/workflow/test_workflow_state_store.py` | Modify | Retarget `TestAttempts` (L151-162) and the remaining `start_attempt` sites (L166, L182, L252-254) to `begin_stage_if_new`; add the lease-stamping regression test before deletion; retarget L719-812 pending sites to ops-level `pending_tool_calls`; retarget `test_find_stale_returns_only_old_attempts` (L517-534) to `recover_stale_attempts` | `REQ-001`/`REQ-002`/`REQ-003`/`REQ-004` | Call sites re-verified at `ad48bfa28` | self | `Verified` |
| `tests/agent/workflow/test_state_store.py` | Modify | Retarget `test_find_stale_running_attempts_exposes_lease_keys` (L256-269) to `recover_stale_attempts` behavior | `REQ-003` | Call site verified | self | `Verified` |
| `tests/agent/workflow/test_workflow_engine.py` | Modify | Replace the seven `count_attempts` asserts (L221, L378, L405, L462, L622, L643, L683) with the inline per-task/per-stage COUNT query; retarget L735 to `tool_call_state_ops.pending_tool_calls` | `REQ-001`/`REQ-004` | Call sites re-verified at `ad48bfa28` | self | `Verified` |
| `tests/agent/workflow/test_workflow_stage_persistence.py` | Modify | Retarget the three `start_attempt` creations (L42, L61, L73) to `begin_stage_if_new` | `REQ-002` | Call sites re-verified at `ad48bfa28` | self | `Verified` |
| `tests/agent/workflow/test_workflow_status_vocabulary.py` | Modify | Retarget the single `start_attempt` creation (L115) to `begin_stage_if_new` | `REQ-002` | Call site re-verified at `ad48bfa28` | self | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/idempotency_ops.py` (`begin_stage_if_new`) | The surviving attempt-creation path that takes over the attempt-creation coverage `start_attempt` tests provided. Confirmed no-change (verification): its behavior is untouched by this plan (its comment-only edit lives in the target table) | `REQ-002` |
| `scripts/agent/workflow/state_store.py` (`recover_stale_attempts` L189-254, `_classify_running_attempts` L257) | Production stale-detection path tests move onto. Confirmed no-change (verification): this plan deletes only the two disjoint public methods; edits inside these functions belong to `wfaudit001`/`wfaudit007` | `REQ-003` |
| `scripts/agent/workflow/tool_call_state_ops.py` (`pending_tool_calls`, L90) | Ops-level function tests move onto. Confirmed no-change (verification): the function survives unchanged as the retarget target | `REQ-004` |

## Acceptance Criteria
- `REQ-001`: `grep -rn "start_attempt\|count_attempts\|find_stale_running_attempts\|pending_tool_calls" scripts/ tests/` shows only `tool_call_state_ops.pending_tool_calls` (kept) and `begin_stage_if_new` internals.
- `REQ-002`: Retargeted tests assert the same row outcomes (status `running`, owner/lease columns, count semantics via the count query used by the retry loop).
- `REQ-003`: Recovery coverage unchanged: stale/expired/legacy-classification assertions survive on the production path.
- `REQ-004`: Pending-listing assertions unchanged.
- `REQ-005`: Full `tests/agent/workflow/` green; no assertion deleted.

## Tests
- Retargeting edits (behavior-preserving), plus: a lease-stamping regression test (new) through `begin_stage_if_new` covering the `owner_id`/`lease_expires_at` stamping `start_attempt`'s `lease_duration_sec` branch provided — untested today (no call site passes the parameter), so the test adds the coverage before deletion lands (columns `owner_id`/`lease_expires_at`).
- Mutation guard: after deletion, `uv run pytest tests/agent/workflow/ -q` green; a grep-test pins REQ-001.

## Documentation Impact
- Check `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` and `docs/41_db` for references to the deleted helper names; update if any API row lists them (wfreview006's "document delegation" precedent). Re-verified at `ad48bfa28`: `grep -rn` for the four helper names across `docs/` returns zero matches — confirmed no-change (verification); Phase 3 is a verification-only step, no docs target row.
- Run docs checkers for domain agent/db if edited (not triggered: no doc matches found).

## Assumptions
- Production alternative paths cover every deleted helper's semantics (verified: engine creates attempts via `begin_stage_if_new`; recovery classifies via `_classify_running_attempts`; pending listing exists at ops level).
- `count_attempts` semantics (per task/stage count) remain testable by an inline COUNT query in the retargeted test — production itself counts attempts via the retry loop's range, so no production counter is needed.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | whether `wfaudit015` will add a `StateStore` facade method for pending listing before this plan lands — if yes, REQ-004 targets the facade instead of the ops function | landing order of 015 | check `wfaudit015` execution status at implementation time; either target is assertion-equivalent | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/attempt_ops.py` | Modify | attempt ops module surface | 1 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/state_store.py` | Modify | facade surface | 6 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/idempotency_ops.py` | Modify | comment only | 2 | N/A | not applicable (rsynced) |
| tests (2 files) | Modify | workflow test suite | N/A | N/A | not applicable (rsynced) |

## Design
**Delete with test migration, assertion-for-assertion.** Each deleted helper maps to an existing production entry point (Design table above). Migration preserves observable assertions; where a helper had a unique untested branch (`start_attempt`'s `lease_duration_sec` lease stamping — no existing call site passes it), the new `begin_stage_if_new` regression test must cover the same columns before deletion lands — the migration test is added first, deletion second (same phase, ordered edits).

**Why not wire them into production:** production paths exist and are battle-tested by engine flows; inserting test-driven helpers into production would add indirection the engine does not need and contradict wfreview006's direction (facade delegation, fewer names).

## Implementation steps
1. **Phase 1: Migration tests (`REQ-002`-`REQ-004`).** Retarget test call sites onto production paths; suite green with helpers still present (proves equivalence before deletion).
2. **Phase 2: Deletion (`REQ-001`, `REQ-005`).** Remove the four helpers and the obsolete comment; grep-clean assertion.
3. **Phase 3: Docs check (`REQ-001` propagation).** Grep docs for deleted names; update rows if found.

### Release units
**Unit**: wfaudit009-full | **Phases**: 1, 2, 3 | **Reason**: migrating tests and deleting the helpers are one atomic collapse — either half alone breaks the suite or keeps the duplication.

## Validation plan
- After Phase 1: `uv run pytest tests/agent/workflow/ -q` green with helpers present (equivalence gate).
- After Phase 2: same suite green + grep-clean REQ-001 check.
- Full `uv run pytest tests/ -q` before completion; lint/type gates per `rules/toolchain.md`; docs checkers if docs edited.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A deleted helper had unique coverage the migration test misses (e.g. lease-less legacy insert semantics) | Medium | Medium (silent coverage loss) | Mutation-style check: before deletion, run the new tests with the production path stubbed; ensure they fail when production behavior changes |
| Test migration accidentally changes what a fixture database contains (order/side effects) | Low | Low | Behavior-preserving migration with identical fixture setup, Phase 1 runs before deletion |

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Phase 1: behavior-preserving test migration | In Progress | — | — | Procedure docs 20261108-170505_04..08 created 20261108-170505 |
| 2 | Phase 2: helper deletion and comment cleanup | In Progress | — | — | Procedure docs 20261108-170505_01..03 created 20261108-170505 |
| 3 | Phase 3: documentation verification | Planned | — | — |  |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261108-170505_01_scripts_agent_workflow_attempt_ops.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261108-170505_02_scripts_agent_workflow_state_store.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261108-170505_03_scripts_agent_workflow_idempotency_ops.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261108-170505_04_tests_agent_workflow_test_workflow_state_store.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261108-170505_05_tests_agent_workflow_test_state_store.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261108-170505_06_tests_agent_workflow_test_workflow_engine.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261108-170505_07_tests_agent_workflow_test_workflow_stage_persistence.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261108-170505_08_tests_agent_workflow_test_workflow_status_vocabulary.py.md` | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203222_wfaudit009_test-only-state-helpers.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084010
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Required Changes (collapse) | attempt_ops + state_store | helpers gone | grep assertion |
| `REQ-002` | Issue Evidence (begin_stage path) | test_workflow_state_store.py | same row outcomes | migration tests |
| `REQ-003` | Issue Evidence (recovery path) | test_state_store.py | recovery coverage kept | migration tests |
| `REQ-004` | Issue Evidence (ops-level twin) | test_workflow_state_store.py | pending assertions kept | migration tests |
| `REQ-005` | Issue Evidence (duplicate-insert comment) | idempotency_ops.py | comment accurate | review |

## Notes
- Source verified against HEAD `926dbc109`; census and the near-duplicate comment verified in the issue's `## Adversarial Validation`.
- Sequence: after `wfaudit001`/`wfaudit007` (recovery shape final), coordinated with `wfaudit008` (test-suite edits), before or coordinated with `wfaudit015` (`UNK-01`).
- Adversarial re-verification at HEAD `ad48bfa28` (2026-11-08):
  - Census claim corrected: "only callers are `test_workflow_state_store.py`" was already wrong at `926dbc109` — `test_workflow_engine.py` (`count_attempts` import L15 + seven asserts; `pending_tool_calls` assert L735) and `test_workflow_stage_persistence.py` (three `start_attempt` creations) were callers then too; `ad48bfa28` added a third `start_attempt` caller `test_workflow_status_vocabulary.py` (import L21; L115). Three new Modify rows added to the Implementation Target Files table; all call sites verified at `ad48bfa28`.
  - Line numbers re-anchored at `ad48bfa28`: `count_attempts` L104-110 (was L96-102, shifted by the `finish_attempt` vocabulary guard); `find_stale_running_attempts` L174-187 (was L175-187); facade `pending_tool_calls` L122-124 (was L123-125); `recover_stale_attempts` L189-254 (was L190-248); `_classify_running_attempts` L257 (was L258). `ad48bfa28` added 18 lines to `test_workflow_state_store.py`, shifting `TestAttempts` to L149-190 and the pending-listing block to L711-812.
  - Lease-stamping coverage claim corrected: none of the ten `start_attempt` call sites passes `lease_duration_sec`, so the branch is untested today; the `begin_stage_if_new` regression test (new) adds equivalent coverage instead of "keeping" existing coverage.
  - Docs check confirmed no-change (verification): `grep -rn` for the four helper names across `docs/` returns zero matches; Phase 3 stays verification-only, no docs target row.
- Sibling overlap reconciliation (disjoint regions, explicit sequencing): `state_store.py` is also targeted by `wfaudit001` (`implementations/20261108-134201_01`) and `wfaudit007` (`implementations/20261108-135741_01`), whose edits live inside `recover_stale_attempts`/`_classify_running_attempts`/`RecoveryReport` and the new `purge_finished_workflow_events` (new); this plan deletes only the two disjoint public methods and anchors its edits by symbol, not line number. `idempotency_ops.py` is also targeted by `wfaudit001` (`134201_02`, semantics comment L42-46) — disjoint from this plan's L57-59 insert comment. Landing order per Scope Dependencies: `wfaudit001` -> `wfaudit007` -> this plan; line citations in this plan shift once those land. `wfaudit008` (`162804_*`) targets `workflow_engine_adapter.py`/`tests/agent/test_orchestrator.py` — no file overlap with this plan; its ~41-line alias deletion shifts adapter line anchors for other plans only.
- Procedure pass (2026-11-08): eight procedure documents generated (target-table rows 1-8); no docs procedure (grep no-op confirmed). `tools/check_plan_target_overlaps.py` reports "No findings" across active Frozen plans.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-170505 -->