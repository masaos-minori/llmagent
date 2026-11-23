# Resolve the ADR-010 contradiction and close the stale ADR-008 matrix item

## Priority
High

## Summary
ADR-010 is `Withdrawn` but keeps present-tense corpus-identity wording, and the governance inventory still tracks an ADR-008 matrix contradiction that the current matrix text no longer shows. Record the maintainer's decisions so each ADR has one normative reading and the inventory matches the documents.

## Background
Source: `docs/00_governance/governance_03_issue-and-uncertainty-management.md` active items CSC-001 (High, Blocking) and SHARED-002 (Medium), and the pending ledger entries AAL-013 and AAL-024 to AAL-028. Evidence (`Explicit in docs`, re-read against the ADR text and `rg` on `scripts/` and `tests/`):
- CSC-001 still holds: `docs/10_adr/adr_02_06_010_rag-fallback.md` has Status `Withdrawn`, yet its Decision item 11 (line 78) and the failure-outcome table row `Identity unverifiable (either identity absent)` (line 91) state the corpus-identity contract in the present tense. No `corpus_identity` file or reference exists under `scripts/` or `tests/`.
- SHARED-002 is stale as a contradiction: in the current ADR-008 Recovery Policy Matrix, `memories_vec` appears only in the `Derived or rebuildable data` row of the session.sqlite column, and the `System of record` row lists `sessions, messages, memories, memory_links, session_diagnostics`. Decision Detail 24 states `memories_vec` is derived. The same ADR's `## Known Deviations` still carries the SHARED-002 bullet, and the matrix edit is a pending, unapproved change (AAL-027, with AAL-024 and AAL-025 for the same ADR).
- `issues/20261119-140519_mcpai012_mcp-design-docs-update.md` aligns ADR-008 with the implemented contracts and carries SHARED-002 only as a constraint. Archived related work (`issues/done/20261107-050702_adrrag002_reconcile-adr-010-contract.md`) was not read; re-verify against current source.

## Problem
A withdrawn decision reads as current behavior in ADR-010. The governance inventory and ADR-008 `## Known Deviations` report a contradiction that the matrix text no longer contains, while the text change that removed it has no recorded approval.

## Reason for Change
CSC-001 is a blocking High canonical-source conflict. A stale Known Issue misleads readers and cannot be removed until the maintainer approves the text that resolved it (the Resolution Rules forbid a documentation-only closure without agreement of implementation and design).

## Implementation Intent
The maintainer decides how the surviving ADR-010 wording is handled and approves or reverts the pending ADR-008 classification; the documents and the inventory then agree. The implementation side prepares the decision package and applies the edits that follow the decision.

## Target Files or Areas
- `docs/10_adr/adr_02_06_010_rag-fallback.md` (Decision item 11, failure-outcome table row, withdrawal record)
- `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (Recovery Policy Matrix, `## Known Deviations`)
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (CSC-001, SHARED-002, AAL-013, AAL-024 to AAL-028)

## Required Changes
- Re-verify both claims first (`rg corpus_identity scripts/ tests/`; the matrix rows and Decision Detail 24).
- For CSC-001, prepare the proposal to move the present-tense wording to the withdrawn record or remove it; apply it after the maintainer decision and remove CSC-001 with validation evidence.
- For SHARED-002, prepare the approval question for AAL-027 (and AAL-024, AAL-025); after the maintainer states the approval or reverts the change, remove SHARED-002 and the matching `## Known Deviations` bullet.

## Constraints
- The maintainer decides both outcomes and states every approval. An implementer writes no approval text, approver, or date, and no ledger entry for a past approval.
- A documentation-only edit cannot close a conflict that implementation evidence contradicts.

## Acceptance Criteria
- [ ] ADR-010 has no present-tense wording that contradicts its `Withdrawn` status.
- [ ] `memories_vec` is classified once in the ADR-008 matrix, and the classification has a recorded maintainer approval or is reverted.
- [ ] CSC-001 and SHARED-002 are removed from the inventory, and the ADR-008 `## Known Deviations` bullet is removed, each with validation evidence.
- [ ] AAL-013, AAL-024 to AAL-028 are removed from the ledger once their approvals are recorded or the changes reverted.

## Testing Expectations
Governance checkers pass (`check_adr_structure.py`, `check_known_deviation_sync.py`, `check_adr_invariant_matrix.py`), and `rg corpus_identity scripts/ tests/` still lists no file.

## Documentation Impact
Yes: ADR-010, ADR-008, and the governance inventory (resolution of items, not new policy).

## Out of Scope
- Reintroducing the RAG fallback or changing DB recovery code.
- The ADR-004 failure-handling exceptions (carried in the `mcpai001`, `mcpai002`, and `mcpai012` issues).

## Dependencies
- Sequence after or together with `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`, which edits ADR-008 and must not decide the classification. `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md` and `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md` reference ADR-008 and are not prerequisites.
- Blocks the ledger work in `issues/20261123-104604_gov005_adr-approval-ledger.md` for AAL-013 and AAL-024 to AAL-028.

## Unresolved Questions
- `不明`: whether the maintainer removes the ADR-010 wording or moves it to the withdrawn record.
- `不明`: whether the maintainer approves AAL-027 (`memories_vec` derived) or reverts it.

## AI Implementation Instruction
Verify against the current ADR text and code first. Prepare the edits as proposals and stop for the maintainer's decision; do not write any approval, approver, or date, and do not touch unrelated ADR sections.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261123-104600
- **Related target files**: `docs/10_adr/adr_02_06_010_rag-fallback.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
