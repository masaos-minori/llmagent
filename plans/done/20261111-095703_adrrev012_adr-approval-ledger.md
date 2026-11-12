> **Resumed 2026-11-11** — the PAUSED banner (added by commit 8ab061b3c to this Plan, adrrev014, adrrev016, adrrev017) is lifted: the owning Plan adrrev009 landed, its three procedures are archived in `implementations/done/` (`20261111-181318_01` through `20261111-181318_03`), and the Plan itself is archived at `plans/done/20261110-233648_adrrev009_adr008-recovery-align.md`. The banner's referenced timestamps (`20261111-193537` etc.) match no file; the actual plans are the archived adrrev009 plan and the paused siblings named in that plan's Execution Status. Gate at conversion: `uv run python tools/plan_dependency_order.py` reports `gated (prose)`, blocked by `plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md` phase `all` (adrrev011 is open, no procedures generated yet).

## Goal
Make the governance ledger (`governance_03`) truthful and well-formed: fix its two format defects, register the contradictions and gaps that are still true when this Plan is implemented (with a valid owner and the sibling Plan that resolves each), and align ADR-016's acceptance wording with its approval record, without inventing any maintainer approval.

## Priority
High

## Scope
- **In-Scope**: In `docs/00_governance/governance_03_issue-and-uncertainty-management.md`: add the Status field to the Part 3 Entry Template, correct the two `### 19. Merge Condition Validation` references to `### 20.`, and register the Canonical Source Conflict and Known Issue entries that re-verification confirms are still true at implementation time. In `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, cite each newly registered Known Issue whose `Target` is ADR-008 in its `## Known Deviations` (the reverse check of `tools/check_known_deviation_sync.py`). In `docs/10_adr/adr_02_07_016_adr-authority-model.md`, make the acceptance sentence match its Approval Record once the maintainer states which path applies. Report every pending approval that sibling Plans create.
- **Out-of-Scope**: Writing approval records for the ADR edits of sibling Plans (each sibling Plan writes its own pending record in the same change, per `governance_05`); past-amendment approval history (ADR-008 "Amendment Approval Mapping" is removed by the history-wording issue `issues/20261109-113318_adrrev017_docs-history-wording.md`); modifying any governance checker; fixing the underlying contradictions and gaps (sibling issues); ADR-015 (its two Approval paragraphs are consistent, see Design).
- **Dependencies**: None to start. The entry phase depends on the state of the sibling Plans at implementation time, so it should run after `plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md` (which closes the empty-token documentation conflict, so no entry is then needed for it). Sibling Plans whose entries this Plan may register: `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md` and `plans/20261110-233648_adrrev009_adr008-recovery-align.md` (the overlap check reports only the 009 Plan as also targeting ADR-008; judged compatible: 009 edits recovery decision text, this Plan edits only `## Known Deviations`, and the 008 Plan does not target ADR-008).

## Background
Re-verification against current source (2026-11-11) changed several memo claims. Confirmed: `governance_03` Part 3's Entry Template lists 12 fields without Status although a Status Values section exists; two sentences in the Temporary Exception Process cite `### 19. Merge Condition Validation` while `governance_04` numbers it `### 20.` (`### 19.` is Area Dependency Graph Validation); `governance_05` line 73 requires a new approval record in the same change for an ADR edit that changes the decision; ADR-016's Approval Record names `repository owner` and 2026-10-29 yet its closing sentence says `Accepted` was reached via a "Task-level approval decision". Refuted: the Needs Confirmation entries do not show `Assigned To: Unknown` (the single entry NC-001 has `maintainer`); Part 3 holds no entries today. Candidates for the ledger: mcp_dedup is absent from ADR-008 (confirmed) and its Plan is open; Dry Run versus WAL is acknowledged in the ADR-008 INV-16 verification row and its Plan is open; posture handling has procedures but no landed change; the empty-token documentation contradiction is confirmed but closed by the MCP security Plan; RAG unverifiable handling is likely stale since remote RAG delegation was removed (`b217f999b`) and ADR-010 is Withdrawn.

