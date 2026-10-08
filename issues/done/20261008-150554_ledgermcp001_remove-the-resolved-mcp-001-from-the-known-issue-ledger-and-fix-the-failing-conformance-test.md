# Remove the resolved MCP-001 from the Known Issue ledger and fix the failing conformance test

## Priority
High

## Summary
The Known Issue ledger still lists MCP-001 with the status "fixed" and an extra field, which breaks the ledger conformance check and keeps the full test suite red; remove the resolved entry as the ledger policy requires and align the documents that cite it.

## Background
An upstream change that completed the git MCP audit-record emission work marked MCP-001 as fixed in the ledger and in ADR-012. The ledger policy says a resolved item is removed from the active inventory rather than kept with a closed status, and the entry template has exactly 17 fields.

## Problem
- The ledger row and the detail section for MCP-001 carry the status "fixed", which is not an allowed Part 1 status (allowed: open, investigating, deferred), and the detail section has 18 fields instead of 17.
- `uv run python tools/check_issue_inventory_conformance.py` reports three errors for MCP-001, and the test that runs the checker against the live ledger fails (`tests/tools/test_check_issue_inventory_conformance.py::TestStatusValues::test_live_governance_document_is_clean`).
- The failure is present on the upstream head, independent of other work in progress, and makes the post-sync full-suite validation red.
- ADR-012 mentions MCP-001 as resolved in its Known Deviations prose, and other documents may cite it.

## Reason for Change
A permanently red suite hides new failures and blocks the validation required before pushing; the ledger would also keep a resolved item against its own policy.

## Implementation Intent
- Remove the MCP-001 row and section from the ledger, and make ADR-012 and any other document describe the current behavior without citing a removed ID; keep the ADR text about audit emission accurate.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`
- `docs/22_mcp/mcp_04_05_git.md` and `docs/22_mcp/mcp_06_05_reading-audit-logs.md` (check for citations)

## Required Changes
- Delete the MCP-001 table row and its detail section.
- Update the ADR-012 Known Deviations text and any other citation so the documents state the current audit behavior without referring to the removed entry.
- Run the ledger conformance and Known Deviation sync checks and the live-ledger test.

## Constraints
- Follow the Current-Specification-Only policy and the ledger entry template; do not add a "resolved" status.
- Documentation content policy applies (no counts, line numbers, or concrete values).

## Acceptance Criteria
- The conformance checker reports no errors and the live-ledger test passes.
- No document cites MCP-001 as an active Known Issue.

## Testing Expectations
Run the documentation checkers listed in `routing.md` and the ledger conformance test; run the full suite once.

## Documentation Impact
This is documentation work: the ledger, ADR-012 Known Deviations, and the git MCP and audit-log documents if they cite the ID.

## Out of Scope
- Changing the audit emission code.
- Other ledger entries.

## Dependencies
- Related to the upstream git MCP audit work; coordinate with its author before editing documents they recently changed.

## Unresolved Questions
- Whether the author intended to keep a record of the fix in ADR-012 (a short statement of current behavior is acceptable; a closed Known Issue entry is not).

## AI Implementation Instruction
Edit documents only. Verify the audit-emission claims in ADR-012 against the code before rewording them, and run the checkers before finishing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261008-143632_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-150554
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`
