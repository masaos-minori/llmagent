## Goal
Close the two workflow-loader validation gaps: verify that `stages` elements and `retry_policy` are dicts before any subscript, and validate `retryable` as a strict bool — so every malformed definition fails as `WorkflowLoadError` at load time instead of leaking a raw `AttributeError`/`TypeError`.

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/agent/workflow/workflow_loader.py` — add `_require_dict` (stages container + elements, retry_policy) and a strict-bool check for `retryable`, mirroring the existing `_require_int` pattern; fix `retryable` coercion (`bool(...)` -> strict bool).
  - Tests: parametrized malformed-shape cases in `tests/agent/workflow/test_workflow_loader.py`.
  - Docs: workflow-definition validation contract (domain agent) updated: the loader contract section exists (`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, "### Workflow Loader Validation Rules", verified at HEAD `ad48bfa28`).
- **Out-of-Scope**:
  - The startup preflight's broad `except (WorkflowLoadError, ValueError, TypeError, AttributeError)` (`scripts/agent/services/workflow_schema.py:38`) — after this fix it stays as defense in depth; removing the extra exception types is a follow-up cleanup recorded in `UNK-01`.
  - Schema validation beyond shape/type (semantic rules like unknown stage fields) — unchanged.
- **Dependencies**: None blocking. Independent of the recovery/status cluster.

## Background
Live repro re-verified at HEAD `ad48bfa28` (issue `## Adversarial Validation`): `stages: ["plan"]` raises raw `AttributeError: 'str' object has no attribute 'get'` from `stage_ids = [s.get("id") for s in stages_data]` (`scripts/agent/workflow/workflow_loader.py:108`); `retry_policy: "default"` raises raw `AttributeError: 'str' object has no attribute 'keys'` at L127; `retryable: "false"` loads successfully as `retryable=True` via `bool(s["retryable"])` (L165); `retryable: 0` / `retryable: null` load silently as `False`. A non-list `stages` container (`stages: {"id": ...}`) already raises `WorkflowLoadError` via the existing list check at L106-107 — the unfixed gaps are the per-element dict check, the `retry_policy` container check, and strict `retryable`. `_validate` performs `.keys()` set-difference checks that assume dict-ness (L122, L127); `_require_int` (L84-97) is the existing strict-validation pattern, already test-pinned (tests L236,254). The startup preflight swallows the raw errors as a generic "invalid definition" message (`workflow_schema.py:38`), while the orchestrator's own catch (`orchestrator.py:130`) covers only `(WorkflowLoadError, FileNotFoundError)` and would propagate raw errors at construction.

## Problem
Malformed workflow definitions crash with the wrong error type: the loader's own error contract (`WorkflowLoadError`) is bypassed, the two entry points handle the failure inconsistently, and a config typo like `"retryable": "false"` silently enables retries the operator meant to disable.

## Reason for Change
The loader already declares typed-error behavior and has the exact validation helper pattern (`_require_int`); extending it is convention-consistent and makes both entry points (preflight and orchestrator) behave identically without touching either.

## Implementation Intent
Type-gate every container the loader subscripts: `stages` must be a list of dicts, `retry_policy` must be a dict, each checked before `.get`/`.keys` use; `retryable` must be a JSON bool (`type(...) is bool`, same bool-rejecting strictness as `_require_int`). Every new failure raises `WorkflowLoadError` naming the field.

## Requirements
- `REQ-001`: A non-list `stages`, or any non-dict stage element, raises `WorkflowLoadError` naming the offending index/field.
- `REQ-002`: A non-dict `retry_policy` raises `WorkflowLoadError`.
- `REQ-003`: `retryable` values that are not JSON booleans raise `WorkflowLoadError`; `"false"`, `"true"`, `0`, `1`, `null` are all rejected; real booleans load unchanged.
- `REQ-004`: No raw `AttributeError`/`TypeError`/`KeyError` can escape `WorkflowLoader.load` for shape errors (the loader wraps subscript paths behind the dict checks).
- `REQ-005`: New parametrized tests pin `REQ-001`-`REQ-003`; both entry points (preflight and orchestrator construction) now receive only `WorkflowLoadError` for these cases.

