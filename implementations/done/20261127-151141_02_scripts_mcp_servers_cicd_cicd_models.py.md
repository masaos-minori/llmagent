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
  `TRUSTED_LOG_HOSTS` (new), `LOG_FETCH_TIMEOUT_S` (new; added 20261127 in Step 3b because
  `fetch_bounded` requires `timeout_sec` and this module has no timeout value). Values are decided at
  implementation (UNK-02); the config row documents them. Decided 20261127 in Step 3a:
  `MAX_RAW_DOWNLOAD_BYTES = 1_048_576` (1 MiB),
  `MAX_DECOMPRESSED_BYTES = 1_048_576` (1 MiB), `MAX_REDIRECTS = 3`, and
  `TRUSTED_LOG_HOSTS = {"api.github.com", "results-receiver.actions.githubusercontent.com",
  "productionresultssa*.blob.core.windows.net"}` — the GitHub-documented Actions log hosts
  (docs.github.com, self-hosted runners network access; observed 302 targets). The blob entry is a
  prefix match, not an allowlist wildcard, so `rules`' wildcard-rejection rule for configured
  allowlists does not apply to this module constant. `LOG_FETCH_TIMEOUT_S = 10` is the per-hop timeout
  the job backend passes to `fetch_bounded` (user decision 20261127); the helper's overall deadline is
  `timeout_sec * (max_redirects + 1)` = 40 s.
- The response model is the carrier for per-job status, included bytes, error code, and truncation
  state, so failure is machine-distinguishable rather than text.
- The response models are frozen dataclasses, matching `DispatchOutcome` added to this same file by
  the mcpci002 pass; the request models stay Pydantic. Per-job status and truncation reason are
  stable string values, not raw exception text.

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
- Add `LogFetchResult` (new): the job list, `output` (new, added 20261127 in Step 3b by user decision —
  the assembled final text of headers, log bytes, and the truncation marker; the procedure's original
  list had no text carrier, which left REQ-003 and REQ-005 unanswerable), `partial_success` (new), and
  the totals.
- Add the constants listed in Design decisions, plus the stable value sets `LOG_JOB_STATUSES` (new),
  `LOG_ERROR_CODES` (new), and `TRUNCATION_REASONS` (new) so the model can reject a value outside the
  contract instead of accepting raw exception text.
- Model invariants (self-checking, frozen dataclasses): a failed job carries an error code and no other
  status carries one; `LogFetchResult.partial_success` must match the per-job statuses; the totals
  counts must match the job list; `totals.visible_bytes` must equal `len(output.encode())`.

### Method
- Lines 248-253 define `GetWorkflowLogsRequest` (re-verified 20261127 against the current file,
  298 lines; the Plan's citation of 133-137 predates the mcpci001 pass). It is no longer the last
  class: the mcpci002 pass appended the dispatch outcome section (lines 255-298), so add the log
  response models at the end of the file, after that section, without changing the request models.

### Details
- Error codes are stable string values, not raw exception text (REQ-004).

## Compatibility considerations
- The request schema shape is unchanged, so the pins in `tests/mcp_servers/cicd/test_cicd_models.py`
  lines 36-104 stay (re-verified 20261127; the Plan's citation of 35-54 covers only the first pin);
  the response-shape tests are added by the sibling test row.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | log limit constants, TRUSTED_LOG_HOSTS, LogJobResult/LogTotals/LogFetchResult with self-checking invariants |
| 2 | Add or update tests per Validation plan | N/A | — | — | the covering test file has its own procedure document (Plan row 9) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff/mypy Pass; shape tests in test_cicd_models.py |
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