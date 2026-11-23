## Goal

Forward an optional resolver through `StateStore.classify_stale_pending` to the stale-classification function.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the `classify_stale_pending` wrapper only (docstring included).

## Assumptions

- Verified: the wrapper has the signature `(self, task_id, timeout_seconds)` and delegates to `tool_call_state_ops.classify_stale_pending(self._db, task_id, timeout_seconds)`.

## Design decisions

- Add keyword `resolver: CallStateResolver | None = None` and pass it through.

## Alternatives considered

N/A: pass-through only.

## Implementation
### Target file
`scripts/agent/workflow/state_store.py`

### Procedure
1. Import the Protocol from `tool_call_state_ops`.
2. Add the keyword and forward it; extend the docstring.

### Method
Two-line change.

### Details
- Existing callers (`WorkflowEngine` before row 13 and tests) keep working unchanged.

## Compatibility considerations

Optional keyword.

## Security considerations

N/A: no new data path.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/workflow/ tests/agent/test_mcp_call_recovery.py`

## Completion criteria

- The wrapper forwards the resolver; behavior without it is unchanged.

## Out of Scope

Resolver implementation and engine plumbing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (ledger-state to Agent-state mapping and Agent recovery)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `scripts/agent/workflow/state_store.py`
