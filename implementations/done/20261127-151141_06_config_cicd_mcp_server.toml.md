# Implementation Procedure — config/cicd_mcp_server.toml

## Goal

Document the raw-download and decompressed byte limits, the maximum redirect count, and the trusted
GitHub log hosts the code enforces.

## Scope
**Release unit**: N/A: not part of a release unit

Requirements implemented: REQ-001 (the redirect policy and trusted hosts are recorded), REQ-002 (the
independent byte limits are recorded), REQ-007 (documentation of the limits). Acceptance criterion: AC-1.

## Assumptions
- The file has `max_log_size_kb = 256` with no stated maximum and no download, decompressed, or redirect
  keys (re-verified 20261127); the change is comment-only, no value changes.
- The enforced values are module constants in `scripts/mcp_servers/cicd/cicd_models.py`
  (`MAX_RAW_DOWNLOAD_BYTES` (new), `MAX_DECOMPRESSED_BYTES` (new), `MAX_REDIRECTS` (new),
  `TRUSTED_LOG_HOSTS` (new)); this document records them, it does not move them into configuration. If
  the owner makes them configuration, the Plan is amended (Plan Assumption, UNK-02).
- The credential-precedence and hard-maximum comments added by the mcpci001 pass on this same file are
  kept; this document adds the streaming-bounds block only (Plan Assumption, compatible overlap).

## Design decisions
- N/A: comment-only change. The values the comment records were decided 20261127 in Step 3a
  (UNK-02): raw download 1 MiB, decompressed 1 MiB, maximum redirects 3, trusted log hosts
  `api.github.com`, `results-receiver.actions.githubusercontent.com`,
  `productionresultssa*.blob.core.windows.net`; the returned-output limit stays `max_log_size_kb`
  (256 here, hard maximum 1024).

## Alternatives considered
- Adding new config keys for the limits: rejected per the Plan's Assumptions — the constants are the
  enforced source, and the config file documents them.

## Implementation
### Target file
`config/cicd_mcp_server.toml`

### Procedure
- Add a comment block stating the raw-download limit, the decompressed limit, the maximum redirect
  count, and the trusted GitHub log hosts.
- State the four limits as the contract: raw download, decompressed, selected job, returned output.

### Method
- Update the comment block above `max_log_size_kb` (lines 18-21; the value is at line 22, re-verified
  20261127) in place; keep the existing value. The block also records `LOG_FETCH_TIMEOUT_S` (new) = 10 as the
  per-hop fetch timeout the job backend passes to `fetch_bounded`.

### Details
- `deploy/deploy.sh:164` already has a `cp` line for this file; no deployment change is needed.

## Compatibility considerations
- N/A: comments only; the parsed values do not change.

## Security considerations
- N/A: the enforcement lives in the job backend and the models rows.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Unit: shipped-config test — `uv run pytest tests/mcp_servers/test_shipped_dedup_config.py` (reference
  file, not modified).
- Cross-check: documented values match the enforced constants —
  `uv run python tools/check_docs_consistency.py --domain mcp`.
- Per `rules/tool-gates.md`, run the applicable docs checker after the change.

## Completion criteria
- The documented values equal the module constants (AC-1); the consistency checker reports no finding.

## Out of Scope
- The enforcement code (`cicd_models.py` and `cicd_service_github_actions_job.py` rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | comment block records the four limits, the redirect policy, the trusted hosts, and the per-hop timeout |
| 2 | Add or update tests per Validation plan | N/A | — | — | config-only change, cross-checked by the docs consistency checker |
| 3 | Run the validation sequence (`rules/tool-gates.md` docs checker) | Completed | — | — | check_docs_structure and check_docs_consistency --domain mcp clean; shipped-config test 41 passed |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-007 (configuration record of the streaming bounds)
- **Source issue**: issues/20261119-141110_mcpci003_cicd-log-streaming-bounds.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-065519_mcpci003_cicd-log-streaming-bounds.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-151141
- **Related target files**: `config/cicd_mcp_server.toml`