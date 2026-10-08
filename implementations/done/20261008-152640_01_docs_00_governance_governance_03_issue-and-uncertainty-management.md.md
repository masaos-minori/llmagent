## Goal
Remove the resolved MCP-001 entry from the Known Issue ledger so the conformance check and the live-ledger test pass (REQ-001 of the Plan).

## Scope
- Delete the MCP-001 table row and its detail section; nothing else in the ledger changes.

## Assumptions
- The audit-record emission defect is resolved in code (the audit helper accepts the target parameters the git server passes), verified during planning.
- The ledger policy removes resolved items rather than marking them.

## Design decisions
- Remove the whole entry including its resolution-note field; history stays in version control.

## Alternatives considered
- Correcting the status and dropping the extra field: rejected; the policy keeps only active items.

## Implementation
### Target file
docs/00_governance/governance_03_issue-and-uncertainty-management.md

### Procedure
1. Fetch and confirm the ledger still contains the entry and has not been edited upstream.
2. Delete the table row beginning with the MCP-001 ID and the detail section from its heading up to the next entry heading.
3. Search the ledger for other mentions of the ID (Related or Target fields) and correct them.
4. Run the conformance checker and the live-ledger test.

### Method
Two targeted deletions located by the ID.

### Details
After the edit the ledger has no string MCP-001. The ADR-012 change in procedure 02 removes the last citation.

## Compatibility considerations
- The sync checker needs the ledger and ADR-012 to agree; apply procedure 02 in the same change.

## Security considerations
- None: documentation only.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run python tools/check_issue_inventory_conformance.py`; `uv run pytest tests/tools/test_check_issue_inventory_conformance.py -q`; `check_known_deviation_sync.py`; `check_docs_structure.py`; `check_docs_quality.py`.

## Completion criteria
- The ledger has no MCP-001; the conformance checker reports no errors and the live-ledger test passes (REQ-001).

## Out of scope
- Other ledger entries.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the MCP-001 row and section | Completed | 20261008-152750 | 20261008-152750 |  |
| 2 | Run the conformance checker and the live-ledger test | Completed | 20261008-152750 | 20261008-152750 |  |

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
- **Requirement ID**: REQ-001 (remove the resolved entry)
- **Source issue**: issues/20261008-150554_ledgermcp001_remove-the-resolved-mcp-001-from-the-known-issue-ledger-and-fix-the-failing-conformance-test.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-150850_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-152640
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md