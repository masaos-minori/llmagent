## Goal
Document the GitHub write outcomes, timeouts, and audit phases (REQ-010).
## Scope
**Release unit**: N/A: not part of a release unit
## Assumptions
- Written in English; the final sweep of the MCP documents stays with a separate work item.
- Edit lands after the code documents.
## Design decisions
- Edit existing text in place; do not append contradicting statements.
## Alternatives considered
N/A: docs-only row.
## Implementation
### Target file
`docs/22_mcp/mcp_04_01_web-search-file-read-github.md`
### Procedure
Edit the relevant sections.
### Method
- Describe the intent and completion audit and the identifiers in each record, and replace the sentence that a failed audit write returns HTTP 500 with the three outcomes: pre-write audit failure (nothing applied), applied_audit_failed, and `outcome_unknown` (HTTP 504).
- State that all GitHub writes are non-retryable, the client never re-sends a write, and the two timeout keys.
- Mention the audit-failure count in `/health`.
### Details
- Run the documentation checkers via `tools/run_validation_gates.py`.
## Compatibility considerations
N/A: docs-only.
## Security considerations
N/A: docs-only.
## Rollback considerations
N/A: revert the commit.
## Validation plan
- `uv run python tools/run_validation_gates.py`
## Completion criteria
- The document matches the implemented behavior and the gates pass.
## Out of Scope
- ADR text (no decision changes) and the MCP design-document final sweep.
## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation > Procedure/Method/Details | Completed | 20261125-192108 | 20261125-192108 | audit bullet rewritten to the three outcomes, write retry policy paragraph added, timeout keys added to the config list, error mapping and health updated |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | 20261125-192108 | 20261125-192108 | run_validation_gates fast mode all Pass after fixing the github_service_init.py docstring separator |
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
- **Requirement ID**: REQ-010
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-124502_mcpai006_github-write-retry-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-125134
- **Related target files**: `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`