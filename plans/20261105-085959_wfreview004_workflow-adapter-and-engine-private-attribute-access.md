## Goal
- Remove the cross-object private attribute access in `WorkflowEngine` and `WorkflowEngineAdapter` (`store._db`, `workflow_engine._wdef`) by using `StateStore.get_connection()`, `StateStore.create_task` / `get_task_by_id`, and a public `WorkflowEngine.version` property, with identical SQL, task ids, and audit payloads.

## Priority
Medium

## Scope
- **In-Scope**: engine use of `get_connection()` for `begin_stage_if_new` and `record_artifact`; adapter use of `StateStore.create_task` / `get_task_by_id`; a public `WorkflowEngine.version` property used at the four adapter sites; migration of the test patches that the adapter rewiring breaks; a unit test for the property.
- **Out-of-Scope**: consolidating `task_ops` and `StateStore` task CRUD; changing the wording of `get_connection()`; private attribute use inside tests that is not broken by this change (`store._db` in `tests/agent/workflow/`, `_wdef` assignments in tests); new `StateStore` wrapper methods.
- **Dependencies**: `N/A: none`. Both dependencies named by the Issue are closed: `issues/done/20261030-105723_wftaskapi001_consolidate-task-persistence.md` with `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`, and `issues/done/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md` with `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md`.

## Background
Adversarial review (2026-11-03) found `self._store._db` in the engine and `store._db` plus `self._workflow_engine._wdef` in the adapter, although `StateStore.get_connection()` and public `create_task` / `get_task_by_id` exist.

## Problem
Verified in Step 2 (line numbers differ slightly from the Issue): `scripts/agent/workflow/workflow_engine.py` passes `self._store._db` to `begin_stage_if_new` and `record_artifact`; `scripts/agent/workflow_engine_adapter.py` `_init_workflow_task` calls `create_task(store._db, ...)` and `get_task_by_id(store._db, ...)` and reads `self._workflow_engine._wdef.version` at four places (an `assert ... is not None` plus three reads, the latter in `_activate_workflow`). `StateStore.create_task` and `get_task_by_id` forward to the same `task_ops` functions with the same arguments, so behavior is identical. `WorkflowEngine._wdef` has no public accessor.

Adversarial finding that changes the scope: 26 test sites patch `agent.workflow_engine_adapter.create_task` or `get_task_by_id` (15 in `tests/agent/test_orchestrator.py`, 11 in `tests/integration/test_orchestrator_integration.py`). Once the adapter stops importing them, `monkeypatch.setattr` raises `AttributeError` and `patch(...)` fails, so those tests become targets. The Issue's rule "do not expand scope to tests unless a chosen seam makes a test unrunnable" applies, and this seam does. The Issue's acceptance grep for `_wdef` must also be read as cross-object access only: `workflow_engine.py` legitimately uses its own `self._wdef`.

## Reason for Change
Both classes are turn-critical; private access freezes internal representation, and a store-level invariant added later would skip the adapter's direct `task_ops` path.

## Implementation Intent
Decisions for the Issue's open question: the engine uses `self._store.get_connection()` (smaller diff, no new public API; `get_connection()` is the sanctioned handle and `Orchestrator.__init__` already uses it); new `StateStore` wrappers for `begin_stage_if_new` / `record_artifact` are rejected for now because they add public surface and the transaction-level helpers still need the same handle. The adapter calls `store.create_task(...)` and `store.get_task_by_id(...)`. The version accessor lands on `WorkflowEngine` as a read-only `version` property returning `self._wdef.version`, not on `WorkflowDef` (which already has `version`; the adapter has no `WorkflowDef` reference). The now-meaningless `assert ... _wdef is not None` is dropped because `_wdef` is typed `WorkflowDef`, not optional.

