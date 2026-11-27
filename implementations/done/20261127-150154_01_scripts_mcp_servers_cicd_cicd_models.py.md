# Implementation Procedure — scripts/mcp_servers/cicd/cicd_models.py

## Goal

Add the structured dispatch-outcome model for the five states and the matched-run fields, reusing `outcome_unknown` from the shared write-outcome vocabulary.

## Scope
**Release unit**: N/A: not part of a release unit

Requirements implemented: REQ-001 (structured dispatch outcome with five states), REQ-003 (matched-run fields, bounded polling constants). Acceptance criteria: AC-1, AC-2, AC-5.

## Assumptions
- The five states stay a cicd-scoped contract; `RECONCILE_OUTCOMES` in `scripts/shared/mcp_call_state_contract.py` is the closed shared vocabulary and is not extended (Plan Design decision, mcpdl004 ownership).
- The polling timeout and interval are module constants here, not configuration (Plan Assumption; UNK-02 resolved as constants unless the owner makes them configuration).
- The strict request models from the mcpci001 pass already exist in this file; this document adds the response counterpart only.

## Design decisions
- `DispatchOutcome` (new) carries `state` plus the matched-run fields (run id, URL, status, workflow, ref); `outcome_unknown` is imported from `scripts/shared/write_outcome.py` (`OUTCOME_UNKNOWN` at line 25) rather than redefined.
- Polling bounds are constants `POLL_TIMEOUT_S` (new) and `POLL_INTERVAL_S` (new), decided at implementation (UNK-02).
  Decided 20261127 in Step 3a: `POLL_TIMEOUT_S = 10`, `POLL_INTERVAL_S = 2`, so the polling loop stays inside
  the lifespan-owned shared HTTP client timeout of 30.0 s (`scripts/mcp_servers/cicd/cicd_server.py:205`).

## Alternatives considered
- Extending the shared `RECONCILE_OUTCOMES` set with accepted and accepted_unconfirmed: rejected per the Plan — that vocabulary is owned by mcpdl004 and read by the control API and the Agent recovery service.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_models.py`

### Procedure
- Define `DispatchState` (new) with the five states: accepted, confirmed, accepted_unconfirmed, `outcome_unknown`, reconciliation_required.
- Define `DispatchOutcome` (new) with `state` and the matched-run fields; confirmed requires a matched run.
- Add `POLL_TIMEOUT_S` (new) and `POLL_INTERVAL_S` (new) constants.

### Method
- The request models at lines 207-247 have no response counterpart (re-verified 20261127 against the
  current file, 251 lines; the Plan's citation of lines 88-137 predates the mcpci001 pass); add the
  response model after them without changing the request models.

### Details
- A 2xx response never becomes confirmed without a matched run (REQ-001); the state is set by the backend row, not by the model.

### Companion test files
- `tests/mcp_servers/cicd/test_cicd_models.py`
  - Procedure: add the response-model shape tests for the five states and the matched-run fields (the
    request-schema pins at lines 36-104 stay; the Plan's citation of 35-54 covers only the first pin,
    re-verified 20261127).
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_cicd_models.py`.

## Compatibility considerations
- The handler contract stays `-> str` (the structured outcome is JSON-serialized), so `dispatch_tool` and the audit `outcome` mapping are unchanged (Plan Assumption).

## Security considerations
- N/A: no security behavior changes here.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Unit: response-model shape and state totality — `uv run pytest tests/mcp_servers/cicd/test_cicd_models.py`.
- Full sequence per `rules/toolchain.md`, including the `agent-mcp-config-models` import-linter contract.

## Completion criteria
- The five states and the matched-run fields are pinned; no state is produced without a matched run (AC-2).

## Out of Scope
- The run lookup and polling execution (`cicd_service_github_actions.py` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261127-222027 | cicd_models.py: DISPATCH_STATES (5 states), DispatchOutcome (frozen dataclass, confirmed requires run_id), POLL_TIMEOUT_S=10 / POLL_INTERVAL_S=2 (UNK-02 user decision) |
| 2 | Add or update tests per Validation plan (companion test file) | Completed | — | 20261127-222027 | tests/mcp_servers/cicd/test_cicd_models.py: response-model shape tests (frozen, run_id required for confirmed) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261127-222027 | ruff/mypy/lint-imports/bandit/pre-commit pass; cicd suite 317 passed; end-of-unit full suite: 6 known baseline failures (compare_test_baseline exit 0), diff-cover 93% >= 90 |
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
- **Requirement ID**: REQ-001, REQ-003 (structured dispatch outcome, matched-run fields)
- **Source issue**: issues/20261119-141109_mcpci002_cicd-dispatch-reconciliation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-005001_mcpci002_cicd-dispatch-reconciliation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-150154
- **Related target files**: `scripts/mcp_servers/cicd/cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_models.py`