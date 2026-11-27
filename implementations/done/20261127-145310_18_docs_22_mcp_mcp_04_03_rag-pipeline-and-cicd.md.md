# Implementation Procedure — docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md

## Goal

Record the credential precedence, the required GitHub Actions permissions, empty-allowlist behavior, the workflow-identifier terminology and both identifier forms, and the module layout in the CI/CD server section.

## Scope
**Release unit**: N/A: not part of a release unit

Requirement implemented: REQ-010 (documentation records the credential, permission, allowlist, identifier, and module-layout contract). Acceptance criterion: AC-8.

## Assumptions
- Per the Plan's Assumptions, run the mcpai012 CI/CD consistency sweep after this row lands, otherwise the sweep rewrites the section against the pre-change source.
- Lines 56-72 currently document the config keys, `GITHUB_TOKEN` authentication, health dependency values, and guard behavior (verified).
- Step 3a verification (20261127): line 64 (not 63) pins `/health` as `dependencies.github_token="not_set"` or `dependencies.config="check failed"`; it must be restated as the effective credential plus the probe outcome, because health now reads the resolved value rather than the environment variable alone. Per the user decision on 20261127, `dependencies.credential_probe` is reported only on probe failure, so an OK or `not_applicable` probe leaves `dependencies` empty and the ready rule is unchanged.
- Step 3a verification (20261127): line 72 states that `trigger_workflow` compares the request's `workflow` value by exact match on the raw value. Under REQ-005 the comparison is on canonical values, so this sentence must change; the startup `server.workflow_pattern_valid` statement stays.
- Step 3a verification (20261127): line 65 names only `GitHubActionsBackend`; the module layout must also name the composite and job backends.
- Step 3a verification (20261127): the required-permission statement is written without concrete threshold values, per `skills/DESIGN.md` "No concrete configuration values"; the values live in `scripts/mcp_servers/cicd/cicd_models.py` and `config/cicd_mcp_server.toml`.

## Design decisions
- N/A: documentation-only change.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`

### Procedure
- State the credential precedence (environment wins, config fallback) and the fail-closed startup rule for a write-capable start.
- State the required GitHub Actions permissions and that dispatch permission is reported `not_applicable` by the probe.
- Keep the empty-allowlist deny-all statement, add the workflow-identifier terminology with both forms (file name and numeric id), and the module layout including the composite and job backends.

### Method
- Update the cicd-mcp section (lines 56-72) in place; keep the cross-reference to `security_02_high-risk-tool-common-policy.md`.

### Details
- N/A.

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` (per `rules/tool-gates.md`).
- `uv run python tools/check_docs_consistency.py --domain mcp` (per `rules/tool-gates.md`, the docs change touches the mcp domain); it cross-checks the config keys and symbol references written here against `config/cicd_mcp_server.toml` and `scripts/`.

## Completion criteria
- The section states the precedence, permissions, empty-allowlist behavior, both identifier forms, and the module layout (AC-8); the doc checkers report no finding.

## Out of Scope
- The allowlist normalization section (`mcp_05_01_access-control-and-allowlists.md` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — |  |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | — | — | check_docs_quality.py, check_docs_structure.py, check_docs_consistency.py --domain mcp: no findings |

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
- **Requirement ID**: REQ-010 (CI/CD server documentation)
- **Source issue**: issues/20261119-141106_mcpci001_cicd-credential-config-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-152931_mcpci001_cicd-credential-config-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-145310
- **Related target files**: `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`