## Goal

Document the two call-state control endpoints, their response shape, the result classes, the reconciler contract, and the failure behavior in the endpoint and transport document.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: one new section before `## MCPServer Base Class`, one bullet in that section's contract list, and keyword entries. No other section changes.

## Assumptions

- Verified: the document lists the common endpoints and the `/v1/call_tool` contract, and the base-class list names Authentication; the control paths are not mentioned today.

## Design decisions

- New section `## Call-State Control Endpoints` with a short table: GET `/v1/call_state/{key}` and POST `/v1/call_state/{key}/reconcile`, who may call (the Agent, with the control Bearer token), and what each returns.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`docs/22_mcp/mcp_02_01_endpoints-and-transport.md`

### Procedure
1. Add the section covering: response fields, the four result classes (`complete`, `secure_reference`, `redacted_preview`, `replay_unavailable`), the reconcile decisions (`reused_completed`, `reconciled`, `operator_review`, `refused`) and reconcile outcome vocabulary, the stable error codes, and the rule that no response carries raw arguments, credentials, signed URLs, raw exceptions, or internal paths.
2. Add a failure-behavior list: unknown key 404, live lease 409, exhausted attempts refusal with operator review, unconfigured or empty control token 401 on control paths only, and Agent degradation to `outcome_unknown`.
3. Add a bullet in the base-class contract list pointing at the control paths and the separate token; add keywords (call-state, control-api, reconcile).

### Method
Edit prose and tables only; link to the access-control document for the authorization posture instead of repeating it.

### Details
- The reference-table drift test must stay green: do not edit any guarded generated block.

## Compatibility considerations

N/A: no behavior change in this row.

## Security considerations

N/A: documentation only; no secret value, approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/run_validation_gates.py`
- `uv run pytest tests/tools/test_generate_reference_table.py`

## Completion criteria

- The section names both endpoints, the result classes, the failure behavior, and the no-sensitive-data rule; the documentation gates pass.

## Out of Scope

Authorization posture text (row 32) and store schema facts (row 33).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-153555 | 20261123-155500 | reflection from verifying row 33 against the code: result facts are recorded at terminal finalization, not only for completed rows (a failed row reports replay_unavailable with the error class), so the field table and the result-class table state that sha256 and size describe the full serialized result whatever the class |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Completed | 20261123-153555 | 20261123-153555 | check_docs_quality, check_docs_structure, check_docs_content_policy, check_docs_consistency --domain mcp pass |

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
- **Requirement ID**: `REQ-001` (control endpoints and response shape), `REQ-004` (reconciler contract), `REQ-007` (documentation of the control contract)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `docs/22_mcp/mcp_02_01_endpoints-and-transport.md`
