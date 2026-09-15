# Add "Completed when" criteria to python-lint-typecheck workflow Steps 3, 7, 8

## Priority
Medium

## Summary
`skills/python-lint-typecheck/workflow.md` Step 3 (Architecture Integrity), Step 7 (Static Security Validation), and Step 8 (Diff Scope Enforcement) each describe a check and its remediation procedure, but state no explicit "Completed when" condition, unlike several other Steps in the same file.

## Background
This issue follows a skill/workflow design review (5 evaluation criteria, 55 files) requested and conducted in this session. Note: the review's initial finding also flagged "no priority rule for mypy/pyright disagreement" — re-verified during this issue's drafting and found already addressed at line 176 ("If mypy and pyright disagree: resolve to the stricter interpretation and annotate why"), so that item is not included here.

## Problem
Confirmed by direct reading:
- Step 3 (lines 75-94): describes the `lint-imports` remediation procedure (4 numbered sub-steps) with no completion condition.
- Step 7 (lines 201-206): states "Priority findings — must resolve before merge" but does not state this as the Step's own completion condition in the same explicit style used elsewhere in the file.
- Step 8 (lines 209-219): describes a 3-step diff-coverage remediation procedure with no completion condition.

This file already applies a shared "Step failure handling" rule (line 18) covering the exit/Blocked side uniformly across all Steps — the gap here is specifically the missing per-Step "Completed when" (the goal side), not the exit condition.

## Reason for Change
A remediation procedure with no stated completion condition leaves ambiguous whether "I ran the remediation steps once" or "the underlying check now passes" is the intended stopping point — these are not always the same (e.g. Step 3's remediation could still leave `lint-imports` failing if the contract update itself was wrong).

## Implementation Intent
Add one "Completed when" line to each of Step 3, 7, and 8, stating that the underlying check now passes (not merely that the remediation procedure was run once), following the phrasing style already used elsewhere in this file.

## Target Files or Areas
- `skills/python-lint-typecheck/workflow.md`

## Required Changes
- Step 3: add "Completed when: `lint-imports` reports no violation, either because no accidental import remained or because every intentional import is now covered by an explicit `.importlinter` contract update."
- Step 7: add "Completed when: `bandit` has been run and every priority finding (per `rules/coding.md` Bandit priority findings) is resolved or suppressed with the required justification (per `rules/coding.md` Suppression governance)."
- Step 8: add "Completed when: `diff-cover` reports the changed-lines coverage at or above the threshold in `rules/toolchain.md` §7, using only tests scoped to the actual change."

## Constraints
Do not restate the shared "Step failure handling" exit condition (line 18) inside each Step — this issue adds only the missing goal-side "Completed when," which is a distinct condition from the already-existing shared exit rule.

## Acceptance Criteria
- Step 3, Step 7, and Step 8 in `skills/python-lint-typecheck/workflow.md` each have an explicit "Completed when" line.
- Each new line ties completion to the underlying check actually passing, not merely to the remediation procedure having been run once.
- `tools/check_skills_references.py` still passes.

## Testing Expectations
Not applicable — prose-only workflow file. Run `tools/check_skills_references.py` per `routing.md`'s relevant row.

## Documentation Impact
This issue's entire scope is `skills/python-lint-typecheck/workflow.md`.

## Out of Scope
- The mypy/pyright disagreement rule — already present at line 176, confirmed during this issue's drafting; no change needed.
- Any other Step in this file not listed above.
- Any other evaluation criterion from the same review — tracked in separate issues.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Add only the three completion-condition lines described in Required Changes; do not duplicate the shared "Step failure handling" rule inside each Step, and do not modify the already-correct mypy/pyright disagreement rule at line 176.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-115214
- **Related target files**: skills/python-lint-typecheck/workflow.md
