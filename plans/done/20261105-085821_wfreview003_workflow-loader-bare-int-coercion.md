## Goal
- Make `WorkflowLoader` accept only strict `int` values for `timeout_sec`, `max_attempts`, and `backoff_sec`, enforce `timeout_sec >= 1`, and report every rejection as `WorkflowLoadError` naming the field, with no bare `int()` coercion left in `scripts/agent/workflow/workflow_loader.py`.

## Priority
Medium

## Scope
- **In-Scope**: a strict-int helper inside `workflow_loader.py`; the `timeout_sec` range check; removal of the post-validation `int()` calls; loader tests for each rejected value class; the loader validation rules in the engine doc.
- **Out-of-Scope**: `workflow.sqlite` schema; engine timeout and lease behavior; the `require_approval` rejection; narrowing the `except` tuple in `scripts/agent/services/workflow_schema.py`; malformed (non-object) `stages` elements.
- **Dependencies**: `N/A: none`. The Issue names wfschema001 as open; its Issue is archived (`issues/done/20261031-135607_wfschema001_schema-preflight-creates-database.md`) and its Plan `plans/20261104-103600_wfschema001_schema-preflight-creates-database.md` edits only `scripts/agent/services/workflow_schema.py` and `tests/agent/test_repl_health.py`, so the two do not share a file; this Plan keeps the preflight `except` tuple unchanged so that Plan's contract is undisturbed.

## Background
Adversarial review (2026-11-03) found bare `int()` coercions in the loader that accept `bool`, `float`, and numeric strings, no check on `timeout_sec`, and a `ValueError` that escapes as a different exception type at each of three call sites.

## Problem
Verified in Step 2 (`scripts/agent/workflow/workflow_loader.py`): `_validate` coerces `policy["max_attempts"]` and `policy["backoff_sec"]` with `int()` and checks only the lower bounds; `load()` coerces `timeout_sec`, `max_attempts`, `backoff_sec` again when building `StageDefinition` and `RetryPolicy`. `timeout_sec` has no type or range check, and `_validate` checks only that the key exists. `True`, `"30"`, and `3.9` load as `1`, `30`, `3`; `timeout_sec: 0` loads; `"abc"` raises a bare `ValueError`. Call sites: `Orchestrator.__init__` catches `(WorkflowLoadError, FileNotFoundError)` only; `check_workflow_schema` catches `(WorkflowLoadError, ValueError, TypeError, AttributeError)`; `agent/workflow/validate.py` catches `WorkflowLoadError` only, so a `ValueError` there is an uncaught traceback. Shipped values in `config/workflows/default.json` are 10, 30, 120, 3, and 1, all valid ints.

## Reason for Change
The loader is the single validation gate for `config/workflows/*.json`; coercing there contradicts `rules/coding.md` Type-coercion policy and gives three different failure behaviors for one bad value.

## Implementation Intent
Add one private helper in `workflow_loader.py` that returns the value only when `type(value) is int` and raises `WorkflowLoadError` naming the field and the value otherwise. Call it once per field in `_validate`, apply the range checks there, and return or store the validated values so `load()` no longer coerces. Scope decision for the Issue's open question: the Type-coercion policy is applied to this loader by analogy; it is worded for `*_models.py` loaders, but its stated rationale applies. `get_typed` is not reused: it raises `ValueError` (the contract this change removes) and its `isinstance(value, int)` check accepts `bool`. Lower bound decision: `timeout_sec >= 1`, no configurable minimum; shipped values are 10 to 120.