Conversion re-verification (2026-11-11, this plan-to-procedure conversion): Part 1 now holds SHARED-001 (Dry Run versus WAL, Target ADR-008) and SHARED-002 (`memories_vec` classification, Target ADR-008), both registered by the landed adrrev009 procedures, so the Dry Run versus WAL candidate is already registered and re-registering it would duplicate SHARED-001. Candidate verdicts at conversion: mcp_dedup gap — closed (documented in ADR-008; `plans/done/20261110-230633_adrrev008_mcp-dedup-ownership.md`, procedures Done); posture gap — closed (documented in `governance_02` Part 5; adrrev007 procedures in `implementations/done/`); `tool_call_state` gap — confirmed false by the landed adrrev005 verification (both tables share `parent_tool_call_state TEXT`, documented in `governance_02` Part 4; deliberately not registered); empty-token contradiction — still true at conversion (`docs/22_mcp/mcp_02_02_startup-modes-and-health.md` last Bearer bullet and the `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md` troubleshooting entry contradict `require_auth_token()` at `scripts/mcp_servers/server.py:134-144` and the fail-closed `attach_auth_middleware()` at line 95), but gated: expected to be landed or updated by `plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md` (adrrev011 is open with no procedures yet); ADR-010 remains Withdrawn yet its Decision 11 and the unverifiable-handling table are unchanged, owner issue `issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md` open. The only live Phase 3 candidate is therefore the empty-token contradiction, and only if adrrev011 has not closed it first.

## Problem
- A ledger that lists no open contradiction while sibling issues are open makes the Known Deviation sync check meaningless and hides real gaps from reviewers.
- The Part 3 template omits a field that its own Status Values section depends on, and two cross-references point to the wrong section, which blocks automated validation.
- ADR-016's acceptance sentence and its Approval Record disagree about the acceptance path.

## Reason for Change
The ledger is the input to the governance checks; accurate entries are needed while the remediation issues are open, and every remediation change must add or close its own entry in the same change.

## Implementation Intent
Fix the two format defects first (independent of any other change), then register only entries that are verified true at that moment, each citing the sibling Plan that resolves it. Prepare, never invent, maintainer statements: where a statement is missing, leave a clearly marked pending record and report it.

