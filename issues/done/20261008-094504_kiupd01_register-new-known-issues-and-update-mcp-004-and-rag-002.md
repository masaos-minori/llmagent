# Register new Known Issues and reconcile MCP-004 and RAG-002

## Priority
High

## Summary
Register MCP-005, MCP-006, and EVENTBUS-015 in the Known Issue ledger and update the existing MCP-004 and RAG-002 entries, so the revised ADRs can cite them.

## Background
Source: local investigation notes (memo2.md, "new Known Issues" section). The memo's IDs are provisional. The existing kiledger01 issue also registers new Known Issues and says to confirm the next free IDs first.

## Problem
- No ledger entry exists for: rag-pipeline-mcp lacking the Bearer authentication middleware (proposed MCP-005, High, target ADR-007); a missing X-Idempotency-Key being treated as key "" in the idempotency cache (proposed MCP-006, High, target ADR-004); auth_token and admin_token granting every role (proposed EVENTBUS-015, Medium, target ADR-013).
- memo2.md asks to raise MCP-004 to High with a refspec force-update note. Verification found the code now has a ref allow-list and branch-required schemas, so MCP-004 and MCP-002 may already be resolved; the ledger still shows MCP-004 as Low/open.
- RAG-002's INV-05 citation must match ADR-009 after its revision.

## Reason for Change
The revised ADRs cite these IDs; unregistered IDs make the Known Deviation sync check fail and leave real defects untracked.

## Implementation Intent
- Allocate IDs by the ledger's own numbering and register entries with the full Known Issue entry template; update MCP-004 and RAG-002 as described.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (Part 1)

## Required Changes
- Confirm the next free IDs for the MCP and EVENTBUS prefixes, then register the three entries.
- Re-verify MCP-002 and MCP-004 against code: remove them from the ledger if resolved (no resolved entries are kept); do NOT raise MCP-004 to High unless still reproducible.
- Update RAG-002 (INV-05 citation).
- Keep the ADR issues in this batch consistent with the final IDs.

## Constraints
- Current-Specification-Only policy: no history or resolved items; the entry template applies.
- Owner assignment needs a user decision.

## Acceptance Criteria
- Three new entries exist with confirmed IDs (MCP-005, MCP-006, EVENTBUS-015 verified free); MCP-002/MCP-004 reflect code state; RAG-002 is updated.
- `check_issue_inventory_conformance.py` and `check_known_deviation_sync.py` pass.

## Testing Expectations
Run the doc checkers listed in `routing.md` (including the issue inventory and Known Deviation sync checks). No code change.

## Documentation Impact
Documentation only: governance_03 Part 1.

## Out of Scope
- Fixing the underlying defects.
- Editing ADRs (separate issues).

## Dependencies
- Blocks the adr004fix, adr007fix, adr013fix, and adridx01 issues.
- Overlaps with `issues/20261007-154111_kiledger01_align-known-issue-ledger-adr-known-deviations-adr-index.md`; merge or sequence the two to avoid double registration.
- The gitref01 issue (MCP-004 fix) is already in `issues/done/`.

## Unresolved Questions
- Whether MCP-002/MCP-004 still exist after the gitref01 work (evidence says likely resolved).
- kiledger01 suggests different ID assignments (MCP-005 to MCP-008); coordinate so each defect gets one ID.
- Who is assigned as Owner of each new entry.

## AI Implementation Instruction
Check the ledger and source before registering anything; register only defects that still exist. Edit only governance_03 Part 1. Run the doc checkers before finishing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-094504
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
