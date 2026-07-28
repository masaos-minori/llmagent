## Goal

Add guard tests for orchestrator.py before refactoring to establish behavioral baseline for turn execution, tool call flow, and approval workflow.

## Scope

**In-Scope:**
- Create `tests/integration/test_orchestrator_integration.py` with tests for:
  - Turn execution: complete turn from message input to response output
  - Tool call flow: tool discovery, validation, execution, result processing
  - Approval workflow: approval flow with real database interactions
  - Error handling: tool failures, network timeouts, etc.

**Out-of-Scope:**
- Changing the behavior of orchestrator itself
- Any changes beyond the test

## Assumptions

1. The orchestrator needs characterization tests due to exceeding 500 lines with deep nesting
2. Current tests use MagicMock exclusively (70-80 items) — zero real integration verification
3. Tests must use SQLite in-memory DB and real WorkflowEngine
4. Tests should verify current behavior, not expected future behavior

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for orchestrator edge cases | Search for `orchestrator` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/integration/test_orchestrator_integration.py`

- **Blast Radius:**
  - Test-only change — no production code affected

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `orchestrator.py`:
```python
# Key behaviors:
# - Orchestrator receives AgentContext at construction
# - Manages turn execution: compression -> LLM loop -> tool dispatch
# - Handles background tasks (session title generation)
# - Coordinates with WorkflowEngine for workflow-based operations
# - Uses callbacks for terminal output and side effects
```

The test will verify turn execution, tool call flow, approval workflow, and error handling using real components where possible.

## Implementation

### Target file
New file: `tests/integration/test_orchestrator_integration.py`

### Procedure
1. Create `tests/integration/` directory if it doesn't exist
2. Create new test file `tests/integration/test_orchestrator_integration.py`
3. Write tests for turn execution
4. Write tests for tool call flow
5. Write tests for approval workflow
6. Write tests for error handling
7. Save the file

### Method
Create integration tests using real components (SQLite in-memory DB, WorkflowEngine) where possible.

### Details
1. Create `tests/integration/test_orchestrator_integration.py`:
   ```python
   """Integration tests for Orchestrator."""
   
   import asyncio
   import pytest
   
   @pytest.mark.asyncio
   async def test_complete_turn_execution():
       """Complete turn from message input to response output."""
       ...
   
   @pytest.mark.asyncio
   async def test_tool_call_flow():
       """Tool discovery, validation, execution, result processing."""
       ...
   
   @pytest.mark.asyncio
   async def test_approval_workflow_with_real_db():
       """Approval flow with real database interactions."""
       ...
   
   @pytest.mark.asyncio
   async def test_tool_failure_handling():
       """Tool failures are handled correctly."""
       ...
   
   @pytest.mark.asyncio
   async def test_network_timeout_handling():
       """Network timeouts are handled correctly."""
       ...
   ```

## Compatibility considerations

N/A — test-only change

## Security considerations

N/A — this test documents current behavior

## Rollback considerations

- Simple revert: delete the test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/integration/test_orchestrator_integration.py` | Integration tests document current behavior | `uv run pytest -k "orchestrator" -v` | All tests pass |

## Out of scope

- Changing the behavior of orchestrator itself
- Any changes beyond the test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-130329_require.md
- Source plan: plans/20260726-172622_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/agent/orchestrator.py, tests/integration/test_orchestrator_integration.py
