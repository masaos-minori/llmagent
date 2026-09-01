# Rollback Directive's application to Plan-document corrections is undefined

## Priority
Medium

## Summary
`AGENTS.md`'s Rollback Directive ("revert the code to its pre-modification state...
before considering the next approach") is written for code changes (`git checkout`)
and never states how, or whether, it applies to `skills/issue-to-plan/workflow.md`
Step 3's Plan-document corrections — leaving open whether a Plan correction that
turns out wrong should be reverted, and if so, how that interacts with the same
correction being re-attempted.

## Background
`AGENTS.md` Loop Prevention > Rollback Directive: "If a proposed fix increases
errors or fails to resolve the issue, revert the code to its pre-modification state
(e.g., `git checkout`) before considering the next approach. Do not accumulate
destructive changes."

`workflow.md` Step 3 (this is `plan-to-implementation-procedure`'s Step 3, but
`issue-to-plan`'s own Step 2/Step 8 correction flow is the same shape): "If
adversarial verification finds an unconfirmed item or an inconsistency..., correct
the [Plan] document itself... via Edit... rather than silently working around the
discrepancy."

`issue-to-plan/workflow.md` Step 2: "...classify it per the rule above... and write
the corrected understanding into the Plan (Step 5)..." — i.e. corrections flow
*into* the Plan as it is being written, not as a later revert-and-redo cycle. But
Step 8 (information-completeness validation) can also surface a correction need
*after* the Plan already exists, and at that point the "Rollback Directive" framing
(revert, then try a different approach) becomes ambiguous: does "revert" mean
discard the Plan edit that Step 8 flagged as wrong, going back to the Plan's
prior (also wrong, since Step 8 flagged it) state? That is not an improvement.

## Problem
`AGENTS.md`'s Rollback Directive is stated in code-modification terms (`git
checkout`, "the code") with no explicit statement of how it maps onto a
document-only phase's Edit-based corrections. Two readings are both plausible from
the current text, with materially different behavior:
1. Rollback does not apply to document-only phases at all (Plan edits are
   corrections, not "fixes" in the code sense, so there is nothing to revert).
2. Rollback applies literally: a Plan edit that turns out wrong must be reverted
   (e.g. via `git checkout -- plans/{file}.md` if uncommitted, or a manual undo)
   before the next correction attempt.

Reading 2, taken literally, risks an unproductive revert-and-redo loop: Step 8
flags an issue → the Step 3/Step 2-originated correction is reverted per Rollback
Directive → the same underlying evidence is re-examined → the same correction is
written again (since the evidence has not changed) → Step 8 flags it again if the
correction was actually right, or a different correction is tried if it was wrong.
Nothing in `workflow.md` states which of these outcomes is expected, or how many
revert-redo cycles are tolerated before escalating.

## Reason for Change
Without an explicit statement, two different agents (or the same agent on two
different runs) could resolve a Step 8 correction-need differently — one silently
skipping Rollback Directive as "not applicable here", another applying it literally
and potentially looping. Making the intended behavior explicit removes this
ambiguity and prevents the loop scenario described above.

## Implementation Intent
Add an explicit statement to `skills/issue-to-plan/workflow.md` (near Step 8, or in
a shared note referenced by both `issue-to-plan` and `plan-to-implementation-procedure`)
clarifying: (a) whether `AGENTS.md`'s Rollback Directive applies to Plan-document
Edit corrections in this workflow, and (b) if it does, what "revert" concretely
means for a Markdown document under active revision (e.g. "revert" means restoring
the specific field/section text that regressed the failure, not necessarily via
`git checkout`, since the file may be uncommitted and Step 8 may need surrounding,
still-correct edits preserved).

## Target Files or Areas
- `skills/issue-to-plan/workflow.md` (Step 8, or a new short note near it)
- `rules/workflow-lifecycle.md` (if the clarification belongs at the shared-rule
  level, since `plan-to-implementation-procedure` has the same correction shape)

## Required Changes
- State explicitly whether `AGENTS.md` Rollback Directive applies to this
  workflow's Plan-document corrections.
- If it applies, define what "revert" means for a document Edit (not a code
  change) and what constitutes "considering the next approach" in that context.
- If it does not apply, state the explicit exception per `rules/ai-execution.md`
  Instruction Precedence > Explicit exceptions (cite the overridden rule by name).

## Constraints
Any exception declared here must follow `rules/ai-execution.md` Instruction
Precedence's requirement that a narrower layer "MAY declare an exception to a
broader rule only by stating it explicitly... and referencing the overridden rule"
— this issue's fix must not silently ignore `AGENTS.md` without that explicit
cross-reference.

## Acceptance Criteria
- `workflow.md` (or the shared rule file) states explicitly whether and how
  Rollback Directive applies to Plan-document corrections.
- The statement resolves the revert-redo loop scenario described in Problem —
  either by ruling it out (Rollback does not apply) or by bounding it (a stated
  retry/escalation limit consistent with `itp003`'s Attempt Limit question).

## Testing Expectations
Manual review: confirm the added clarification is unambiguous and does not
introduce a contradiction with `AGENTS.md` Instruction Precedence.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this mechanism.

## Out of Scope
- Changing `AGENTS.md`'s Rollback Directive itself.
- Resolving the identical question for `code-implementation`'s own "Rollback on
  Failure" section, which already explicitly addresses code reverts for that
  (different, code-modifying) phase and is not in scope here.

## Dependencies
Related to `itp003` (Attempt Limit for retries) and `itp011` (chained corrections) —
the same underlying "how many correction cycles are tolerated" question surfaces in
all three; resolve consistently, but each may be implemented independently.

## Unresolved Questions
- Whether the correct answer is "Rollback Directive does not apply to document-only
  phases" (simplest, and arguably already implied by `AGENTS.md`'s code-specific
  wording) or a document-specific redefinition — left to implementation planning.

## AI Implementation Instruction
Read `AGENTS.md` Loop Prevention in full, and `skills/issue-to-plan/workflow.md`
Step 2/Step 3/Step 8, before proposing the clarification. Prefer the simplest
resolution that removes the ambiguity (e.g. an explicit "does not apply" statement
with justification) over inventing a new, document-specific rollback procedure
unless the evidence shows the simple resolution is insufficient.
