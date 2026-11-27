# Implementation Procedure — scripts/mcp_servers/cicd/cicd_models.py

## Goal

Add the log response model with per-job status, included bytes, error code, truncation state,
`partial_success` (new), and the totals, plus the raw-download and decompressed byte-limit constants.

## Scope
**Release unit**: N/A: not part of a release unit

Requirements implemented: REQ-002 (the independent limit constants), REQ-003 (the budget the constants
express), REQ-004 (per-job fields and `partial_success` (new)), REQ-005 (totals). Acceptance criteria: AC-1,
AC-4.

## Assumptions
- The raw-download and decompressed limits and the redirect maximum are module constants, not
  configuration (Plan Assumption; UNK-02 resolved as constants unless the owner makes them
  configuration, in which case the Plan is amended with the config row already present).
- The strict request models from the mcpci001 pass already exist in this file; this document adds the
  log response model and the constants only.
- The mcpci002 pass adds the dispatch response model to the same file; the two models are separate
  contracts on different functions (Plan Assumption, compatible overlap).

## Design decisions
- Constants: `MAX_RAW_DOWNLOAD_BYTES` (new), `MAX_DECOMPRESSED_BYTES` (new), `MAX_REDIRECTS` (new),
  `TRUSTED_LOG_HOSTS` (new). Values are decided at implementation (UNK-02); the config row documents
  them.
- The response model is the carrier for per-job status, included bytes, error code, and truncation
  state, so failure is machine-distinguishable rather than text.

## Alternatives considered
- Enforcing the byte budget in the shared helper: rejected per the Plan's Byte-budget ownership
  decision — `FetchLimits.returned_bytes` is carried, not enforced, so the model only reports what the
  job backend enforced.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_models.py`

### Procedure
- Add `LogJobResult` (new): job id, status, included bytes, error code, truncation state.
- Add `LogTotals` (new): jobs, included jobs, failed jobs, downloaded bytes, visible bytes, truncation
  reason.
- Add `LogFetchResult` (new): the job list, `partial_success` (new), and the totals.
- Add the four constants listed in Design decisions.

### Method
- Lines 133-137 define `GetWorkflowLogsRequest`, the last class in the file (re-verified 20261127);
  add the response models after it without changing the request models.

### Details
- Error codes are stable string values, not raw exception text (REQ-004).

## Compatibility considerations
- The request schema shape is unchanged, so the pins in `tests/mcp_servers/cicd/test_cicd_models.py`
  lines 35-54 stay; the response-shape tests are added by the sibling test row.

## Security considerations
- N/A: model definitions only; no token or raw upstream text is stored.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Unit: response-model shape and limit constants —
  `uv run pytest tests/mcp_servers/cicd/test_cicd_models.py` (the tests are written by the sibling
  document for that row).
- Full sequence per `rules/toolchain.md`, including the `agent-mcp-config-models` import-linter contract.

## Completion criteria
- Per-job fields, `partial_success` (new), and the totals are pinned (AC-4); the constants express the
  independent raw and decompressed bounds (AC-1).

## Out of Scope
- Enforcing the budget at call time (`cicd_service_github_actions_job.py` row); the config record
  (`config/cicd_mcp_server.toml` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | N/A | — | — | the covering test file has its own procedure document (Plan row 9) |
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
- **Requirement ID**: REQ-002, REQ-003, REQ-004, REQ-005 (log response model and limit constants)
- **Source issue**: issues/20261119-141110_mcpci003_cicd-log-streaming-bounds.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-065519_mcpci003_cicd-log-streaming-bounds.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-151141
- **Related target files**: `scripts/mcp_servers/cicd/cicd_models.py`
