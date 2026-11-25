## Goal
Record that GitHub writes are non-retryable and fail closed on a dedup-store failure (REQ-010).
## Scope
**Release unit**: N/A: not part of a release unit
## Assumptions
- Retryable fail-open text for other servers stays unchanged.
## Design decisions
- Edit existing text in place; do not append contradicting statements.
## Alternatives considered
N/A: docs-only row.
## Implementation
### Target file
`docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
### Procedure
Edit the relevant sections.
### Method
- Add GitHub writes to the non-retryable fail-closed examples and state that a timeout never implies non-application.
- Correct any statement listing a GitHub write as retryable fail-open.
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
| 1 | Edit the document per Implementation > Procedure/Method/Details | Completed | 20261125-192309 | 20261125-192309 | retry-classification paragraph added after the fail-closed runtime paragraph; table rows unchanged |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | 20261125-192309 | 20261125-192309 | run_validation_gates fast mode all Pass |
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
- **Related target files**: `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`