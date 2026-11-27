# Match whole words in the Change Responsibility create hints

## Priority
Medium

## Summary
Stop `tools/fill_affected_areas.py` (and evaluate `tools/audit_plan_target_paths.py`) from treating a substring such as `new` inside another word or phrase as a create signal.

## Background
Evidence (`Explicit in code`): `tools/fill_affected_areas.py` `change_kind` tests `hint in text` for `create`, `new`, and `generated`; `tools/audit_plan_target_paths.py` `CREATE_HINTS` (`create`, `new`, `generated`, `manifest;`, `registry;`) is tested with `any(h in rest ...)`. In the wfeff008 Plan the `Change Responsibility` text "Update the Index and Work Items or runner rows ... with the new options" made `fill_affected_areas.py` print `Create` for an existing file; the row had to be corrected by hand.

## Problem
A substring match classifies existing files as new when the text contains words such as "new options" or "renewed".

## Reason for Change
A wrong `Change` and a wrong churn and bus factor (`N/A (new)`) in the `Affected areas` table; the audit tool could skip the existence check of a row that is not new.

## Implementation Intent
Match whole words with a boundary rule and keep every existing accepted spelling working.

## Target Files or Areas
- `tools/fill_affected_areas.py`
- `tools/audit_plan_target_paths.py`
- `tests/tools/test_fill_affected_areas.py`
- `tests/tools/test_audit_plan_target_paths.py`

## Required Changes
- Use a word-boundary match for `create`, `new`, `generated`, and keep `manifest;` and `registry;` as exact tokens.
- Run `tools/audit_plan_target_paths.py` over every Plan under `plans/` and `plans/done/` before and after and compare the findings; record any change.
- Add tests: "new options" and "renewed" are `Modify`; "New file", "Create the tool", and "generated block" are `Create`.

## Constraints
- The audit tool's exit code and findings on existing Plans must not change except for rows the comparison shows were misclassified.
- `tools/fill_affected_areas.py` stays under the 24576 B tools size gate.

## Acceptance Criteria
- [ ] "new options" is `Modify` in `fill_affected_areas.py`; the three create spellings above stay `Create`.
- [ ] The before and after audit results over all Plans are identical or the differences are listed and justified.
- [ ] Existing tests of both tools pass.

## Testing Expectations
Unit tests for both tools; ruff, mypy, bandit; the before and after audit comparison.

## Documentation Impact
Yes. The `tools/TOOL_DESCRIPTIONS.md` row text for the hint rule if it names substring matching (check first).

## Out of Scope
- Changing which hints exist.
- Other Change values.

## Dependencies
N/A: none

## Unresolved Questions
- `不明`: whether any archived Plan relies on a substring spelling such as `renewed`; the comparison run answers it.

## AI Implementation Instruction
Change matching only. If the comparison shows a regression on an existing Plan, stop and report.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-120102
- **Related target files**: `tools/fill_affected_areas.py`, `tools/audit_plan_target_paths.py`, `tests/tools/test_fill_affected_areas.py`, `tests/tools/test_audit_plan_target_paths.py`