## Implementation Target Files
**Freeze status**: Frozen
Amended 2026-11-08 (scope): added docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md — State the strict shape/bool loader contract in the Workflow Loader Validation Rules section (L148-158)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/workflow_loader.py` | Modify | Add `_require_dict` helper; check `stages` container/elements (L108, L127 paths) and `retry_policy`; strict-bool `retryable` (L165) | `REQ-001`-`REQ-004` | Live repro of raw `AttributeError` and `retryable="false"->True` re-verified at HEAD `ad48bfa28` | `tests/agent/workflow/test_workflow_loader.py` | `Verified` |
| `tests/agent/workflow/test_workflow_loader.py` | Modify | Parametrized malformed-shape cases: string stage, int stage, string retry_policy, non-bool retryable values | `REQ-005` | Current fixtures use only valid shapes (grep) | self | `Verified` |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Modify | State the strict shape/bool loader contract in the Workflow Loader Validation Rules section (L148-158) | REQ-005 / N/A: none cites REQ-005 | Section verified at L148-158 HEAD ad48bfa28; bullets omit stage-element/retry_policy object rules and strict retryable bool | docs checkers | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/workflow_loader.py` (`_require_int`, `_validate_retry_on`) | The strict-validation patterns to mirror (L84-97, L64-81) | `REQ-003` |
| `scripts/agent/services/workflow_schema.py` | Confirmed no-change (verified at HEAD `ad48bfa28`): preflight catch (L38) stays as defense in depth | `UNK-01` context |
| `scripts/agent/orchestrator.py` | Construction-time catch (L130) that only handles `WorkflowLoadError`/`FileNotFoundError` — the consistency target | `REQ-005` |
| `config/workflows/default.json` | The shipped definition must keep loading unchanged | Regression |

## Acceptance Criteria
- `REQ-001`: `load` on `stages: ["plan"]` raises `WorkflowLoadError` (message names stages[0]); `stages: {"id": ...}` raises `WorkflowLoadError` (already satisfied at HEAD by the L106-107 list check — pinned as a regression case).
- `REQ-002`: `retry_policy: "default"` raises `WorkflowLoadError`.
- `REQ-003`: `retryable: "false"` raises `WorkflowLoadError`; a valid definition loads with `retryable is False` exactly as written.
- `REQ-004`: Loader test walks the repro set from the issue's validation section — every case ends in `WorkflowLoadError`, none in a raw exception.
- `REQ-005`: New element/`retry_policy`-container/`retryable` tests fail on HEAD (raw `AttributeError` / silent acceptance); already-handled container shapes stay green as regression pins; shipped `default.json` still loads.

## Tests
- Parametrized shape-rejection tests in `tests/agent/workflow/test_workflow_loader.py` (string/int stage elements, non-dict retry_policy, non-bool retryable variants).
- Entry-point test through `check_workflow_definition` (`scripts/agent/services/workflow_schema.py:22`) asserting a single `RuntimeError`-wrapping behavior for the loader case. `validate_path` exists in `scripts/agent/workflow/validate.py:22` (the deploy-time CLI entry point; its happy path is already pinned by `test_preflight_validate_path_loads_shipped_retry_on` at L341) and needs no new test beyond the loader contract itself.
- Regression: shipped definition loads identically.

## Documentation Impact
- The loader contract section exists: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, "### Workflow Loader Validation Rules" (L148-158 at HEAD `ad48bfa28`). State the strict shape/bool contract there.
- Run docs checkers for domain agent for the doc edit.

## Assumptions
- JSON-sourced definitions cannot produce non-bool `retryable` except via string/number typos — the strict-bool rule accepts exactly what valid JSON definitions contain (validated: all test fixtures use JSON booleans).
- `WorkflowLoadError` remains the loader's only public error type.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | whether to later narrow the preflight catch to `(WorkflowLoadError, FileNotFoundError)` now that the loader no longer leaks raw errors | cleanup scope decision | follow-up cleanup after this plan lands | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/workflow_loader.py` | Modify | workflow definition loading (startup) | 5 | N/A | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_loader.py` | Modify | tests only | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Modify | Not assessed (amendment 2026-11-08) | N/A | N/A | Not assessed (amendment 2026-11-08) |

## Design
**Extend, don't restructure.** `_require_dict(value, label)` sits next to `_require_int` and raises the same error style ("`<label>` must be a dict"). Call order inside `load`: container checks (stages list, per-element dict, retry_policy dict) run before any existing `.get`/`.keys` usage, so the current validation body becomes unreachable for malformed input rather than crashing mid-way. `retryable` validation reuses the `type(value) is not bool` strictness (rejects bool-vs-int subtleties in both directions).

**Why not catch-and-convert at the entry points:** converting `AttributeError` to `WorkflowLoadError` in preflight (the current de-facto behavior via the broad catch) hides which field was wrong; fixing at the loader gives field-named messages and makes the two entry points consistent by construction.

