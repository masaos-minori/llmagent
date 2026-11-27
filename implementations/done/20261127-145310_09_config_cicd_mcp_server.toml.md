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
- Step 3a verification (20261127, conflict with the tool gate): the `workflow_allowlist` block is 8 consecutive comment lines and is recorded as a grandfathered exception at `config/cicd_mcp_server.toml:8` in `tools/check_config_comment_length.py`. Growing it or inserting a comment line before it changes the block's length or position, which the checker treats as an error-level finding. So the hard-maximum statement is written as a new block of at most 5 consecutive comment lines attached to `max_log_size_kb`, and the `repo_allowlist` / `workflow_allowlist` blocks are left unchanged.
- Step 3a verification (20261127): the documented values match the enforced constants — `MAX_LOG_SIZE_KB = 1024`, `MAX_ALLOWLIST_SIZE = 100` (`scripts/mcp_servers/cicd/cicd_models.py:31-32`).

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
- `uv run python tools/check_config_comment_length.py` (per `rules/tool-gates.md`, a `config/**/*.toml` edit): the added comment text must stay within the 5-consecutive-comment-line threshold (`CFG-COMMENT-001`). The current `github_token` block is 2 lines, so the precedence and hard-maximum statements must be written as separate blocks of at most 5 consecutive comment lines.

## Completion criteria
- The documented values equal the module constants (AC-5); the consistency checker reports no finding.

## Out of Scope
- The enforcement code (`cicd_models.py` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | precedence stated in the github_token block; hard maximums stated in a new 4-line block at max_log_size_kb; grandfathered workflow_allowlist block left unchanged |
| 2 | Add or update tests per Validation plan | N/A | — | — | config-only change, cross-checked by the docs consistency checker |
| 3 | Run the validation sequence (`rules/tool-gates.md` docs checker) | Completed | — | — | check_config_comment_length.py: 0 errors, 7 grandfathered warnings; check_docs_consistency.py --domain mcp: no issues |

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