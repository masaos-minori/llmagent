# Implementation Procedure — config/cicd_mcp_server.toml

## Goal

Document the effective-credential precedence and the hard maximum values the new validation enforces in the server configuration file.

## Scope
**Release unit**: N/A: not part of a release unit

Requirements implemented: REQ-001 (documented credential precedence), REQ-006 (allowlist hard maximum), REQ-007 (`max_log_size_kb` hard maximum). Acceptance criterion: AC-5.

## Assumptions
- The file already documents `github_token` as the fallback when `GITHUB_TOKEN` is unset (verified); the comment is kept and extended to state the precedence as the contract.

## Design decisions
- N/A: comment-only change; the enforced constants live in `scripts/mcp_servers/cicd/cicd_models.py` (`MAX_LOG_SIZE_KB` (new), `MAX_ALLOWLIST_SIZE` (new)).

## Alternatives considered
- N/A: documentation-only change in a config file.

## Implementation
### Target file
`config/cicd_mcp_server.toml`

### Procedure
- State the precedence explicitly: the `GITHUB_TOKEN` environment variable wins, the config value is the fallback.
- State the hard maximums: `max_log_size_kb` 1..1024, allowlist size 1..100.

### Method
- Update the existing comment blocks for `repo_allowlist`, `workflow_allowlist`, `max_log_size_kb`, and `github_token`; no value changes.

### Details
- `deploy/deploy.sh:164` already has a `cp` line for this file; no deployment change is needed.

## Compatibility considerations
- N/A: comments only; the parsed values do not change.

## Security considerations
- N/A: the enforcement lives in the models and guards rows.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Cross-check: documented values match the enforced constants — `uv run python tools/check_docs_consistency.py --domain mcp`.
- Per `rules/tool-gates.md`, run the applicable docs checker after the change.

## Completion criteria
- The documented values equal the module constants (AC-5); the consistency checker reports no finding.

## Out of Scope
- The enforcement code (`cicd_models.py` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | N/A | — | — | config-only change, cross-checked by the docs consistency checker |
| 3 | Run the validation sequence (`rules/tool-gates.md` docs checker) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-006, REQ-007 (configuration record of the precedence and hard maximums)
- **Source issue**: issues/20261119-141106_mcpci001_cicd-credential-config-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-152931_mcpci001_cicd-credential-config-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-145310
- **Related target files**: `config/cicd_mcp_server.toml`
