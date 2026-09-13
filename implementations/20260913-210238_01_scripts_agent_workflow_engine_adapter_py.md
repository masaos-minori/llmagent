## Goal

Eliminate redundant per-turn WorkflowEngine instantiation in `WorkflowEngineAdapter.execute_turn` by reusing the injected engine instance stored in `self._workflow_engine`, per REQ-001 through REQ-003.

## Scope

- In-Scope: Replace inline `WorkflowEngine(...)` instantiation with `self._workflow_engine` in `execute_turn`; add assertion verifying `self._workflow_engine` is never None; update class docstring to note engine lifecycle management responsibility
- Out-of-Scope: Changing WorkflowEngine's internal state management; modifying the engine's run() interface

## Assumptions

- The injected WorkflowEngine supports multiple `run()` calls without side effects — confirmed by inspection of workflow_engine.py: `run()` does not mutate `_wdef`, `_store`, or `_tracer` between calls
- The backward-compatible public API methods (`init_workflow_task`, `activate_workflow`) must not change their signatures — confirmed by inspection of orchestrator.py callers

## Design decisions

1. Replace the inline `WorkflowEngine(...)` instantiation with `self._workflow_engine` directly. Since `WorkflowEngine.run()` does not mutate `_wdef`, `_store`, or `_tracer` between calls (confirmed by inspecting `workflow_engine.py`), the injected instance can safely be reused across turns.
2. Add an assertion to verify `self._workflow_engine` is never None before reuse, as recommended by the AI Implementation Instruction in the Issue.
3. If the engine needs per-turn initialization, add a dedicated method rather than creating a new instance.
4. Update the class docstring to note engine lifecycle management responsibility.

## Alternatives considered

- **Add per-turn initialization method**: Instead of replacing the instantiation entirely, add a dedicated `reset_for_turn()` method on WorkflowEngine. Rejected because `run()` already handles multiple invocations without mutating internal state — no reset is needed.
- **Keep both instances and merge state**: Maintain both the injected and newly-created engines, merging their states after each turn. Rejected because it adds complexity without benefit — the injected engine is sufficient.

## Implementation
### Target file
`scripts/agent/workflow_engine_adapter.py`

### Procedure
1. Add assertion verifying `self._workflow_engine` is not None before reuse
2. Replace `engine = WorkflowEngine(...)` with `engine = self._workflow_engine`
3. Update class docstring to note engine lifecycle management responsibility
4. Run validation sequence

### Method
Inline variable replacement + assertion addition in `execute_turn`; docstring update in class definition.

### Details
1. **Phase 1: Preparation — Confirm current state**
   a. Locate `execute_turn` method in `scripts/agent/workflow_engine_adapter.py` (lines 162-166 contain the current instantiation gap)
   b. Verify that `self._workflow_engine` is set in the constructor and is always injected
   
2. **Phase 2: Core Logic Implementation**
   a. Add assertion before engine usage in `execute_turn`:
      ```python
      assert self._workflow_engine is not None, "WorkflowEngine must be injected via constructor"
      ```
   
   b. Replace the inline `WorkflowEngine(...)` instantiation with `self._workflow_engine`:
      ```python
      # Before:
      engine = WorkflowEngine(self._workflow_engine._wdef, self._state_store, tracer=self._tracer)
      
      # After:
      engine = self._workflow_engine
      ```
   
   c. Update the class docstring to note engine lifecycle management responsibility:
      - Add a note in the class-level docstring explaining that `self._workflow_engine` is the single source of truth for engine lifecycle and should not be recreated per-turn

3. **Phase 3: Deployment & Verification**
   a. Run unit tests for `execute_turn` with reused engine:
      ```bash
      pytest scripts/agent/test_workflow_engine_adapter.py::test_execute_turn_single_engine_instance
      ```
      Expected outcome: Test passes — no duplicate engine creation
   
   b. Run integration test confirming turn execution correctness:
      ```bash
      pytest scripts/agent/test_workflow_engine_adapter.py::test_execute_turn_correctness_with_reused_engine
      ```
      Expected outcome: Test passes — identical results to current behavior
   
   c. Run regression tests for backward-compatible public API methods:
      ```bash
      pytest scripts/agent/test_workflow_engine_adapter.py::test_init_workflow_task_backwards_compat
      ```
      Expected outcome: Test passes — no signature change

## Compatibility considerations

- The public API methods (`init_workflow_task`, `activate_workflow`) must preserve existing signatures — confirmed by inspection of orchestrator.py callers
- Reusing the engine may cause state leakage between turns if the engine mutates internal state during `run()` — mitigated by verification that `WorkflowEngine.run()` does not mutate `_wdef`, `_store`, or `_tracer`
- Python GC handles abandoned engine instances automatically — no external references to discarded instances exist

## Security considerations

N/A: Refactoring only, no security impact.

## Rollback considerations

Simple revert of the three modifications (assertion addition, variable replacement, docstring update) — no data migration or state rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/workflow_engine_adapter.py | Unit test: verify single WorkflowEngine instance per adapter | pytest scripts/agent/test_workflow_engine_adapter.py::test_execute_turn_single_engine_instance | Test passes — no duplicate engine creation |
| scripts/agent/workflow_engine_adapter.py | Integration test: confirm turn execution correctness after change | pytest scripts/agent/test_workflow_engine_adapter.py::test_execute_turn_correctness_with_reused_engine | Test passes — identical results to current behavior |
| scripts/agent/workflow_engine_adapter.py | Regression test: backward-compatible public API methods work unchanged | pytest scripts/agent/test_workflow_engine_adapter.py::test_init_workflow_task_backwards_compat | Test passes — no signature change |

## Completion criteria

- [ ] Only one WorkflowEngine instance exists per WorkflowEngineAdapter lifetime
- [ ] Turn execution produces identical results to the current behavior
- [ ] No resource leaks from abandoned engine instances
- [ ] `self._workflow_engine` is verified non-None before reuse
- [ ] No regressions in callers using the backward-compatible public API

## Out of scope

- Modifying `scripts/agent/orchestrator.py` (reference file only)
- Modifying `scripts/agent/workflow/workflow_engine.py` (reference file only)
- Changing WorkflowEngine's internal state management
- Modifying the engine's run() interface

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add assertion for non-None check | Pending | — | — | Before engine usage in execute_turn |
| 2 | Replace WorkflowEngine(...) with self._workflow_engine | Pending | — | — | Line 162-166 |
| 3 | Update class docstring with lifecycle note | Pending | — | — | Note engine lifecycle management |
| 4 | Run unit test: single engine instance | Pending | — | — | test_execute_turn_single_engine_instance |
| 5 | Run integration test: turn correctness | Pending | — | — | test_execute_turn_correctness_with_reused_engine |
| 6 | Run regression test: backward compat | Pending | — | — | test_init_workflow_task_backwards_compat |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 through REQ-003 — eliminate redundant per-turn WorkflowEngine instantiation
- **Source issue**: issues/20260913-160637_redundant_workflow_engine_instantiation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-193738_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-210238
- **Related target files**: scripts/agent/workflow_engine_adapter.py