## Requirements
- `REQ-001`: `timeout_sec`, `max_attempts`, and `backoff_sec` must be strict `int` (rejecting `bool`, `float`, `str`, `None`); a rejection raises `WorkflowLoadError` naming the field and value.
- `REQ-002`: `timeout_sec >= 1` is enforced; the existing `max_attempts >= 1` and `backoff_sec >= 0` checks remain.
- `REQ-003`: No bare `int()` coercion remains in `workflow_loader.py`, and `load()` does not re-validate or coerce values `_validate` already checked.
- `REQ-004`: Loader tests cover boolean, numeric-string, fractional, and zero or negative `timeout_sec`, and the type classes on `max_attempts` and `backoff_sec`, asserting `WorkflowLoadError`; the shipped `default.json` still loads.
- `REQ-005`: The engine doc states the accepted types and ranges and the rejection behavior.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/workflow_loader.py` | Workflow definition validation | Add the strict-int helper, the `timeout_sec` range check, and drop the `int()` calls in `_validate` and `load()` | REQ-001, REQ-002, REQ-003 / AC-1, AC-2, AC-3 | `int(policy["max_attempts"])`, `int(policy["backoff_sec"])` in `_validate`; `int(s["timeout_sec"])` and two `int()` in `load()` (checked in Step 2) | `tests/agent/workflow/test_workflow_loader.py` | Verified |
| `tests/agent/workflow/test_workflow_loader.py` | Loader tests | Add parametrized rejection cases; existing cases cover missing keys, duplicate ids, `retry_on` and `backoff_sec < 0` but no type or `timeout_sec` case | REQ-004 / AC-4 | `rg "def test_"` of the file lists no timeout or type case (checked in Step 2) | itself | Verified |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Engine doc | "Workflow Loader Validation Rules" lists `max_attempts >= 1` and `backoff_sec >= 0` but not types or the `timeout_sec` range | REQ-005 / AC-5 | The section's bullets, checked in Step 2 | `tools/check_docs_consistency.py --domain agent` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/config_utils.py` | `get_typed` raises `ValueError` and accepts `bool`, so it is not reused | REQ-001 |
| `scripts/agent/services/workflow_schema.py` | Preflight catches `WorkflowLoadError`; unchanged | REQ-001 |
| `scripts/agent/workflow/validate.py` | CLI catches `WorkflowLoadError` only; unchanged | REQ-001 |
| `scripts/agent/orchestrator.py` | `__init__` wraps `WorkflowLoadError` into `RuntimeError`; unchanged | REQ-001 |
| `config/workflows/default.json` | Shipped values must still load | REQ-004 |
| `rules/coding.md` | Type-coercion policy | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001): `"timeout_sec": "120"`, `true`, `2.5`, and `"max_attempts": 2.5` each fail `WorkflowLoader.load()` with `WorkflowLoadError` whose message names the field.
- AC-2 (REQ-002): `"timeout_sec": 0` and a negative value fail with `WorkflowLoadError`.
- AC-3 (REQ-003): `rg "int\(" scripts/agent/workflow/workflow_loader.py` finds no coercion call.
- AC-4 (REQ-004): the new tests fail before the change and pass after; `test_default_json_has_no_retry_stage` and the shipped-default tests still pass.
- AC-5 (REQ-005): the engine doc lists strict `int`, `timeout_sec >= 1`, `max_attempts >= 1`, `backoff_sec >= 0`, and `WorkflowLoadError` with the field name; docs checkers pass.
- AC-6: `uv run pytest tests/agent/workflow`, ruff, and mypy pass.

## Tests
- `REQ-001`, `REQ-004`: parametrized over `timeout_sec`, `max_attempts`, `backoff_sec` and the values `True`, `"5"`, `2.5`, `None`; assert `WorkflowLoadError` and the field name in the message.
- `REQ-002`, `REQ-004`: `timeout_sec` in `0`, `-1`; assert `WorkflowLoadError`.
- `REQ-004`: shipped `config/workflows/default.json` loads with values unchanged.

## Documentation Impact
Update the loader validation rules in the agent workflow-engine doc (target row above; found via `docs/00_index.md` "Document References by Task"); drives REQ-005.

## Assumptions
- The error text of the new rejections is not a persisted or asserted contract outside the new tests (existing tests assert only `WorkflowLoadError`).
- Narrowing the `check_workflow_schema` `except` tuple is not done here: `AttributeError` is still reachable from a non-object `stages` element, and that file belongs to the wfschema001 Plan.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | A non-object element in `stages` raises `AttributeError` from `s.get` in `_validate` | Outside this Issue's numeric-field scope | File a separate Issue if the owner wants it; not handled here | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/workflow_loader.py` | Modify | Medium: used by startup preflight, orchestrator init, and the validate CLI | N/A | N/A | Runtime code under `scripts/`; copied by deploy; deployed `config/workflows/*.json` must be valid (shipped file is) |
| `tests/agent/workflow/test_workflow_loader.py` | Modify | Low | N/A | N/A | None (tests are not deployed) |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Modify | Low | N/A | N/A | None (docs are not deployed) |

