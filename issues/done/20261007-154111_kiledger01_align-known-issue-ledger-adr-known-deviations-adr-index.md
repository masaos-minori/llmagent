# Align Known Issue ledger, ADR Known Deviations, and adr-index

## Priority
Low

## Summary
Keep the Known Issue ledger, ADR Known Deviations, and the adr-index verification status consistent with the real implementation, by registering the newly found defects now and updating the documents whenever each related fix lands.

## Background
Source: local investigation notes (memo1.md, ISSUE-15), from an earlier finding and the follow-up work of the other issues in the same batch. Known Issues live centrally in governance_03 Part 1 (resolved items are removed, not kept); ADR Known Deviations cite them as `- **Known Issue**: <ID> — ...`.

## Problem
- The defects described in the sibling issues (MCP idempotency cache, git-mcp ref validation scope, git-mcp error paths, rag-pipeline authentication, health-check authentication, empty allow-list semantics, shared failure count, git-mcp event-loop blocking) are not registered as Known Issues.
- AGENT-003 and MCP-001 are rated lower than the actual impact; MCP-004 lacks the note that reachability is confirmed.
- ADR-004 Known Deviations lacks AGENT-004, and adr-index still marks INV-09 as Confirmed.
- ADR-012 Known Deviations lacks MCP-002 and MCP-004, and adr-index still marks INV-01 to INV-04 as Confirmed.
- ADR-008 lists EVENTBUS-008, which is unrelated to its content; ADR-006 lacks EVENTBUS-014.
- ADR-009 and ADR-010 Completion Checklists keep a stale "not registered" note for the already registered RAG-001/002.
- security_01 says rag-pipeline requires Bearer authentication, but the current implementation has none.
- Ledger format problems: the detail sections do not follow the convention (they start with AGENT-003 instead of RAG-), Related fields mix file paths and IDs, the MCP-002 Summary and Current Description are the same sentence, First Found holds the trigger instead of a date, and every Owner is Unassigned.

## Reason for Change
- A ledger or ADR that disagrees with the implementation leads reviewers and operators to decide on a false "confirmed" premise; a wrong "Confirmed" in adr-index is especially risky because security decisions rely on it.
- Without owners, the quarterly review defined in governance_03 does not function.
- Format drift makes `check_issue_inventory_conformance.py` and `check_known_deviation_sync.py` fail or miss findings.

## Implementation Intent
- Documents always reflect the implementation; closing each sibling issue includes the ledger and ADR update so documentation never lags.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- ADR-004 / 006 / 008 / 009 / 010 / 012 / 013, `docs/10_adr/adr-index.md`, security_01
- `tools/check_issue_inventory_conformance.py`, `tools/check_known_deviation_sync.py`, `config/documentation_canonical_sources.toml`, `routing.md` (to be read)

## Required Changes
- Register the new Known Issues with fresh IDs allocated according to the ledger's own numbering (the investigation notes suggested MCP-005 to MCP-008, AGENT-005, EVENTBUS-015, EVENTBUS-016; confirm the next free IDs first).
- Raise the severity of AGENT-003, MCP-001 and MCP-004 to High and record that MCP-004 is reachable.
- Fix ADR Known Deviations: add AGENT-004 to ADR-004, MCP-002 and MCP-004 to ADR-012, EVENTBUS-014 to ADR-006; remove EVENTBUS-008 from ADR-008.
- In adr-index, remove "Confirmed" for ADR-004 INV-09 and ADR-012 INV-01 to INV-04.
- Remove the stale "not registered" notes from the ADR-009 and ADR-010 Completion Checklists.
- Record the current rag-pipeline state in security_01's authentication table as a Known Deviation (to be removed when the RAG authentication issue is completed).
- Fix the ledger format: ordering, Related-field notation, MCP-002 wording, First Found as a date, and assign Owners to Medium-and-above entries.
- As each sibling issue completes, remove its Known Issue from the ledger (no resolved entries).

## Constraints
- Follow the Current-Specification-Only policy and the 17-field Known Issue entry template; no history or resolved items.
- The documentation content policy applies (no literal defaults, counts, or line numbers).
- Owner assignments need user decisions.

## Acceptance Criteria
- `check_issue_inventory_conformance.py` and `check_known_deviation_sync.py` pass.
- adr-index contains no "Confirmed" row that contradicts a registered Known Issue.

## Testing Expectations
- Run the doc checkers listed in `routing.md` (structure, ADR structure, Known Deviation sync, issue inventory, content policy); no code change.

## Documentation Impact
This issue is itself documentation work: Known Issues, ADR Known Deviations, adr-index verification status, security_01 table, and ledger format.

## Out of Scope
- Fixing the underlying defects (covered by the sibling issues).
- Restructuring governance_03.

## Dependencies
- Depends on every sibling issue in this batch: register new entries immediately; steps tied to a fix are done when that fix completes.

## Unresolved Questions
- How the ledger checks are handled in CI (`tools/check_issue_inventory_conformance.py`, `tools/check_known_deviation_sync.py`, `config/documentation_canonical_sources.toml`, `routing.md` not re-read for this issue).
- Who should be assigned as Owner for the Medium-and-above entries.

## AI Implementation Instruction
Edit documents only; do not change code. Verify each claim against current source before registering it, and run the doc checkers before finishing. Do not record resolved items.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-154111
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `docs/10_adr/ADR-004-environment-failure-handling-policy.md`, `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/ADR-008-sqlite-4db-separation.md`, `docs/10_adr/ADR-009-rag-ft5-text-separation.md`, `docs/10_adr/ADR-010-rag-fallback.md`, `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`, `docs/10_adr/ADR-013-eventbus-authentication-authorization.md`, `docs/10_adr/adr-index.md`, security_01
