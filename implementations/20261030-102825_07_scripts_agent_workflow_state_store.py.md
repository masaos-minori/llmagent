# Implementation Procedure: scripts/agent/workflow/state_store.py

## Goal

Add task-scoped tool-call state read/write helpers over the new `tool_call_state` (new) table so
turn entry can detect pending calls (REQ-008 persistence side).

## Scope

**In scope:**
- `scripts/agent/workflow/state_store.py`: new helper methods on `StateStore` (`:26`).

**Out of scope:**
- DDL (row 06), detection/injection logic (row 08).

## Assumptions

- `StateStore` owns `workflow.sqlite` access "through the operation modules under
  `agent/workflow/`" (docs `agent_04_03` responsibility scope, `:71` paragraph). Whether
  the helpers live directly on `StateStore` or in a new operation module (e.g.
  `tool_call_state_ops.py`) must match that pattern — the frozen row names this file, so
  direct methods are the default; Needs Confirmation if the owner wants an operation
  module instead (that would be an additional target file).
- Table shape exactly as row 06 defines it.

## Design decisions

- Methods (all new): `record_tool_call(task_id, idempotency_key, tool, retry_class,
  snapshot_id)` (INSERT state='pending'), `finalize_tool_call(idempotency_key, state)`
  (UPDATE, `updated_at` bump), `pending_tool_calls(task_id) -> list[ToolCallState]`
  (SELECT WHERE task_id=? AND state='pending', ordered by `created_at`),
  `classify_stale_pending(task_id, timeout_seconds)` — marks rows pending longer than
  `pending_timeout_minutes` (new) (row 10 config via the row-02 loader) as `interrupted` and
  returns them.
- Reads/writes use the same connection/lock discipline the existing `StateStore` methods
  use (short transactions on the workflow connection); no cross-DB reads — the dedup store
  stays behind the dispatcher boundary (ADR-008).

## Alternatives considered

- Reading `mcp_dedup.sqlite` directly here — rejected: two-DB reach from the agent layer
  violates DB separation; the agent view is its own `tool_call_state` (new) copy written by the
  executor path (Needs Confirmation of the write trigger site — the row-04
  `DispatchResult`/transport path carries it; same open wiring question as row 05).

## Implementation
### Target file
`scripts/agent/workflow/state_store.py`

### Procedure
1. Add a `ToolCallState` (new) dataclass in this module (row-local).
2. Add the four methods above following the existing method style (docstring + typed
   signature).
3. Keep `create_task()` and task-UUID semantics untouched (REQ-010).

### Method
Pure SQL helpers; no new imports above the workflow layer's contract.

### Details
- `pending_tool_calls` (new) is the only method row 08 calls at turn entry; keep it cheap via
  the `(task_id, state)` index from row 06.

## Compatibility considerations

- Additive methods only; existing `StateStore` API byte-stable; existing workflow tests
  unaffected.

## Security considerations

- N/A: no new externally-reachable surface; values originate from the dispatcher path.

## Rollback considerations

- N/A: revert the commit; row 08 loses its data source and disables itself per its own
  no-pending fallback.

## Validation plan

- Row 20 (`test_workflow_engine.py`) covers end-to-end use; direct helper coverage rides
  on the existing workflow-store tests named in `tests/agent/workflow/` (extend the
  state-store test module in the same row-20 edit set — Related-Tests disclosure, no
  frozen row of its own).
- `uv run pytest tests/agent/workflow`; `uv run mypy --no-namespace-packages scripts/
  tests/agent`; `lint-imports`.

## Completion criteria

- A pending row written for a task is returned by `pending_tool_calls` (new) for that task and
  only that task; `classify_stale_pending` (new) transitions only expired pending rows to
  `interrupted` (idempotent on re-run).

## Out of Scope

- Turn-context injection (row 08); control message text (rows 08-09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the helper methods | Pending | — | — | Needs row 06 tables present |
| 2 | Extend workflow-store test coverage (with row 20) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on row 06 DDL (itself gated on dbmig001 rows 01-02) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-008` (pending-call detection data access)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: scripts/agent/workflow/state_store.py
