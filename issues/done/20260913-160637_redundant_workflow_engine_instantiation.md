# Redundant WorkflowEngine instantiation per turn in WorkflowEngineAdapter

## Priority
Low

## Summary
Eliminate unnecessary per-turn WorkflowEngine instantiation in `execute_turn` by reusing the injected engine instance.

## Background
The constructor accepts `workflow_engine: WorkflowEngine` and stores it as `self._workflow_engine`. However, `execute_turn` ignores this and creates a new WorkflowEngine instance on every turn.

## Problem
Lines 162-166 create a new WorkflowEngine from `self._workflow_engine._wdef`, bypassing the injected instance. This wastes resources and discards any state the injected engine may hold between turns.

## Reason for Change
Per-turn instantiation adds unnecessary overhead and prevents lifecycle management of the engine across turns.

## Implementation Intent
Replace the inline `WorkflowEngine(...)` instantiation with `self._workflow_engine` directly. If the engine needs per-turn initialization, add a dedicated method rather than creating a new instance.

## Target Files or Areas
- `/home/sugimoto/llmagent/scripts/agent/workflow_engine_adapter.py`

## Required Changes
- Replace `engine = WorkflowEngine(self._workflow_engine._wdef, self._state_store, tracer=self._tracer)` with `engine = self._workflow_engine`
- Update the `await engine.run(...)` call to use the reused instance
- Verify that `self._workflow_engine` is never mutated between turns in a way that would break reuse

## Constraints
- The injected engine must support multiple `run()` calls; verify this before removing instantiation
- Must not change the engine's public interface or behavior

## Acceptance Criteria
- Only one WorkflowEngine instance exists per WorkflowEngineAdapter lifetime
- Turn execution produces identical results to the current behavior
- No resource leaks from abandoned engine instances

## Testing Expectations
- Unit test verifying single WorkflowEngine instance per adapter
- Integration test confirming turn execution correctness after the change

## Documentation Impact
Update class docstring to note engine lifecycle management responsibility.

## Out of Scope
- Changing WorkflowEngine's internal state management
- Modifying the engine's run() interface

## Dependencies
N/A: none

## Unresolved Questions
- Is there any reason the original developer created a new engine per turn instead of reusing the injected one?
- Could this be a leftover from an earlier refactoring where the engine was not yet injected?

## AI Implementation Instruction
Before making this change, verify that `self._workflow_engine` is always initialized in the constructor and never None. Add an assertion if needed.

## Traceability
- **Workflow phase**: python-code-review + issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-160637
- **Related target files**: scripts/agent/workflow_engine_adapter.py
