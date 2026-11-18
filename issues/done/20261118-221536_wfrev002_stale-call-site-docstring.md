# Correct the stale `pending_tool_calls` docstring that claims a production caller it does not have

## Priority
Low

## Summary
Rewrite the docstring of `pending_tool_calls` (`scripts/agent/workflow/tool_call_state_ops.py`) so it stops asserting that the turn-entry detection path calls it. The engine detects stale pending tool calls through `classify_stale_pending`, and `pending_tool_calls` has no caller in `scripts/`. Fix only the docstring; leave the function itself as-is unless a follow-up removes it.

## Background
`tool_call_state_ops.pending_tool_calls` documents itself as "The only method the turn-entry detection path (workflow_engine) calls; kept cheap via the ``idx_tool_call_state_task_state`` index." That description is false on two counts. The turn-entry detection path in `scripts/agent/workflow/workflow_engine.py:180` calls `self._store.classify_stale_pending(task_id, timeout_seconds)`, not `pending_tool_calls`. And a repository-wide grep finds zero callers of `pending_tool_calls` inside `scripts/`; only `tests/agent/workflow/test_workflow_state_store.py` invokes it. `issues/done/20261107-203222_wfaudit009_test-only-state-helpers.md` already established that `pending_tool_calls` is test-only (five test sites, zero in `scripts/`), but that issue scoped the fix to removing or wiring the helper, not to correcting the ops-level docstring that still names a nonexistent production caller.

## Problem
The docstring points future readers and agents at a call edge that does not exist. Anyone tracing "who detects stale pending tool calls" from this docstring will land on `pending_tool_calls`, which is never called in production, instead of the real entry point `classify_stale_pending`. The mismatch is purely documentary; no behavior depends on it.

## Reason for Change
Doc/code mismatches compound: the next person who removes this test-only helper (a natural follow-up to wfaudit009) inherits a docstring that blames a wrong caller, and any agent following the docstring wastes time on a dead path. It is a small, self-contained correction with no behavioral risk.

## Implementation Intent
Update the `pending_tool_calls` docstring to describe reality: it returns a task's pending tool-call rows oldest-first and is exercised by tests, while the turn-entry stale-detection path uses `classify_stale_pending`. Do not rename the function, change its signature, or wire it into production here — those belong to a separate test-only-helper cleanup if the owner chooses it. Reference the real caller (`classify_stale_pending`) only to correct the record, not to imply `pending_tool_calls` is production-used.

## Target Files or Areas
- `scripts/agent/workflow/tool_call_state_ops.py` (docstring only)
- No test changes required.

## Required Changes
- Rewrite the `pending_tool_calls` docstring so it no longer claims the turn-entry detection path calls it.
- State accurately that the function returns pending rows oldest-first and is used by tests; point to `classify_stale_pending` as the actual stale-detection entry point if a cross-reference adds clarity.
- Leave the function body, signature, and the `idx_tool_call_state_task_state` index reference accurate.

## Constraints
- Behavior must be unchanged: this is a docstring-only edit.
- Do not remove `pending_tool_calls` or retarget its test callers; that is a separate test-only-helper decision.
- Do not touch `classify_stale_pending` or any other function.

## Acceptance Criteria
- A grep for `pending_tool_calls` in `scripts/` still shows zero production callers.
- The docstring no longer states that the turn-entry detection path (or the engine) calls `pending_tool_calls`.
- No test fails; the function remains importable and tested.

## Testing Expectations
Not required. Docstring-only change with no behavior impact; ruff/mypy clean on the touched file is sufficient.

## Documentation Impact
This is the documentation change: correct one code docstring so it matches the code. No operator-facing docs are affected.

## Out of Scope
- Removing or wiring `pending_tool_calls` into production (separate test-only-helper issue).
- Changing `classify_stale_pending`, `workflow_engine.py`, or any caller.
- Renaming the function or changing its return contract.

## Dependencies
- Context (not blocking): `issues/done/20261107-203222_wfaudit009_test-only-state-helpers.md` established that `pending_tool_calls` is test-only; this issue only corrects the docstring that wfaudit009 left in place. If wfaudit009's follow-up later removes the function, this issue becomes moot and should be closed.

## Unresolved Questions
- N/A: none. The docstring fix is unambiguous once the real call graph is confirmed.

## AI Implementation Instruction
Docstring-only refactor. Edit only `scripts/agent/workflow/tool_call_state_ops.py`'s `pending_tool_calls` docstring to stop claiming a production caller. Do not change the function body, signature, imports, or any other file. Verify with ruff/mypy; no tests needed.

## Traceability
- **Workflow phase**: `python-code-review` (review of `scripts/agent/workflow/` and the `workflow_engine_adapter.py` integration), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261118-221536
- **Related target files**: `scripts/agent/workflow/tool_call_state_ops.py`