## Requirements
- `REQ-001`: Add `Status` to the Part 3 Entry Template field list in `governance_03` and update its field count (12 to 13), so the list agrees with its Status Values section.
- `REQ-002`: Correct both `### 19. Merge Condition Validation` references in `governance_03` to `### 20. Merge Condition Validation`.
- `REQ-003`: Register in Part 3 each Canonical Source Conflict that is still true when this Plan is implemented (candidates: posture handling until the posture Plan lands; empty-token documentation until the MCP security Plan lands; RAG unverifiable handling until its owning issue lands), with all 13 fields, a valid owner, and the sibling Plan or issue as validation evidence. Do not register an entry that re-verification refutes.
- `REQ-004`: Register in Part 1 each Known Issue still true at implementation time (candidates: Dry Run versus WAL, mcp_dedup missing from ADR-008, and a `tool_call_state` gap only if the schema issue confirmed one; conversion status 2026-11-11: Dry Run versus WAL already registered as SHARED-001, mcp_dedup closed by the landed adrrev008 procedures, `tool_call_state` confirmed false, see Background), with all 17 fields and a valid owner; cite each ADR-008-targeted entry in the ADR's `## Known Deviations`.
- `REQ-005`: After the maintainer states the acceptance path, make ADR-016's closing acceptance sentence match its Approval Record without altering the Approved By, Approval Date, or Approval Reference fields.
- `REQ-006`: Report the pending maintainer approvals created by the batch (ADR-017 new ADR, ADR-007 decision change, and each sibling Plan's ADR decision edits) as a list of approver, date, and scope marked `不明`, and write none of them.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | Add Status to the Part 3 Entry Template; fix the two `### 19` references (lines 250 and 264 as of 2026-11-11); register the confirmed Part 1 and Part 3 entries | REQ-001, REQ-002, REQ-003, REQ-004 / AC-1 to AC-4 | Part 3 "Entry Template" lists 12 fields without Status; Part 3 "Active Items" (line 209) reads "No active Canonical Source Conflict items remain."; Part 1 holds SHARED-001 and SHARED-002 (registered by the landed adrrev009 procedures), not the "No active Known Issue items remain." placeholder; `governance_04` line 251 is `### 20. Merge Condition Validation` and line 232 is `### 19. Area Dependency Graph Validation` (checked in Step 2) | `tools/check_known_deviation_sync.py`, `tools/check_needs_confirmation_inventory.py`, `tools/check_metadata_field_policy.py` | Verified |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify | Cite each newly registered ADR-008-targeted Known Issue ID in `## Known Deviations` (lines 348-351), so the reverse sync check passes; conditional row: Phase 3 re-verification found no new ADR-008-targeted candidate, so the expected outcome is a reported no-op | REQ-004 / AC-4 | `## Known Deviations` (line 348) no longer reads "Not applicable": it already cites SHARED-001 and SHARED-002 (added by the landed adrrev009 procedures); GV-022 check 3 warns when a Known Issue whose `Target` is an ADR is not cited there (`tools/check_known_deviation_sync.py` module docstring) (checked in Step 3) | `tools/check_known_deviation_sync.py`, `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Modify | Make the closing acceptance sentence (line 166, "reached `Accepted` via a Task-level approval decision") match the Approval Record that names `repository owner` and 2026-10-29 | REQ-005 / AC-5 | Approval Record lines 161-164: Approved By `repository owner`, Approval Date 2026-10-29, Approval Reference; line 166 states the task-level path (checked in Step 2) | `tools/check_adr_preservation.py`, `tools/check_adr_structure.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/00_governance/governance_04_documentation-checks.md` | The correct numbering (`### 20. Merge Condition Validation`) and the GV rules; it needs no change (the issue's "reference fix" lives in `governance_03`) | REQ-002 |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Line 73 (ADR edit that changes the decision requires a new approval record in the same change) | REQ-006 |
| `docs/00_governance/governance_01_documentation-policy.md` | ADR Acceptance Evidence Standard and Canonical Source Conflict routing, severity, and blocking rules | REQ-003, REQ-005 |
| `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Checked and left unchanged: its Named Approval Record (2026-09-19) and the task-level Current Decision Approval line are consistent | REQ-005 |
| `docs/10_adr/adr_01_index.md` | Approval and amendment status summary; no change in this Plan | REQ-006 |
| `plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md` | Decides whether the empty-token conflict still exists | REQ-003 |
| `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md` | Decides whether the mcp_dedup gap still exists | REQ-004 |
| `plans/20261110-233648_adrrev009_adr008-recovery-align.md` | Decides whether the Dry Run versus WAL gap still exists | REQ-004 |
| `issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md` | Owner of the RAG unverifiable-identity handling | REQ-003 |
| `tools/check_known_deviation_sync.py` | Run only; defines the Known Issue and ADR Known Deviations sync rules | REQ-004 |
| `tools/check_needs_confirmation_inventory.py` | Run only; confirms Part 2 stays valid | REQ-001 |
| `tools/check_metadata_field_policy.py` | Run only; the field-set policy for governance documents | REQ-001 |

## Acceptance Criteria
- AC-1: The Part 3 Entry Template lists 13 fields including Status, and its count text agrees (`REQ-001`).
- AC-2: `governance_03` contains no `### 19. Merge Condition Validation` reference and both sentences cite `### 20.` (`REQ-002`).
- AC-3: Every registered Part 3 entry has all 13 fields, owner `Repository owner` (the Part 1 Owner Values set), Status `open`, and names the sibling Plan or issue as validation evidence; no refuted claim is registered (`REQ-003`).
- AC-4: Every registered Part 1 entry has all 17 fields and a valid owner; each ADR-008-targeted entry is cited in ADR-008 `## Known Deviations`; `check_known_deviation_sync.py` reports no finding for them (`REQ-004`).
- AC-5: ADR-016's acceptance sentence matches its Approval Record (or the edit is withheld and reported until the maintainer states the path), with the Approved By, Approval Date, and Approval Reference text unchanged (`REQ-005`).
- AC-6: The final report lists every pending maintainer approval with approver, date, and scope as `不明`, and no approval text was written by the implementer (`REQ-006`).
- AC-7: `check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py`, `check_adr_structure.py`, `check_adr_authority.py`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_metadata_field_policy.py`, and `check_docs_consistency.py --domain overview` pass; `check_adr_preservation.py` reports only the intended ADR-016 Approval-section sentence.

## Tests
N/A: documentation-only; no Python file is modified. The checkers in the Validation plan gate the edits.

## Documentation Impact
`governance_03` (ledger), ADR-008 (`## Known Deviations`), and ADR-016 (acceptance sentence); load them through `docs/00_index.md` "Document References by Task" under governance. Each entry states owner, status, and resolution target and cites the sibling Plan; implementation details are not copied into entries. Write in English.

