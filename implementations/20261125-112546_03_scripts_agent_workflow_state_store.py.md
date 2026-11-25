## Goal
Pass the canonical argument hash through the `StateStore` facade to the tool-call state writer.

## Scope
**Release unit**: persisted directive store

## Assumptions
- `StateStore` is a thin delegation layer; it does not compute the hash itself.

## Design decisions
- The new parameter is positional in the same order as `tool_call_state_ops.record_tool_call`, so
  the facade stays a pass-through with no logic.

## Alternatives considered
- Computing the hash inside `StateStore` — rejected: hash computation belongs to the preparation
  phase (`_canonical_args_hash`), and duplicating it would allow two different values for one call.

## Implementation
### Target file
`scripts/agent/workflow/state_store.py`

### Procedure
Add the `args_hash` parameter to `StateStore.record_tool_call` and forward it.

### Method
Extend the signature with `args_hash: str` and pass it to `tool_call_state_ops.record_tool_call` in
the same argument order as the underlying helper.

### Details
- No other method in this module touches `tool_call_state`, so no further change is needed.
- The `ToolCallRecorder` Protocol that this class satisfies is updated by sibling procedure seq 04;
  the two must land in the same release unit.

## Compatibility considerations
Every existing caller passes the new argument; the affected call sites are separate target rows
(`tests/agent/test_tool_runner.py`, `tests/agent/test_mcp_call_recovery.py`,
`tests/agent/workflow/test_workflow_state_store.py`,
`tests/agent/workflow/test_workflow_status_vocabulary.py`).

## Security considerations
N/A: pass-through only.

## Rollback considerations
N/A: revert the commit as part of release unit A.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_state_store.py` — pass-through populates the
  column.
- Full sequence per `rules/toolchain.md`.

## Completion criteria
A call recorded through the facade stores the same hash the caller computed.

## Out of Scope
No hash computation, no change to the recorder facade's other methods.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add and forward the `args_hash` parameter | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (the write path populates the persisted hash)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `scripts/agent/workflow/state_store.py`
