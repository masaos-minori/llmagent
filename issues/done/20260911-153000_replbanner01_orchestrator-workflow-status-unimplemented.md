# StartupBanner's workflow-tracking status always reports "not loaded" (Orchestrator.workflow_status() doesn't exist)

## Priority
Low

## Summary
`StartupBanner._get_workflow_status()` (`scripts/agent/startup_banner.py`) is
meant to show the startup banner's workflow-tracking status as "enabled",
"not loaded", or "unknown" depending on the running `Orchestrator`'s state,
but `Orchestrator` has no `workflow_status()` method anywhere in the current
codebase. The banner therefore always reports "not loaded" once an
orchestrator instance exists.

## Background
While fixing `tests/agent/test_repl.py::TestGetWorkflowStatus` (3 tests), I
found `_get_workflow_status()` was checking `self._ctx._orchestrator` — an
attribute that is never set anywhere (the real orchestrator instance lives
on `AgentREPL._orchestrator`, assigned from `StartupOrchestrator.run()`'s
return tuple, never stashed on `ctx`). Since `hasattr(MagicMock(),
"_orchestrator")` is always `True`, this bug was invisible in the two
mock-based tests it should have failed, and in real usage the `hasattr`
check on a real `AgentContext` (which has no `_orchestrator` attribute)
always short-circuited to `"not loaded"` before ever reaching the
`orchestrator.workflow_status()` call below it.

I fixed the immediate bug: `StartupBanner.print_startup_banner()` /
`_get_workflow_status()` now take `orchestrator` as an explicit parameter,
threaded in from `AgentREPL.run()`'s own `self._orchestrator` (the correct
source), instead of the never-populated `ctx._orchestrator`. This makes the
`orchestrator is None` -> `"unknown"` branch reachable for the first time.

Doing so exposed a second, previously-unreachable bug: `Orchestrator` has no
`workflow_status()` method at all (confirmed via repo-wide grep — the only
reference is this one call site). Calling it would raise `AttributeError` in
real production usage now that the first bug's accidental protection is
gone. I made the call site defensive (`getattr(orchestrator,
"workflow_status", None)`, falling back to `"not loaded"` when absent) to
avoid introducing a live crash, rather than guessing what a real
`workflow_status()` implementation should report.

## Problem
The startup banner's "workflow tracking" status has never meaningfully
reflected anything — it either short-circuited to "not loaded" via the dead
`ctx._orchestrator` check, or (after that particular fix) would call a
method that doesn't exist. There is no current concept of "workflow
tracking enabled/disabled" anywhere else in the codebase to base a real
implementation on (grepped for `workflow_mode`/`workflow_tracking`; the
former appears only in a test asserting it is deliberately NOT mentioned in
an error message, suggesting it was already removed as a concept
elsewhere).

## Reason for Change
Decide whether this banner field should report something real, or be
removed as vestigial.

## Implementation Intent
Either:
- Implement a real `Orchestrator.workflow_status()` returning
  `{"tracking": "enabled" | "not_loaded"}` based on whichever real signal
  reflects "is workflow tracking active" (e.g. whether a workflow engine
  adapter / workflow DB is wired up) — audit `WorkflowEngineAdapter` and
  `agent.workflow.*` for the actual current concept of "workflow tracking",
  since `workflow_mode` itself appears to already be gone; or
- Remove the "workflow tracking" banner field and its 3
  `TestGetWorkflowStatus` tests entirely, if there is no longer a
  meaningful "tracking enabled/disabled" state to report.

## Target Files or Areas
- `scripts/agent/startup_banner.py` (`_get_workflow_status`)
- `scripts/agent/orchestrator.py` (would need a real `workflow_status()`)
- `tests/agent/test_repl.py::TestGetWorkflowStatus`

## Required Changes
N/A: see Implementation Intent — this is a decide-then-implement issue, not
a list of independent required changes.

## Constraints
N/A: none beyond the design decision itself.

## Acceptance Criteria
- Either `Orchestrator.workflow_status()` exists and reports real state, and
  `startup_banner.py`'s `getattr(...)` defensive fallback is removed since
  it's no longer needed; or the banner field and its tests are removed.

## Testing Expectations
`tests/agent/test_repl.py::TestGetWorkflowStatus` updated to match whichever
direction is chosen.

## Documentation Impact
N/A: no user-facing docs currently describe the startup banner's workflow
status field.

## Out of Scope
Do not change `_get_chunk_count()` or any other `StartupBanner` method —
unaffected by this issue.

## Dependencies
N/A: none

## Unresolved Questions
- What, concretely, should "workflow tracking enabled" mean today, given
  `workflow_mode` itself appears to have already been removed as a concept?

## AI Implementation Instruction
Do not invent workflow_status() semantics without first confirming what (if
anything) "workflow tracking" is supposed to mean in the current
architecture — it may be entirely vestigial.

## Traceability
- **Workflow phase**: N/A: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260911-153000
- **Related target files**: scripts/agent/startup_banner.py, scripts/agent/orchestrator.py, tests/agent/test_repl.py
