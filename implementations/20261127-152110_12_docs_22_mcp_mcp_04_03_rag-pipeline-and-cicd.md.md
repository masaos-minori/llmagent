# Implementation Procedure — docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md

## Goal

Add the CI/CD error mapping table and correct the audit statement in the CI/CD server section.

## Scope
**Release unit**: N/A: not part of a release unit

Requirement implemented: REQ-009 (the document carries the error mapping table and the corrected audit
statement). Acceptance criterion: AC-7.

## Assumptions
- Line 74 states that a disabled-tool rejection returns before the audit call and writes no record, which
  this Plan makes false (re-verified 20261127); line 66 records only that records are written via
  `_audit_log()` with `server_key="cicd"`.
- The credential, permission, and allowlist passages are the mcpci001 pass's work and the log-retrieval
  paragraph is the mcpci003 pass's work; this document changes the audit statement and adds the error
  mapping section only (Plan Assumptions, compatible overlap).
- Per the mcpci001 plan's Assumptions, run the mcpai012 CI/CD consistency sweep after these rows land,
  otherwise the sweep rewrites the section against the pre-change source.

## Design decisions
- N/A: documentation-only change.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`

### Procedure
- Add an error mapping table mirroring the status-to-(exception, error-code) table the backend row
  implements: 401, 403, 404, 409, 422, 429, 5xx, and the transport failures, with the HTTP status each one
  answers.
- Correct the audit statement at line 74: every authenticated call produces exactly one record, including
  a disabled-tool rejection and an exception, and an audit-write failure is logged and counted.

### Method
- Update the audit passage at line 74 in place; keep the three-layer naming and the cross-reference to
  `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` rather than restating the field list.

### Details
- N/A.

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_structure.py` and `uv run python tools/check_docs_quality.py` (per
  `rules/tool-gates.md`).

## Completion criteria
- The section carries the error mapping table and the corrected audit statement (AC-7); the doc checkers
  report no finding.

## Out of Scope
- The credential and allowlist paragraphs (mcpci001's row) and the log-retrieval paragraph (mcpci003's
  row) in the same file.

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
- **Requirement ID**: REQ-009 (CI/CD error mapping table and corrected audit statement)
- **Source issue**: issues/20261119-141111_mcpci004_cicd-error-audit-coverage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-070305_mcpci004_cicd-error-audit-coverage.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-152110
- **Related target files**: `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`
