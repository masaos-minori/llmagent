## Goal
- `check_workitem_traceability.py --plan-coverage` reports `companion-multi-row` only for a companion that a procedure of the checked Plan declares and that two or more rows of that Plan name, so an unrelated Plan's procedures can no longer produce the finding.

## Priority
Medium

## Scope
- **In-Scope**: restrict the `companion_candidates` set in `find_plan_coverage_findings` to implementation documents whose `Source plan` is the checked Plan; add a regression test and keep a positive test.
- **Out-of-Scope**: the `row-uncovered`, `path-covered-twice`, and `companion-not-eligible` rules; finding codes, output format, and exit codes; revisiting the startretry001 Plan workaround.
- **Dependencies**: N/A: none (no open issue or Plan targets `tools/check_workitem_traceability.py` or its test file; checked in Step 3). Later Plans that touch the same tool (`toolreport001`, `toolcommon001`) follow this one.

## Background
`find_plan_coverage_findings` skips implementation documents whose `Source plan` is another Plan in its per-document loop, but the later `companion_candidates` set is built from every implementation document passed in. Adversarial verification on 2026-11-05 confirmed this against the current source (`companion_candidates` comprehension filters only on `doc.kind == "implementation"`). The issue's Background also records a real false positive seen while generating the startretry001 procedures.

## Problem
The rule is meant to find a companion that two rows of one Plan both name, but its candidate set is repository-wide. Unrelated Plans can fail each other's coverage check, and the only workaround is editing the Plan.

## Reason for Change
`check_workitem_traceability` runs in pre-commit (`workitem-traceability` hook with `--active-only`); a defect in it forces Plan edits to satisfy the checker.

## Implementation Intent
Select the checked Plan's procedures once with one small helper and use that list for both the per-document loop and the candidate set. Keep every finding code and the rule's meaning unchanged.

## Requirements
- `REQ-001`: `companion_candidates` MUST be built only from implementation documents whose `Source plan` basename equals the checked Plan's basename (the same predicate the per-document loop uses).
- `REQ-002`: A regression test MUST show that a companion declared only by procedures of Plan A, and named in `Related Tests` of two rows of Plan B, yields no `companion-multi-row` when Plan B is checked.
- `REQ-003`: A positive test MUST show that when both rows of the same Plan name the companion and a procedure of that Plan declares it, `companion-multi-row` is still reported.
- `REQ-004`: Finding codes, output format, exit codes, and the other three rules MUST stay unchanged.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/check_workitem_traceability.py` | Scope the candidate set to the checked Plan's procedures | Replace the repository-wide `companion_candidates` comprehension with one built from the checked Plan's procedures; share the selection with the per-document loop | `REQ-001`, `REQ-004`; AC-1, AC-4 | `find_plan_coverage_findings`: loop skips by `Source plan` basename, `companion_candidates` filters only `doc.kind == "implementation"` (checked in Step 3) | `tests/tools/test_check_workitem_traceability.py` | Verified |
| `tests/tools/test_check_workitem_traceability.py` | Add regression and positive tests | Add the cross-plan regression test and the same-plan positive test using the file's existing procedure-document helper | `REQ-002`, `REQ-003`; AC-2, AC-3 | File exists with companion helpers and `extract_companion_files` tests (checked in Step 3) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Confirm it does not state the candidate scope (no `companion` mention found) | `REQ-004`; Documentation Impact |

## Acceptance Criteria
- AC-1: A companion declared only by another Plan's procedure never yields `companion-multi-row` for the checked Plan (`REQ-001`).
- AC-2: The regression test in `REQ-002` fails on the current code and passes after the change (`REQ-002`).
- AC-3: The same-plan multi-row case still reports `companion-multi-row` (`REQ-003`).
- AC-4: `uv run pytest tests/tools/test_check_workitem_traceability.py -q` passes and `--plan-coverage` on an existing Plan reports no new findings (`REQ-004`).

## Tests
- Unit: cross-plan regression (`REQ-002`), same-plan positive (`REQ-003`), existing tests unchanged (`REQ-004`).
- Manual: run `uv run python tools/check_workitem_traceability.py --plan-coverage <existing plan>` before and after the change and compare the findings (`REQ-004`).

## Documentation Impact
N/A: neither the module docstring of the changed function's scope nor `tools/TOOL_DESCRIPTIONS.md` states the candidate scope; update the `find_plan_coverage_findings` docstring in the same change only if it is inaccurate afterwards (`REQ-001`).

## Assumptions
- The `Source plan` basename comparison used by the per-document loop is the correct plan-identity predicate for the candidate set too (judgment; same predicate, so no new behavior).
- The `startretry001` Plan workaround stays as is (Issue Out of Scope).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the startretry001 Plan should regain the removed `Related Tests` entry after the fix | Owner decision; the Plan is archived | Owner decides after this fix lands; not part of this Plan | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/check_workitem_traceability.py` | Modify | Low (one function; pre-commit hook and `run_validation_gates.py` call the tool) | N/A | N/A | not applicable (rsynced) |
| `tests/tools/test_check_workitem_traceability.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Path A (2 target files, no interface or schema change). Baseline: `radon cc` grades `find_plan_coverage_findings` D (25); the change MUST NOT raise it, so the shared selection moves into a small helper rather than adding another inline condition.
- Add a helper (for example `_procedures_of_plan(plan_path, documents)`) returning implementation documents whose `Source plan` basename equals `plan_path.name`. Use it in the per-document loop and as the source of `companion_candidates`.
- Consumer scan: not applicable; no persisted schema, public API, or shared constant changes.

## Implementation steps
1. **Phase 1: Failing tests first**
   - [ ] Add the cross-plan regression test and the same-plan positive test (`REQ-002`, `REQ-003`; `tests/tools/test_check_workitem_traceability.py`)
2. **Phase 2: Scope the candidate set**
   - [ ] Add the helper and build `companion_candidates` from it; keep the per-document loop semantics (`REQ-001`, `REQ-004`; `tools/check_workitem_traceability.py`)
3. **Phase 3: Verification**
   - [ ] Run the targeted tests, the tool against an existing Plan before and after, and the tool-change checks of `routing.md` "Adding a new tool" (`REQ-004`; both files). No deploy step: only `tools/` and `tests/` change.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_workitem_traceability.py` | Unit regression and positive tests | `uv run pytest tests/tools/test_check_workitem_traceability.py -q` | All pass; regression test fails before Phase 2 |