## Implementation steps
1. **Phase 1: Loader validation (`REQ-001`-`REQ-004`).** Add helpers and checks; extend the loader test file.
2. **Phase 2: Entry-point consistency + docs (`REQ-005`).** Entry-point test; docs update of the "Workflow Loader Validation Rules" contract section (the section exists).
   - [ ] Modify (REQ-005; `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`) — amendment 2026-11-08

### Release units
**Unit**: wfaudit004-full | **Phases**: 1, 2 | **Reason**: one loader contract change with its tests.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_loader.py tests/agent/services/ -q` after each phase; full `uv run pytest tests/ -q` before completion.
- New tests fail on HEAD exactly as the issue's live repro behaved (`AttributeError` / silent `True`).
- Confirm shipped `config/workflows/default.json` loads with identical `WorkflowDef` values before/after.
- Lint/type gates per `rules/toolchain.md`; docs checkers only if docs edited.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A currently-loading odd definition (e.g. string `"true"` retryable in some deployed config) starts failing at startup | Low | Medium (refused startup with a clear message) | Probe deployed `config/workflows/*.json` values during validation; the error message names the field |
| Check ordering changes an existing accepted-but-unusual definition's error message | Low | Low | Existing parametrized tests (L236,254) stay green — they pin the messages that must not change |

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Loader validation (loader helpers + loader test file extension) | Completed | 20261108-151141 | 20261109-005543 | procedures 151141_01-02 generated 2026-11-08 |
| 2 | Phase 2: Entry-point consistency + docs (entry-point test; docs contract section update) | Completed | 20261108-151141 | 20261109-005513 | procedure 151141_03 generated 2026-11-08 |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Work Item | Type | Link | Created |
|---|---|---|---|
| `151141_01` | implementation-procedure | `implementations/20261108-151141_01_scripts_agent_workflow_workflow_loader.py.md` | 2026-11-08 |
| `151141_02` | implementation-procedure | `implementations/20261108-151141_02_tests_agent_workflow_test_workflow_loader.py.md` | 2026-11-08 |
| `151141_03` | implementation-procedure | `implementations/20261108-151141_03_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md` | 2026-11-08 |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203217_wfaudit004_loader-validation-gaps.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084007
- **Related target files**: see Implementation Target Files table, docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Problem + live repro | `scripts/agent/workflow/workflow_loader.py` | stages shape -> WorkflowLoadError | parametrized tests |
| `REQ-002` | Issue Problem + live repro | same | retry_policy dict check | parametrized tests |
| `REQ-003` | Issue Problem (bool coercion) | same | strict bool retryable | parametrized tests |
| `REQ-004` | Issue Problem (error-type escape) | same | no raw exceptions for shape errors | repro-set test |
| `REQ-005` | Issue Testing Expectations | tests | fail on HEAD | pytest |
| REQ-005 | Amendment 2026-11-08: State the strict shape/bool loader contract in the Workflow Loader Validation Rules section (L148-158) | docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md | Phase 2 | N/A: none cites REQ-005 | docs checkers | Confirmed by repository evidence |

## Notes
- Source verified against HEAD `926dbc109`; the issue's `"id" in s` mechanism description was corrected during validation (current code uses `.keys()` difference; the escape is real but crashes at the `s.get` list comprehension, per the issue's `## Adversarial Validation`).
- 20261108 re-verification at HEAD `ad48bfa28` (line citations corrected; loader file unchanged since `926dbc109` — the cited numbers were stale): `stage_ids` comprehension crash L103 -> L108; `retry_policy` `.keys()` crash L118 -> L127; `bool(s["retryable"])` L158 -> L165; `_require_int` L84-95 -> L84-97; `_validate_retry_on` L63-81 -> L64-81. Live repro at `ad48bfa28` reproduced all escape behaviors (`"false"->True`, `0`/`null`->silent `False`).
- 20261108 correction: `validate_path` exists (`scripts/agent/workflow/validate.py:22`, the deploy-time CLI `python -m agent.workflow.validate`); the earlier "no-longer-existent" claim was wrong. The startup preflight entry point is `check_workflow_definition` (`scripts/agent/services/workflow_schema.py:22`).
- 20261108 discovery: a non-list `stages` container already raises `WorkflowLoadError` (`workflow_loader.py:106-107`); `stages: {"id": ...}` is a regression pin, not a new fix.
- 20261108 inventory edits: `scripts/agent/services/workflow_schema.py` moved from Implementation Target Files to Reference Files (verify-only row, catch confirmed unchanged at L38); `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` appended as a target row via `tools/amend_plan.py` (class `scope`) because the plan's Documentation Impact condition ("if a loader contract section exists") resolved to true — the "### Workflow Loader Validation Rules" section exists at L148-158.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-151141 -->