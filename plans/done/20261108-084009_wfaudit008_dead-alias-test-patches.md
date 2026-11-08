## Goal
Collapse the adapter's public/private alias pairs to a single method set: keep `deactivate_workflow` (its only real name — the orchestrator calls it), make the truly dead aliases private-only, and retarget the inert test patches so orchestrator tests intercept what production actually calls.

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/agent/workflow_engine_adapter.py` — delete the alias block (L106-146: section-header comment L106 containing "Backward-compatible", wrappers L108-146): `init_workflow_task`, `activate_workflow`, `handle_workflow_halt` public wrappers removed; `_init_workflow_task`, `_activate_workflow`, `_handle_workflow_halt` become the sole methods; `deactivate_workflow` public / `_deactivate_workflow` private pair collapsed to one method (keep the public name with the private twin's body, delete the twin at L336-341; the only call to `_deactivate_workflow` is inside the deleted wrapper at L137 and disappears with the collapse).
  - `tests/agent/test_orchestrator.py` — retarget the 10 public-name patch groups (24 patch sites) to the real methods (activation/task-init patches -> private names; `deactivate_workflow` patches stay live); flip the already-private group's twin patch at L2873 (`_deactivate_workflow` -> `deactivate_workflow`).
  - Docs: adapter API description in `docs/23_agent` if it lists the public alias surface. Re-verified 2026-11-08 at HEAD `ad48bfa28`: no docs list the public alias surface — no docs change (row demoted to Reference Files).
- **Out-of-Scope**:
  - Renaming the private methods to public names across the board (rejected in Design — keeps churn contained and honors the one live caller).
  - `wfaudit013` (production asserts in the same file) and `wfaudit012` (checker case-sensitivity) — separate plans; 012's checker fix will no longer have this alias block to flag once this plan lands.
- **Dependencies**: After neither strictly; but land before `wfaudit012` implementation to avoid checker churn on code that will be deleted. `wfaudit009` touches sibling test files — coordinate test edits.

## Background
The adapter exposes four "Backward-compatible alias" methods (`scripts/agent/workflow_engine_adapter.py:108-146`). Caller census at HEAD (issue `## Adversarial Validation`, corrected): `deactivate_workflow` has one live production caller (`scripts/agent/orchestrator.py:200`) — it is not dead. `init_workflow_task`, `activate_workflow`, `handle_workflow_halt` have zero callers outside the adapter's own alias block. The halt-alias "drops the return value" claim is stale: `_handle_workflow_halt` returns `None` (L343-349). `tests/agent/test_orchestrator.py` patches public names at 10 patch groups / 24 patch sites (groups L311-316, 340-345, 433-441, 530-538, 630-637, 859-868, 978-985, 1072-1079, 2753-2760, 2796-2803: 4 `init_workflow_task`, 10 `activate_workflow`, 10 `deactivate_workflow`); production turn flow calls `_init_workflow_task`/`_activate_workflow` (adapter L168-171), so `activate_workflow`/`init_workflow_task` patches intercept nothing (real methods run against the fixture database while the tests present themselves as mocking lifecycle), while `deactivate_workflow` patches do intercept the real orchestrator call. Two groups already patch private names (L1558 `_activate_workflow`; L2867-2873 `_init_workflow_task`/`_activate_workflow`/`_deactivate_workflow`) — the L2873 twin patch must flip to `deactivate_workflow` when the twin is deleted, or that test errors with AttributeError.

## Problem
A public API surface with no production users, plus a test suite whose lifecycle "mocks" are silently inert — tests pass while exercising real DB lifecycle code, hiding breakage in the very flows they claim to isolate.

## Reason for Change
Archived precedent retires dead surfaces incrementally (wfreview006 dead-method drop; compat policy `issues/done/20261020-123232_compat007...`). Inert patches are a test-integrity problem: they misrepresent coverage today, not just cleanliness.

## Implementation Intent
Collapse, don't rename broadly: delete the three dead public wrappers (their private methods become the API), collapse the deactivate pair to the single public name the production caller already uses, and retarget every test patch to the method production actually invokes so patches intercept real calls.

