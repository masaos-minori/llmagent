# Step 3/Step 4 tool-invocation success is judged by exit code alone

## Priority
Medium

## Summary
`skills/plan-to-implementation-procedure/workflow.md` Step 3's
`tools/generate_workitem.py --kind implementation-procedure` integration and
Step 4's `tools/manage_workitem_stage.py close-plan` integration both describe
success only via exit code / refusal condition, without instructing the agent to
independently verify the resulting artifact (file existence, or the Plan's
`done/` relocation) before proceeding — the same gap as `itp009`, but for this
workflow's own tool calls.

## Background
`rules/ai-execution.md` Repository Tool Usage #8: "Tool output MUST be verified
before relying on it as evidence. Empty standard output alone MUST NOT be treated
as proof of success — expected output files, summaries, exit results, or
repository changes MUST be independently verified."

`workflow.md` Step 3's tool text: "it reproduces `templates/implementation-
procedure.md`'s current field order exactly, computes `target_file_slug` per the
naming rule above, and shares this pass's timestamp automatically..." — describes
what the tool does on success, but not what the workflow should independently
verify afterward.

`workflow.md` Step 4's tool text: "it performs the same move and refuses
(non-zero exit, no move) if [conditions]." — again describes the refusal path in
detail, but not the post-success verification for the success path, unlike
`rules/workflow-lifecycle.md` Archival Move's existing "After running the move,
verify... destination exists / source no longer exists / recorded as a Git
rename" pattern, which this Step's manual `git mv` fallback already inherits by
reference but the tool-call path does not restate.

## Problem
An agent could treat a `0` exit from either tool call as sufficient, skipping the
destination-existence check that `rules/workflow-lifecycle.md` Archival Move
already requires for the manual `git mv` path — reintroducing the "empty output as
proof of success" failure mode specifically for the newer tool-delegated paths.

## Reason for Change
Same reasoning as `itp009`, applied to this workflow's own two tool integrations
(Step 3's document generation, Step 4's archival move) rather than
`issue-to-plan`'s.

## Implementation Intent
Add an explicit post-success verification instruction to both Step 3's and Step
4's tool-integration text: after a `0` exit, confirm the expected artifact
(generated file at Step 3; destination existence + source absence at Step 4)
independently, following the same pattern `rules/workflow-lifecycle.md` Archival
Move already specifies for the manual path.

## Target Files or Areas
- `skills/plan-to-implementation-procedure/workflow.md` (Step 3, Step 4)

## Required Changes
- Add a post-success file-existence check to Step 3's `generate_workitem.py`
  integration text.
- Add an explicit restatement (or cross-reference) of `rules/workflow-lifecycle.md`
  Archival Move's post-move verification checklist to Step 4's
  `manage_workitem_stage.py close-plan` integration text, so it is not implied only
  by the fallback `git mv` path.

## Constraints
Keep the added checks lightweight and consistent with `itp009`'s phrasing for the
sibling workflow, for consistency across the pipeline.

## Acceptance Criteria
- Step 3 states that a `0` exit is followed by an independent file-existence
  check.
- Step 4 states that the tool-call path is followed by the same post-move
  verification checklist the manual `git mv` path already requires.

## Testing Expectations
Manual review: confirm the added instructions are consistent with `itp009`'s
phrasing and with `rules/workflow-lifecycle.md` Archival Move.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Changing either tool's own output or exit-code behavior.

## Dependencies
Same underlying gap as `itp009` (issue-to-plan's equivalent) — resolve
consistently if practical; each is independently implementable since they target
different `workflow.md` files.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `rules/ai-execution.md` Repository Tool Usage #8 and `rules/workflow-lifecycle.md`
Archival Move before wording the additions, and mirror `itp009`'s phrasing for
consistency across the two workflows.
