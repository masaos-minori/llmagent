# Consolidate Context Loader validation definitions in prompts/05_skills.md (H-003)

## Priority
High

## Summary
`prompts/05_skills.md` defines Context Loader / ownership-boundary validation
expectations in `### Context Loader Pattern Validation` and then restates an
overlapping checklist in `#### Step 4: Validate the reorganization`. Keep
`Context Loader Pattern Validation` as the single authoritative validation
definition and reduce `Step 4`'s restated checklist to a reference.

## Background
Confirmed by direct inspection: `### Context Loader Pattern Validation` (lines
236-269) defines two concrete checks — "Minimal loading, measured" and "Circular
reference check" — each with its own procedure. `#### Step 4: Validate the
reorganization` (lines 373-389) says "Apply Validation and Context Loader Pattern
Validation above" (a correct reference) but then adds "Additionally confirm the
Context Loader Pattern still holds" followed by five bullets (378-385) that mostly
restate `### Validation`'s ownership-boundary bullet (lines 229-232) rather than the
two concrete checks actually defined in `Context Loader Pattern Validation`. In
other words: the restatement in `Step 4` duplicates `### Validation`'s content more
than it duplicates `Context Loader Pattern Validation`'s content, even though the
task list that requested this consolidation names `Context Loader Pattern
Validation` as the counterpart. See Dependencies below — this overlaps with the
H-002 issue's scope on `### Validation`.

## Problem
`Step 4`'s five-bullet "Additionally confirm..." list re-derives, in expanded form,
constraints that are already fully stated once in `### Validation` (compressed) and
again in `### Deduplication Rules`' acceptance criteria (see the H-002 issue). This
means the same ownership-boundary check exists in three places by the time `Step 4`
is reached, and `Step 4` never actually references the two concrete measurements
(default load size, circular-reference graph) that `Context Loader Pattern
Validation` defines — it only tells the reader to "Apply" that section by name.

## Reason for Change
- Maintenance risk: `Step 4`'s five bullets must be kept in sync with `Validation`'s
  bullet and `Deduplication Rules`' acceptance criteria (H-002 scope) by hand.
- Clarity risk: because `Step 4` says "Apply Context Loader Pattern Validation
  above" and then lists bullets that are not actually from that section, a reader
  can mistake the five bullets for a summary of `Context Loader Pattern Validation`
  when they are not.
- Context cost: fixed per-invocation overhead from restating the same
  ownership-boundary check for a third time.

## Implementation Intent
Keep `### Context Loader Pattern Validation` (236-269) as the authoritative
definition of the two concrete checks (minimal loading measurement,
circular-reference check). In `#### Step 4`, keep the existing correct reference
("Apply Validation and Context Loader Pattern Validation above") and remove the
five-bullet "Additionally confirm..." restatement, since it duplicates
`### Validation`'s ownership-boundary bullet rather than adding new instruction
beyond what "Apply Validation... above" already covers. If, during implementation,
any of the five bullets is found to state something genuinely absent from both
`Validation` and `Context Loader Pattern Validation`, keep that specific bullet
(do not remove information that exists nowhere else) and note it in the PR
description.

## Target Files or Areas
- `prompts/05_skills.md` — `### Context Loader Pattern Validation` (lines 236-269)
  and `#### Step 4: Validate the reorganization` (lines 373-389)

## Required Changes
- Leave `### Context Loader Pattern Validation`'s two concrete checks unchanged.
- In `#### Step 4`, remove the "Additionally confirm the Context Loader Pattern
  still holds" five-bullet list (lines 378-385) where each bullet is confirmed
  duplicative of `### Validation` or `### Deduplication Rules`' acceptance
  criteria.
- Retain `Step 4`'s existing reference sentence ("Apply Validation and Context
  Loader Pattern Validation above") and its closing sentence ("Per Step
  Responsibilities: validate only here...").
- If any bullet in the five-bullet list is not duplicative (see Implementation
  Intent), move it to the section it actually belongs to (`Validation` or `Context
  Loader Pattern Validation`) rather than leaving it only in `Step 4`.

## Constraints
- Must preserve both concrete checks defined in `Context Loader Pattern Validation`
  exactly as they are (no change to the minimal-loading measurement procedure or the
  circular-reference check procedure).
- Must not remove any validation expectation that exists only in `Step 4`'s
  five-bullet list and nowhere else — verify each bullet against `Validation` and
  `Deduplication Rules`' acceptance criteria individually before deleting it.
- Coordinate with the H-002 issue, which also edits `### Validation` — see
  Dependencies.

## Acceptance Criteria
- The two Context Loader Pattern checks (minimal loading, circular reference) are
  defined in exactly one place.
- `Step 4` no longer restates ownership-boundary language that is already fully
  covered by its "Apply Validation and Context Loader Pattern Validation above"
  reference.
- No validation expectation present before the edit is missing afterward.
- `Step 4` still clearly instructs the implementer to run both concrete Context
  Loader Pattern checks before reporting Step 4 as `Pass` (this instruction
  currently lives in `Context Loader Pattern Validation`'s opening line: "do not
  report Step 4 `Pass` without running both" — confirm this line is preserved,
  since it is the one piece of `Context Loader Pattern Validation` that
  specifically talks about `Step 4`'s reporting behavior).

## Testing Expectations
Not required in the automated-test sense (Markdown-only change). Manual
verification expected: diff review confirming the two concrete checks and the
"do not report Step 4 Pass without running both" instruction both survive intact,
and that `Step 4` still reads as a complete, self-contained instruction after the
five-bullet list is removed or trimmed.

## Documentation Impact
This issue is itself a documentation consolidation. No other file is known to
reference `Step 4`'s five-bullet list specifically; verify during implementation.

## Out of Scope
- Any change to the two concrete Context Loader Pattern checks themselves.
- Any change to `### Step Responsibilities` / `### Tasks`' step numbering or
  sequencing (covered by H-001).
- Redesigning `Step 4`'s role in the five-step workflow.

## Dependencies
This issue and the H-002 issue both touch overlapping ownership-boundary language:
H-002 consolidates `### Deduplication Rules`' acceptance criteria and
`### Validation`'s ownership bullet into a reference to `Canonical Ownership
Model`; this issue removes `Step 4`'s restatement of that same ownership-boundary
bullet. Implement H-002 first, then re-derive this issue's `Step 4` diff against
the post-H-002 wording of `### Validation`, so `Step 4`'s reference resolves to the
already-consolidated text rather than to text this issue would otherwise have to
edit twice.

## Unresolved Questions
- After H-002 lands, does `Step 4` need any bullet content at all beyond its two
  existing reference sentences, or can the "Additionally confirm..." paragraph be
  removed in full? Decide once the H-002 diff exists.

## AI Implementation Instruction
- Implement the H-002 issue first (see Dependencies); do not start this issue's
  edit against the pre-H-002 wording of `### Validation`.
- Do not rewrite `prompts/05_skills.md` from scratch; edit only `#### Step 4` (and,
  only if a genuinely non-duplicative bullet is found, its true home section).
- Preserve the "do not report Step 4 Pass without running both" instruction and
  both concrete Context Loader Pattern checks verbatim.
- Do not touch `### Step Responsibilities`, `### Tasks`' step bodies other than
  `Step 4`, `### Canonical Ownership Model`, `### Architectural Principles`,
  `### Normative vs. Descriptive Content`, or `### Canonical References` — those
  are out of scope for this issue.
- Stop and report back if the line numbers cited here no longer match the current
  file content, or if the H-002 issue has not yet been applied.
