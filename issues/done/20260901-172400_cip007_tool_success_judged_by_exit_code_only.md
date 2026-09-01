# Step 1/7 tool-invocation success is judged by exit code alone

## Priority
Medium

## Summary
`skills/code-implementation/workflow.md` Step 1's all-steps-completed move and
Step 7's final move both describe `tools/manage_workitem_stage.py
close-implementation` success only via exit code, without an explicit
post-success verification instruction for the tool-call path — the same gap as
`itp009`/`ptip008`, here for this workflow's own two invocation sites.

## Background
`rules/ai-execution.md` Repository Tool Usage #8: "Tool output MUST be verified
before relying on it as evidence... expected output files... MUST be
independently verified."

`workflow.md` Step 7: "Prefer `uv run python tools/manage_workitem_stage.py
close-implementation implementations/{filename}.md` — it performs the same `git
mv` move and refuses (non-zero exit, no move) if [conditions]... Verify the file
exists in `implementations/done/` after the move." — this Step *does* include a
post-move verification instruction ("Verify the file exists..."), unlike the
sibling workflows' equivalent Step. Step 1's all-steps-completed check, however,
only says "Move it to `implementations/done/`... Report `Moved to done:
{filename}...`" with no equivalent explicit post-move verification instruction
mirroring Step 7's.

## Problem
Step 7 already does this correctly; Step 1 does not, despite performing the exact
same kind of move via the exact same tool. This is a narrower, more localized gap
than `itp009`/`ptip008` (which found the verification step missing entirely for
their workflows) — here it is inconsistently present between two Steps in the
same file that should have identical post-move verification.

## Reason for Change
Consistency: Step 1's short-circuit move should not be held to a lower
verification standard than Step 7's final move, since both perform the identical
operation.

## Implementation Intent
Add the same "verify the file exists in `implementations/done/` after the move"
instruction to Step 1's all-steps-completed check that Step 7 already has.

## Target Files or Areas
- `skills/code-implementation/workflow.md` (Step 1)

## Required Changes
- Add a post-move existence verification instruction to Step 1's all-steps-
  completed check, mirroring Step 7's existing wording.

## Constraints
Reuse Step 7's existing phrasing rather than inventing new wording for the same
check.

## Acceptance Criteria
- Step 1's all-steps-completed check includes the same post-move verification
  instruction Step 7 already has.

## Testing Expectations
Manual review: confirm the added instruction is worded identically (or
near-identically) to Step 7's existing text.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Changing `tools/manage_workitem_stage.py`'s own behavior.

## Dependencies
Same underlying gap as `itp009` (issue-to-plan) and `ptip008`
(plan-to-implementation-procedure) — this instance is narrower since Step 7
already has the fix; only Step 1 needs it added for internal consistency.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `workflow.md` Step 1 and Step 7 in full before wording the addition. Copy
Step 7's existing "Verify the file exists in `implementations/done/` after the
move" sentence into Step 1 rather than rewording it independently.
