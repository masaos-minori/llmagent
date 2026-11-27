# Implementation Procedure — docs/22_mcp/mcp_05_01_access-control-and-allowlists.md

## Goal

Record the CI/CD allowlist normalization, wildcard and oversized-value rejection, and the new credential posture check.

## Scope
**Release unit**: N/A: not part of a release unit

Requirements implemented: REQ-006 (allowlist normalization and rejection), REQ-010 (documentation). Acceptance criteria: AC-5, AC-8.

## Assumptions
- Lines 39, 88, 133-142 currently document the cicd allowlists and the posture check that refuses bind (verified).

## Design decisions
- N/A: documentation-only change.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`

### Procedure
- State that CI/CD allowlist entries are normalized with the shared `owner/repo` policy and that wildcard and oversized entries are rejected before bind.
- Add the credential posture check (`server.github_credential` (new)) to the posture-check description.

### Method
- Update the existing cicd passages at lines 39, 88, 133-142 in place; keep the fail-closed statement.

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
- The section states normalization, wildcard and oversized rejection, and the credential posture check (AC-8); the doc checkers report no finding.

## Out of Scope
- The CI/CD server section (`mcp_04_03_rag-pipeline-and-cicd.md` row).

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
- **Requirement ID**: REQ-006, REQ-010 (allowlist normalization documentation and credential posture check)
- **Source issue**: issues/20261119-141106_mcpci001_cicd-credential-config-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-152931_mcpci001_cicd-credential-config-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-145310
- **Related target files**: `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`
