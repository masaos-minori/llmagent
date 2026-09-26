# Stale pre-reorg governance doc paths in checker tests

## Priority
High

## Summary
Three doc-consistency checker tests still assert against pre-docs-reorg file paths/snapshots. They fail because the docs reorg (docsreorg01/02) renamed governance/eventbus/rag doc files but the tests' hardcoded expectations were never updated.

## Background
The repository underwent a docs/ folder reorganization (see `plans/20260925-072438_plan.md` and `issues/20260923-141508_docsreorg16_run-full-validation-sweep-after-docs-folder-reorganization.md`). This issue was discovered while executing that sweep's implementation procedure (`implementations/20260925-111411_04_tests___full_suite_.md`), which found 97 full-suite test failures; this is one root-cause cluster extracted from that investigation.

## Problem
- `tests/tools/test_check_dependency_graph_cycles.py::TestRealGraphIntegration::test_real_repo_graph_has_no_cycle` and `tests/tools/test_check_issue_inventory_conformance.py::TestGovernanceDocPathIntegration::test_governance_doc_path_resolves_on_disk` assert `Path("docs/00_governance/00_governance_0X_....md").is_file()` — a pre-reorg path with a duplicated `00_` prefix. The actual current file is `docs/00_governance/governance_0X_....md` (no duplicated prefix).
- `tests/tools/test_check_docs_quality.py::TestRegressionFullDocsTree::test_cross_file_duplication_detected_on_full_docs_tree` compares cross-file duplication output against a golden snapshot written with old flat pre-reorg filenames (e.g. `24_eventbus/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`) instead of the current nested post-reorg paths (e.g. `24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md`).

## Reason for Change
These tests are meant to validate the doc-consistency tooling against the real repository tree. As written, they will always fail after any doc path rename, which defeats their purpose and currently masks whether the checkers themselves still work correctly post-reorg.

## Implementation Intent
Update each test's expected path(s)/snapshot to match the current post-reorg `docs/` layout. Do not change the checker tools themselves (`tools/check_dependency_graph_cycles.py`, `tools/check_issue_inventory_conformance.py`, `tools/check_docs_quality.py`) unless investigation shows the checkers — not the tests — hold the stale assumption.

## Target Files or Areas
- `tests/tools/test_check_dependency_graph_cycles.py`
- `tests/tools/test_check_issue_inventory_conformance.py`
- `tests/tools/test_check_docs_quality.py`

## Required Changes
- Update the hardcoded governance doc path(s) in the two path-integration tests to the current `docs/00_governance/governance_0X_....md` naming.
- Regenerate/update the golden duplication-snapshot fixture in the docs-quality regression test to reflect current post-reorg paths.
- Re-run each test individually to confirm it passes against the current tree.

## Constraints
N/A: none beyond not changing the checker tools' own logic without separate justification.

## Acceptance Criteria
- `uv run pytest tests/tools/test_check_dependency_graph_cycles.py tests/tools/test_check_issue_inventory_conformance.py tests/tools/test_check_docs_quality.py -q` passes with 0 failures.
- No other test in the full suite newly fails as a result of this change.

## Testing Expectations
Run the three target test files directly; also run `uv run pytest -q` full suite once to confirm no regression introduced.

## Documentation Impact
N/A: this is a test-fixture correction, not a documented-behavior change.

## Out of Scope
- Any further docs/ file renames or restructuring.
- Fixing other unrelated failing tests from the same full-suite run (tracked as separate issues).

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Fix only the hardcoded path/snapshot expectations in the three named test files so they reflect the current on-disk `docs/` layout. Do not modify `tools/check_*.py` source unless you confirm the checker itself (not the test) contains the stale path assumption. Do not touch unrelated tests.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/tools/test_check_dependency_graph_cycles.py, tests/tools/test_check_issue_inventory_conformance.py, tests/tools/test_check_docs_quality.py
