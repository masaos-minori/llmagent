# Record the six pre-existing failing tests in the known-failure baseline

## Priority
Medium

## Summary
Six tests fail on a clean checkout of HEAD and are unrelated to the redaction work in progress.
Record them in `tools/known_test_failures_baseline.txt` so `tools/compare_test_baseline.py` reports
them as known failures instead of new failures during full-suite runs.

## Background
`tools/known_test_failures_baseline.txt` is currently empty. The full-suite run of the
`code-implementation` batch for `plans/done/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`
reported 13 failures, of which 7 were caused by that plan's rendering change and 6 are pre-existing.

## Problem
The six pre-existing failures are indistinguishable from regressions in a full-suite run, so every
batch close reports them as new failures and the gate cannot be used to judge a diff.

## Reason for Change
The baseline is the mechanism that separates a diff-caused failure from a known one; without entries
the gate reports noise on every run.

## Implementation Intent
Confirm the six failures reproduce on a clean worktree at HEAD, then add one baseline entry per test
with this issue path as the reason. No test or production code is changed by this issue.

## Target Files or Areas
- `tools/known_test_failures_baseline.txt`

## Required Changes
- Add one entry per failing test id, each with this issue path as the reason.

## Constraints
- The baseline is read-only for the comparison tool; nothing is skipped, xfailed, or deselected.
- Entries are added only with `tools/compare_test_baseline.py --add` and the owner's approval.

## Acceptance Criteria
- `uv run python tools/compare_test_baseline.py <junit-xml>` reports these six as known failures and
  no new failures for a run that changes nothing else.
- Each entry names this issue path as its reason.

## Testing Expectations
- Re-run the six tests on a clean worktree at HEAD before adding the entries.
- Re-run `compare_test_baseline.py` after the entries are added and confirm the classification.

## Documentation Impact
None beyond the baseline file itself. No `docs/` change is required.

## Out of Scope
- Fixing the six tests. Root-cause work is a separate issue.
- Any change to `scripts/` or `tests/`.

## Dependencies
N/A: none

## Unresolved Questions
- Whether each failure is environment-dependent (host uid, filesystem race, git configuration) or a
  real defect. Not confirmed; the baseline entry records the state, not the cause.

## AI Implementation Instruction
Do not modify test or production code. Verify reproduction at HEAD first, then add the entries with
`--add` and the reason naming this issue path.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-093113
- **Related target files**: `tools/known_test_failures_baseline.txt`
