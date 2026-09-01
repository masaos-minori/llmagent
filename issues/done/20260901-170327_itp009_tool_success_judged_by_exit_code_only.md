# Tool-invocation success in Steps 5/6 is judged by exit code alone

## Priority
Medium

## Summary
`skills/issue-to-plan/workflow.md` Steps 5 and 6 describe `tools/generate_workitem.py`
success only in terms of its exit code / refusal condition, without instructing the
agent to independently verify the resulting file actually exists with the expected
content before proceeding — contrary to `rules/ai-execution.md` Repository Tool
Usage #8's own general requirement.

## Background
`rules/ai-execution.md` Repository Tool Usage #8: "Tool output MUST be verified
before relying on it as evidence. Empty standard output alone MUST NOT be treated
as proof of success — expected output files, summaries, exit results, or
repository changes MUST be independently verified."

`rules/workflow-lifecycle.md` Archival Move already follows this pattern
correctly for `git mv`: "After running the move, verify all of the following:
destination exists / source no longer exists / the move is recorded as a Git
rename or staged move."

By contrast, `workflow.md` Step 5's tool-integration text only states: "The tool
refuses (non-zero exit, no write) on a path collision rather than auto-
incrementing; treat that refusal as the trigger for the zero-padded sequence rule
above, not as a workflow failure." Step 6's parallel text is the same shape. Neither
states the success-path verification: after a `0` exit, confirm the output file
exists at the expected path and its section headings match the current template
(the same check `tests/tools/test_generate_workitem.py`'s T2 performs for the
tool itself, but nothing tells the *workflow* to re-verify this at call time).

## Problem
An agent following only the literal Step 5/6 text could treat exit code `0` as
sufficient confirmation that scaffolding succeeded, and proceed to fill in the
Plan/Unknown/Risk content without confirming the file is actually present and
correctly named — reintroducing exactly the "empty output as proof of success"
failure mode Repository Tool Usage #8 already warns against, in the one place this
workflow newly delegates a write operation to a tool instead of doing it directly
via `Write`.

## Reason for Change
The Archival Move step already models the correct pattern (verify post-conditions,
don't trust the command alone); the newer tool-scaffolding steps should follow the
same pattern for consistency and to close this specific gap.

## Implementation Intent
Add an explicit post-success verification instruction to Step 5 and Step 6's
tool-integration text: after a `0` exit from `tools/generate_workitem.py`, confirm
the reported output path exists and contains the expected section headings before
proceeding to fill in its content.

## Target Files or Areas
- `skills/issue-to-plan/workflow.md` (Step 5, Step 6)

## Required Changes
- Add a post-success file-existence/structure check to Step 5's `generate_workitem.py
  --kind plan` integration text.
- Add the same to Step 6's `--kind unknowns` / `--kind risks` integration text.

## Constraints
Keep the added check lightweight (existence + a quick structural glance, e.g. `##`
heading count) — this is not a request to duplicate `tests/tools/
test_generate_workitem.py`'s full field-order assertion inside the workflow
document.

## Acceptance Criteria
- Step 5 and Step 6 each state that a `0` exit from the tool is followed by an
  independent check that the output file exists before its content is edited.

## Testing Expectations
Manual review: confirm the added instruction is consistent with
`rules/ai-execution.md` Repository Tool Usage #8 and `rules/workflow-lifecycle.md`
Archival Move's existing verification pattern.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this mechanism.

## Out of Scope
- Changing `tools/generate_workitem.py`'s own output or exit-code behavior.
- The equivalent gap in `plan-to-implementation-procedure/workflow.md`'s own tool
  integration text, if the same gap is confirmed there — file separately.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `rules/ai-execution.md` Repository Tool Usage #8 and `rules/workflow-lifecycle.md`
Archival Move before wording the addition, and mirror their existing phrasing
("verify... exists", "independently verified") rather than introducing new
vocabulary for the same concept.