## Requirements
- `REQ-001`: `WorkflowEngine` passes `self._store.get_connection()` instead of `self._store._db` to `begin_stage_if_new` and `record_artifact`.
- `REQ-002`: `WorkflowEngine` exposes a read-only public `version` property, and the adapter reads the workflow version only through it.
- `REQ-003`: `_init_workflow_task` creates and fetches tasks through `StateStore.create_task` and `StateStore.get_task_by_id`; the resume error paths (`Task ... not found`, `... is halted and cannot be automatically resumed`) keep their messages.
- `REQ-004`: Tests that patch the removed adapter names are migrated to the new seam without changing what they assert.
- `REQ-005`: A unit test covers `WorkflowEngine.version`.
- `REQ-006`: Behavior is unchanged: same SQL, same task ids, same audit payloads.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/workflow_engine.py` | Stage execution | Use `get_connection()` at the two call sites; add the `version` property | REQ-001, REQ-002 / AC-1, AC-2 | `self._store._db` in `begin_stage_if_new(...)` and `record_artifact(...)` calls; `self._wdef = workflow_def` in `__init__` (checked in Step 2) | `tests/agent/workflow/test_workflow_engine.py` | Verified |
| `scripts/agent/workflow_engine_adapter.py` | Turn adapter | Replace `create_task(store._db, ...)`, `get_task_by_id(store._db, ...)`, and four `_wdef.version` reads; remove the unused `task_ops` imports and the `_wdef` assert | REQ-002, REQ-003, REQ-006 / AC-2, AC-3, AC-5 | `_init_workflow_task` and `_activate_workflow` bodies (checked in Step 2) | `tests/agent/test_orchestrator.py`, `tests/integration/test_orchestrator_integration.py` | Verified |
| `tests/agent/workflow/test_workflow_engine.py` | Engine tests | Add the `WorkflowEngine.version` test next to the existing engine construction tests | REQ-005 / AC-4 | Engine constructed as `WorkflowEngine(_make_wdef(), store)` in this file (checked in Step 2) | itself | Verified |
| `tests/agent/test_orchestrator.py` | Orchestrator and adapter tests | Migrate 15 `agent.workflow_engine_adapter.create_task` / `get_task_by_id` patch sites | REQ-004 / AC-6 | `rg "workflow_engine_adapter\.(create_task\|get_task_by_id)"` gives 15 matches (checked in Step 2) | itself | Verified |
| `tests/integration/test_orchestrator_integration.py` | Integration tests | Migrate 11 patch sites of the same names | REQ-004 / AC-6 | Same `rg` gives 11 matches (checked in Step 2) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/state_store.py` | `get_connection()`, `create_task`, `get_task_by_id` are the public seams; unchanged | REQ-001, REQ-003 |
| `scripts/agent/workflow/task_ops.py` | `create_task` and `get_task_by_id` that the store forwards to | REQ-003, REQ-006 |
| `scripts/agent/workflow/idempotency_ops.py` | `begin_stage_if_new` signature | REQ-001 |
| `scripts/agent/workflow/artifact_ops.py` | `record_artifact` signature | REQ-001 |
| `scripts/agent/orchestrator.py` | Builds the adapter and the store; existing `get_connection()` use at startup | REQ-003 |
| `scripts/agent/workflow/models.py` | `WorkflowDef.version` | REQ-002 |
| `rules/coding.md` | Conventions | all |

## Acceptance Criteria
- AC-1 (REQ-001): `rg "_store\._db" scripts/agent/workflow/workflow_engine.py` finds nothing.
- AC-2 (REQ-002): `rg "_workflow_engine\._wdef" scripts/agent` finds nothing; `WorkflowEngine.version` returns the definition's version.
- AC-3 (REQ-003): `rg "store\._db" scripts/agent/workflow_engine_adapter.py` finds nothing; the two resume `RuntimeError` messages are unchanged.
- AC-4 (REQ-005): the new property test passes.
- AC-5 (REQ-006): all pre-existing assertions in the migrated tests still pass unchanged, and `tests/agent/workflow` passes.
- AC-6 (REQ-004): no remaining patch of `agent.workflow_engine_adapter.create_task` or `get_task_by_id`.
- AC-7: `lint-imports`, ruff, mypy, and `generate_reference_table.py --check` pass.

## Tests
- `REQ-005`: `WorkflowEngine(wdef, store).version == wdef.version`.
- `REQ-004`, `REQ-006`: existing orchestrator and integration tests are the behavior lock. Migration pattern: where a test substitutes a fake task, patch `StateStore.create_task` / `get_task_by_id` on the store the adapter receives (`orch._state_store`, or `patch.object(StateStore, ...)`); where the test only restored the real function (`monkeypatch.setattr(..., create_task)` with a `TempStateStore`), delete the line because the real store method is now used.
- `REQ-003`: the existing resume-error-path tests (`not found`, `halted`) must keep passing.