## Requirements
- `REQ-001`: `grep -n "Backward-compatible" scripts/agent/workflow_engine_adapter.py` returns nothing; the adapter exposes exactly one method per lifecycle action.
- `REQ-002`: `orchestrator.py:200` keeps working: `deactivate_workflow` remains callable with its current signature (it becomes the real method, private twin deleted, internal call site updated).
- `REQ-003`: No test patches a method name that production never calls: every `patch.object(orch._workflow_adapter, ...)` target matches a method invoked in the exercised flow (verified per test, not bulk-renamed).
- `REQ-004`: Retargeted tests assert the same observable behavior as before (they now mock the real call instead of an unused name).
- `REQ-005`: The deleted public names produce `AttributeError` (no shims, no deprecation wrappers) — external users, if any, fail loudly per project compat policy (manifest tracking via `wfaudit012`'s ADR/manifest context).

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Modify | Delete alias block incl. the L106 header comment (L106-146); collapse deactivate pair (keep public name with the private body, delete twin L336-341); keep private methods as sole implementation | `REQ-001`/`REQ-002` | Alias block + caller census verified (Step 2) | adapter tests | `Verified` |
| `tests/agent/test_orchestrator.py` | Modify | Retarget the 10 public-name patch groups to real call targets; keep `deactivate_workflow` patches; flip the private-group twin patch L2873 (`_deactivate_workflow` -> `deactivate_workflow`) | `REQ-003`/`REQ-004` | Patch groups verified (L311-316 etc., full map in Notes) | self | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` (`execute_turn` body L168-171,239,243) | The real private call targets tests must patch | `REQ-003` |
| `tests/agent/test_orchestrator.py` (patch context manager groups) | Determines which tests exercise which lifecycle call — retarget per test | `REQ-003` |
| `scripts/agent/orchestrator.py` (L200 call site) | Confirmed no-change: calls `deactivate_workflow`, which survives as the real method; no procedure document needed | `REQ-002` |
| `issues/done/20261020-123232_compat007_track-compatibility-exceptions-and-obsolete-symbols-in-a-manifest-with-owner-and-expiry.md` | Compat-exception tracking policy for deleted public names | `REQ-005` |
| `docs/23_agent/` (adapter API sections) | Confirmed no-change (2026-11-08 docs grep at HEAD `ad48bfa28`): no doc lists the public alias surface; only private-name mentions exist (`agent_03_03_turn-processing-flow-workflow-engine.md:124`) | `REQ-001` |

## Acceptance Criteria
- `REQ-001`: Alias block gone; adapter public lifecycle API = `deactivate_workflow` + the private trio (used internally and by tests).
- `REQ-002`: Orchestrator flow tests green without changing `orchestrator.py`.
- `REQ-003`: A CI-detectable check: for each retargeted test, the patched method is called at least once in the exercised flow — enforced by the mock's `assert_called*` now actually passing (on HEAD those asserts would fail against private names, proving interception).
- `REQ-004`: Test pass/fail semantics unchanged (no test weakened or deleted to pass).
- `REQ-005`: Full suite green; `grep -rn "init_workflow_task(\|activate_workflow(\|handle_workflow_halt(" scripts/ tests/` shows only private-underscore usages.

## Tests
- Retarget existing patch sites (not new tests): each retargeted patch must make previously-inert mocks assert real interception.
- New small adapter test: the deleted public names no longer exist (`not hasattr(adapter, "activate_workflow")` etc.) — pins REQ-005; new file `tests/agent/workflow/test_adapter_alias_surface.py`.
- Full `tests/agent/` regression.

## Documentation Impact
- Docs grep for the alias names (`init_workflow_task` etc.) across `docs/` — re-verified 2026-11-08 at HEAD `ad48bfa28`: no doc row presents the public alias surface (only a private-name mention, `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md:124` `_handle_workflow_halt`, which stays valid). No docs change; no docs checkers needed.

## Assumptions
- No external (out-of-repo) caller of the dead aliases — repository-wide grep is the census boundary; the aliases were introduced by this repo's own history.
- Tests that patched alias names while real methods ran against the fixture DB still encode valid expected behavior (validated behavior-preserving retarget, per test).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | the issue claims "some tests additionally replace real methods" — the exact set needs per-test review to avoid behavior drift when retargeting | test-by-test reading | implementation-time review pass over each patch site, recorded per-test in the procedure doc | `False` |
| `UNK-02` | whether tests patched `activate_workflow` were actually asserting real-DB effects that will now surface as failures when properly mocked | needs a HEAD experiment | run tests with private-name patches on HEAD first (they should fail where interception matters) to map real assertions before rewriting | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Modify | adapter public surface | 11 | N/A | not applicable (rsynced) |
| `tests/agent/test_orchestrator.py` | Modify | orchestrator test suite only | N/A | N/A | not applicable (rsynced) |
| docs (if alias rows exist) | Modify | docs only | N/A | N/A | not applicable |

## Design
**Collapse-to-real-name rule.** For each pair, keep the name production uses: `deactivate_workflow` survives as the real method (private twin deleted); the other three keep their private names (public wrappers deleted, no shim). This honors the one live caller (orchestrator L200); the only call to `_deactivate_workflow` (L137) sits inside the deleted wrapper and disappears with the collapse — no surviving internal call site to update.

**Test retargeting is the substance.** Patch targets move to the methods actually invoked (`_init_workflow_task`, `_activate_workflow`, `_handle_workflow_halt` — and `deactivate_workflow` stays). Where a test asserted only indirect effects, the retargeted mock must add `assert_called` so the interception is real (UNK-02 experiment maps which tests change semantics).

**Why not rename all privates to public**: broader churn for no caller demand — only `deactivate_workflow` has a user; the project's compat posture is fewer names, not symmetric naming.

## Implementation steps
1. **Phase 1: HEAD interception experiment (`UNK-02`).** Patch private names in the test file on HEAD, run, record which tests actually depend on interception. (No source changes.)
2. **Phase 2: Test retargeting (`REQ-003`, `REQ-004`).** Retarget all patch sites using Phase 1 results; suite green with real interception.
3. **Phase 3: Alias deletion (`REQ-001`, `REQ-002`, `REQ-005`).** Delete dead wrappers, collapse the deactivate pair, update internal call site; hasattr-pinning test; docs grep/updates.

### Release units
**Unit**: wfaudit008-full | **Phases**: 1, 2, 3 | **Reason**: deleting the aliases before the tests are honest would leave the inert patches pointing at nothing; the two changes ship as one retargeting package.

## Validation plan
- After each phase: `uv run pytest tests/agent/test_orchestrator.py -q`; full `uv run pytest tests/ -q` before completion.
- Phase 1 output recorded in the procedure document (per-test interception map).
- Lint/type gates per `rules/toolchain.md`; docs checkers if docs edited.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Retargeted mocks expose tests that only passed because nothing was intercepted (they now fail for real reasons) | High (expected) | Medium (test fixes needed) | Phase 1 experiment isolates this before deletion; each newly-visible failure is fixed or the test redesigned — never deleted to pass |
| `deactivate_workflow` collapse breaks an internal call site silently | Low | Low | The only internal call sits inside the deleted wrapper (L137); orchestrator L200 keeps the same public name; suite green |
| Private-group twin patch (L2873) left pointing at the deleted `_deactivate_workflow` | Low (caught at test setup) | Low | Flipped to `deactivate_workflow` in the same edit as the collapse (test-file procedure) |
| External user of a dead alias fails at runtime post-deletion | Low | Low | Loud `AttributeError` per compat policy (`REQ-005`); manifest tracking per compat007 precedent |

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: HEAD interception experiment (`UNK-02`, per-test interception map) | In Progress | — | — |  |
| 2 | Phase 2: Test retargeting (`REQ-003`, `REQ-004`) | In Progress | — | — |  |
| 3 | Phase 3: Alias deletion + hasattr-pinning test (`REQ-001`, `REQ-002`, `REQ-005`) | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261108-162804_01_scripts_agent_workflow_engine_adapter.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261108-162804_02_tests_agent_test_orchestrator.py.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203221_wfaudit008_dead-alias-test-patches.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084009
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Required Changes (delete aliases) | `scripts/agent/workflow_engine_adapter.py` | alias block gone | grep + hasattr test |
| `REQ-002` | Validation correction (deactivate has a caller) | same + orchestrator | live caller unaffected | suite |
| `REQ-003` | Issue Problem (inert patches) | `tests/agent/test_orchestrator.py` | patches intercept real calls | interception asserts |
| `REQ-004` | Plan Design (behavior preserving) | tests | no weakened/deleted tests | review |
| `REQ-005` | Issue Required Changes + compat policy | adapter | names removed loudly | hasattr test |

## Notes
- Source verified against HEAD `926dbc109`; the issue's "production uses private methods exclusively" and "halt alias drops a return value" claims were corrected during validation (issue `## Adversarial Validation` rows 2-3).
- Coordination: `wfaudit009` edits overlapping test files (`test_workflow_state_store.py`); `wfaudit012`'s checker fix lands after this plan removes the flagged alias block.
- Adversarial re-verification at HEAD `ad48bfa28` (2026-11-08):
  - Alias deletion range corrected to L106-146: the section-header comment `# ── Backward-compatible public API ──` at L106 contains the literal "Backward-compatible" that `REQ-001`'s grep acceptance check requires gone (docstring matches at L121, 128, 135, 144; last wrapper body at L146). `wfaudit012`'s plan cites the same L106-146 range.
  - Test patch census at `ad48bfa28`: 10 public-name patch groups / 24 sites — `init_workflow_task` L312, 341, 2755, 2798 (all with `return_value=` stubs that never take effect); `activate_workflow` L315, 344, 435, 532, 632, 862, 980, 1074, 2758, 2801; `deactivate_workflow` L316, 345, 439, 536, 636, 867, 984, 1078, 2759, 2802. Two groups already patch private names: L1558 (`_activate_workflow`, `test_failure_before_activate_emits_single_turn_end`) and L2869-2873 (`_init_workflow_task`/`_activate_workflow`/`_deactivate_workflow`, `test_execute_failure_returns_typed_tuple_without_adapter_status_write`); the L2873 twin patch must flip to `deactivate_workflow` when the twin is deleted. Comments at L420/L518 claim private names while patching public aliases — they become accurate after retargeting.
  - Only internal call to `_deactivate_workflow` is L137, inside the deleted wrapper; no other call site exists (`grep -n "_deactivate_workflow" scripts/agent/workflow_engine_adapter.py`: L135 docstring, L137 body, L336 def). Orchestrator L200 calls the surviving public name.
  - Docs row demoted to Reference Files (no-change confirmed): `grep -rn` for the four alias names across `docs/` returns only `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md:124` (private `_handle_workflow_halt` mention, stays valid).
  - Sibling landing order: `wfaudit006`'s procedures (`implementations/20261108-155554_01/02`) share `workflow_engine_adapter.py` in disjoint regions (flag deletion at L104, execute_turn finally L254-258, `_init_workflow_task` store-less branch L290-294) and plan a new regression test `tests/agent/workflow/test_adapter_store_ownership.py` (new) that calls the public `init_workflow_task` — after this plan lands it must call `_init_workflow_task`. Deleting L106-146 shifts all later adapter line numbers by ~41; `wfaudit006`/`wfaudit013`/`wfaudit014` anchors after L146 must be re-anchored on symbols.
- Procedure pass (2026-11-08): `scripts/agent/orchestrator.py` row demoted from Implementation Target Files to Reference Files — a no-change row needs no procedure document and `check_workitem_traceability.py --plan-coverage` reports target-table Reference rows as uncovered findings (`wfaudit006` demotion convention). Procedure documents generated: `implementations/20261108-162804_01_scripts_agent_workflow_engine_adapter.py.md` (step 3) and `implementations/20261108-162804_02_tests_agent_test_orchestrator.py.md` (steps 1-2).

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-162804 -->