## Goal

Create the one shared, closed-vocabulary module that the ledger, the MCP control API, and the Agent recovery service all read: result classes, reconcile outcomes, control error codes, the reconciler Protocol, the ledger-state to Agent-state mapping, and tolerant control-token resolution.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the new module and nothing else. It imports only the standard library and `shared.config_utils`, so `.importlinter` contract `shared-is-leaf` holds. Consumers are wired by later rows.

## Assumptions

- Verified: `shared/tool_metadata.py` already holds closed vocabularies (frozensets) readable from `shared`, `mcp_servers`, and `agent`; this module follows that precedent.
- Verified: `agent.workflow.models.TOOL_CALL_STATES` has no `in_progress` member, so `in_progress` exists here only as a recovery outcome of the mapping; the Agent row stays unchanged for it (Plan correction made in this cycle).
- Verified: `shared.config_utils.resolve_env_ref` raises `ValueError` for an unset variable; the control token must instead degrade to an empty string, so `resolve_control_token` (new) wraps it.

## Design decisions

- Vocabularies are `frozenset` constants: `RESULT_CLASSES` (new) = complete, secure_reference, redacted_preview, replay_unavailable; `RECONCILE_OUTCOMES` (new) = evidence_found, no_evidence, ambiguous, unverifiable; `CONTROL_ERROR_CODES` (new) = none, unknown_key, lease_live, attempts_exhausted, not_reconcilable, reconciler_failed, handler_failed, store_unavailable; `AGENT_RECOVERY_STATES` (new) = completed, in_progress, outcome_unknown, reconciliation_required, failed.
- `agent_state_for(ledger_status, lease_live)` is the single authoritative mapping and raises `ValueError` on an unknown ledger status (totality is tested): pending+live lease gives in_progress, pending+expired lease gives reconciliation_required, completed gives completed, failed gives failed, interrupted gives reconciliation_required.
- `ReconcileEvidence` (new) is a frozen dataclass (`outcome`, `digest`, optional `external_ref` (new)) and `Reconciler` (new) is a `typing.Protocol` with one method `reconcile(tool_name, call_key, snapshot)`; no default implementation is registered here.

## Alternatives considered

Rejected: defining the vocabularies inside `mcp_servers` or `agent` (the ledger in `shared` and both consumers must read one source; importing upward would break `shared-is-leaf`).

## Implementation
### Target file
`scripts/shared/mcp_call_state_contract.py` (new)

### Procedure
1. Create the module with the four frozensets above and a module docstring that names the issue and the consumers.
2. Add `ReconcileEvidence` (new), the `Reconciler` (new) Protocol, `agent_state_for` (new), and `resolve_control_token` (new).
3. Keep `__all__` exact so the facade row can re-export by name.

### Method
`resolve_control_token(raw)` returns `""` unless `raw` is a non-empty string; it calls `resolve_env_ref` and maps `ValueError` to `""`. It never logs the value; callers log the server name only.

### Details
- `ReconcileEvidence.digest` must be a non-sensitive digest (hex hash or fixed label); the dataclass validates `outcome` in `RECONCILE_OUTCOMES` (new) in `__post_init__`.
- No I/O, no globals, no registration state: the registry lives in the MCP server row.

## Compatibility considerations

N/A: new module; nothing imports it before later rows.

## Security considerations

The token resolver never raises and never echoes the value; an unset variable yields an empty token, which every consumer treats as control closed.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_mcp_call_state_contract.py` (row 25)
- `uv run lint-imports` and `uv run mypy scripts/` stay clean

## Completion criteria

- The module exports the vocabularies, mapping, Protocol, evidence type, and token resolver; every ledger status maps; `shared-is-leaf` passes.

## Out of Scope

Reconciler implementations, the registry, and any I/O.

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
- **Requirement ID**: `REQ-001` (control endpoints and response shape), `REQ-003` (result metadata and result classes at finalization), `REQ-004` (reconciler contract), `REQ-005` (ledger-state to Agent-state mapping and Agent recovery)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `scripts/shared/mcp_call_state_contract.py`