## Documentation Impact
N/A: no hand-written doc describes these private accesses (`rg` over `docs/` finds `begin_stage_if_new` only by function name, unchanged). The generated reference lists classes and functions, not members, and `uv run python tools/generate_reference_table.py --check` reported no drift in Step 3; it is re-run in Phase 3.

## Assumptions
- `StateStore.create_task` and `get_task_by_id` forward all arguments unchanged to `task_ops` (read in Step 2), so behavior is identical.
- Overlap on `tests/agent/test_orchestrator.py` with `plans/20261104-115736_partialcount001_partial-completion-counter-dead.md` judged compatible: that Plan edits five `stat_partial_completions` assertions; this Plan edits the `create_task` / `get_task_by_id` patch sites; the regions are disjoint (Step 8b). Edits are sequential in one file, so the later one rebases on the earlier.
- The wfreview001 Plan changes only the third argument of `execute_turn` in `scripts/agent/orchestrator.py` and adds a new test file, so it does not collide with this Plan.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether every migrated test can keep its exact assertions after the seam change | The 26 sites were counted, not individually read | The implementation procedure reads each site; any site that cannot migrate without changing its assertion is reported as `Blocked` per `rules/workflow-lifecycle.md` | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/workflow_engine.py` | Modify | Medium: every workflow stage runs through it; importers: `workflow/__init__.py`, `orchestrator.py` | 4 | High: one author (name variants) | Runtime code under `scripts/`; copied by deploy, no schema or config change |
| `scripts/agent/workflow_engine_adapter.py` | Modify | Medium: every turn; one importer, `orchestrator.py` | 10 | High: one author | Runtime code under `scripts/`; copied by deploy, no schema or config change |
| `tests/agent/workflow/test_workflow_engine.py` | Modify | Low | N/A | N/A | None (tests are not deployed) |
| `tests/agent/test_orchestrator.py` | Modify | Medium: 15 sites in a large file | N/A | N/A | None (tests are not deployed) |
| `tests/integration/test_orchestrator_integration.py` | Modify | Medium: 11 sites | N/A | N/A | None (tests are not deployed) |

## Design
Path B (5 target files; reclassified from the Issue's 3-file framing because of the test migration). Architecture: `lint-imports` reports 6 contracts kept, 0 broken, and no new import edge is added (the adapter already imports `StateStore`; it loses its `task_ops` imports). Dependency graph: `WorkflowEngine` is imported by `agent/workflow/__init__.py` and `orchestrator.py`; `begin_stage_if_new` and `record_artifact` are called only by the engine; `WorkflowEngineAdapter` is imported only by `orchestrator.py`. Historical analysis: 30-day commits are 10 (adapter), 5 (`state_store.py`, reference only), 4 (engine); the adapter is the riskiest file to touch. Operational: no schema, config, port, or dependency change, so no process or lock inspection applies.

The change is delivered in two release groups: the engine change and the property are independent; the adapter rewiring and the test migration are one unit because the migrated tests fail until the adapter changes and the unmigrated tests fail after it. Consumer scan (`tools/scan_change_consumers.py --seed _wdef --seed get_task_by_id`): the candidates in `scripts/` are `task_ops`, the store forwarders, and the adapter; the tests are the migration targets above; `docs/` and ADR hits name `begin_stage_if_new` only (not affected: names unchanged). Testmon was stale, so the scan is text-only.

## Implementation steps
1. **Phase 1: Version accessor and engine seam**
   - [ ] Add a failing `WorkflowEngine.version` test (REQ-005; `tests/agent/workflow/test_workflow_engine.py`)
   - [ ] Add the property and switch both call sites to `get_connection()` (REQ-001, REQ-002; `scripts/agent/workflow/workflow_engine.py`)
2. **Phase 2: Adapter rewiring with test migration (one release unit)**
   - [ ] Switch the adapter to `store.create_task`, `store.get_task_by_id`, and `workflow_engine.version`; remove dead imports and the assert (REQ-002, REQ-003, REQ-006; `scripts/agent/workflow_engine_adapter.py`)
   - [ ] Migrate the patch sites (REQ-004; `tests/agent/test_orchestrator.py`, `tests/integration/test_orchestrator_integration.py`)
3. **Phase 3: Deployment & Verification**
   - [ ] Hand-off to `skills/deploy/SKILL.md`: committed and pushed first; deploying is the user's decision (approval gate). Run the Validation plan commands, `lint-imports`, and `generate_reference_table.py --check` (REQ-006; `scripts/agent/workflow_engine_adapter.py`)

### Release units
**Unit**: adapter-seam | **Phases**: 2 | **Reason**: the adapter change and the migration of the 26 patch sites cannot be validated alone; either half leaves `tests/agent/test_orchestrator.py` and `tests/integration/test_orchestrator_integration.py` failing.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/workflow/workflow_engine.py` | Unit (existing real-DB engine tests are the lock) | `uv run pytest tests/agent/workflow` | Pass |
| `scripts/agent/workflow_engine_adapter.py` | Unit and integration | `uv run pytest tests/agent/test_orchestrator.py tests/integration/test_orchestrator_integration.py` | Pass with unchanged assertions |
| both scripts | Lint, type, import contract, security, size, reference drift | `uv run ruff check`, `uv run mypy`, `lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run python tools/check_module_size.py`, `uv run python tools/generate_reference_table.py --check` | No new findings (radon, vulture, grimp, pyan3, pydeps: Not available) |
| coverage | diff-cover per `rules/toolchain.md` section 7 | command sequence in that section | At or above the threshold in `rules/toolchain.md` Completion checklist |

