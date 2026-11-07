## Goal
Collapse the duplicated workflow persistence API surface: delete the test-only helpers (`attempt_ops.start_attempt`, `attempt_ops.count_attempts`, `StateStore.find_stale_running_attempts`, `StateStore.pending_tool_calls`) and move their tests onto the production helpers that already do the same jobs.

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/agent/workflow/attempt_ops.py` — delete `start_attempt` (L42-77) and `count_attempts` (L96-102).
  - `scripts/agent/workflow/state_store.py` — delete `find_stale_running_attempts` (L175-187) and `pending_tool_calls` (L123-125).
  - `scripts/agent/workflow/idempotency_ops.py` — remove the now-obsolete "not attempt_ops.start_attempt ... change together" comment (L57-59) since the near-duplicate insert path disappears.
  - Tests: `tests/agent/workflow/test_workflow_state_store.py` (import L20, uses L145-160, L706-735) and `tests/agent/workflow/test_state_store.py` (L267) retargeted to production paths (`begin_stage_if_new`, `recover_stale_attempts`/`_classify_running_attempts`, `tool_call_state_ops.pending_tool_calls` directly).
- **Out-of-Scope**:
  - Wiring the helpers into production instead of deleting (rejected in Design: production already has the executing paths; wiring would create a second API for the same job).
  - `wfaudit015` facade routing (separate plan; this deletion shrinks what 015 must route).
- **Dependencies**: Land after `wfaudit001`/`wfaudit007` (they extend `recover_stale_attempts`, the production path the tests move onto) and coordinate with `wfaudit008` (overlapping test-suite edits).

## Background
Caller census at HEAD (issue `## Adversarial Validation`, grep-verified): `attempt_ops.start_attempt` and `attempt_ops.count_attempts` — only callers are `tests/agent/workflow/test_workflow_state_store.py` (import L20; tests L145-160); zero callers in `scripts/`. Production creates attempts only through `begin_stage_if_new` (`idempotency_ops.py`), whose comment at L57-59 warns its insert is a near-duplicate of `start_attempt` that "must change together". `StateStore.find_stale_running_attempts` — called only from `test_state_store.py:267` and `test_workflow_state_store.py:515`; production recovery uses `recover_stale_attempts` (L190-248) over the private `_classify_running_attempts` (L258). `StateStore.pending_tool_calls` (L123-125) — five test call sites (L706-735), zero production; the engine calls `tool_call_state_ops` functions directly.

## Problem
Two near-duplicate insert paths (start_attempt vs begin_stage_if_new) invite drift, and four public helpers advertise API that nothing uses while tests exercise code paths production never runs — the suite measures the wrong surface.

## Reason for Change
Precedent: wfreview006 already deleted the StateStore facade-level twins of these methods (`cbb58b12a`); this plan finishes the job at the ops level. Deleting removes the drift hazard and aligns tests with production call paths.

## Implementation Intent
Delete, not wire: every deletion target has a production path already used by the engine (attempt creation via `begin_stage_if_new`, stale detection via `recover_stale_attempts`/`_classify_running_attempts`, pending listing via `tool_call_state_ops.pending_tool_calls`). Tests move to those production entry points, keeping each assertion's observable meaning.

## Requirements
- `REQ-001`: The four helpers no longer exist (`grep` clean in `scripts/` and `tests/`).
- `REQ-002`: Attempt-creation tests now exercise `begin_stage_if_new` (including its lease/owner stamping previously tested through `start_attempt`) with identical observable assertions.
- `REQ-003`: Stale-detection tests now exercise `recover_stale_attempts` (and its classification report) instead of the deleted finder.
- `REQ-004`: Pending-tool-call tests now call `tool_call_state_ops.pending_tool_calls(store._db, task_id)` (or the facade path kept alive via `wfaudit015`, whichever exists at implementation time).
- `REQ-005`: The `idempotency_ops.py` near-duplicate comment is replaced by a single-source statement (the insert lives here only).

## Implementation Target Files
**Freeze status**: Draft

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/attempt_ops.py` | Modify | Delete `start_attempt` (L42-77), `count_attempts` (L96-102) | `REQ-001` | Test-only callers (grep census) | `tests/agent/workflow/test_workflow_state_store.py` | `Verified` |
| `scripts/agent/workflow/state_store.py` | Modify | Delete `find_stale_running_attempts` (L175-187), `pending_tool_calls` (L123-125) | `REQ-001` | Test-only callers (grep census) | `test_state_store.py`, `test_workflow_state_store.py` | `Verified` |
| `scripts/agent/workflow/idempotency_ops.py` | Modify | Replace near-duplicate warning comment (L57-59) | `REQ-005` | Comment verified verbatim | n/a | `Verified` |
| `tests/agent/workflow/test_workflow_state_store.py` | Modify | Retarget L145-160 to `begin_stage_if_new`; L706-735 to ops-level `pending_tool_calls` | `REQ-002`/`REQ-004` | Call sites verified | self | `Verified` |
| `tests/agent/workflow/test_state_store.py` | Modify | Retarget L267 to `recover_stale_attempts` behavior | `REQ-003` | Call site verified | self | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/idempotency_ops.py` (`begin_stage_if_new`) | The surviving attempt-creation path whose lease/owner stamping must keep the coverage `start_attempt` tests provided | `REQ-002` |
| `scripts/agent/workflow/state_store.py` (`recover_stale_attempts`, `_classify_running_attempts`) | Production stale-detection path tests move onto | `REQ-003` |
| `scripts/agent/workflow/tool_call_state_ops.py` (`pending_tool_calls`) | Ops-level function tests move onto | `REQ-004` |

## Acceptance Criteria
- `REQ-001`: `grep -rn "start_attempt\|count_attempts\|find_stale_running_attempts\|pending_tool_calls" scripts/ tests/` shows only `tool_call_state_ops.pending_tool_calls` (kept) and `begin_stage_if_new` internals.
- `REQ-002`: Retargeted tests assert the same row outcomes (status `running`, owner/lease columns, count semantics via the count query used by the retry loop).
- `REQ-003`: Recovery coverage unchanged: stale/expired/legacy-classification assertions survive on the production path.
- `REQ-004`: Pending-listing assertions unchanged.
- `REQ-005`: Full `tests/agent/workflow/` green; no assertion deleted.

## Tests
- Retargeting edits (behavior-preserving), plus: a lease-stamping regression test through `begin_stage_if_new` proving the `start_attempt` coverage was not lost (columns `owner_id`/`lease_expires_at`).
- Mutation guard: after deletion, `uv run pytest tests/agent/workflow/ -q` green; a grep-test pins REQ-001.

## Documentation Impact
- Check `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` and `docs/41_db` for references to the deleted helper names; update if any API row lists them (wfreview006's "document delegation" precedent).
- Run docs checkers for domain agent/db if edited.

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
**Delete with test migration, assertion-for-assertion.** Each deleted helper maps to an existing production entry point (Design table above). Migration preserves observable assertions; where a helper had unique coverage (start_attempt's lease stamping), the retargeted `begin_stage_if_new` test must cover the same columns before deletion lands — the migration test is added first, deletion second (same phase, ordered edits).

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
| Work Item | Status | Owner | Started | Completed | Notes |
|---|---|---|---|---|---|
| Phase 1: migration tests | Planned | engineer | | | |
| Phase 2: deletion | Planned | engineer | | | |
| Phase 3: docs check | Planned | engineer | | | |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Work Item | Type | Link | Created |
|---|---|---|---|

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
