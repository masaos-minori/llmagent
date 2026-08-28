# DOC-003: resource_scope.py module docstring still says `_scopes_conflict()` is "not wired up yet"

## Priority
Low

## Summary
`scripts/shared/resource_scope.py`'s module docstring states that `_scopes_conflict()` is
"consumed later by `scripts/agent/tool_scheduler.py`'s conflict-graph grouping (not wired up
yet)." This is stale: `tool_scheduler.py` already imports and calls `_scopes_conflict()` to build
the conflict-graph groups it describes. Update the comment to match current implementation.

## Background
N/A: covered by Summary

## Problem
`scripts/shared/resource_scope.py` line 8-9 (module docstring):

    `_scopes_conflict()` is the overlap predicate consumed later
    by `scripts/agent/tool_scheduler.py`'s conflict-graph grouping (not wired up yet).

`scripts/agent/tool_scheduler.py` line 42 imports `_scopes_conflict` directly
(`from shared.resource_scope import _scopes_conflict`) and calls it at line 171 inside the
function that partitions a phase's calls into conflict-graph groups, exactly the usage the
docstring describes as still pending. The "(not wired up yet)" qualifier is therefore incorrect
under the current implementation.

## Reason for Change
A stale "not wired up yet" note on a function that is in fact load-bearing for the scheduler's
conflict-graph grouping can mislead a future reader (human or AI) into believing the function is
dead code or still pending integration, when it is an active dependency of
`tool_scheduler.py::build_execution_groups()`'s conflict detection.

## Implementation Intent
Comment-only change in `scripts/shared/resource_scope.py`'s module docstring. Remove or replace
the "(not wired up yet)" qualifier so the docstring states that `_scopes_conflict()` is used by
`tool_scheduler.py`'s conflict-graph grouping, without a stale pending/future-tense qualifier.
No other part of the docstring or any code needs to change — the function's own docstring
(directly above its definition) is already accurate and does not need edits.

## Target Files or Areas
- `scripts/shared/resource_scope.py` (module docstring, confirmed stale line)

## Required Changes
- Update the module docstring's `_scopes_conflict()` sentence to state it is used (not "not
  wired up yet") by `scripts/agent/tool_scheduler.py`'s conflict-graph grouping.

## Constraints
Comment-only change: do not modify any executable code, function signature, or behavior in
`scripts/shared/resource_scope.py` or `scripts/agent/tool_scheduler.py`.

## Acceptance Criteria
- `scripts/shared/resource_scope.py`'s module docstring no longer states or implies that
  `_scopes_conflict()` is unused or pending integration.
- No functional code changes are present in the diff — comment/docstring text only.

## Testing Expectations
Not required — comment-only change with no behavior impact.

## Documentation Impact
None expected. `docs/04_mcp_03_01_dispatch-and-routing.md` and
`docs/05_agent_06_01_tool-execution-and-approval-execution.md` already correctly describe
`_scopes_conflict()` as the active conflict predicate used by the scheduler; neither repeats the
stale "not wired up" claim, so no design-doc update is needed alongside this comment fix.

## Out of Scope
- Do not change `_scopes_conflict()`'s logic, signature, or the function-level docstring directly above its definition.
- Do not modify `scripts/agent/tool_scheduler.py`.
- Do not update the design docs listed above — they are already accurate.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Edit only the module-docstring sentence in `scripts/shared/resource_scope.py` that currently
reads "...conflict-graph grouping (not wired up yet)." Confirm before editing that
`scripts/agent/tool_scheduler.py` still imports and calls `_scopes_conflict()`
(`grep -n "_scopes_conflict" scripts/agent/tool_scheduler.py`) so the replacement wording matches
current usage. Do not touch any other line in the file or any other file.
