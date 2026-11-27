# Implementation Procedure — docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md

## Goal

Record the credential precedence, the required GitHub Actions permissions, empty-allowlist behavior, the workflow-identifier terminology and both identifier forms, and the module layout in the CI/CD server section.

## Scope
**Release unit**: N/A: not part of a release unit

Requirement implemented: REQ-010 (documentation records the credential, permission, allowlist, identifier, and module-layout contract). Acceptance criterion: AC-8.

## Assumptions
- Per the Plan's Assumptions, run the mcpai012 CI/CD consistency sweep after this row lands, otherwise the sweep rewrites the section against the pre-change source.
- Lines 56-72 currently document the config keys, `GITHUB_TOKEN` authentication, health dependency values, and guard behavior (verified).

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

## Completion criteria
- The section states the precedence, permissions, empty-allowlist behavior, both identifier forms, and the module layout (AC-8); the doc checkers report no finding.

## Out of Scope
- The allowlist normalization section (`mcp_05_01_access-control-and-allowlists.md` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
