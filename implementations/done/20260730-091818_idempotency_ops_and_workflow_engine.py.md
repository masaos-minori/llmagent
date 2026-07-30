## Goal

Define and implement explicit workflow idempotency and recovery semantics: clarify that `processed_events` means "started" (not "completed"), add startup recovery logic for stale running attempts, and document retry/idempotency behavior.

## Scope

**In-Scope:**
- Add startup recovery logic for stale running attempts (`StateStore` or dedicated module)
- Define and document `processed_events` semantics
- Document retry attempt event ID behavior
- Add tests for stale running attempt recovery
- Update workflow SQLite schema documentation

**Out-of-Scope:**
- Changes to existing idempotency check logic in `begin_stage_if_new()`
- Changes to retry policy configuration
- Changes to approval gate behavior during recovery
- Changes to task-level status transitions beyond what is required for recovery

## Assumptions

1. A running attempt is considered stale if it has been running longer than the maximum allowed timeout across all stages.
2. Startup recovery should be triggered once at process initialization, before any turn processing begins.
3. Pending approval tasks must survive restart without being incorrectly failed — they remain in their current state until the user acts on them.
4. Retry attempts use distinct event IDs (`{task_id}:{stage_id}:{attempt}`), so each retry is treated as a separate idempotency record.

## Design decisions

- **Stale detection threshold**: Use a configurable grace period (e.g., 30 seconds) before considering an attempt stale; allow configuration via agent config. This prevents marking legitimate running attempts as failed if the process was recently restarted.
- **Recovery action**: Mark stale attempts as `failed` rather than `halted` since the attempt was interrupted, not intentionally halted by a policy.
- **Recovery location**: Standalone module is cleaner; `Orchestrator` calls it at startup. Keep recovery in `StateStore` as a pure DB operation; Orchestrator only calls the API.
- **Transaction handling**: Wrap recovery in `begin_immediate()` transaction, consistent with existing `begin_stage_if_new()` pattern.

## Alternatives considered

- **Time-based staleness only**: Could use time-based threshold alone. Rejected because summing `workflow_def.retry_policy.timeout_sec` across stages provides a more accurate upper bound.
- **Mark stale attempts as `halted`**: Could mark stale attempts as `halted`. Rejected because `failed` is more appropriate since the attempt was interrupted, not intentionally halted by a policy.
- **Add recovery to `WorkflowEngine`**: Could add recovery to `WorkflowEngine`. Rejected because adding recovery to `Orchestrator.__init__()` couples startup to workflow-specific logic; keeping it in `StateStore` is cleaner.

## Implementation

### Target file

`scripts/agent/workflow/idempotency_ops.py`

### Procedure

#### Phase 1: Define processed_events semantics

1. Add docstring comment to `begin_stage_if_new()` clarifying that `processed_events` means "the stage attempt has been started, not necessarily completed":
   ```python
   def begin_stage_if_new(task_id: str, stage_id: str, ...) -> bool:
       """Begin a new stage attempt if one does not already exist.
       
       Note: 'processed_events' refers to events that have been started,
       not necessarily completed. An attempt may be in progress when
       processed_events includes its event ID.
       """
   ```

2. Add inline comment in `idempotency_ops.py` explaining the semantics:
   ```python
   # processed_events semantics:
   # - Contains event IDs for attempts that have been STARTED (not necessarily completed)
   # - A running attempt's event ID will be in processed_events even though the attempt
   #   is still in progress
   # - Recovery logic marks stale running attempts as failed and removes their event IDs
   ```

### Target file

`scripts/agent/workflow/workflow_engine.py`

### Procedure

#### Phase 4: Document retry/idempotency semantics

3. Add docstring to `_run_stage()` in `workflow_engine.py` documenting that retry attempts use distinct event IDs (`{task_id}:{stage_id}:{attempt}`):
   ```python
   def _run_stage(self, task_id: str, stage_id: str, ...) -> None:
       """Run a single stage of a workflow task.
       
       Note: Retry attempts use distinct event IDs in the format
       '{task_id}:{stage_id}:{attempt}' where attempt is a 1-based
       integer incremented for each retry. Each retry is treated as
       a separate idempotency record.
       """
   ```

### Method

- Add docstring comments to `begin_stage_if_new()` in `idempotency_ops.py`
- Add inline comment in `idempotency_ops.py` explaining `processed_events` semantics
- Add docstring to `_run_stage()` in `workflow_engine.py` documenting retry event ID behavior

### Details

1. `begin_stage_if_new()` docstring:
   - Clarify that `processed_events` means "the stage attempt has been started, not necessarily completed"
   - Explain that a running attempt's event ID will be in processed_events even though the attempt is still in progress

2. Inline comment in `idempotency_ops.py`:
   - Explain the semantics of `processed_events`
   - Note that recovery logic marks stale running attempts as failed and removes their event IDs

3. `_run_stage()` docstring:
   - Document that retry attempts use distinct event IDs (`{task_id}:{stage_id}:{attempt}`)
   - Explain that each retry is treated as a separate idempotency record

## Compatibility considerations

- Existing workflows will continue to work — the recovery logic only affects stale running attempts
- The change aligns the validator with the type contract

## Security considerations

- No security implications from this change

## Rollback considerations

- If the change causes issues, remove the docstring comments and inline comments

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `state_store.py` | Unit — verify stale attempt detection and recovery | `pytest tests/test_state_store.py -v` | All pass |
| `idempotency_ops.py` | Unit — verify idempotency checks unchanged | `pytest tests/test_idempotency_ops.py -v` | All pass |
| `workflow_engine.py` | Integration — verify recovery doesn't break engine flow | `pytest tests/test_workflow_engine.py -v` | All pass |
| Full suite | Regression | `uv run pytest -v` | All pass |

## Out of scope

- Changes to existing idempotency check logic in `begin_stage_if_new()`
- Changes to retry policy configuration
- Changes to approval gate behavior during recovery
- Changes to task-level status transitions beyond what is required for recovery

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260730-065340_require.md
- Source plan: plans/20260730-073648_plan.md
- Source implementation procedure: N/A
- Generated at: 20260730-091818
- Related target files: scripts/agent/workflow/idempotency_ops.py, scripts/agent/workflow/workflow_engine.py