## Design
Path A (3 files, no schema or public signature change; the exception type for malformed numbers changes from `ValueError` to `WorkflowLoadError`, which every call site already handles). `type(value) is int` is used instead of `isinstance` so `bool` is rejected. Validated values are carried from `_validate` to `load()` (for example by `_validate` returning them) so the same value is never validated twice. `_StageJson` and `_RetryPolicyJson` stay as they are; their `int` annotations already match the new checks. Consumer scan not required: no persisted schema or shared constant changes.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] Add the rejection tests and confirm they fail on current code (REQ-004; `tests/agent/workflow/test_workflow_loader.py`)
2. **Phase 2: Strict validation**
   - [ ] Add the helper, the range check, and remove the `int()` calls (REQ-001, REQ-002, REQ-003; `scripts/agent/workflow/workflow_loader.py`)
3. **Phase 3: Documentation**
   - [ ] Update "Workflow Loader Validation Rules" (REQ-005; `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`)
4. **Phase 4: Deployment & Verification**
   - [ ] Hand-off to `skills/deploy/SKILL.md`: committed and pushed first; deploying is the user's decision (approval gate). Run `python -m agent.workflow.validate config/workflows/default.json` (REQ-004; `scripts/agent/workflow/workflow_loader.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/workflow/test_workflow_loader.py` | Unit | `uv run pytest tests/agent/workflow tests/agent/test_repl_health.py` | New cases fail before Phase 2, all pass after |
| `scripts/agent/workflow/workflow_loader.py` | Lint, type, security, size | `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run python tools/check_module_size.py` | No new findings (radon, vulture: Not available) |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Docs checkers | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent` | Pass |

## Risks
- **Risk**: A deployed workflow file written with float or string numbers stops loading at startup → **Mitigation**: shipped `default.json` verified valid in Step 2; the Phase 4 validate CLI run covers the deployed file before restart.
- **Risk**: `timeout_sec >= 1` is too strict or too loose for a future stage → **Mitigation**: recorded as a design decision; a configurable minimum is a separate change.
- **Risk**: A test elsewhere relies on `ValueError` from the loader → **Mitigation**: `rg "ValueError" tests/agent/workflow tests/agent/test_repl_health.py` in Phase 1 before editing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add failing rejection tests | In Progress | — | — |  |
| 2 | Strict validation in the loader | In Progress | — | — |  |
| 3 | Update loader validation rules doc | In Progress | — | — |  |
| 4 | Deploy hand-off and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-092603_01_scripts_agent_workflow_workflow_loader.py.md | 1, 2 | Procedure | Pending | — | — |
| implementations/20261105-092603_03_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261103-134147_wfreview003_workflow-loader-bare-int-coercion.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261105-085821
- **Related target files**: `scripts/agent/workflow/workflow_loader.py`, `tests/agent/workflow/test_workflow_loader.py`, `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes 1-2; `_validate`, `load()` | `scripts/agent/workflow/workflow_loader.py` | Phase 2 | AC-1 | parametrized rejection tests | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes 3 | `scripts/agent/workflow/workflow_loader.py` | Phase 2 | AC-2 | `timeout_sec` 0 and -1 tests | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes 4, Acceptance Criteria 2 | `scripts/agent/workflow/workflow_loader.py` | Phase 2 | AC-3 | `rg "int\("` check | Explicit in issue |
| REQ-004 | Issue Required Changes 5, Testing Expectations | `tests/agent/workflow/test_workflow_loader.py` | Phase 1 | AC-4 | pytest command in Validation plan | Explicit in issue |
| REQ-005 | Issue Documentation Impact | `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Phase 3 | AC-5 | docs checkers | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261105-092603 -->