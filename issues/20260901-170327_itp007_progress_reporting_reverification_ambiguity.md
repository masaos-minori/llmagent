# Progress Reporting does not state whether reported values are re-derived or reused

## Priority
Low

## Summary
`skills/issue-to-plan/workflow.md` Step 9's Final Validation report lists several
values (Path A/B classification, Requirement counts, freeze status, etc.) without
stating whether producing that report re-verifies each value against current state
or simply reuses the value already recorded earlier in the cycle — leaving open
whether the act of reporting can itself trigger re-investigation.

## Background
`workflow.md` Step 9: "Report: generated Plan path; generated Unknown/Risk files
(or `None`); number of Requirements; number of `Implementation Target Files` rows;
Path A/B classification (one word; rationale is in the Plan's Design section, do
not restate); information-completeness result; traceability result;
`Implementation Target Files` freeze status..."

`rules/ai-execution.md` Progress Reporting (Base): "Report progress once per step,
in one line, after the step completes... Do not repeat the same result as a
summary, detail, and conclusion." This governs *how much* to report and *how
often*, but not *how the reported value is obtained* — freshly re-checked, or read
back from what Step 5/8 already recorded.

`workflow.md`'s own "Progress recording during Steps 3-6" section addresses report
*frequency* ("do not report for a routine, expected verification step") but not
report *content derivation*.

## Problem
"Path A/B classification" is a concrete example: Step 3 already classified the
Issue and "Record[ed] the Path A/B decision for reuse in Step 5." If Step 9's
report re-derives this by re-running Step 3's classification criteria instead of
reading back the Step 3 record, that is redundant work at best and a source of
inconsistency at worst (if repository state changed between Step 3 and Step 9,
re-classifying could produce a different answer than what the Plan's Design
section already states, without any stated rule for which one wins).

More generally, without a stated "reuse recorded values, don't re-derive them for
the report" rule, an agent could treat each Final Validation field as its own
mini-investigation, which risks the report step silently re-triggering work that
should have been finished by the time Step 9 runs.

## Reason for Change
An explicit "report from the record, do not re-derive" rule keeps Step 9 a genuine
final summary rather than a second investigation pass, consistent with `rules/ai-
execution.md` Context Reading's existing principle ("Reuse a verified fact only
while its source file is unchanged...").

## Implementation Intent
Add a short statement to Step 9 (or to `rules/ai-execution.md` Progress Reporting
(Base), since this generalizes beyond `issue-to-plan`) that every reported value
must be read back from where the workflow already recorded it (the Plan document,
Step 3's decision, Step 8's validation result) — not recomputed for the report —
unless the source itself is stale per `rules/ai-execution.md` Context Reading's
existing recheck-on-change rule.

## Target Files or Areas
- `skills/issue-to-plan/workflow.md` (Step 9)
- `rules/ai-execution.md` (Progress Reporting (Base), if the clarification belongs
  at the shared-rule level)

## Required Changes
- Add a "report from the record, do not re-derive" statement to Step 9 or to the
  shared Progress Reporting (Base) rule.
- Cross-reference `rules/ai-execution.md` Context Reading's existing "reuse a
  verified fact only while its source is unchanged" rule so the two are explicitly
  linked, not independently stated.

## Constraints
The clarification must not override `rules/ai-execution.md` Context Reading's
existing "recheck after the source changes" exception — reporting from the record
is the default, not an absolute prohibition on re-verification when the source is
known to be stale.

## Acceptance Criteria
- Step 9 (or Progress Reporting (Base)) states that reported values are read back
  from prior Step records by default, re-derived only when the source is known
  stale.

## Testing Expectations
Manual review: confirm the added statement is consistent with, and cross-referenced
to, `rules/ai-execution.md` Context Reading.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this mechanism.

## Out of Scope
- Changing what Step 9 reports — only how each reported value is obtained.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `workflow.md` Step 3, Step 8, and Step 9, and `rules/ai-execution.md` Context
Reading and Progress Reporting (Base), before wording the clarification. Prefer
adding the rule to `rules/ai-execution.md` Progress Reporting (Base) if the same
ambiguity plausibly applies to other workflows' final-report Steps, not only
`issue-to-plan`'s.
