# Step 3/4 fix-loops and Rollback on Failure are not connected to Attempt Limit

## Priority
High

## Summary
`skills/code-implementation/workflow.md` Step 3 ("Fix all errors before proceeding
to Step 4") and Step 4 ("fix all related failures") each describe an implicit
fix-and-recheck loop with no stated iteration bound, and the separate "Rollback on
Failure" section's "revert changes immediately... Do not proceed until the issue
is resolved" does not state what happens after a revert — try a different
approach up to some limit, or stop and escalate. Neither is connected to
`AGENTS.md`'s Attempt Limit (3 attempts for the same error), which is precisely the
rule meant to bound this kind of loop.

## Background
`workflow.md` Step 3: "After implementing: Run repository-defined non-test
validation: formatting, linting, type checking, architecture/import-boundary
checks, security checks. Fix all errors before proceeding to Step 4." No stated
bound on how many fix-and-rerun cycles this may take.

`workflow.md` Step 4: "Run targeted tests during implementation; fix all related
failures." Same shape — no stated bound.

`workflow.md` "Rollback on Failure": "If implementation breaks existing
functionality, revert changes immediately and report `Blocked: {description}`. Do
not proceed until the issue is resolved." This states the revert action but not
what comes after it — attempt a different approach (bounded how many times?), or
stop for human input immediately.

`AGENTS.md` Loop Prevention > Attempt Limit: "Maximum 3 attempts for the same
error. After 3 failures, stop executing and report a summary of 'what was tried
and what failed' to the user — do not continue blindly." This is the rule that
should govern exactly this situation, but `workflow.md` never cites it.

`AGENTS.md` Loop Prevention > Prohibit Repeating Failed Approaches and Failure Log
are also directly relevant (reassess prerequisites after one failure; log
attempted approach + error + reason to avoid duplicating a failed approach) and
are likewise never cited from `workflow.md`.

## Problem
This is the code-implementation-specific instance of a gap `itp003`/`ptip007` also
raise for their own workflows, but it is more consequential here because Step 3/
Step 4 actually modify source code and run real validation/test commands — an
unbounded "fix and recheck" loop here has real time/token cost and real risk of
accumulating partial, inconsistent code changes if each fix attempt is not
tracked against a Failure Log per `AGENTS.md`. Without an explicit citation of
Attempt Limit and Failure Log, an agent could iterate on the same lint/test
failure indefinitely, or repeat a failed approach because nothing forced
consulting a record of what was already tried.

## Reason for Change
`code-implementation` is the one phase in this pipeline that actually performs
the code modification AGENTS.md's Loop Prevention section is written for — it is
the most direct, natural place to apply Attempt Limit, Prohibit Repeating Failed
Approaches, and Failure Log explicitly, yet it is currently the phase that omits
citing them.

## Implementation Intent
Add explicit citations to `AGENTS.md` Loop Prevention (Attempt Limit, Prohibit
Repeating Failed Approaches, Failure Log) in Step 3's and Step 4's fix-loop text,
and in "Rollback on Failure," stating: (a) the same error/failure may be attempted
at most 3 times before stopping per Attempt Limit; (b) each failed attempt must be
recorded per Failure Log's fields (approach, error, reason) before trying a
different approach; (c) after Attempt Limit is reached, "Rollback on Failure"'s
revert-and-report action is the required outcome, not an optional one.

## Target Files or Areas
- `skills/code-implementation/workflow.md` (Step 3, Step 4, Rollback on Failure)

## Required Changes
- Cite `AGENTS.md` Attempt Limit explicitly in Step 3's and Step 4's fix-loop
  text, stating the 3-attempt bound applies to each distinct error/failure.
- Cite `AGENTS.md` Failure Log explicitly, requiring each failed attempt be
  recorded before a different approach is tried.
- Amend "Rollback on Failure" to state that reaching Attempt Limit is what
  triggers the revert-and-report action (closing the "what happens next" gap),
  rather than leaving the revert trigger as only "breaks existing functionality."

## Constraints
Do not weaken the existing, correct instruction to fix all errors before Step 4 —
this issue adds a bound and a record-keeping requirement to that instruction, not
a way to skip validation.

## Acceptance Criteria
- Step 3 and Step 4 each cite Attempt Limit's 3-attempt bound explicitly for their
  respective fix loops.
- "Rollback on Failure" states the Failure Log requirement and clarifies that
  reaching Attempt Limit (not only "breaks existing functionality") triggers the
  revert-and-report action.

## Testing Expectations
Manual review: confirm the added citations are consistent with `AGENTS.md`'s
existing wording and do not introduce a second, conflicting attempt-count rule.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Changing `AGENTS.md`'s Attempt Limit, Failure Log, or Rollback Directive
  themselves.

## Dependencies
Related to `itp003`/`itp004`/`itp011` and `ptip007`/`ptip009` (the same
Attempt-Limit/Rollback ambiguity raised for `issue-to-plan` and
`plan-to-implementation-procedure`) — this is the `code-implementation`-specific
instance, most directly relevant since this phase actually modifies code.
Implement independently.

## Unresolved Questions
N/A: none — `AGENTS.md`'s Attempt Limit and Failure Log are already fully
specified; this issue only requires citing and connecting them.

## AI Implementation Instruction
Read `AGENTS.md` Loop Prevention in full (all four subsections: Prohibit
Repeating Failed Approaches, Attempt Limit, Hypothesis Before Action, Failure
Log) and `workflow.md` Step 3, Step 4, and Rollback on Failure, before wording the
citations. Cite the specific `AGENTS.md` subsection names rather than
paraphrasing them, so the connection is unambiguous.