| `tools/check_workitem_traceability.py` | Smoke on live data | `uv run python tools/check_workitem_traceability.py --plan-coverage <existing plan>` before and after | Identical findings |
| both files | Lint, format, type, security | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages tools/check_workitem_traceability.py`, `uv run bandit tools/check_workitem_traceability.py` | Clean |
| diff | Coverage | `uv run diff-cover coverage.xml --compare-branch=master` | N/A: baseline needs a diff; at least 90 percent on changed lines after Phase 2 |

## Risks
- **Risk**: The filter hides a genuine same-plan multi-row case whose procedure carries a different `Source plan` spelling → **Mitigation**: reuse the exact predicate of the per-document loop and keep the positive test.
- **Risk**: Complexity of `find_plan_coverage_findings` (grade D) grows → **Mitigation**: extract the selection into a helper and re-run `radon cc` on the file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the regression and positive tests | Pending | — | — | |
| 2 | Scope the candidate set to the checked Plan | Pending | — | — | |
| 3 | Verify with tests, live-data smoke run, and tool checks | Pending | — | — | |

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
- **Source issue**: issues/20261104-152002_tracecompanion001_scope-companion-candidates-to-target-plan.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261105-105230
- **Related target files**: tools/check_workitem_traceability.py, tests/tools/test_check_workitem_traceability.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; `find_plan_coverage_findings` (Step 3) | `tools/check_workitem_traceability.py` | 2 | AC-1 | Unit regression test | Confirmed by repository evidence |
| REQ-002 | Required Changes bullet 2 | `tests/tools/test_check_workitem_traceability.py` | 1 | AC-2 | Regression test | Explicit in issue |
| REQ-003 | Required Changes bullet 3 | `tests/tools/test_check_workitem_traceability.py` | 1 | AC-3 | Positive test | Explicit in issue |
| REQ-004 | Constraints; Acceptance Criteria 3 | `tools/check_workitem_traceability.py` | 2, 3 | AC-4 | Existing suite plus live-data smoke run | Explicit in issue |