## Risks
- **Risk**: A migrated test silently stops exercising the adapter path (mock returns on the wrong object) → **Mitigation**: keep every assertion unchanged; review each site against the migration pattern; run the suite before and after.
- **Risk**: `mock_engine.version` on a `MagicMock` engine returns a `MagicMock` where tests expected a string → **Mitigation**: those tests patched `create_task`/audit anyway; any failure is fixed in the test by setting `version` on the mock.
- **Risk**: High-churn adapter conflicts with parallel work → **Mitigation**: the only overlap (`partialcount001`, `tests/agent/test_orchestrator.py`) edits disjoint lines (see Assumptions); commit the adapter and tests together.
- **Risk**: Dropping the `_wdef is not None` assert changes the failure of a misconfigured engine from `AssertionError` to `AttributeError` → **Mitigation**: `_wdef` is typed non-optional and the constructor always sets it; accepted.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Version accessor and engine seam | Pending | — | — | |
| 2 | Adapter rewiring with test migration | Pending | — | — | |
| 3 | Deploy hand-off and verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261103-134147_wfreview004_workflow-adapter-and-engine-private-attribute-access.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261105-085959
- **Related target files**: `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `tests/integration/test_orchestrator_integration.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes 1; engine call sites | `scripts/agent/workflow/workflow_engine.py` | Phase 1 | AC-1 | `uv run pytest tests/agent/workflow` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes 3 | `scripts/agent/workflow/workflow_engine.py` | Phase 1 | AC-2 | `WorkflowEngine.version` test | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes 3 | `scripts/agent/workflow_engine_adapter.py` | Phase 2 | AC-2 | orchestrator tests | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes 2; Testing Expectations (resume paths) | `scripts/agent/workflow_engine_adapter.py` | Phase 2 | AC-3 | resume-error-path tests | Confirmed by repository evidence |
| REQ-004 | Issue Constraints 2 (tests only when a seam makes one unrunnable), verified by the 26 patch sites | `tests/agent/test_orchestrator.py` | Phase 2 | AC-6 | orchestrator tests | Derived from confirmed evidence |
| REQ-004 | same | `tests/integration/test_orchestrator_integration.py` | Phase 2 | AC-6 | integration tests | Derived from confirmed evidence |
| REQ-005 | Issue Testing Expectations (focused unit tests for new public members) | `tests/agent/workflow/test_workflow_engine.py` | Phase 1 | AC-4 | new property test | Derived from confirmed evidence |
| REQ-006 | Issue Required Changes 4, Constraints 1 | `scripts/agent/workflow_engine_adapter.py` | Phase 2 | AC-5 | existing suites unchanged | Explicit in issue |
