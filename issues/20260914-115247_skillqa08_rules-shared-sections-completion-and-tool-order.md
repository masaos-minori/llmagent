# Add completion conditions and explicit tool-order guidance to rules/ai-execution.md and rules/toolchain.md shared sections

## Priority
Medium

## Summary
`rules/ai-execution.md`'s "Tool Usage" and "Step-Level Failure Triage (Base)" sections, and `rules/toolchain.md`'s standard 9-step validation sequence, are applied by nearly every skill in this project but state no completion condition of their own, and `rules/ai-execution.md`'s "Repository Tool Usage" (12 numbered items) does not state whether the numbering reflects required execution order.

## Background
This issue follows a skill/workflow design review (5 evaluation criteria, 55 files) requested and conducted in this session. These two files are the most widely-shared base rules referenced by nearly every skill reviewed, so a gap here has broader downstream effect than the same gap in one skill's own workflow.

## Problem
Confirmed by direct reading:
- `rules/ai-execution.md` "Tool Usage" (lines 111-125): a set of bullet rules (batch independent calls, don't repeat unchanged commands, etc.) with no stated condition for "this section's guidance has been correctly applied."
- `rules/ai-execution.md` "Step-Level Failure Triage (Base)" (98-109): three branches (tool unavailable / task-caused failure / pre-existing failure) with no completion condition for the section as a whole (contrast with `rules/workflow-lifecycle.md`'s Completion Criteria / Correction-and-Recheck Cycle Bound, cited by the same review as a good model).
- `rules/ai-execution.md` "Repository Tool Usage" (151-201): 12 numbered items presented as a flat list; it is not stated whether the numbering is the required execution order, or whether items with no dependency between them may be checked in any order.
- `rules/toolchain.md`'s "Standard validation sequence" (9 numbered steps): each step names its own command, but the file does not state, as a whole, how many fix-and-recheck attempts are permitted before stopping — it currently relies on skills that reference it to supply that bound individually (which several do consistently via `AGENTS.md` Loop Prevention, but the base file itself does not state this).

## Reason for Change
Because these sections are the shared foundation nearly every skill's own workflow builds on, an ambiguity here (e.g. "is item 5 required before item 3, or are they independent?") propagates into every skill that references `rules/ai-execution.md` Repository Tool Usage, rather than being contained to one file.

## Implementation Intent
Add a completion condition to "Tool Usage" and "Step-Level Failure Triage (Base)"; add an explicit statement to "Repository Tool Usage" clarifying whether its 12 items are ordered or independent; add a cross-reference in `rules/toolchain.md`'s standard sequence to `AGENTS.md` Loop Prevention's Attempt Limit as the sequence's own retry bound, rather than leaving it to be supplied ad hoc by each referencing skill.

## Target Files or Areas
- `rules/ai-execution.md`
- `rules/toolchain.md`

## Required Changes
- `rules/ai-execution.md` "Tool Usage": add "Completed when: no available information already answers the question, calls have been batched where independent, and no unchanged command was re-run against the same input."
- `rules/ai-execution.md` "Step-Level Failure Triage (Base)": add "Completed when: the failing check's cause has been classified into exactly one of the three branches above and the corresponding action (continue, fix, or record-and-continue) has been taken."
- `rules/ai-execution.md` "Repository Tool Usage": add a note stating whether items 1-12 must be applied in the listed order, or whether some (name specifically, if determinable from the existing item dependencies — e.g. item 1's "inspect `tools/` first" logically precedes items that assume a tool has already been selected) are independent and may be checked in any order.
- `rules/toolchain.md` "Standard validation sequence": add a line stating the sequence's own retry bound by cross-reference: "Apply `AGENTS.md` Loop Prevention > Attempt Limit (3 attempts) to any step that fails and is fixed in place before re-running; stop and report `Blocked` rather than continuing to patch beyond that bound."

## Constraints
Do not introduce a retry-bound value different from `AGENTS.md`'s existing 3-attempt Loop Prevention rule — cross-reference it, don't restate a new number.

## Acceptance Criteria
- "Tool Usage" and "Step-Level Failure Triage (Base)" in `rules/ai-execution.md` each have an explicit "Completed when" line.
- "Repository Tool Usage" states explicitly whether its 12 items are ordered or independent.
- `rules/toolchain.md`'s standard sequence cross-references `AGENTS.md` Loop Prevention's Attempt Limit as its own retry bound.
- `tools/check_skills_references.py` still passes.

## Testing Expectations
Not applicable — prose-only rule files. Run `tools/check_skills_references.py` per `routing.md`'s relevant row.

## Documentation Impact
This issue's entire scope is `rules/ai-execution.md` and `rules/toolchain.md`.

## Out of Scope
- Any other section of `rules/ai-execution.md` (e.g. Context Reading, Instruction Precedence, Adversarial Verification, Progress Reporting) — these already state adequate completion conditions or are inherently descriptive rather than procedural, per this review.
- Any other evaluation criterion from the same review — tracked in separate issues.

## Dependencies
N/A: none.

## Unresolved Questions
Whether all 12 "Repository Tool Usage" items have a genuine ordering dependency, or only a subset do — resolve during implementation by re-reading each item's actual content rather than assuming full ordering or full independence without checking.

## AI Implementation Instruction
Add only the four items described in Required Changes; do not restructure the surrounding sections. For "Repository Tool Usage," read each of the 12 items' actual content before deciding which (if any) have a genuine ordering dependency — do not assume full ordering or full independence without checking.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-115247
- **Related target files**: rules/ai-execution.md, rules/toolchain.md
