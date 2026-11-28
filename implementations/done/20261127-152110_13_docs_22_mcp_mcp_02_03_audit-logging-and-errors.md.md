# Implementation Procedure — docs/22_mcp/mcp_02_03_audit-logging-and-errors.md

## Goal

State the exactly-one-event rule for the CI/CD server, the redaction rules, and the audit-failure policy
decided by the owner.

## Scope
**Release unit**: N/A: not part of a release unit

Requirements implemented: REQ-007 (the audit-failure policy), REQ-009 (the exactly-one-event rule and the
redaction rules). Acceptance criteria: AC-4, AC-7.

## Assumptions
- Line 30 states the one-record rule for every server that writes the shared audit log, which the CI/CD
  server currently violates on the disabled and validation paths (re-verified 20261127); line 58 states the
  exactly-once rule for web-search-mcp only; the Common Error Formats table (section at line 68) lists
  "Server error | 500" at line 75 with no per-server mapping.
- The three audit layers named at line 22 stay three separate layers; this document does not merge the
  Agent-side audit log, the server application log, and the `mcp_tool_exec` event (Plan Assumptions).

## Design decisions
- N/A: documentation-only change.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`

### Procedure
- Extend the one-record rule at line 30 so the CI/CD server is covered on every path: success, disabled
  tool, unknown tool, validation, authorization, upstream, dedup, and unexpected outcome.
- State the audit-failure policy for the CI/CD server as the never-propagate pattern: log the failure and
  increment `audit_failure_count` (the owner's decision on 20261127, matching
  `scripts/mcp_servers/git/git_server.py`), and name the raise-on-failure pattern as the rejected
  alternative.
- Record the redaction rules already provided by `scripts/mcp_servers/audit.py` as the contract the CI/CD
  record follows: no token, no workflow input value, no raw upstream payload text.

### Method
- Update the exactly-once paragraph at line 58 in place so it names the CI/CD server as well as
  web-search-mcp; keep the Common Error Formats table and add the per-server CI/CD mapping reference
  rather than duplicating the table from the CI/CD document.
- Step 3b correction: the citations hold at revision da8097e74 (line 30, line 58, the table section at 68
  with the "Server error | 500" row at 75). The reference is one sentence after the table pointing to
  `mcp_04_03_rag-pipeline-and-cicd.md`; the table itself is unchanged.

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
- The audit document carries the exactly-one-event rule for the CI/CD server, the redaction rules, and the
  never-propagate audit-failure policy (AC-7); the doc checkers report no finding.

## Out of Scope
- The CI/CD error mapping table, which the sibling CI/CD document row owns; the shared helper itself,
  whose only change is the duplicate assignment removal.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261128 | 20261128 | line 30 extended to cover the CI/CD server on every path; line 58 paragraph names cicd-mcp; never-propagate policy recorded with the rejected raise-on-failure alternative; redaction contract restated; one reference sentence added after the Common Error Formats table |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | 20261128 | 20261128 | `check_docs_structure.py` and `check_docs_quality.py` pass |

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
- **Requirement ID**: REQ-007, REQ-009 (exactly-one-event rule, redaction rules, audit-failure policy)
- **Source issue**: issues/20261119-141111_mcpci004_cicd-error-audit-coverage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-070305_mcpci004_cicd-error-audit-coverage.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-152110
- **Related target files**: `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`