## Assumptions
- Plan classification is Path A: three documentation files, no interface or schema change.
- Part 3 and Part 2 define no owner set, so Part 3 entries use the Part 1 "Owner Values" set (`Repository owner`); NC-001's existing `maintainer` value is not changed.
- ADR-015 needs no edit: its Named Approval Record (2026-09-19, acceptance) and the task-level Current Decision Approval line (2026-10-08, later text) describe different approvals.
- "Register design-gap entries for the issues in this batch's first group" is not actionable as written (the group is undefined); it is recorded as UNK-03 instead of being guessed.
- The reverse sync rule means a Known Issue with `Target` ADR-008 requires an ADR-008 Known Deviations citation in the same change, so the ADR-008 row exists only if such an entry is registered.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether ADR-016 reached `Accepted` through a Named Approval Record or the task-level decision | Only the maintainer can state the path; the record names a repository owner and date but the sentence says task-level | **Resolved:** the maintainer stated the Named Approval Record path (2026-11-12, same shape as ADR-015); the closing sentence was reworded to match | False |
| UNK-02 | The allowed owner values for Part 3 entries | `governance_03` defines "Owner Values" for Part 1 only | **Resolved:** the Part 1 set was used; CSC-001's owner is `Repository owner`; no separate issue raised | False |
| UNK-03 | What "the issues in this batch's first group" means for the design-gap entries | The issue does not define the group | Maintainer clarifies; until then register no design-gap entry | False |
| UNK-04 | Which candidate entries are still true at implementation time (posture handling, RAG unverifiable handling, Dry Run versus WAL, mcp_dedup, `tool_call_state`) | Depends on which sibling Plans have landed by then | **Resolved at implementation 2026-11-12:** posture, mcp_dedup, `tool_call_state` refuted; Dry Run versus WAL already SHARED-001; empty-token candidate resolved by landed adrrev011 procedures 20261111-231122_09/_10 (not registered); RAG candidate confirmed and registered as CSC-001 | False |
| UNK-05 | Maintainer approvals for decision-changing ADR edits in the batch | Approver, date, and scope are `不明`; they are statements the implementer cannot write | **Resolved:** the pending list was reported (REQ-006); the adrrev011 approvals (ADR-017, ADR-007 decision change) were supplied by the maintainer's task-level approval decision of 2026-11-12 and their records completed | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | Medium (read by `check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py`, and cited by many docs) | N/A (Path A) | N/A (Path A) | not applicable (docs) |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify | Medium (edited by two sibling Plans) | N/A (Path A) | N/A (Path A) | not applicable (docs) |
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Modify | Low | N/A (Path A) | N/A (Path A) | not applicable (docs) |

