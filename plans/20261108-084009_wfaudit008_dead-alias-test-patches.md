## Goal
Collapse the adapter's public/private alias pairs to a single method set: keep `deactivate_workflow` (its only real name — the orchestrator calls it), make the truly dead aliases private-only, and retarget the inert test patches so orchestrator tests intercept what production actually calls.

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/agent/workflow_engine_adapter.py` — delete the alias block (L108-146): `init_workflow_task`, `activate_workflow`, `handle_workflow_halt` public wrappers removed; `_init_workflow_task`, `_activate_workflow`, `_handle_workflow_halt` become the sole methods; `deactivate_workflow` public / `_deactivate_workflow` private pair collapsed to one method (keep the public name, delete the private twin, update the internal call site L137->direct).
  - `tests/agent/test_orchestrator.py` — retarget ~10 patch sites from alias names to the real methods (activation/task-init patches -> private names; `deactivate_workflow` patches stay live).
  - Docs: adapter API description in `docs/23_agent` if it lists the public alias surface.
- **Out-of-Scope**:
  - Renaming the private methods to public names across the board (rejected in Design — keeps churn contained and honors the one live caller).
  - `wfaudit013` (production asserts in the same file) and `wfaudit012` (checker case-sensitivity) — separate plans; 012's checker fix will no longer have this alias block to flag once this plan lands.
- **Dependencies**: After neither strictly; but land before `wfaudit012` implementation to avoid checker churn on code that will be deleted. `wfaudit009` touches sibling test files — coordinate test edits.

## Background
The adapter exposes four "Backward-compatible alias" methods (`scripts/agent/workflow_engine_adapter.py:108-146`). Caller census at HEAD (issue `## Adversarial Validation`, corrected): `deactivate_workflow` has one live production caller (`scripts/agent/orchestrator.py:200`) — it is not dead. `init_workflow_task`, `activate_workflow`, `handle_workflow_halt` have zero callers outside the adapter's own alias block. The halt-alias "drops the return value" claim is stale: `_handle_workflow_halt` returns `None` (L343-349). `tests/agent/test_orchestrator.py` patches public names at ~10 sites (L315-316, 344-345, 2758-2759, 2801-2802, ...); production turn flow calls `_init_workflow_task`/`_activate_workflow` (adapter L168-171), so `activate_workflow`/`init_workflow_task` patches intercept nothing (real methods run against the fixture database while the tests present themselves as mocking lifecycle), while `deactivate_workflow` patches do intercept the real orchestrator call.

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
**Freeze status**: Draft

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Modify | Delete alias block (L108-146); collapse deactivate pair; keep private methods as sole implementation | `REQ-001`/`REQ-002` | Alias block + caller census verified (Step 2) | adapter tests | `Verified` |
| `tests/agent/test_orchestrator.py` | Modify | Retarget ~10 patch sites to real call targets; keep `deactivate_workflow` patches | `REQ-003`/`REQ-004` | Patch sites verified (L315-316 etc.) | self | `Verified` |
| `scripts/agent/orchestrator.py` | Reference | Confirmed no-change: calls `deactivate_workflow` (L200), which survives as the real method | `REQ-002` | Caller verified | existing | `Verified` |
| `docs/23_agent/` (adapter API sections) | Modify (if alias surface documented) | Remove/replace alias API description | `REQ-001` | To be confirmed at implementation (docs grep) | docs checkers | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` (`execute_turn` body L168-171,239,243) | The real private call targets tests must patch | `REQ-003` |
| `tests/agent/test_orchestrator.py` (patch context manager groups) | Determines which tests exercise which lifecycle call — retarget per test | `REQ-003` |
| `issues/done/20261020-123232_compat007_track-compatibility-exceptions-and-obsolete-symbols-in-a-manifest-with-owner-and-expiry.md` | Compat-exception tracking policy for deleted public names | `REQ-005` |

## Acceptance Criteria
- `REQ-001`: Alias block gone; adapter public lifecycle API = `deactivate_workflow` + the private trio (used internally and by tests).
- `REQ-002`: Orchestrator flow tests green without changing `orchestrator.py`.
- `REQ-003`: A CI-detectable check: for each retargeted test, the patched method is called at least once in the exercised flow — enforced by the mock's `assert_called*` now actually passing (on HEAD those asserts would fail against private names, proving interception).
- `REQ-004`: Test pass/fail semantics unchanged (no test weakened or deleted to pass).
- `REQ-005`: Full suite green; `grep -rn "init_workflow_task(\|activate_workflow(\|handle_workflow_halt(" scripts/ tests/` shows only private-underscore usages.

## Tests
- Retarget existing patch sites (not new tests): each retargeted patch must make previously-inert mocks assert real interception.
- New small adapter test: the deleted public names no longer exist (`not hasattr(adapter, "activate_workflow")` etc.) — pins REQ-005.
- Full `tests/agent/` regression.

## Documentation Impact
- Docs grep for the alias names (`init_workflow_task` etc.) in `docs/23_agent` and `docs/23_agent` turn-flow descriptions; update any row that presents them as the API.
- Run docs checkers for domain agent if edited.

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
**Collapse-to-real-name rule.** For each pair, keep the name production uses: `deactivate_workflow` survives as the real method (private twin deleted); the other three keep their private names (public wrappers deleted, no shim). This honors the one live caller (orchestrator L200) and keeps internal call-site churn to one line (L137).

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
| `deactivate_workflow` collapse breaks an internal call site silently | Low | Low | Single internal call site (L137) updated in the same edit; suite green |
| External user of a dead alias fails at runtime post-deletion | Low | Low | Loud `AttributeError` per compat policy (`REQ-005`); manifest tracking per compat007 precedent |

## Execution Status
### Execution Status
| Work Item | Status | Owner | Started | Completed | Notes |
|---|---|---|---|---|---|
| Phase 1: interception experiment | Planned | engineer | | | |
| Phase 2: test retargeting | Planned | engineer | | | |
| Phase 3: alias deletion | Planned | engineer | | | |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Work Item | Type | Link | Created |
|---|---|---|---|

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
