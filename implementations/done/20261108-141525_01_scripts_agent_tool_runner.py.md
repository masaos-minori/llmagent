## Goal
Scope the `tool_call_state` row key per task: `_state_key` returns the transport dedup key with the `task_id` appended, so an identical tool call in a different task gets its own lifecycle row, while the wire `X-Idempotency-Key` and intra-task retry-invariance stay unchanged (`REQ-001`/`REQ-003`).

## Scope
**Release unit**: wfaudit002-full

- Covers Plan `plans/20261108-084005_wfaudit002_tool-state-key-collisions.md` row 1 only: `scripts/agent/tool_runner.py`.

## Assumptions
- `ctx.workflow.current_task_id` is set whenever a state row is written (`_record_pending_state` already returns `None` when the task context is unwired, L162-170); the composition reuses the same `task_id` value that `_record_pending_state` passes to `recorder.record_tool_call`.
- Appending `:{task_id}` to the 64-hex transport key is safe: the `tool_call_state.idempotency_key` column is TEXT with no length or format validation (`scripts/agent/workflow/tool_call_state_ops.py` performs none; the `^[A-Za-z0-9_-]{1,64}$` house key shape applies only to the transport key in `scripts/shared/http_transport.py`).

## Design decisions
- Compose at the single derivation point `_state_key` (L149-160) using `ctx.workflow.current_task_id`; record (L172) and finalize (L194, via the key returned by `_record_pending_state`) inherit the change with no other call-site edits.
- The transport call site in `scripts/shared/http_transport.py` keeps calling `derive_idempotency_key` with today's inputs — the wire key is byte-identical by construction (`REQ-002`).

## Alternatives considered
- Composite `PRIMARY KEY (idempotency_key, task_id)`: rejected in the plan Design — DDL change on a table with no migration path; value composition keeps the single-column PK contract `INSERT OR IGNORE` relies on.

## Implementation
### Target file
`scripts/agent/tool_runner.py`

### Procedure
Extend `_state_key` to append the task-scope component and update its docstring.

### Method
`_state_key` returns the existing `derive_idempotency_key("call_tool", pc.name, pc.args, str(ctx.session.session_id))` result with `f":{ctx.workflow.current_task_id}"` appended. Docstring: state that the key is the transport key scoped to the current task (per-task lifecycle rows, `REQ-001`), that the audit-only `_idempotency_key` (L138-146) stays separate, and that the wire key sent by the transport is the unscoped transport key.

### Details
- No other edits: record and finalize already flow through the single helper; `tool_call_state_ops` keeps treating keys as opaque (`REQ-004`).

## Compatibility considerations
- Existing production rows keep their old unscoped keys and are no longer reachable by the new key form — plan `UNK-01` deploy probe (`SELECT COUNT(*) FROM tool_call_state WHERE state='pending';`); rows are audit history, acceptable to leave.
- Same-task identical content still maps to one row (`INSERT OR IGNORE` retry-invariance, `REQ-003`).

## Security considerations
- No new sensitive data in the key: `task_id` is an internal identifier already stored in the same row's `task_id` column.

## Rollback considerations
- Revert the commit; keys revert to the unscoped form with no schema state to unwind.

## Validation plan
- Cross-task distinctness test (two tasks, identical call content -> two `_state_key` values, both recorded as pending rows with their own `task_id`) and intra-task retry-invariance test in `tests/agent/test_tool_runner.py` (extend `TestToolCallStateProducer`).
- Finalize isolation test: finalize for task A's key leaves task B's identical-content row pending; `classify_stale_pending(A)` never lists B's row (`tests/agent/workflow/test_workflow_state_store.py`).
- Transport regression fixture test: outgoing `X-Idempotency-Key` value equals the HEAD-computed value for the same call (`tests/shared/test_http_transport.py`); passes on HEAD and after.
- New collision tests fail on HEAD (second row silently swallowed). `uv run pytest tests/agent/ -q` then full `uv run pytest tests/ -q`; lint/type gates per `rules/toolchain.md`.

## Completion criteria
- Identical call content across tasks yields distinct lifecycle rows; wire key and intra-task retry behavior unchanged; all suite green.

## Out of Scope
- `tool_call_state` DDL changes and retention/purge (plan Out-of-Scope, `UNK-02`).
- The docs key-description update (row 2 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-070023 | 20261109-070023 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261109-070023 | 20261109-070023 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-070023 | 20261109-070023 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-070023 | 20261109-070023 | docs update is row 2's scope N/A: docs updates owned by procedure 141525_02 |

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
- **Requirement ID**: `REQ-001` (composed key), `REQ-003` (cross-task distinct, intra-task invariant)
- **Source issue**: `issues/20261107-203215_wfaudit002_tool-state-key-collisions.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084005_wfaudit002_tool-state-key-collisions.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-141525
- **Related target files**: `scripts/agent/tool_runner.py`