## Design
Path A (three files, no public interface, no schema). Direct verification found: `governance_03` Part 3 template and cross-reference defects (references now at lines 250 and 264); Part 3 empty, Part 1 holding only the SHARED-001/SHARED-002 entries registered by the landed adrrev009 procedures; `check_known_deviation_sync.py` also requires ADR Known Deviations citations for Known Issues targeting an ADR (GV-022 check 3), which is why ADR-008 is a target.

Decision for ordering: Phases 1-2 are independent of every other Plan and are safe to run first. Phase 3 (entries) is evaluated at implementation time: an entry is registered only if its contradiction or gap still exists, so landing the MCP security Plan first removes the empty-token entry entirely. This keeps the ledger truthful without register-then-delete churn.

ADR-016 versus ADR-015: ADR-015's Approval Record states a Named Approval Record for acceptance and a task-level line for later text, which agree; ADR-016's Approved By, Approval Date, and Approval Reference are named while its closing sentence claims the task-level path, which disagree. Editing that sentence is an Approval-section text change that `check_adr_preservation.py` reports as ERROR, so it is gated on the maintainer's statement (UNK-01) and the ERROR is expected and reported, not suppressed.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Fix the Part 3 template** (REQ-001; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
   - [x] Add `Status` to the Part 3 Entry Template field list and update the count text.
