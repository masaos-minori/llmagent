# Hardcoded content-similarity baseline test is fragile to docs edits

## Priority
Low

## Summary
`tests/tools/test_check_docs_quality.py::TestRegressionFullDocsTree::test_cross_file_duplication_detected_on_full_docs_tree`
asserts an exact hardcoded count of within-file content-similarity findings across the
entire `docs/` tree (line 292). A 2026-09-20 batch of 21 legitimate `docs/*.md` edits
(mechanical-content removal per `skills/DESIGN.md` Docs content policy) silently
shifted this count from 206 to 205, and the drift was discovered only when the full
test suite happened to be run at the very end of a 22-file `code-implementation`
batch — with no earlier signal that any individual edit had touched this count.

## Background
The test's own docstring calls 206 a "Plan baseline," confirming it was hardcoded to
match a specific past state of the `docs/` tree rather than derived from a
content-invariant property. `code-implementation`'s Step 3e (per-file validation) does
not run the full suite — only targeted tests — and the full suite is run once per
`code-implementation` cycle (`skills/code-implementation/workflow.md` Step 4), so for
a batch of many small `docs/*.md`-only implementation procedures (which mostly skip
Step 4's full-suite run when no `scripts/` code changed, though this session's batch
did run it once at the end per its own judgment), a hardcoded whole-tree count baked
into one regression test is the only thing that would catch this class of drift, and
only at whatever point the full suite is actually run — potentially much later than
the edit that caused it.

## Problem
`within_file_count == 206` at
`tests/tools/test_check_docs_quality.py:292` failed after the 2026-09-20 batch (actual
count: 205). Verified via `git stash` that the assertion passed before the batch's 21
docs edits and failed after, confirming the drift was caused by this session's
legitimate content-policy cleanup (removing duplicate/mechanical content that
happened to also count as "content similarity" under `check_docs_quality.py`'s
detector), not a bug in that detector. The test was updated in place to assert 205
with an explanatory comment, but the underlying fragility — an opaque, hard-to-predict
exact-count assertion with no diagnostic breakdown of *which* file pairs contribute to
the count — remains for the next edit that touches `docs/`.

## Reason for Change
An exact-count regression test with no per-file breakdown gives a future editor (human
or AI) no way to predict, before running the full suite, whether their change will
shift this number — and no way to tell, when it fails, which specific sections newly
match or newly stopped matching without independently re-running
`check_docs_quality.py` and diffing its output. This makes every future
content-policy-style cleanup batch across `docs/` liable to hit the same
late-discovered, opaque failure this session did.

## Implementation Intent
Reduce the assertion's fragility while preserving its regression-catching intent,
e.g.:
- Replace the exact-count assertion with a tolerance range or a trend-direction check
  (e.g. "count did not *increase*," since the test's purpose per its own docstring is
  confirming duplication is *detected*, not pinning an exact number) if an increase
  specifically indicates a newly-introduced duplication worth catching.
- Or, keep an exact-count assertion but add a companion assertion/diagnostic that
  prints the specific file:section pairs contributing to the count on failure, so a
  future mismatch is self-diagnosing instead of requiring a manual
  `check_docs_quality.py` re-run and diff.
- Or, snapshot the current set of file:section pairs (not just the count) and assert
  set equality with a clear per-pair diff on mismatch, which also naturally tolerates
  the count staying the same while the underlying pairs change (a blind spot the
  current count-only assertion has).

## Target Files or Areas
- `tests/tools/test_check_docs_quality.py`

## Required Changes
1. Replace or augment the exact-count assertion at
   `tests/tools/test_check_docs_quality.py:292` per one of the Implementation Intent
   options, choosing based on what `check_docs_quality.py`'s output format makes
   easiest to implement reliably (confirm during implementation).
2. If moving to a per-pair/set-based assertion, generate and commit the current
   snapshot of file:section pairs (post-2026-09-20-batch) as the new baseline.
3. Verify the updated test still fails meaningfully if a genuine new duplication is
   introduced (e.g. temporarily duplicate a section between two `docs/*.md` files in a
   throwaway local test run, confirm the assertion catches it, then revert).

## Constraints
- Do not remove the regression-detection intent of this test — a real, unintentional
  increase in cross-file/within-file duplication should still fail some assertion.
- Do not change `check_docs_quality.py`'s own detection logic — this issue is about
  the test's assertion shape, not the checker being tested.

## Acceptance Criteria
- Running the test against the current `docs/` tree (post-2026-09-20-batch) passes.
- Introducing a synthetic new duplicate section between two `docs/*.md` files causes
  the test to fail with a message that identifies which files/sections are newly
  duplicated (not just a changed count).
- Removing an existing duplicate section (making the count go down further) does not
  fail the test if the chosen implementation treats "decrease" as acceptable per
  Implementation Intent's first option — otherwise, updating the baseline for a
  legitimate decrease should require touching only the test file, not investigating
  which of many unrelated files caused it.

## Testing Expectations
`uv run pytest tests/tools/test_check_docs_quality.py -v`, focusing on
`TestRegressionFullDocsTree`. No `scripts/` changes are involved, so no broader test
run is required beyond this file and a lint/type check
(`uv run ruff check tests/tools/test_check_docs_quality.py`,
`uv run mypy tests/tools/test_check_docs_quality.py`).

## Documentation Impact
N/A: this is an internal test-tooling maintainability fix with no `docs/00_index.md`
task-scope mapping.

## Out of Scope
- The already-applied baseline update (206→205) for the 2026-09-20 batch — already
  correct and landed; this issue is about preventing the *next* occurrence of the same
  late-discovered, opaque failure.
- `check_docs_quality.py`'s detection logic itself.
- The other test in the same class, `test_no_new_false_positives_on_full_docs_tree` —
  only `test_cross_file_duplication_detected_on_full_docs_tree`'s assertion shape is in
  scope, unless investigation finds the sibling test shares the same fragility, in
  which case note it as a `Plan Gap` rather than silently expanding scope.

## Dependencies
N/A: none.

## Unresolved Questions
Which of the three Implementation Intent options (tolerance/trend check,
diagnostic-on-failure, or set-based snapshot) best fits `check_docs_quality.py`'s
actual output structure is an implementation-time investigation, not decided here.

## AI Implementation Instruction
Read `check_docs_quality.py`'s content-similarity detection output format before
choosing an approach. Prefer the option that gives the clearest actionable failure
message with the least added test-maintenance burden. Confirm the chosen approach
still fails on a genuinely reintroduced duplication before considering the fix
complete — do not weaken the test to the point it can no longer catch real
regressions.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-175221
- **Related target files**: tests/tools/test_check_docs_quality.py
