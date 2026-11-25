## Goal
List the two new GitHub configuration keys (REQ-010).
## Scope
**Release unit**: N/A: not part of a release unit
## Assumptions
- The inventory lists GitHub keys such as `max_file_read_size_kb`; follow its format.
## Design decisions
- Edit existing text in place; do not append contradicting statements.
## Alternatives considered
N/A: docs-only row.
## Implementation
### Target file
`docs/22_mcp/mcp_06_01_configuration-file-inventory.md`
### Procedure
Edit the relevant sections.
### Method
- Add `connect_timeout_sec` and `read_timeout_sec` to the GitHub key list with defaults 5 and 30 and the strict positive-number rule.
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
| 1 | Edit the document per Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — |  |
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
- **Related target files**: `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`