2. **Phase 2: Fix the merge-condition references** (REQ-002; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
   - [x] Change both `### 19. Merge Condition Validation` references to `### 20.`.
3. **Phase 3: Register verified ledger entries** (REQ-003, REQ-004; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`)
   - [x] Re-verify each candidate (UNK-04) against current docs and source; record which were refuted or already resolved.
   - [x] Write the confirmed Part 3 entries (13 fields) and Part 1 entries (17 fields, ID prefix per the Active Items ordering convention) with owner `Repository owner` and the sibling Plan as evidence.
   - [x] Cite each newly registered ADR-008-targeted Known Issue in ADR-008 `## Known Deviations` (leave the existing SHARED-001/SHARED-002 citations from adrrev009 untouched); if none is registered, report that this row needed no edit.
4. **Phase 4: ADR-016 acceptance wording** (REQ-005; `docs/10_adr/adr_02_07_016_adr-authority-model.md`)
   - [x] Proceed only after the maintainer states the acceptance path (UNK-01); otherwise skip and report.
   - [x] Reword line 166 to match the Approval Record; leave Approved By, Approval Date, and Approval Reference untouched.
5. **Phase 5: Pending-approval report and verification** (REQ-006; all three target files)
   - [x] Run the Validation plan commands.
   - [x] Report the pending maintainer approvals (approver, date, scope as `不明`) created by the batch; write none.
   - [x] Docs only: no deploy step is needed because no `scripts/` or `config/` file changes.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Known Issue and ADR Known Deviation sync | `uv run python tools/check_known_deviation_sync.py` | Pass |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Needs Confirmation inventory | `uv run python tools/check_needs_confirmation_inventory.py` | Pass |
| governance and ADR docs | Documentation structure and policy | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` | Pass |
| governance docs | Metadata and workitem field policy (warning-only) | `uv run python tools/check_metadata_field_policy.py` | Exit 0 with no new warning |
| governance docs | Cross-document claims | `uv run python tools/check_docs_consistency.py --domain overview` | Pass |
| ADR files | ADR structure and authority | `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_authority.py` | Pass |
| ADR-016 | ADR preservation | `uv run python tools/check_adr_preservation.py` | Only the intended Approval-section sentence is reported (expected ERROR, reported to the user) |

Validation quality baseline: `N/A: no Python target`.

## Risks
- **Risk**: Registering an entry for a claim that a sibling change already resolved makes the ledger untruthful. → **Mitigation**: Phase 3 re-verifies every candidate first and records refuted or resolved ones instead of registering them (UNK-04).
- **Risk**: A Known Issue targeting ADR-008 without an ADR citation raises a GV-022 warning, and two sibling Plans also edit ADR-008. → **Mitigation**: Add the citation in the same Phase, edit only `## Known Deviations`, and run `tools/check_plan_target_overlaps.py`; the overlap is compatible (different sections).
- **Risk**: Rewording ADR-016 without the maintainer's statement fabricates an approval path. → **Mitigation**: Phase 4 is gated on UNK-01; the reworded sentence only restates fields already in the Approval Record.
- **Risk**: `check_adr_preservation.py` reports ERROR for the ADR-016 Approval-section edit. → **Mitigation**: The ERROR is the intended signal that Approval text changed; report it and do not suppress or modify the checker.
- **Risk**: The approvals report is mistaken for approval itself. → **Mitigation**: Every record is labelled pending with approver, date, and scope as `不明`.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix the Part 3 template (REQ-001) | Completed | 20261112-054929 | 20261112-054929 | Procedure 20261112-062831_01 archived; Part 3 template lists 13 fields incl. Status |
| 2 | Fix the merge-condition references (REQ-002) | Completed | 20261112-054929 | 20261112-054929 | Both references cite `### 20. Merge Condition Validation` |
| 3 | Register verified ledger entries (REQ-003, REQ-004) | Completed | 20261112-054929 | 20261112-054929 | CSC-001 (RAG candidate) registered; empty-token candidate resolved by landed adrrev011, not registered; Part 1 registrations no-op; fallout fix to `check_issue_inventory_conformance.py` Part 3/4 parsing with regression tests |
| 4 | ADR-016 acceptance wording (REQ-005) | Completed | 20261112-055129 | 20261112-055129 | Maintainer stated the Named Approval Record path; closing sentence reworded; approval fields untouched; check_adr_preservation intended ERROR reported |
| 5 | Pending-approval report and verification (REQ-006) | Completed | 20261112-055300 | 20261112-055300 | All Validation-plan checkers green; pending-approval list reported in the completion report; docs-only, no deploy step |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261112-062831_01_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md | 1, 2, 3 | Procedure | Completed | 20261112-054929 | 20261112-054929 |
| implementations/20261112-062831_02_docs_10_adr_adr_02_05_008_db-sqlite-4db-separation.md.md | 3 | Procedure | Completed | 20261112-055020 | 20261112-055020 |
| implementations/20261112-062831_03_docs_10_adr_adr_02_07_016_adr-authority-model.md.md | 4 | Procedure | Completed | 20261112-055129 | 20261112-055129 |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261109-113054_adrrev012_adr-approval-ledger.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261111-095703
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_02_07_016_adr-authority-model.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes: add Status to the Part 3 required fields | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Step 1 | AC-1 | `check_known_deviation_sync.py`, `check_docs_quality.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes: fix `### 19` to `### 20` | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Step 2 | AC-2 | `check_docs_quality.py`, `check_docs_consistency.py --domain overview` | Confirmed by repository evidence |
| REQ-003 | Required Changes: register Canonical Source Conflicts that remain true | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Step 3 | AC-3 | `check_known_deviation_sync.py` | Needs confirmation |
| REQ-004 | Required Changes: register Known Issues that remain true | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Step 3 | AC-4 | `check_known_deviation_sync.py` | Needs confirmation |
| REQ-004 | Verification: GV-022 check 3 requires an ADR Known Deviations citation for an ADR-targeted Known Issue | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Step 3 | AC-4 | `check_known_deviation_sync.py`, `check_adr_structure.py` | Derived from confirmed evidence |
| REQ-005 | Required Changes: fix ADR-016's "Task-level" wording | `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Step 4 | AC-5 | `check_adr_preservation.py`, `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-006 | AI Implementation Instruction and Unresolved Questions: never fabricate an approval; report pending ones | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Step 5 | AC-6 | final report content | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261112-062831 -->