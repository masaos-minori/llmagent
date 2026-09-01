# Rollback Directive's application to Step 3's Plan-document corrections is undefined

## Priority
Medium

## Summary
`AGENTS.md`'s Rollback Directive ("revert the code to its pre-modification state...
before considering the next approach") is written for code changes and never
states how it applies to `skills/plan-to-implementation-procedure/workflow.md`
Step 3's Plan-document corrections — the same gap `itp004` identifies for
`issue-to-plan`, applying here with an additional wrinkle: Step 3 also allows the
same tool call (`tools/generate_workitem.py --kind implementation-procedure`) to
append a durable marker to the Plan file, which a naive "revert the Plan document"
action could destroy.

## Background
`AGENTS.md` Loop Prevention > Rollback Directive: "If a proposed fix increases
errors or fails to resolve the issue, revert the code to its pre-modification
state (e.g., `git checkout`) before considering the next approach."

`workflow.md` Step 3: "If adversarial verification finds an unconfirmed item or an
inconsistency..., correct the Plan document itself (`plans/{filename}_plan.md`,
via Edit) in the same cycle..."

Separately, `workflow.md` `Allowed file operations` documents that
`tools/generate_workitem.py --kind implementation-procedure` "appends a
timestamp-marker HTML comment to the Plan file being processed" as a side effect
of Step 3's tool-assisted document generation. If a Rollback Directive-style
`git checkout -- plans/{filename}_plan.md` were applied to undo a bad correction,
it would also discard this timestamp marker, breaking the very mechanism this
session's own tool-integration work added to keep timestamps consistent across
repeated invocations in the same pass.

## Problem
Same ambiguity as `itp004` (does Rollback Directive apply to document-only Plan
edits at all, and if so, what does "revert" concretely mean), plus a
workflow-specific complication: a literal revert-via-`git checkout` would also
undo the timestamp marker the tool relies on, potentially causing the *next*
`generate_workitem.py --kind implementation-procedure` call (for a still-pending
row) to mint a *new*, different timestamp instead of reusing the pass's original
one — silently breaking the "one shared timestamp per pass" guarantee Step 3
otherwise depends on.

## Reason for Change
This workflow's Rollback Directive ambiguity has a concrete failure mode
(`itp004`'s issue-to-plan version does not, since that workflow has no equivalent
marker mechanism) that should be called out explicitly rather than left to be
discovered the first time a revert actually happens mid-pass.

## Implementation Intent
Resolve the same question as `itp004` for this workflow (does Rollback Directive
apply; if so, what does "revert" mean for a Plan-document Edit), and additionally
state that any revert of `plans/{filename}_plan.md` during an active Step 3 pass
MUST preserve the existing timestamp-marker line (re-add it if a full-file revert
removed it) rather than letting it silently regenerate with a new value.

## Target Files or Areas
- `skills/plan-to-implementation-procedure/workflow.md` (Step 3, or a new short
  note near Allowed file operations)

## Required Changes
- State explicitly whether `AGENTS.md` Rollback Directive applies to this
  workflow's Plan-document corrections (same question as `itp004`, this
  workflow's file).
- If it applies, state the timestamp-marker preservation requirement explicitly.

## Constraints
Follow `rules/ai-execution.md` Instruction Precedence's requirement that any
declared exception cite the overridden rule explicitly (same constraint `itp004`
already states).

## Acceptance Criteria
- `workflow.md` states explicitly whether and how Rollback Directive applies to
  Plan-document corrections in this workflow.
- If a revert scenario is retained as valid, the workflow states the
  timestamp-marker preservation requirement.

## Testing Expectations
Manual review: confirm the resolution is consistent with `itp004`'s resolution for
the sibling workflow, and that the timestamp-marker preservation requirement (if
added) does not contradict `tools/generate_workitem.py`'s documented behavior.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Changing `AGENTS.md`'s Rollback Directive itself (same scope boundary as
  `itp004`).
- Changing `tools/generate_workitem.py`'s marker-writing behavior.

## Dependencies
Directly related to `itp004` — resolve the core question (does Rollback Directive
apply to document-only Plan edits) consistently across both issues; this issue
adds the timestamp-marker-preservation requirement specific to this workflow.

## Unresolved Questions
Same as `itp004`: whether "does not apply" or a redefined document-specific
rollback is the right resolution — left to implementation planning, resolved
consistently with `itp004`.

## AI Implementation Instruction
Read `itp004`'s issue body (`issues/20260901-170327_itp004_rollback_directive_undefined_for_plan_documents.md`)
before implementing this one, and resolve the core question the same way for
both. Additionally verify `tools/generate_workitem.py`'s current marker format
(`_PASS_TIMESTAMP_MARKER_RE` in `tools/generate_workitem.py`) before wording the
preservation requirement, so the requirement's wording matches the tool's actual
marker syntax.
