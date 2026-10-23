## Goal

Make `tasks.idempotency_key` globally unique per task row so a retained `workflow.sqlite` cannot fail the first turn of a new process run (`plans/20261023-084918_plan.md`).

## Scope

`scripts/agent/workflow/task_ops.py`, `create_task()`: replace the composite-key branch with an unconditional `uuid.uuid4()` key and extend the docstring with the uniqueness scope and the informational role of `turn_number` (first line frozen).

## Assumptions

- `uuid` is already imported (`task_ops.py:5`); no new import.
- The old `None` branch's `str(uuid.uuid4())` is the existing run-unique mechanism and the only one needing no new state.
- Existing rows written with composite keys remain valid; the UNIQUE constraint and column type are unchanged.

## Design decisions

- Assign `idempotency_key = str(uuid.uuid4())` unconditionally — the collision class is removed by construction, not masked by a try/except at the call site.
- Freeze the docstring's first line byte-identical (`"Create a new task record."`) and place the scope statement on the following lines, so the generated API table (`docs/23_agent/agent_13_reference-api-generated.md`) does not drift.

## Alternatives considered

N/A: single-function change with a persistence impact already decided by the Plan (Option B); Options A and C were rejected there.

## Implementation
### Target file
`scripts/agent/workflow/task_ops.py`

### Procedure
1. In `create_task()`, delete the composite-key conditional and assign `idempotency_key = str(uuid.uuid4())` unconditionally.
2. Extend the `create_task()` docstring after the unchanged first line with the uniqueness scope and the informational, process-local role of `turn_number`. Do not alter the first line.

### Method
- Leave the `INSERT` statement, column list, parameter tuple, `db.commit()`, and the `TaskRecord(...)` return untouched — only the `idempotency_key` value derivation changes.
- `turn_number` stays a recorded column and a `TaskRecord` field; only its documented meaning changes.
- Do not wrap the `db.execute(...)` INSERT in `try/except` (REQ-006); `_init_workflow_task` / `execute_turn` bodies are unchanged.

### Details
Current body (`task_ops.py:20-24`):
```python
"""Create a new task record."""
if session_id is not None and turn_number is not None:
    idempotency_key = f"{session_id}:{turn_number}"
else:
    idempotency_key = str(uuid.uuid4())
```
Replace with:
```python
"""Create a new task record.

The `idempotency_key` is a globally unique opaque identifier (UUID4) generated here
for this task row; it is never derived from caller-supplied fields. `session_id` and
`turn_number` are recorded metadata only; `turn_number` is a process-local counter
(`agent/conversation_state_manager.py`, incremented in `append_user_message`) and is
not part of task identity. The `tasks.idempotency_key` UNIQUE constraint therefore
stays inert (a backstop against a future key-derivation regression), and resume across
a retained `workflow.sqlite` uses `task_id`, not this key.
"""
idempotency_key = str(uuid.uuid4())
```
`uuid` is already imported (`task_ops.py:5`); add no import.

## Compatibility considerations
- `get_task_by_idempotency_key` and its `state_store` wrapper are unchanged and stay exercised by tests.
- Pre-existing rows (old composite keys such as `":0"`) remain readable through `get_task_by_id` and `get_task_by_idempotency_key` (REQ-004; regression `T-3`).
- `execute_turn` / `_init_workflow_task` signatures and the `existing_task_id` resume path are unchanged (REQ-005, REQ-009).

## Security considerations
N/A: UUID4 generation is not a security boundary and handles no secret.

## Rollback considerations
Revert the single commit; the change is one function body plus a docstring paragraph.

## Validation plan
- `grep -n 'f"{session_id}' scripts/agent/workflow/task_ops.py` returns no match (AC-2).
- `uv run pytest tests/agent/workflow/test_workflow_state_store.py -q` passes with `T-1`..`T-3` (AC-1, AC-3).
- `uv run python tools/generate_reference_table.py --check` reports no drift (AC-5).
- Full sequence per `rules/toolchain.md` (ruff, mypy `--no-namespace-packages`, bandit, lint-imports, pre-commit) — AC-8.

## Completion criteria
- The composite branch is gone and `idempotency_key` is assigned `str(uuid.uuid4())` on every call.
- The docstring first line is byte-identical to today's and the scope paragraph is present.
- No `try/except` surrounds the INSERT.
- `T-1`..`T-3` pass and the mutation check `T-4` fails when the composite branch is restored.

## Out of Scope
- `session_id` plumbing (`orchestrator.py` still passes `""`) — REQ-009.
- Schema / `WORKFLOW_SCHEMA_VERSION` and any row migration — REQ-004.
- Resume path, `get_task_by_idempotency_key`, and status transitions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | First docstring line frozen |
| 2 | Add or update tests per Validation plan | Pending | — | — | Cross-restart regression in test_workflow_state_store.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Including generate_reference_table.py --check |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: documentation rows are separate target files | — | — | — |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | N/A: none |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-006
- **Source issue**: `issues/20261021-093421_turn001_task-idempotency-key-collides-across-restarts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-084918_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-074027
- **Related target files**: `scripts/agent/workflow/task_ops.py`
