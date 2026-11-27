# Implementation Procedure — scripts/mcp_servers/cicd/cicd_service_github_actions.py

## Goal

Make `trigger_workflow` return the structured dispatch outcome, add the correlation marker to the
dispatch inputs, poll for the matching run with bounded constants, and provide the run lookup the
reconciler uses.

## Scope
**Release unit**: structured-state contract

Requirements implemented: REQ-001 (structured outcome instead of the success string), REQ-002
(correlation marker or fallback correlation), REQ-003 (bounded polling and the distinct states),
REQ-004 (pre-dispatch run search for the same logical call), REQ-007 (the lookup implements the
shared `Reconciler` contract). Acceptance criteria: AC-1, AC-2, AC-3.

## Assumptions
- The response model and the polling constants are defined by the `cicd_models.py` row and imported
  here; this document does not define them.
- The polling client is the lifespan-owned shared HTTP client injected by mcpci001; this Plan is
  implemented after mcpci001 (blocking dependency UNK-03).
- The correlation marker is added only when the workflow contract allows an input key (UNK-01);
  otherwise the fallback correlation is workflow identifier, ref, actor, and dispatch time. If
  neither path works, stop and report per Phase 1.

## Design decisions
- The correlation is recorded as a non-sensitive digest in `ReconcileEvidence` at dispatch time,
  because the `Reconciler` receives the component-keyed execution snapshot, which carries no call
  arguments (Plan Design decision, `scripts/shared/execution_snapshot.py` reference).
- The pre-dispatch run search is implemented independently of the idempotency key: adding a marker
  to `inputs` changes the args hash, so the same logical call with and without the marker produces
  different dedup keys (Plan Risk).
- Polling is bounded by the constants from the models row; a timeout produces `outcome_unknown`,
  never a retry.

## Alternatives considered
- Relying on the dedup gate to block a duplicate dispatch: rejected per REQ-004 — the gate cannot
  block a call whose args hash changed through the marker, and the shared fail-closed rule
  (`scripts/mcp_servers/dedup_gate.py`, reference) must not be bypassed by the lookup.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_service_github_actions.py`

### Procedure
- Change `trigger_workflow` (lines 102-132) to return `DispatchOutcome` from the models row instead
  of the `f"Workflow dispatched: ..."` string.
- Add the correlation marker to the dispatch inputs when the workflow contract allows it; otherwise
  build the fallback correlation from workflow identifier, ref, actor, and dispatch time.
- Add bounded polling for the matching run using `POLL_TIMEOUT_S` / `POLL_INTERVAL_S` from the models
  row: confirmed on a unique match with run id, URL, status, workflow, and ref;
  accepted_unconfirmed when none is found; reconciliation_required for multiple candidates;
  `outcome_unknown` on response loss or timeout.
- Add the pre-dispatch run search for the same logical call before any repeat dispatch.
- Expose the run lookup as the `Reconciler` implementation the server row registers.

### Method
- Lines 102-132 currently return the success string on 204 and on any other 2xx with no run id, no
  marker, and no polling (re-verified 20261127); `get_workflow_runs` at line 134 is the only run
  read and is reused by the lookup, so no new HTTP path is introduced.
- Reuse `_GITHUB_API_BASE` and `build_auth_headers` from `scripts/mcp_servers/cicd/cicd_service_defs.py`
  (reference, not modified).

### Details
- A 2xx response never becomes confirmed without a matched run (REQ-001).
- The lookup records evidence as a digest, never a raw payload (REQ-007).

### Companion test files
- `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`
  - Procedure: write the response-loss, no-run, delayed-run, and multiple-match tests before any
    code change (Phase 1), then replace the pinned immediate-success assertion at lines 57-73
    (`assert "dispatched" in result.lower()`) with the structured-state contract. Mocked HTTP, no
    live GitHub call.
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`.

## Compatibility considerations
- The handler contract stays `-> str` (the outcome is JSON-serialized), so `dispatch_tool` and the
  audit `outcome` mapping are unchanged (Plan Assumption).
- Non-2xx fail-fast behavior on the jobs path must not change
  (`tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py`, reference).

## Security considerations
- The correlation evidence is a digest; no raw input value is recorded (REQ-006, REQ-007).

## Rollback considerations
- N/A: revert the commit; the release unit is validated together with the composite and handler rows.

## Validation plan
- Unit: mocked HTTP — `uv run pytest tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`.
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- Confirmed, unconfirmed, ambiguous, and unknown outcomes are distinct and polling is bounded
  (AC-1, AC-2); the pre-dispatch search runs before a repeat dispatch (AC-3).

## Out of Scope
- Reconciler registration (`cicd_server.py` row); the response model and constants (`cicd_models.py` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | characterization tests first (Plan Phase 1) |
| 2 | Add or update tests per Validation plan (companion test file) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | documentation is covered by the Plan's docs row |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-007 (structured outcome, correlation, bounded polling, pre-dispatch search, reconciler lookup)
- **Source issue**: issues/20261119-141109_mcpci002_cicd-dispatch-reconciliation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-005001_mcpci002_cicd-dispatch-reconciliation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-150154
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_github_actions.py`, `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`
