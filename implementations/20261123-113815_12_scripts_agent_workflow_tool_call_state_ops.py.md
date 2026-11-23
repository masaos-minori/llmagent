## Goal

Consult an optional call-state resolver before declaring `outcome_unknown` for stale dispatched rows and apply the mapped state inside the existing guarded UPDATE.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `classify_stale_pending` and a small `CallStateResolver` (new) Protocol. Never-dispatched rows still become `interrupted` exactly as before.

## Assumptions

- Verified: `TOOL_CALL_STATES` contains completed, failed, reconciliation_required, and outcome_unknown but not in_progress; the mapped `in_progress` outcome therefore leaves the row unchanged and unlisted.
- Verified: the UPDATE is optimistic-lock style (`WHERE idempotency_key=? AND state=?`); the resolver changes only the target state value.

## Design decisions

- Define the `CallStateResolver` (new) Protocol with `resolve_state(row) -> str | None` (row type `ToolCallState`); add keyword `resolver: CallStateResolver | None = None` to `classify_stale_pending`.
- For a source state in the dispatched group: target is `outcome_unknown` unless the resolver returns `completed`, `failed`, or `reconciliation_required`; `in_progress` skips the row; any other value, `None`, or a resolver exception keeps `outcome_unknown` (exception logged by class name).
- Without a resolver the function behaves byte-identically to today.

## Alternatives considered

Rejected: adding `in_progress` to `TOOL_CALL_STATES` (changes the mcpdl001 vocabulary, the schema comment, and tests outside this Plan).

## Implementation
### Target file
`scripts/agent/workflow/tool_call_state_ops.py`

### Procedure
1. Add the Protocol and the keyword parameter.
2. Resolve the target state per row before the UPDATE; skip `in_progress` rows.
3. Update the docstring to describe the resolver and the AC-6 guarantee (no automatic replay).

### Method
Resolver is called with the row fetched by `_STALE_SCAN_SQL`; wrap the call in try/except Exception with a justified noqa comment per repo rules.

### Details
- The returned list contains only rows this call transitioned, so `in_progress` rows do not appear in turn control messages.

## Compatibility considerations

Optional keyword; existing callers and tests are unchanged.

## Security considerations

The resolver result is validated against `TOOL_CALL_STATES` by the existing `finalize` vocabulary rules; an out-of-vocabulary value is ignored.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_mcp_call_recovery.py tests/agent/workflow/`

## Completion criteria

- With a resolver, stale dispatched rows take the mapped state; without one, behavior is unchanged; `in_progress` leaves the row as it is.

## Out of Scope

The resolver implementation (row 11) and its wiring (rows 13, 37, 47).

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
- **Related target files**: `scripts/agent/workflow/tool_call_state_ops.py`
