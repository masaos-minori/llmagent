# Consolidate context and tool usage guidance in prompts/05_skills.md (L-001)

## Priority
Low

## Summary
Investigate and, where confirmed, consolidate restated context-management and
tool-usage guidance across `### Context Efficiency`, `### Tasks`, and
`### Repository Tool Usage` in `prompts/05_skills.md`.

## Background
The source task list for this consolidation effort names these three sections as
containing duplicated rather than referenced guidance. Direct inspection during
issue creation found the overlap smaller than for H-001/H-002/H-003:
- `### Repository Tool Usage` (lines 324-329) already delegates by reference
  ("Apply `rules/ai-execution.md`, section 'Repository Tool Usage'") rather than
  restating tool-usage guidance in full.
- `#### Step 5: Report results` (lines 390-400, under `### Tasks`) already
  references `### Context Efficiency` ("Apply Context Efficiency above for the
  report format") rather than restating its reporting rules — though it then lists
  five specific items to report (394-400) that overlap in spirit with `Context
  Efficiency`'s own "In the final report, list only..." bullet (lines 319-322).

This issue is filed as **Confidence: low**, same basis as M-001 — it records the
requested investigation rather than a confirmed duplicate pair, with one
plausible overlap identified (Step 5's report-item list vs. Context Efficiency's
final-report bullet).

## Problem
Unconfirmed at the level of H-001/H-002/H-003: whether `Step 5`'s five-item report
list is a genuine duplicate of `Context Efficiency`'s final-report bullet, or a
necessary elaboration specific to this workflow's Step 5 output, needs to be
decided against the equivalence test, not assumed.

## Reason for Change
- If `Step 5`'s list is confirmed duplicative of `Context Efficiency`'s bullet, the
  same single-source-of-truth reasoning as the other issues in this set applies.
- If not, closing this issue with that finding corrects the source task list.

## Implementation Intent
Apply `prompts/05_skills.md`'s own Deduplication Rules equivalence test to:
1. `#### Step 5`'s five-item report list (394-400) against `### Context
   Efficiency`'s final-report bullet (319-322).
2. `### Repository Tool Usage` against `### Context Efficiency`'s "Keep the full
   rule inventory internal..." bullets, to confirm no unexpected overlap.
Only consolidate where the test confirms equivalence; otherwise report "no
confirmed duplicate" for that pair.

## Target Files or Areas
- `prompts/05_skills.md` — `### Context Efficiency` (lines 300-322), `### Tasks`
  `#### Step 5` (lines 390-400), `### Repository Tool Usage` (lines 324-329)

## Required Changes
- Apply the equivalence test to the two comparisons named in Implementation Intent.
- If `Step 5`'s report-item list is confirmed duplicative of `Context Efficiency`'s
  final-report bullet, reduce `Step 5` to a reference plus only the items that are
  not already covered (e.g. "the two Context Loader Pattern Validation
  measurements" is workflow-specific and may not be covered by `Context
  Efficiency`'s generic bullet — verify before removing).
- If no duplicate is confirmed for either comparison, close with that finding and
  make no edit.

## Constraints
- Do not remove `Step 5`'s specific reporting items (e.g. the Context Loader
  Pattern Validation measurements, deferred items, new files created) unless each
  one is confirmed to already be covered by `Context Efficiency`'s bullet.
- Must preserve every reporting requirement currently stated in either section.

## Acceptance Criteria
- Both named comparisons have been evaluated against the equivalence test, with the
  result recorded in the implementation's summary.
- Any confirmed duplicate is consolidated with a reference; unconfirmed ones are
  left unchanged with the reasoning documented.
- `Step 5`'s specific, workflow-unique reporting items (Context Loader Pattern
  Validation measurements, Deferred items, new-file creation, Step 4 validation
  result) are preserved regardless of the consolidation outcome.

## Testing Expectations
Not required in the automated-test sense (Markdown-only investigation and, where
warranted, edit). Manual verification expected: reviewer confirms the equivalence
test was applied for both comparisons.

## Documentation Impact
This issue is itself a documentation task. No other file is known to reference
`Step 5`'s report-item list or `Repository Tool Usage`'s content directly; verify
during implementation.

## Out of Scope
- Any change to sections covered by H-001, H-002, H-003, or M-001.
- Rewriting `Context Efficiency`, `Step 5`, or `Repository Tool Usage` for style
  reasons unrelated to confirmed duplication.

## Dependencies
Should be implemented after H-001 (which edits `### Tasks`, including `Step 5`'s
surrounding structure) and after M-001, to avoid re-deriving this issue's diff
against text that those issues have already changed.

## Unresolved Questions
- Is `Step 5`'s five-item report list a genuine restatement of `Context
  Efficiency`'s final-report bullet, or a necessary Step-5-specific elaboration?
  Needs the equivalence test applied during implementation, not assumed from the
  source task list.

## AI Implementation Instruction
- Treat this issue as an investigation-first task: apply the equivalence test
  before making any edit, and be willing to report "no confirmed duplicate found"
  as a valid outcome for either or both comparisons.
- Do not delete `Step 5`'s specific reporting items without confirming each is
  already covered elsewhere.
- Implement after H-001 and M-001 (see Dependencies).
- Do not touch sections out of scope for this issue.
- Stop and report back if the line numbers cited here no longer match the current
  file content.
