## Goal
Describe the current audit behavior in ADR-012 and remove the resolved MCP-001 and MCP-002 lines from its Known Deviations (REQ-002, REQ-003 of the Plan).

## Scope
- Edit the audit bullet in Security Consequences and the Known Deviations lines for MCP-001 and MCP-002; keep the MCP-004 line unchanged.

## Assumptions
- The user decided to remove the MCP-002 prose line as well.
- The audit behavior stated in the git MCP reference is current: every call that passes argument validation is audited; the canonical repository path is in the target field; the pre- and post-condition state is recorded on dispatched calls.

## Design decisions
- State behavior, not history: no mention of a fix or a former defect.

## Alternatives considered
- Keeping a short "resolved" note: rejected; the ADR describes current behavior and the ledger is the only Known Issue record.

## Implementation
### Target file
docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md

### Procedure
1. Verify the audit claim against the audit module and the git server.
2. Replace the second Security Consequences bullet with the current-behavior statement.
3. Remove the MCP-001 line and the MCP-002 prose line from Known Deviations; leave the MCP-004 line.
4. Run the checkers.

### Method
Unique-text edits.

### Details
New bullet: audit records identify the affected repository and capture the pre- and post-condition state; every call that passes argument validation is audited, with the canonical repository path in the target field (Explicit in code — the git server and audit modules). Known Deviations then contains only the MCP-004 residual-deviation line.

## Compatibility considerations
- The Decision and Invariants do not change, so no new approval record is needed.

## Security considerations
- None: documentation only.

## Rollback considerations
- Revert the commit.

## Validation plan
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_known_deviation_sync.py`, `check_docs_consistency.py --domain mcp`; `rg -n 'MCP-001|MCP-002' docs/10_adr/ADR-012-*.md` returns nothing.

## Completion criteria
- The audit bullet matches the code and the reference; no MCP-001 or MCP-002 mention remains; the MCP-004 line remains; the checkers pass (REQ-002, REQ-003).

## Out of scope
- Decision, Invariants, Verification, and other sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the audit bullet | Completed | 20261008-152750 | 20261008-152750 |  |
| 2 | Remove the MCP-001 and MCP-002 lines | Completed | 20261008-152750 | 20261008-152750 |  |
| 3 | Run the checkers | Completed | 20261008-152750 | 20261008-152750 |  |

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
- **Requirement ID**: REQ-002 (audit sentence), REQ-003 (Known Deviations)
- **Source issue**: issues/20261008-150554_ledgermcp001_remove-the-resolved-mcp-001-from-the-known-issue-ledger-and-fix-the-failing-conformance-test.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-150850_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-152640
- **Related target files**: docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md