# No mechanism to identify a repeated identical command and reuse its result

## Priority
Low

## Summary
`rules/ai-execution.md` Tool Usage states "Do not repeat a command when neither
its input nor the environment has changed," but defines no mechanism for
determining what counts as the same "input"/"environment," where a prior result
would be recorded to compare against, or how a workflow like `issue-to-plan`
(which processes multiple Issues that may reference the same source files) should
detect and skip a redundant re-run.

## Background
`rules/ai-execution.md` Tool Usage: "Do not repeat a command when neither its
input nor the environment has changed." This is the only statement on this topic;
no companion mechanism exists.

`rules/ai-execution.md` Context Reading separately states: "Reuse a verified fact
only while its source file is unchanged. Store the source path and evidence
location with each cached fact, and recheck it after the source changes." This
defines a caching mechanism for *facts* (the conclusions drawn from a file), but
`skills/issue-to-plan/workflow.md`'s Multi-file processing explicitly forbids
carrying investigation *across* Issue cycles ("investigation MUST NOT carry from
one file's cycle into the next; cycles MUST run one at a time") — which appears to
foreclose reusing a Context-Reading-cached fact from a prior Issue's cycle even
when the underlying source file is genuinely unchanged and the same command would
be run again in Step 3.

## Problem
Two of the workflow's own rules point in different directions for the common case
of two Issues in the same batch both naming the same target module:
- Tool Usage says not to repeat the identical command.
- Multi-file processing says investigation must not carry across cycles.

Neither states how to reconcile them: is "the identical `rg` search over
`scripts/agent/foo.py` in Issue B's Step 3" a forbidden carry-over (per Multi-file
processing) or a redundant repeat that should be skipped (per Tool Usage)? As
written, the literal, safe reading is "run it again for Issue B" (satisfying
Multi-file processing's isolation requirement), which means Tool Usage's "do not
repeat" guidance has no defined mechanism to actually apply within this workflow —
it is aspirational, not actionable.

## Reason for Change
Leaving this unresolved means the "do not repeat a command" principle is
effectively inert for the one workflow (`issue-to-plan`'s Multi-file processing)
where repeated commands across cycles are most likely to occur, and any future
attempt to implement caching risks silently violating the cycle-isolation
requirement Multi-file processing exists to enforce.

## Implementation Intent
Clarify, in `rules/ai-execution.md` Tool Usage or in `skills/issue-to-plan/
workflow.md` Multi-file processing, how the two rules interact: e.g. state that
Multi-file processing's isolation requirement is about *conclusions/investigation
state* carrying over (which remains forbidden), not about *re-running an identical,
side-effect-free read-only command* against an unchanged file (which Tool Usage's
"do not repeat" may still apply to, provided the command's output is re-verified
fresh each cycle per `rules/ai-execution.md` Repository Tool Usage #8, not silently
reused from a stale cache).

## Target Files or Areas
- `rules/ai-execution.md` (Tool Usage)
- `skills/issue-to-plan/workflow.md` (Multi-file processing)

## Required Changes
- State explicitly whether "do not repeat a command" can apply across separate
  target-file cycles in a Multi-file-processing workflow, or only within a single
  cycle.
- If it can apply across cycles, define what "unchanged input/environment" means
  concretely enough to check (e.g. same file path + same file mtime/git-blob-hash +
  same command string).

## Constraints
Any resolution must not weaken Multi-file processing's existing isolation
requirement — cross-cycle *investigation conclusions* must still not carry over;
only a candidate re-run of an identical, read-only, side-effect-free command is in
scope for potential reuse.

## Acceptance Criteria
- `rules/ai-execution.md` and/or `workflow.md` state explicitly how "do not repeat
  a command" and cycle-isolation interact, resolving the ambiguity described in
  Problem.

## Testing Expectations
Manual review: confirm the added clarification does not weaken Multi-file
processing's cycle-isolation requirement.

## Documentation Impact
N/A: internal shared-rule fix; no `docs/*.md` file describes this mechanism.

## Out of Scope
- Building an actual caching implementation (this issue is a documentation/
  clarification fix, not a tooling change).

## Dependencies
N/A: none.

## Unresolved Questions
- Whether the reconciliation should favor "always allow reuse of read-only command
  results across cycles" or "never allow it, treat Tool Usage's rule as
  within-cycle only" — left to implementation planning, but the current silence
  must be resolved one way or the other.

## AI Implementation Instruction
Read `rules/ai-execution.md` Tool Usage, Context Reading, and Repository Tool
Usage, and `skills/issue-to-plan/workflow.md` Multi-file processing, in full before
proposing the reconciliation. Prefer the more conservative resolution (isolation
wins; "do not repeat" applies only within one cycle) unless a concrete case shows
material cost from not reusing across cycles.
