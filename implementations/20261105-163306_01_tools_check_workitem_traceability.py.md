## Goal
- Make `find_plan_coverage_findings` report `companion-multi-row` only for a companion that a procedure of the checked Plan declares, and pin it with a cross-plan regression test written and seen failing before the fix (`REQ-001`: candidate set limited to the checked Plan's procedures; `REQ-002`: cross-plan regression test; `REQ-003`: same-plan positive case still reported; `REQ-004`: finding codes, output, and exit codes unchanged).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `companion_candidates` set in `find_plan_coverage_findings` of `tools/check_workitem_traceability.py`, and one new test in its companion test file. The existing same-plan positive test is kept unchanged.
- Plan: `plans/done/20261105-105230_tracecompanion001_scope-companion-candidates-to-target-plan.md` (archived under `plans/done/`; the original draft path `plans/...` is stale), Plan steps 1 and 2 (Phases 1 and 2).

## Adversarial Verification (20261106)

**Result: the structural claims are accurate; one path reference was stale and is now
corrected.** Verified by reading `tools/check_workitem_traceability.py` directly.

- Per-document loop skip (doc says lines 735-739): confirmed. Lines 734-739 skip
  non-`implementation` docs and docs whose `Source plan` basename differs from
  `plan_path.name`.
- `companion_candidates` (doc says lines 783-788): confirmed. Lines 783-788 build the set
  filtering only on `doc.kind == "implementation"` (iterating `extract_companion_files`),
  i.e. it does NOT yet scope to the checked Plan — the cross-plan pollution this fix targets.
- Grade (doc says `D (25)` by `radon cc`): confirmed exactly —
  `F 714:0 find_plan_coverage_findings - D (25)`.
- Same-plan positive case (doc says
  `TestPlanCoverage.test_companion_named_in_two_rows_is_multi_row` at
  `tests/tools/test_check_workitem_traceability.py:590`): confirmed present at line 590.
- Callers (doc says the `workitem-traceability` pre-commit hook with `--active-only` and the
  `check_workitem_traceability` gate in `tools/run_validation_gates.py` are unaffected):
  confirmed — `.pre-commit-config.yaml:116` runs
  `python -m tools.check_workitem_traceability --active-only` (flag defined at
  `tools/check_workitem_traceability.py:883/934`); gate registered at
  `tools/run_validation_gates.py:1238`. Finding codes/output/exit codes are unchanged by the
  proposed scope narrowing.

Correction only: the Plan path was cited as `plans/...` in two places; the file actually
lives at `plans/done/20261105-105230_tracecompanion001_scope-companion-candidates-to-target-plan.md`
(the same archived-path pattern seen in cycle 02). Both references updated. Implementation
steps left `Pending`; nothing was executed.

## Assumptions
- Verified 2026-11-05: the per-document loop skips documents whose `Source plan` basename differs from the checked Plan's basename (lines 735-739), while `companion_candidates` (lines 783-788) filters only on `doc.kind == "implementation"`; `find_plan_coverage_findings` is graded D (25) by `radon cc`, so the shared selection moves into a small helper instead of another inline condition.
- The same-plan positive case (`REQ-003`) is already tested by `TestPlanCoverage.test_companion_named_in_two_rows_is_multi_row` (`tests/tools/test_check_workitem_traceability.py:590`); it stays and no second positive test is added.
- The test row is eligible as a companion (a row of the Plan under `tests/`, named in `Related Tests` of exactly this one other row, no design decision of its own), so this single document covers both rows and keeps the red-then-green order inside one cycle.
- Callers of the tool (the `workitem-traceability` pre-commit hook with `--active-only`, and the `check_workitem_traceability` gate in `tools/run_validation_gates.py`) are unaffected: finding codes, output, and exit codes do not change.
- Plan overlap: `tools/check_workitem_traceability.py` is also targeted by the `toolcommon001` and `toolreport001` Plans, which are sequenced after this Plan (a sequencing dependency, not a conflict; `toolcommon001` records a `Depends on` line for it).

## Design decisions
- A helper `_procedures_of_plan` (new) takes the Plan path and the documents and returns the implementation documents whose `Source plan` basename equals the Plan's basename; the per-document loop and the candidate set both iterate over its result.
- The helper's predicate is the exact one the loop uses today (`doc.kind == "implementation"`, `Source plan` present, `Path(source_plan).name == plan_path.name`), so no new behavior is introduced.

## Alternatives considered
- Adding the Plan-basename condition inline to the `companion_candidates` comprehension: rejected, it duplicates the predicate and raises the complexity of a grade D function.

## Implementation
### Target file
`tools/check_workitem_traceability.py`

### Procedure
1. Companion test first: add the cross-plan regression test (below) and run it against the current code; confirm it fails.
2. Add `_procedures_of_plan` (new) next to `find_plan_coverage_findings`.
3. In `find_plan_coverage_findings`, replace the loop's inline skip conditions with iteration over `_procedures_of_plan(plan_path, documents)`, and build `companion_candidates` from the same list.
4. Re-run the new test and the file's existing tests; confirm they pass.

### Method
- The loop body (target and companion extraction, `companion-not-eligible`, `row-uncovered`, `path-covered-twice`) is unchanged; only its iterable and the candidate source change.
- Update the function docstring only if a sentence became inaccurate.

### Details
- Run `uv run radon cc tools/check_workitem_traceability.py -s` before and after and confirm `find_plan_coverage_findings` is not worse than D (25).
- Before and after the change, run `uv run python tools/check_workitem_traceability.py --plan-coverage <an existing plan under plans/done/>` and compare the findings; they must be identical.

### Companion test files
- `tests/tools/test_check_workitem_traceability.py`
  - Procedure: in `TestPlanCoverage`, add one test (`test_companion_declared_by_another_plan_is_not_multi_row` (new)) that rewrites the Plan with two rows naming the same test file in `Related Tests` (as in the existing multi-row test), writes a procedure declaring that companion with `plan="20261101-999999_other.md"`, and asserts `companion-multi-row` is not among the categories of the findings.
  - Validation: the new test fails before the change and passes after; the existing `test_companion_named_in_two_rows_is_multi_row` and the rest of the file pass unchanged.

## Compatibility considerations
- Finding codes, messages, output format, and exit codes are unchanged; a Plan that today gets a false `companion-multi-row` from another Plan's procedures stops getting it.

## Security considerations
N/A: the tool reads work item documents only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_workitem_traceability.py -q` passes; the new test failed before the change.
- The before-and-after `--plan-coverage` runs on an existing Plan give identical findings.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy tools/check_workitem_traceability.py`, `uv run bandit tools/check_workitem_traceability.py` are clean; `radon` grade of the function is not worse.
- diff-cover is N/A: `tools/` is outside `[tool.coverage.run] source = ["scripts"]`.

## Completion criteria
- A companion declared only by another Plan's procedure never yields `companion-multi-row` for the checked Plan, the same-plan case still does, and the checks above pass.

## Out of Scope
- The `row-uncovered`, `path-covered-twice`, and `companion-not-eligible` rules, finding codes and output, and the startretry001 Plan workaround.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the cross-plan regression test (companion) and confirm it fails | Completed | 20261106-112315 | 20261106-112401 | Changed: tests/tools/test_check_workitem_traceability.py (new cross-plan test, failed before the change) |
| 2 | Add the helper and scope the candidate set | Completed | 20261106-112401 | 20261106-112401 | Changed: tools/check_workitem_traceability.py (_procedures_of_plan, candidate set scoped to the Plan) |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the before-and-after `--plan-coverage` comparison | Completed | 20261106-112401 | 20261106-112401 | ruff, mypy, bandit clean; 88 tests pass; radon D(25)->D(21); --plan-coverage output identical on two archived plans; diff-cover N/A (tools/ outside coverage source) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (candidate set scoped to the Plan), `REQ-002` (cross-plan regression test), `REQ-003` (same-plan positive case kept), `REQ-004` (codes, output, and exit codes unchanged)
- **Source issue**: issues/20261104-152002_tracecompanion001_scope-companion-candidates-to-target-plan.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261105-105230_tracecompanion001_scope-companion-candidates-to-target-plan.md (archived under `plans/done/`)
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-163306
- **Related target files**: `tools/check_workitem_traceability.py`, `tests/tools/test_check_workitem_traceability.py`
