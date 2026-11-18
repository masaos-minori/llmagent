# Procedure: tests/tools/test_check_workitem_structure.py - scaffold leftover tests

## Goal

Test the new plan and procedure leftover rules end to end through the checker, and reverse the prerequisite Plan's assertion that plan and procedure skeletons get no leftover rule.

## Scope
**Release unit**: N/A: not part of a release unit

- Add the scaffold, filled, Freeze-rewrite, dash-row, and fence-derivation tests, and the several-paths and archived-not-scanned coverage for the new kinds. (REQ-003)
- Reverse `test_plan_and_procedure_skeletons_get_no_leftover_rule` (re-verified present in the current module) into the reported-scaffold assertion. (REQ-003)

## Assumptions

- The module's existing end-to-end style is the fixture base: tests install the real templates under `tmp_path` and monkeypatch the checker's `ROOT_DIR`, and the issue leftover tests already model what a scaffold test looks like (`_issue_scaffold` reads the fenced example of the real issue template). The plan and procedure scaffold helpers follow the same pattern against `templates/plan.md` and `templates/implementation-procedure.md`.
- The generator (`tools/generate_workitem.py`) is not invoked as a subprocess in tests; AC-3's "scaffolds of `tools/generate_workitem.py`" is satisfied by testing the generator's template scaffolds, the same source the generator writes, matching how the existing tests use the templates directly. (The generator's own behavior is covered by its tests, out of scope here.)
- Function names of the rule module come from `implementations/20261118-072547_01_tools__workitem_leftover_rules.py.md`; import-level rule tests import them from `tools._workitem_leftover_rules` (the established module-import style for `tools/` helpers).

## Design decisions

- Two fixture variants per kind: the raw scaffold (template fence content a generator would emit, with placeholder values still in place) and a filled document built from the existing filled fixtures of this module. Scaffold tests assert the report names each unfilled line (the finding details carry the line number and text); filled tests assert exit 0.
- The dash-row test keeps a filled plan whose `### Blocker Log` and `### Work Items Created` tables hold the `| — |` rows of `templates/execution-status.md` unreported — the rule must not read those as empty rows.
- The Freeze-rewrite test takes a filled plan whose Freeze paragraph equals the template's verbatim text and asserts no finding, proving the rules never compare prose.
- The fence-derivation test rewrites the fenced plan template inside a temporary template tree (adds or removes one bracket-wrapped placeholder line) and shows the reported bracket findings follow the change, proving no recorded list is involved.

## Alternatives considered

- Keep the clean-skeleton test and add a flag to disable the new rule. Rejected: the Plan explicitly reverses that assertion (its Problem finding); a disable flag would let a scaffold pass the gate, which is the gap being closed.
- Drive scaffolds through `tools/generate_workitem.py` calls in tests. Rejected: the generator writes real files and stamps its timestamp marker into the source plan; reading the template fences directly is how this module already builds scaffolds and keeps the test deterministic.

## Implementation

### Target file

`tests/tools/test_check_workitem_structure.py` (exists, 20155 B)

### Procedure

1. Add scaffold fixture helpers for the plan kind and the procedure kind, following `_issue_scaffold`: read the real template fence under the monkeypatched template tree.
2. Reverse `test_plan_and_procedure_skeletons_get_no_leftover_rule`: the renamed test asserts both scaffolds are reported with exit 1 and that the findings name their unfilled lines (whole-value `{...}` Traceability lines and all-empty table rows for the plan scaffold; the whole-value `{...}` Traceability lines for the procedure scaffold).
3. Add filled-document tests: a filled plan and a filled procedure report nothing; the Freeze-rewrite variant reports nothing; the dash-row variant reports nothing; braces inside a document's own content stay unreported (extend the existing issue test to plan/procedure fixtures if the shared helper allows, otherwise new tests).
4. Add the fence-derivation test (Design decisions) for the bracket rule.
5. Extend the existing multi-path `--file` test and the directory-scan test family so one call covers a plan scaffold plus a procedure scaffold plus a filled document, and add the archived-not-scanned case for the new kinds (a scaffold placed under a `done/` directory produces no finding without `--include-done`).
6. Add at least one import-level test pair for the rule module entry points (scaffold reported, filled not reported) so AC-1 is testable without the checker layer.

### Method

Targeted edits: extend the existing leftover test family (its fixtures and tmp_path roots), replace the one reversed test, keep unrelated families (sections, release units, archived-status) untouched.

### Details

- Tests must not depend on the number of bracket lines in the current plan template (the set is derived at run time); assertions name specific placeholder lines the scaffold fixture itself introduces.
- Keep every test deterministic: no clock, no corpus reads; the corpus measurement is plan Phase 3, not a test (its script is not committed).

## Compatibility considerations

- The reversed assertion is a deliberate characterization change declared in the Plan; the prerequisite Plan's documentation rows already say skeletons are clean only for issues, and the documentation procedure documents land the wording change.
- Tests keep the module's existing monkeypatch style, so the sibling status-value Plan's added tests (different family) merge cleanly.

## Security considerations

- Standard `subprocess`-free test style already used in this module (direct `main(argv)` calls); nothing new.

## Rollback considerations

- Reverting this module restores the clean-skeleton assertion; revert together with the checker and rule-module documents.

## Validation plan

- `uv run pytest tests/tools/test_check_workitem_structure.py -v` — the new tests fail before the rule module and checker wiring land (plan Phase 1 order) and pass after.
- `uv run ruff format tools tests/tools`, `uv run ruff check tools tests/tools`.
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`.

## Completion criteria

- AC-3: the scaffolds are reported with their unfilled lines named; filled, Freeze-rewrite, and dash-row documents are not reported; the clean-skeleton assertion is reversed; several paths work in one call; archived files are not scanned.

## Out of Scope

- Corpus measurement (plan Phase 3, recorded, script not committed).
- The rule implementations and checker wiring (sibling procedure documents).
- Smoke runs over the live active set (plan Phase 5).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261117-132204_wftoolfu004_plan-leftover-detection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-134334_wftoolfu004_plan-leftover-detection.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-072547
- **Related target files**: `tests/tools/test_check_workitem_structure.py`, `tools/check_workitem_structure.py`, `tools/_workitem_leftover_rules.py`
