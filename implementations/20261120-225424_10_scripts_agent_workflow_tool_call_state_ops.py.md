## Goal

Key `tool_call_state` rows by the logical call id, implement the intent transitions, and split stale classification so never-dispatched rows become `interrupted` (replayable) while dispatched rows become `outcome_unknown` (never replayable) (`REQ-005` transitions, `REQ-009` stale split, AC-6).

## Scope
**Release unit**: auth-intent

## Assumptions
- The `idempotency_key` column name is kept; its value is the opaque uuid7 logical call id (collision merging via `INSERT OR IGNORE` at :63-69 can no longer merge distinct calls because ids are unique by construction).
- `reconciliation_required` is written by no code path in this Plan (UNK-03).
- `workflow_engine.py`'s interrupted-replay contract stays valid because never-dispatched rows still land in `interrupted`.

## Design decisions
- `record_tool_call` (:55-70) keeps inserting `pending` but the key is now the logical call id supplied by the caller.
- `finalize_tool_call` (:73-87) already validates against `TOOL_CALL_STATES` (row 9) — it accepts the intermediate states dispatch_starting (new), dispatched, response_received (new) with no extra branching.
- `classify_stale_pending` (:105-141): the stale query widens to the dispatch-stage states past the timeout; rows still at `pending`/dispatch_starting transition to `interrupted` (existing WHERE-guard pattern), rows at dispatched/response_received transition to `outcome_unknown` (new) under the same guard.

## Alternatives considered
- Treating every stale row as `interrupted` (today's behavior): rejected — replaying a dispatched call whose response was lost risks double side effects (AC-6).

## Implementation
### Target file
`scripts/agent/workflow/tool_call_state_ops.py`

### Procedure
Update the `state` value comment (:31), the docstrings, and `classify_stale_pending`; keep `_row_to_state` (:35-46) unchanged.

### Method
Per-key guarded UPDATE, one branch per source state; `db.commit()` once as today (:139).

### Details
- Return value keeps "rows this call transitioned" for both branches so the dispatcher's replay-control path sees `interrupted` exactly as before.
- `pending_tool_calls` (:90-101) keeps selecting `state='pending'` only — dispatched rows are intentionally invisible to replay listing.

### Companion test files
- `tests/agent/workflow/test_workflow_engine.py`
  - Procedure: add cases — stale never-dispatched row stays replayable (`interrupted`); stale dispatched row becomes `outcome_unknown` and is never replayed.
  - Validation: `uv run pytest tests/agent/workflow/test_workflow_engine.py` passes.

## Compatibility considerations
`workflow_engine.py` (reference only) consumes `interrupted` lists; unchanged semantics preserved per the Plan's consumer-scan disposition.

## Security considerations
`outcome_unknown` prevents automatic re-execution of side-effecting calls whose outcome is unknown.

## Rollback considerations
N/A: revert the commit together with rows 9 and 12 (vocabulary + DDL land as one unit).

## Validation plan
`uv run pytest tests/agent/workflow/test_workflow_state_store.py tests/agent/workflow/test_workflow_engine.py` — transitions and the stale split verified; `uv run mypy scripts/`.

## Completion criteria
A dispatched-then-timed-out row ends `outcome_unknown` (new) and is excluded from every replay path; a never-dispatched timed-out row keeps today's `interrupted` behavior.

## Out of Scope
outcome_unknown reconciliation procedure (mcpdl004); DDL (row 12); recorder facade (row 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs sweep owned by mcpai012 |

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
- **Requirement ID**: `REQ-005`, `REQ-009`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `scripts/agent/workflow/tool_call_state_ops.py`, `tests/agent/workflow/test_workflow_engine.py`
