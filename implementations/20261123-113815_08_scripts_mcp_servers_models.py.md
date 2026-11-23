## Goal

Add the two control-response Pydantic models whose fields are closed vocabularies, so the response boundary cannot carry free-form payloads.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `CallStateResponse` (new) and `ReconcileResponse` (new). `CallToolRequest`/`CallToolResponse` are unchanged. Placed before the control API row so that module can import them.

## Assumptions

- Verified: the module already uses Pydantic `BaseModel` with `field_validator` and imports closed vocabularies from `shared`.
- Row order corrected in this cycle: this row precedes `control_api.py` (the API imports these models).

## Design decisions

- `CallStateResponse` (new): key, ledger_status, agent_state, attempt_number, lease_live, lease_expires_epoch, result_class, result_code, result_size_bytes, result_sha256, external_ref, reconciliation_required, error_code; validators check `agent_state`, `result_class`, `error_code` against the contract vocabularies.
- `ReconcileResponse` (new): key, decision (`reused_completed` (new), `reconciled`, `operator_review` (new), `refused`), outcome (a reconcile outcome or `none`), ledger_status, agent_state, operator_review, evidence_digest, error_code.
- `model_config` forbids extra fields so an accidental raw field fails fast.

## Alternatives considered

Rejected: returning plain dicts from the handlers (no boundary check on the closed vocabularies).

## Implementation
### Target file
`scripts/mcp_servers/models.py`

### Procedure
1. Import the vocabularies from `shared.mcp_call_state_contract`.
2. Add both models with `extra='forbid'` and the vocabulary validators.

### Method
Reuse the existing validator style in `CallToolRequest`; keep field descriptions short and free of examples with real values.

### Details
- No field accepts arbitrary strings except `key`, `result_code`, `external_ref`, and `evidence_digest` (new); document each as opaque.

## Compatibility considerations

Additive models.

## Security considerations

`extra='forbid'` plus vocabulary validators keep raw arguments, paths, and exception text out of control responses.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/test_call_state_api.py` (row 29)
- `uv run mypy scripts/`

## Completion criteria

- Both models validate their vocabulary fields and reject unknown fields.

## Out of Scope

Handlers and wiring (rows 09 and 10).

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
- **Requirement ID**: `REQ-001` (control endpoints and response shape)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `scripts/mcp_servers/models.py`
