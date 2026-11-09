# Add missing ADR approval records and make the governance ledger truthful

## Priority
High

## Summary
Record approvals for ADR decision changes made after acceptance, register the contradictions and gaps found in the ADR review in the governance ledger (`governance_03`) with real owners until the issues that resolve them merge, and fix the ledger's own format defects.

## Background
- Source: `memo-issue.md` item H-15, re-checked against current source on 2026-11-09. In the memo this item is a merge condition that applies to every PR created from the list.
- `Explicit in documentation` (ADR-008, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, Approval section): acceptance rests on a task-level approval decision; the Amendment Approval Mapping states that the dbmig001 amendment (2026-10-30) and its supersession (2026-11-07) have no separate approval record. Maintainer decision of 2026-11-09: ADR amendment history is not needed, so past amendments are not documented and need no per-amendment approval record; the history wording issue in this batch removes those passages.
- `Explicit in documentation` (`docs/00_governance/governance_03_issue-and-uncertainty-management.md`): Part 3 (Canonical Source Conflict) says "No active Canonical Source Conflict items remain"; its required-field list does not contain a Status field although a Status Values section exists; two sentences cite the merge-condition check as "### 19. Merge Condition Validation" while `docs/00_governance/governance_04_documentation-checks.md` numbers it `### 20. Merge Condition Validation` (and `### 19` is the Area Dependency Graph Validation). Needs Confirmation entries show `Assigned To: Unknown`.
- `Needs confirmation`: the Known Issues Active Items content (Part 1), the current approval state of ADR-001, ADR-003, ADR-010, ADR-013, and ADR-015 (the memo lists missing records for their past amendments, which are now out of scope), the "Task-level" wording in ADR-016 versus ADR-015 (ADR-016 states a task-level decision with no named reviewers; ADR-015 contains both "Task-level" and "Named Approval Record" wording in adjacent paragraphs, which the memo did not describe), and the memo's rule is confirmed: `governance_05` (change-impact table) requires, for an ADR edit that changes the decision, a new approval record in the same change (Blocking). Past amendments are out of scope after the maintainer's decision above.
- The memo lists the ledger entries to add (below); several of them depend on facts that the sibling issues in this batch re-verify, so the entries must be written from the verified state of each issue, not from the memo's wording.

## Problem
- ADR decision changes without approval records are Blocking under the governance rules cited in the memo, so the current ADR set may not pass its own merge condition.
- An empty ledger makes the Known Deviation sync check meaningless and hides real contradictions and design-versus-implementation gaps from reviewers.
- A missing Status field, an invalid owner value, and a wrong section reference prevent automated validation and assignment.

## Reason for Change
- The ledger is the input to the checks; accurate entries are needed while the remediation issues in this batch are open.
- Timing: every remediation PR in this batch must add or close its ledger entry in the same change.

## Implementation Intent
- The governance state is truthful: every decision change is approved, and every open contradiction or gap is recorded with a valid owner until the issue that resolves it is merged.
- Approvals are maintainer statements; the implementer prepares the records and requests the statement, and does not invent them.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `docs/00_governance/governance_04_documentation-checks.md`, `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`
- ADR files needing approval records under `docs/10_adr/`: ADR-001, ADR-003, ADR-008, ADR-010, ADR-013, ADR-015, ADR-016; `docs/10_adr/adr_01_index.md`
- `tools/check_known_deviation_sync.py` and `tools/check_needs_confirmation_inventory.py` (run only; do not modify)

## Required Changes
- Add approval records (approver, date, scope) only for ADR edits that change a decision in the current text, in the same change as the edit (the issues in this batch that amend ADR-003, 004, 006, 008, 010, 013 and similar). No approval record is added for past amendment history, which is removed rather than documented; maintainers state each approval.
- Register Canonical Source Conflicts that remain true after re-verification: posture handling (until the posture issue merges), empty-token documentation (until the MCP security issue merges), and RAG unverifiable handling (until the RAG delegation removal merges).
- Register Known Issues that remain true: Dry Run versus WAL (until the ADR-008 alignment issue merges), mcp_dedup missing from ADR-008 (until the mcp_dedup issue merges), and any `tool_call_state` gap the schema issue confirms.
- Register design-gap entries for the issues in this batch's first group until each merges.
- Add Status to the Part 3 required fields, assign real owners to the Needs Confirmation entries, and fix the `### 19` to `### 20` merge-condition reference.
- Fix ADR-016's "Task-level" wording so it matches its approval record.

## Constraints
- Do not register an entry that re-verification refuted (several memo claims are stale; see sibling issues).
- Ledger formats are checked by `check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py`, and `check_metadata_field_policy.py`; follow their rules instead of changing them.
- Owner values must be from the allowed set defined in `governance_03` "Owner Values".

## Acceptance Criteria
- Every ADR edit in this batch that changes a decision has an approval record in the same change, and every open item from this batch that remains true is in the ledger with a valid owner.
- The Part 3 required fields include Status, and the merge-condition reference resolves to the right section.
- `check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py`, `check_adr_structure.py`, `check_adr_authority.py`, `check_docs_quality.py`, `check_docs_structure.py`, and `check_docs_content_policy.py --strict` pass.

## Testing Expectations
- Documentation-only; run the checkers listed above and `check_docs_consistency.py --domain overview`.

## Documentation Impact
- `governance_03`, `governance_04` (reference fix), ADR approval sections, and the ADR index change. State the owner, status, and resolution target of each entry; do not copy implementation details into entries.

## Out of Scope
- Fixing the underlying contradictions and gaps (the other issues in this batch).
- Changing governance checker tools.

## Dependencies
- Depends on: none to start; it applies to every other issue in this batch (each remediation PR adds or closes its own ledger entry in the same change).
- Related: every other issue of this batch (`issues/*_adrrev0*.md`, 19 files in total); each remediation PR adds or closes its own ledger entry in the same change.

## Unresolved Questions
- Maintainer approvals (`不明`): approver, date, and scope for each decision-changing ADR edit in this batch; none for past amendments.
- `Needs confirmation`: the current Known Issues content and which listed entries are still true.
- `Needs confirmation`: whether `governance_05` actually requires a same-change approval record.

## AI Implementation Instruction
- Never fabricate an approval, approver, or date; leave a clearly marked pending record and report it.
- Write only entries that re-verification confirms; cite the sibling issue path instead of restating its content.
- Do not modify the governance checkers.
- Write documentation in English and follow the docs content policy; do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-113054
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `docs/00_governance/governance_04_documentation-checks.md`, `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_02_06_010_rag-fallback.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`, `docs/10_adr/adr_02_07_016_adr-authority-model.md`, `docs/10_adr/adr_01_index.md`
