# docs quality regression golden pairs drifted for governance_03

## Priority
Low

## Summary
`tests/tools/test_check_docs_quality.py::TestRegressionFullDocsTree::test_cross_file_duplication_detected_on_full_docs_tree` fails: the hardcoded `EXPECTED_WITHIN_FILE_PAIRS` golden set no longer matches `tools/check_docs_quality`'s live output — one previously-expected pair is no longer detected.

## Background
Discovered during the post-docs-reorg full-suite validation re-check (`implementations/20260925-111411_04_tests___full_suite_.md`, Execution Status Step 3). A prior run of this same procedure (20260927) found 97 failures across many modules; a re-run today found only 4 remaining, including this one — this test's golden set is a fixed regression fixture that drifts whenever the referenced doc's content changes.

## Problem
`assert current_pairs == EXPECTED_WITHIN_FILE_PAIRS` fails with:
```
Removed: frozenset({"00_governance/governance_03_issue-and-uncertainty-management.md:'CI-009' <-> 'CI-012'"})
```
i.e. `tools/check_docs_quality` no longer reports a content-similarity pair between sections `'CI-009'` and `'CI-012'` in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` that the test's hardcoded expectation still lists.

## Reason for Change
The test is a regression guard (see its docstring reference to "governance_04 duplication is now detected cross-file") — its golden set must track the current, intentional state of `docs/00_governance/governance_03_issue-and-uncertainty-management.md`. Left as-is, the test permanently fails and cannot detect a real future regression.

## Implementation Intent
Confirm whether `governance_03_issue-and-uncertainty-management.md`'s `CI-009`/`CI-012` sections were edited (as part of the docs reorg or a later change) such that they are no longer textually similar — if so, this is expected drift and the golden set should be updated to match current tool output. If the sections are unchanged, investigate whether `tools/check_docs_quality`'s similarity detection itself regressed.

## Target Files or Areas
- `tests/tools/test_check_docs_quality.py` (`EXPECTED_WITHIN_FILE_PAIRS` constant)
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- `tools/check_docs_quality.py` (similarity detection, only if the doc content is confirmed unchanged)

## Required Changes
- Confirm current `docs/00_governance/governance_03_issue-and-uncertainty-management.md` content for the `CI-009`/`CI-012` sections against repository history.
- If the removal is legitimate drift, update `EXPECTED_WITHIN_FILE_PAIRS` in `tests/tools/test_check_docs_quality.py` to match.
- If the tool's detection regressed, fix `tools/check_docs_quality.py` instead of the test.

## Constraints
N/A: none beyond standard doc-checker validation.

## Acceptance Criteria
- `tests/tools/test_check_docs_quality.py::TestRegressionFullDocsTree::test_cross_file_duplication_detected_on_full_docs_tree` passes.
- The fix does not silently mask a real future duplication regression (i.e. the golden set is corrected to match verified current content, not merely made permissive).

## Testing Expectations
Run `uv run pytest tests/tools/test_check_docs_quality.py -v`; run full suite once after the fix.

## Documentation Impact
None beyond the golden-fixture update itself — no `docs/*.md` content change is implied unless the investigation finds the doc needs correcting.

## Out of Scope
The other 3 failures found in the same full-suite re-check (eventbus ack ownership, orchestrator config restore, ingestion embedding-failure test) — tracked as separate issues.

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: which side is stale — the test's golden set, or the doc content — requires diffing `governance_03_issue-and-uncertainty-management.md`'s `CI-009`/`CI-012` sections against the version this golden set was authored against.

## AI Implementation Instruction
Do not simply delete the removed pair from `EXPECTED_WITHIN_FILE_PAIRS` without first confirming the doc content genuinely no longer overlaps — this test exists specifically to catch unintentional duplication drift.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260928-124754
- **Related target files**: tests/tools/test_check_docs_quality.py, docs/00_governance/governance_03_issue-and-uncertainty-management.md
