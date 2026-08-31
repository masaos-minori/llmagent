# Consolidate shared rule references in prompts/05_skills.md (M-001)

## Priority
Medium

## Summary
Investigate and, where confirmed, consolidate restated explanatory text across
`### Architectural Principles`, `### Normative vs. Descriptive Content`, and
`### Canonical References` in `prompts/05_skills.md`, replacing confirmed
duplicates with references to whichever section is the authoritative source.

## Background
The source task list for this consolidation effort names these three sections as
restating information defined elsewhere. Direct inspection during issue creation
found this claim harder to confirm than the duplications documented in the H-001,
H-002, and H-003 issues:
- `### Architectural Principles` (lines 34-63) already contains a
  cross-reference for its "shared normalization" bullet ("see Canonical Ownership
  Model") rather than restating that section's content in full.
- `### Normative vs. Descriptive Content` (lines 109-129) and
  `### Canonical References` (lines 196-204) each define distinct concepts (a
  normative/descriptive classification test, and a reference-citation format,
  respectively) that are not obviously restated elsewhere in the file.

This issue is filed as **Confidence: low** relative to H-001/H-002/H-003 — it
records the requested investigation rather than a confirmed duplicate pair.

## Problem
Unconfirmed: the source task list asserts restated content across these three
sections without citing which specific sentences duplicate which other section.
This issue's problem statement is "determine whether a real duplicate exists" more
than "fix a confirmed duplicate."

## Reason for Change
- If a real duplicate is found during investigation, the same maintenance and
  context-cost reasoning as H-001/H-002/H-003 applies (single source of truth,
  reduced per-invocation load).
- If no real duplicate is found, closing this issue with that finding still has
  value: it corrects the source task list for future reference and prevents
  someone re-raising the same unconfirmed claim later.

## Implementation Intent
Re-run the equivalence test that `prompts/05_skills.md`'s own
`### Deduplication Rules` defines ("Treat content as duplicated only when its
scope, requirements, conditions, exceptions, and effects are equivalent") against
each pair of sections named in Background. Only consolidate where two sections
genuinely restate the same normative content; do not force a consolidation to
satisfy the source task list if the equivalence test fails. Where consolidation is
warranted, follow the same reference pattern used in H-001/H-002/H-003 (keep one
canonical statement, replace the other with a `See <file path>, section
"<heading>".` reference per `### Canonical References`).

## Target Files or Areas
- `prompts/05_skills.md` — `### Architectural Principles` (lines 34-63),
  `### Normative vs. Descriptive Content` (lines 109-129), `### Canonical
  References` (lines 196-204)

## Required Changes
- Apply the Deduplication Rules equivalence test to every pair among these three
  sections and to each section against `### Canonical Ownership Model` and
  `### Deduplication Rules` (the sections H-002 treats as canonical for
  ownership/dedup content, since `Architectural Principles` references ownership
  concepts).
- Where the test confirms a duplicate, replace the non-canonical restatement with a
  reference and record which section was judged canonical and why.
- Where the test does not confirm a duplicate, close this issue's corresponding
  scope item with "no change — not a confirmed duplicate" and the reasoning,
  rather than forcing a stylistic merge.

## Constraints
- Do not remove or compress content solely because the source task list assumed it
  was duplicated; require a passing equivalence-test result first.
- Must preserve every requirement, condition, and exception currently stated in any
  of the three sections.

## Acceptance Criteria
- Each of the three named sections has been evaluated against the Deduplication
  Rules equivalence test, with the result (duplicate found / not found) recorded in
  the implementation's summary.
- Any confirmed duplicate is consolidated to one canonical location with a
  reference at the other location(s).
- No unconfirmed consolidation is made — every change traces to an explicit
  equivalence-test pass.

## Testing Expectations
Not required in the automated-test sense (Markdown-only investigation and, where
warranted, edit). Manual verification expected: reviewer confirms the equivalence
test was actually applied (not assumed) for each of the three sections.

## Documentation Impact
This issue is itself a documentation task. If a section is found to be
non-duplicative, no further documentation change is needed there. If a
consolidation is made, follow the same Documentation Impact pattern as
H-001/H-002/H-003 (edit in place, no other file affected unless discovered
otherwise during implementation).

## Out of Scope
- Any change to `### Step Responsibilities` / `### Tasks` (H-001),
  `### Canonical Ownership Model` / `### Deduplication Rules` acceptance criteria /
  `### Validation` (H-002), or `### Context Loader Pattern Validation` /
  `#### Step 4` (H-003) beyond using them as equivalence-test comparison targets.
- Rewriting `### Architectural Principles`, `### Normative vs. Descriptive Content`,
  or `### Canonical References` for style reasons unrelated to confirmed
  duplication.

## Dependencies
Should be implemented after H-001, H-002, and H-003 land, since those issues
change the exact wording of `### Canonical Ownership Model` and `### Validation`
that this issue's equivalence test compares against.

## Unresolved Questions
- Does any specific sentence in `### Architectural Principles`,
  `### Normative vs. Descriptive Content`, or `### Canonical References` actually
  fail the equivalence test against another section? The source task list did not
  cite specific sentence pairs; this needs to be determined during implementation,
  not assumed from the task list alone.

## AI Implementation Instruction
- Treat this issue as an investigation-first task: apply the equivalence test
  before making any edit, and be willing to report "no confirmed duplicate found"
  as a valid outcome.
- Do not delete or compress content in these three sections without a documented
  equivalence-test pass.
- Implement after H-001, H-002, and H-003 (see Dependencies).
- Do not touch sections out of scope for this issue.
- Stop and report back if the line numbers cited here no longer match the current
  file content.
