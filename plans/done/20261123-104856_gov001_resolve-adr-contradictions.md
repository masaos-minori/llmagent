## Goal
- Remove the canonical-source conflict CSC-001 by marking the surviving present-tense corpus-identity wording of the Withdrawn ADR-010 as historical record, without writing any maintainer approval, and close CSC-001 in the governance inventory with validation evidence.

## Priority
High

## Scope
- **In-Scope**: re-marking the identity-contract wording in `docs/10_adr/adr_02_06_010_rag-fallback.md` (Decision Details 11 and 14, the two identity rows of the failure-outcome table, the INV-09 identity clause, the identity Negative Consequence bullet, the identity Review Trigger); extending the pending scope of ledger entry AAL-013 to cover that re-marking; removing CSC-001 from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 3 with its validation evidence.
- **Out-of-Scope**: the SHARED-002 part of the Issue (its matrix text is already consistent and only the maintainer's approval of AAL-027 is pending, see Assumptions); ledger entries AAL-024, AAL-025, AAL-026, AAL-028 and every other entry except AAL-013 (they stay with the ADR Approval Ledger issue, gov005); the other present-tense record text of ADR-010 (Decision Details 1 to 10, 12, 13, INV-01 to INV-08, INV-10, Fallback Policy), which CSC-001 does not name (UNK-01); any code, test, or configuration change; writing an approver, a date, or an approval sentence.
- **Dependencies**: None open. The ADR-008 alignment issue (mcpai012) no longer overlaps because this Plan does not edit ADR-008. This Plan narrows the ledger work that the ADR Approval Ledger issue (gov005) expects from this issue to AAL-013 only.

## Background
Source Issue: `gov001`, from the governance inventory items CSC-001 (High, Blocking) and SHARED-002 (Medium). Verified in Step 2 (adversarial verification against the ADR text and `rg`):
- CSC-001 holds. `docs/10_adr/adr_02_06_010_rag-fallback.md` is `Withdrawn`; its Status paragraph says the text below remains as the record of the withdrawn decision (line 32) and names CSC-001. Decision Detail 11 (line 78), the table rows `Identity mismatch` and `Identity unverifiable` (lines 90 and 91), Decision Detail 14 (line 94), INV-09 (line 185), the Negative Consequence at line 162, and the Review Trigger at line 266 still describe the corpus-identity gate in the present tense, while `Implementation Notes` (line 246) records that the identity contract, reader module, and gate were removed under Option B. `rg corpus_identity scripts/ tests/` lists no file and `scripts/rag/` holds no corpus identity module.
- The Issue named only Decision Detail 11 and one table row. The other identity statements listed above carry the same conflict, so the corrected scope covers them.
- SHARED-002 is already consistent in the text: the ADR-008 matrix lists `memories_vec` only in the `Derived or rebuildable data` row of the session.sqlite column, Decision Detail 24 states it is derived, and the ADR's `## Known Deviations` bullet already says the matrix classifies it as derived only, pending AAL-027, with the Known Issue open until that approval. No implementation work remains for it.
- The Issue also grouped AAL-024 to AAL-028 with this work. Only AAL-013 relates to ADR-010; AAL-024, AAL-025, AAL-026, and AAL-028 concern ADR-008 scope, schema-mismatch, retention, and `dlq_outbox` text unrelated to either item.

## Problem
A reader of the Withdrawn ADR-010 can take the corpus-identity comparison and its failure outcomes as current behavior, although the contract no longer exists. The inventory lists this as a blocking High conflict.

## Reason for Change
CSC-001 is a blocking canonical-source conflict; the conflicting wording is confined to one ADR and can be marked without deciding anything beyond the record's tense.

## Implementation Intent
Keep the withdrawn decision's text as the record, but make every identity-contract statement explicitly historical (a visible Withdrawn marker and past tense), keep ledger entry AAL-013 pending with its scope extended, and remove CSC-001 once the check shows no present-tense identity wording remains.

## Requirements
- `REQ-001`: Every corpus-identity statement of ADR-010 (Decision Details 11 and 14, the `Identity mismatch` and `Identity unverifiable` rows, the INV-09 identity clause, the identity Negative Consequence, the identity Review Trigger) is marked as withdrawn and written in the past tense, with its numbering and cross-references kept.
- `REQ-002`: Ledger entry AAL-013 stays pending (approver and date `Not recorded`) and its Scope names the re-marked ADR-010 passages; no approval text, approver, or date is written anywhere.
- `REQ-003`: CSC-001 is removed from `governance_03` Part 3, which then states that no active Canonical Source Conflict items remain, and the validation evidence (`rg corpus_identity scripts/ tests/` empty; the marked passages) is recorded in the commit message.
- `REQ-004`: SHARED-002, the ADR-008 text, and AAL-024 to AAL-028 are unchanged.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| docs/10_adr/adr_02_06_010_rag-fallback.md | modify: mark the identity-contract passages as withdrawn history in the past tense | The Withdrawn ADR keeps present-tense identity wording (CSC-001) | REQ-001; AC-1 | `adr_02_06_010_rag-fallback.md:32,78,90-91,94,162,185,246,266` (checked in Step 2) | N/A: documentation (checkers in Validation plan) | Verified |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | modify: remove CSC-001 and extend the AAL-013 scope | The conflict is resolved and the pending ledger entry must name the re-marked passages | REQ-002, REQ-003; AC-2, AC-3 | `governance_03...md:345-359` (CSC-001), `:508-515` (AAL-013) (checked in Step 2) | N/A: documentation (`check_issue_inventory_conformance.py`) | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | Evidence that the SHARED-002 text is already consistent and the pending AAL-027 wording | REQ-004 |
| docs/21_rag/rag_05_01-configuration-reference.md | States the removed remote-delegation keys that confirm the withdrawn contract | REQ-001 |
| docs/21_rag/rag_05_07-rag-index-consistency-checks.md | Target of the identity cross-reference kept in the historical text | REQ-001 |
| tools/check_adr_structure.py | Structure rules a Withdrawn ADR must still pass | REQ-001 |
| tools/check_issue_inventory_conformance.py | Part 3 entry shape and the empty-part wording | REQ-003 |
| tools/check_known_deviation_sync.py | Known Issue citation sync for ADR Known Deviations | REQ-004 |
| config/adr_authority.toml | ADR-010 contributes no authority node and must stay so | REQ-001 |

## Acceptance Criteria
- `AC-1` (REQ-001): Decision Details 11 and 14, the two identity table rows, the INV-09 identity clause, the identity Negative Consequence, and the identity Review Trigger each carry an explicit Withdrawn marker and past-tense wording; Decision Detail numbering and the failure-outcome table shape are unchanged.
- `AC-2` (REQ-003): CSC-001 is absent from `governance_03` Part 3, which states that no active items remain, and `rg corpus_identity scripts/ tests/` still lists no file.
- `AC-3` (REQ-002): AAL-013 remains in Part 5 with approver and date `Not recorded` and a Scope that names the re-marked passages; ADR-010's Withdrawal Approval Record still says the maintainer statement is pending.
- `AC-4` (REQ-004): SHARED-002, the ADR-008 file, and AAL-024 to AAL-028 are unchanged.
- `AC-5` (REQ-001 to REQ-004): `check_adr_structure.py`, `check_known_deviation_sync.py`, `check_issue_inventory_conformance.py`, and the documentation gates pass.

## Tests
- No test change is needed: the edit is documentation-only and no test cites the ADR-010 identity wording (`tests/tools/test_check_issue_inventory_conformance.py` builds its own CSC fixture).
- Checker runs that apply: `check_adr_structure.py`, `check_known_deviation_sync.py`, `check_issue_inventory_conformance.py`, `check_adr_invariant_matrix.py`, `check_needs_confirmation_inventory.py`, and `tools/run_validation_gates.py` (REQ-001 to REQ-004).
- `rg corpus_identity scripts/ tests/` returns no file (REQ-003).

## Documentation Impact
Yes. The two target documents are the change itself: ADR-010 history marking and the governance inventory (resolution of an item, no new policy). Documents named by `docs/00_index.md`'s task mapping for governance are limited to these two.

## Assumptions
- Re-marking in place (not deleting) is the default because the ADR states that its text remains as the record of the withdrawn decision; deletion is the alternative the maintainer may choose (UNK-02).
- The re-marking is part of the withdrawal's record-keeping, so it extends the pending scope of AAL-013 instead of adding a new ledger entry; the entry stays unapproved.
- SHARED-002 closes only through the maintainer's approval or revert of AAL-027, which an implementer cannot record; it is outside this Plan and stays tracked in the inventory.
- The ADR-008 alignment issue (mcpai012) edits ADR-008 only and does not conflict with these two files.
- Path A: two documentation files, no interface, no schema, no Python target; the validation quality baseline is `N/A: no Python target`.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the other present-tense record text of ADR-010 (Decision Details 1 to 10, 12, 13, INV-01 to INV-08, INV-10, Fallback Policy) needs the same historical marking | CSC-001 names only the identity wording; no maintainer scope decision exists | The maintainer decides at review; a separate Issue covers it if wanted | False |
| UNK-02 | Whether the maintainer prefers removing the identity passages instead of marking them historical, and whether AAL-013 or a new ledger entry should carry the change | No maintainer statement | Design default is mark-in-place under AAL-013; the maintainer confirms or reverts at review | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| docs/10_adr/adr_02_06_010_rag-fallback.md | Modify | Low | N/A | N/A | none (documentation) |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Modify | Medium | N/A | N/A | none (documentation) |

## Design
- ADR-010: prefix each identity passage with a visible marker `Withdrawn (identity gate removed):` and rewrite it in the past tense (for example, "the comparison was performed before ..."). Decision Detail numbers, the table's row count, and the cross-reference to `rag_05_07-rag-index-consistency-checks.md` stay. The INV-09, Negative Consequence, and Review Trigger passages get the same marker so no passage reads as live behavior. The Status paragraph's CSC-001 sentence is removed because the conflict is closed.
- `governance_03`: delete the CSC-001 entry and write `No active Canonical Source Conflict items remain.` under Part 3 Active Items, matching Part 4's wording; extend the AAL-013 Scope to `Status, Withdrawal Approval Record, historical marking of the identity passages`.
- Alternatives: deleting the passages (loses the record the ADR says it keeps); a new ledger entry (the change is the withdrawal's own record-keeping); leaving item 11 only (the same conflict would remain at items 14, INV-09, and elsewhere).
- Predictable fallout check (Step 3): module size gate and pinned counts do not apply to documentation; no tool inventory change; no generated block references ADR-010's identity text (`not affected`). Consumer scan: not applicable (no symbol, constant, or schema change).
- Complexity and coverage baseline: `N/A: no Python target`.

## Implementation steps
1. **Phase 1: Mark the ADR-010 identity passages**
   - [ ] Re-read each passage and apply the historical marker and past tense (REQ-001; docs/10_adr/adr_02_06_010_rag-fallback.md)
   - [ ] Remove the CSC-001 sentence from the Status paragraph (REQ-001, REQ-003; docs/10_adr/adr_02_06_010_rag-fallback.md)
2. **Phase 2: Update the governance inventory**
   - [ ] Extend the AAL-013 Scope and keep approver and date `Not recorded` (REQ-002; docs/00_governance/governance_03_issue-and-uncertainty-management.md)
   - [ ] Remove CSC-001 and write the empty-part sentence (REQ-003; docs/00_governance/governance_03_issue-and-uncertainty-management.md)
3. **Phase 3: Verification**
   - [ ] Run the checkers in Validation plan and `rg corpus_identity scripts/ tests/`; record the evidence in the commit message (REQ-001 to REQ-004). No deploy step: no `scripts/` or `config/` change.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/10_adr/adr_02_06_010_rag-fallback.md | Documentation checkers | `uv run python tools/check_adr_structure.py`; `uv run python tools/check_adr_invariant_matrix.py`; `uv run python tools/check_known_deviation_sync.py` | No findings |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Documentation checkers | `uv run python tools/check_issue_inventory_conformance.py`; `uv run python tools/check_needs_confirmation_inventory.py` | Part 3 passes with the empty-part sentence |
| Both | Gates and evidence | `uv run python tools/run_validation_gates.py`; `rg corpus_identity scripts/ tests/` | Gates pass; `rg` lists no file |

## Risks
- **Risk**: CSC-001 is removed before the maintainer states the withdrawal approval for the re-marking → **Mitigation**: AAL-013 stays pending with the extended scope and the change is a plain documentation commit the maintainer can revert (UNK-02).
- **Risk**: A re-marked passage breaks an ADR structure or invariant-matrix check → **Mitigation**: numbering, headings, and the table shape are unchanged, and the checkers run in Phase 3.
- **Risk**: Marking only the identity wording leaves the rest of the present-tense record unmarked → **Mitigation**: recorded as UNK-01 for the maintainer; the conflict tracked as CSC-001 is limited to the identity wording.
- **Risk**: The ADR Approval Ledger issue (gov005) still lists AAL-024 to AAL-028 under this work → **Mitigation**: this Plan states the narrowed scope; gov005 handles those entries.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Mark the ADR-010 identity passages | Completed | — | 20261123-105353 |  |
| 2 | Update the governance inventory | Completed | — | 20261123-105353 |  |
| 3 | Verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261123-105126_01_docs_10_adr_adr_02_06_010_rag-fallback.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261123-105126_02_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md | 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261123-104600_gov001_resolve-adr-contradictions.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261123-104856
- **Related target files**: docs/10_adr/adr_02_06_010_rag-fallback.md, docs/00_governance/governance_03_issue-and-uncertainty-management.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (CSC-001); ADR text lines 32, 78, 90-91, 94, 162, 185, 266 | docs/10_adr/adr_02_06_010_rag-fallback.md | Phase 1 | AC-1 | `check_adr_structure.py`, `check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-002 | Issue Constraints (no approval text); ADR-010 Withdrawal Approval Record and AAL-013 | docs/00_governance/governance_03_issue-and-uncertainty-management.md | Phase 2 | AC-3 | `check_issue_inventory_conformance.py` | Derived from confirmed evidence |
| REQ-003 | Issue Acceptance Criteria (CSC-001 removed); `rg corpus_identity` evidence | docs/00_governance/governance_03_issue-and-uncertainty-management.md | Phase 2 | AC-2 | `check_issue_inventory_conformance.py`, `rg corpus_identity scripts/ tests/` | Confirmed by repository evidence |
| REQ-003 | Issue Acceptance Criteria (CSC-001 removed) | docs/10_adr/adr_02_06_010_rag-fallback.md | Phase 1 | AC-2 | `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-004 | Step 2 evidence: ADR-008 matrix, Decision Detail 24, Known Deviations bullet | docs/00_governance/governance_03_issue-and-uncertainty-management.md | Phase 2 | AC-4 | `check_known_deviation_sync.py` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261123-105126 -->