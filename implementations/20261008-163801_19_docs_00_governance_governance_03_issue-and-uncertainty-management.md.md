## Goal
Remove the resolved RAG-001 and MCP-005 ledger entries. (REQ-001, REQ-003 of the Plan).

## Scope
- Only `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; no other file is modified by this procedure.

## Assumptions
- User decisions (2026-10-08): add a new inbound `auth_token` for the rag-pipeline server and keep `rag_auth_token` as the outbound token; the external RAG service accepts `Authorization: Bearer`.

## Design decisions
- Do this last, after the code and tests pass.

## Alternatives considered
- Reusing `rag_auth_token` for the inbound check: rejected by the user decision above.

## Implementation
### Target file
docs/00_governance/governance_03_issue-and-uncertainty-management.md

### Procedure
1. Delete both entries from Part 1 (resolved items are removed).
2. Check that no other document still cites the IDs.

### Method
Do this last, after the code and tests pass.

### Details
Resolved items are removed per governance_03.

## Compatibility considerations
- Documentation only.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- `check_known_deviation_sync.py`, `check_issue_inventory_conformance.py`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py`.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-001, REQ-003).

## Out of scope
- Any file other than `docs/00_governance/governance_03_issue-and-uncertainty-management.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the change in Implementation > Procedure | Completed | 20261008-165853 | 20261008-165853 |  |
| 2 | Run the validation in the Validation plan | Completed | 20261008-165853 | 20261008-165853 |  |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20261007-153933_ragauth01_add-rag-http-delegation-authentication-and-fail-closed-responses.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-095953_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-163801
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md