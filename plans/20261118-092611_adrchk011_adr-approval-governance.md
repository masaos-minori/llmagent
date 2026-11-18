## Goal
- Define the ADR approval ledger, the pending-amendment form, the allowed ADR Status values (including `Withdrawn`), and the Required Reviewer to RACI role mapping in governance, apply them to every ADR that carries a pending marker, and enforce the Status set and the pending form in `tools/check_adr_structure.py`.

## Priority
High

## Scope
- **In-Scope**: inventory of pending approval markers; registration of the unapproved ADR-004 Exceptions; the CSC-001 reference from ADR-010; governance definitions (ledger, pending form, Withdrawn, reviewer mapping); application of the forms to the ADRs in the inventory; Status value validation and pending-form validation in `tools/check_adr_structure.py` with tests; the documentation and tool-description updates that keep those checks in sync.
- **Out-of-Scope**: approving any pending decision; deciding the substance of the ADR-004 Exceptions; writing approval text; creating ledger entries for past approvals; editing archived files under `issues/done/`; the stale CSC-001 Validation evidence path (tracked as UNK-06).
- **Dependencies**: This Plan blocks `issues/20261117-123001_adrchk001_mcp-auth-contract.md`, `issues/20261117-123005_adrchk005_startup-fail-closed.md`, `issues/20261117-123009_adrchk009_plan-code-reconcile.md`, and `issues/20261117-123013_adrchk013_invariant-matrix-checks.md`, which use the pending form. `issues/20261117-123006_adrchk006_rag-failure-policy.md` decides the substance of the RAG-related ADR-004 Exception; this Plan only fixes how that Exception is registered and approved. No other Plan or Issue has to land first. Other issues edit the same ADR files and `docs/10_adr/adr_01_index.md`; this Plan goes first and the order against them is the owner's call.

## Background
Governance defines only the `Proposed` and `Accepted` ADR statuses and the Merge Conditions that block an unapproved decision change. ADRs already carry pending amendments, a withdrawn ADR, and unapproved Exceptions that those rules do not describe, and ADR pending bullets cite an "ADR approval ledger" that no governance document defines. The Issue was filed from a consolidated ADR review (`memo-issue.md`, package `ADRCHK2-H11`) and re-verified in Step 2 of this cycle.

## Problem
- No governance document defines the approval ledger (location, entry fields, citation format) that ADR pending bullets cite by name.
- A pending-amendment form exists only as a convention: `- **Current Decision Approval (pending)**:` bullets under `### Approval Record` in ADR-001, 004, 005, 006, 008, 009, 012, 014, 015, 016, plus ADR-010's `### Withdrawal Approval Record`. The pending changes are already applied in the ADR text.
- `Withdrawn` is used by ADR-010 and `docs/10_adr/adr_01_index.md` but is not a governed status, and `tools/check_adr_structure.py` only checks that a `## Status` heading exists.
- ADR-004 Exceptions lack approval references: the dedup fail-open and warning-only exceptions have a rationale but no approval reference, the spawn-failure exception states none, and the `path_denylist` rationale is PENDING (NC-001). ADR-004 `## Known Deviations` says `Not applicable`.
- Required Reviewer names in ADRs do not map to the RACI roles of `governance_05`.

## Reason for Change
- Governance treats an unapproved decision change as a Blocking merge condition, but the repository holds unapproved text with no governed way to show it.
- ADRs 001, 004, 005, 006, 008, 009, 012, 014, 015, and 016 are blocked from a clean state, and four open issues need the pending form defined first.

## Implementation Intent
- Governance defines the ledger, the pending-amendment form, the allowed Status values, and the reviewer mapping, as a proposal that merges only with the maintainer's approval.
- Every ADR either has approved text or shows its pending amendment in the defined form, citing a ledger ID.
- `tools/check_adr_structure.py` rejects an unknown Status value and a pending bullet that does not follow the form.

## Requirements
- `REQ-001`: Inventory every pending approval marker in the ADRs and report the list with the change (no decision needed).
- `REQ-002`: Register each ADR-004 Exception that lacks an approval reference or rationale: a Known Issue entry per exception in `governance_03` Part 1, a Known Deviations bullet citing it, and an approval reference or NC ID on each Exception (no decision needed).
- `REQ-003`: ADR-010 references CSC-001 without changing its Status line or its decision (no decision needed).
- `REQ-004`: Governance defines the ADR approval ledger: location, entry fields (ID, ADR, decision, approver, date, scope), and the citation format (maintainer decision).
- `REQ-005`: Governance defines the pending-amendment form without changing the ADR Status line (maintainer decision).
- `REQ-006`: Governance defines `Withdrawn` and its content rules (maintainer decision; the alternative of moving ADR-010 out of the active set is UNK-02).
- `REQ-007`: Governance maps each Required Reviewer name to a RACI role (maintainer decision).
- `REQ-008`: Apply the defined forms to every ADR in the REQ-001 inventory.
- `REQ-009`: `tools/check_adr_structure.py` rejects a Status value outside the set defined in `governance_01`, with a test.
- `REQ-010`: `tools/check_adr_structure.py` rejects a pending bullet that lacks a ledger ID or cites an ID absent from the ledger, with a test.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/00_governance/governance_01_documentation-policy.md` | Status set, pending form, Withdrawn rules, ledger citation format | `## ADR Status Definitions` lists only Proposed and Accepted; add Withdrawn, the pending-amendment form, and the ledger citation format | REQ-004, REQ-005, REQ-006 / AC-4 | `## ADR Status Definitions` and `### ADR Acceptance Evidence Standard` define no pending form or ledger (checked in Step 2) | `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_content_policy.py` | Verified |
| `docs/00_governance/governance_02_documentation-metadata.md` | Front matter `status` versus ADR Status | Add one sentence that front matter `status` (`stable`, `draft`) is independent of the ADR `## Status` values, so a Withdrawn ADR does not conflict with the no-historical-status rule | REQ-006 / AC-4 | `### status` allows `stable` and `draft` and removes deprecated or superseded documents from the active set (checked in Step 2) | `tools/check_docs_quality.py`, `tools/check_docs_structure.py` | Verified |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Known Issue entries, ledger part and entries | Add Known Issue entries for the ADR-004 Exceptions (REQ-002), a new ADR approval ledger part after Part 4, and a pending ledger entry per inventory item | REQ-002, REQ-004 / AC-2, AC-4 | Part 1 requires 17 fields and an ID-prefix convention; Part 2 holds only NC-001; no ledger exists (checked in Step 2) | `tools/check_known_deviation_sync.py`, `tools/check_needs_confirmation_inventory.py`, `tools/check_docs_quality.py` | Verified |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Reviewer-to-RACI mapping | Add the mapping table to `## RACI Model` | REQ-007 / AC-4 | `## RACI Model` lists area-lead handles only; no Required Reviewer mapping exists (checked in Step 2) | `tools/check_docs_quality.py`, `tools/check_docs_structure.py` | Verified |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Exceptions, Known Deviations, pending bullet | Cite an approval reference or NC ID on each Exception, list the Known Issue IDs in `## Known Deviations`, and add the ledger ID to the pending bullets | REQ-002, REQ-008 / AC-2, AC-5 | `## Exceptions` ends with `not fabricated here` and no reference; `## Known Deviations` is `Not applicable`; two pending bullets; NC-001 at the Group 1 marker (checked in Step 2) | `tools/check_adr_structure.py`, `tools/check_known_deviation_sync.py`, `tools/check_needs_confirmation_inventory.py` | Verified |
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | CSC-001 reference, withdrawal record form | Reference CSC-001 in the Status body (first Status line stays `Withdrawn`) and apply the defined form to `### Withdrawal Approval Record` | REQ-003, REQ-006, REQ-008 / AC-3, AC-5 | `## Status` is `Withdrawn`; the document has no CSC-001 reference; `### Withdrawal Approval Record` says `Pending maintainer statement` (checked in Step 2) | `tools/check_adr_structure.py`, `tools/check_canonical_source_registry.py` | Verified |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Pending form | Add the ledger ID to the INV-02 pending bullet | REQ-008 / AC-5 | `- **Current Decision Approval (pending)**:` bullet under `### Approval Record` for the INV-02 Blocking change (checked in Step 2) | `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Pending form | Add ledger IDs to the pending bullets | REQ-008 / AC-5 | Two pending bullets under `### Approval Record` (Decision 10 remediation, Decision 8 rewrite) (checked in Step 2) | `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Pending form | Add ledger IDs to the pending bullets | REQ-008 / AC-5 | Four pending bullets under `### Approval Record` (dlq_outbox, Replay Contract, INV-13, ADR-008 relation) (checked in Step 2) | `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Pending form | Add ledger IDs to the pending bullets | REQ-008 / AC-5 | Two pending bullets under `### Approval Record` (dlq_outbox, rag-pipeline-mcp target component) (checked in Step 2) | `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Pending form | Add the ledger ID to the pending bullet | REQ-008 / AC-5 | One pending bullet (INV-09 fold and Failure Conditions relabel) (checked in Step 2) | `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Pending form | Add ledger IDs to the pending bullets | REQ-008 / AC-5 | Two pending bullets (Decision Detail 5 and 9) (checked in Step 2) | `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | Pending form | Add the ledger ID to the pending bullet | REQ-008 / AC-5 | One pending bullet (INV-02 wording, `LlmTurnExecutor` creator) (checked in Step 2) | `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Pending form | Add the ledger ID to the pending bullet | REQ-008 / AC-5 | One pending bullet (manifest status correction) (checked in Step 2) | `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Pending form | Add the ledger ID to the pending bullet | REQ-008 / AC-5 | One pending bullet (section rename to `ADR Dependency Graph`) (checked in Step 2) | `tools/check_adr_structure.py` | Verified |
| `tools/check_adr_structure.py` | Status and pending-form checks | Add a Status value check (REQ-009) and a pending-form and ledger-ID resolution check (REQ-010) | REQ-009, REQ-010 / AC-6, AC-7 | `check_section_headings` verifies the `## Status` heading only; 10669 B against the 24576 B gate, no baseline entry (checked in Step 3) | `tests/tools/test_check_adr_structure.py` | Verified |
| `tests/tools/test_check_adr_structure.py` | Tests for the new checks | Add tests for an unknown Status value, an allowed value with a trailing paragraph, a pending bullet without an ID, and an unresolved ID | REQ-009, REQ-010 / AC-6, AC-7 | The file tests `check_section_headings` with `omit="Status"` and no Status value case (checked in Step 3) | `uv run pytest tests/tools/test_check_adr_structure.py` | Verified |
| `docs/00_governance/governance_04_documentation-checks.md` | Check documentation sync (fallout) | Update `### 10. ADR Structure Check` and the matching rule row so the new checks are listed; fallout of REQ-009 and REQ-010 (`AGENTS.md` Global Rule 9) | REQ-009, REQ-010 / AC-6, AC-7 | `### 10. ADR Structure Check` lists four checks and no Status or pending-form check (checked in Step 3) | `tools/check_docs_quality.py`, `tools/check_docs_structure.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Tool description sync (fallout) | Update the two `check_adr_structure.py` rows; fallout of REQ-009 and REQ-010 (`AGENTS.md` Global Rule 9) | REQ-009, REQ-010 / AC-6, AC-7 | Two rows describe `check_adr_structure.py` and list neither check (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/10_adr/adr_01_index.md` | The Status column carries `Accepted` and `Withdrawn`; it changes only if UNK-02 chooses removal | REQ-006 |
| `tools/check_known_deviation_sync.py` | Known Deviations bullets must cite a Part 1 Known Issue ID; Part 2 `NC-` headings are excluded | REQ-002 |
| `tools/check_needs_confirmation_inventory.py` | Inline `Needs confirmation` markers must have an NC entry | REQ-002 |
| `tools/check_canonical_source_registry.py` | ADR-sourced entries require a first Status line of `Accepted`, so the pending form must not alter it | REQ-005 |
| `tools/check_canonical_source_conflicts.py` | Same Status-line constraint (non-Accepted ADR-sourced entry) | REQ-005 |
| `tools/_validation_gate_defs.py` | Gate definition that runs `check_adr_structure.py`; confirms no gate change is needed | REQ-009 |
| `config/documentation_canonical_sources.toml` | ADR-004 is a registered source, ADR-010 is not; limits the Status-line constraint to ADR-004 | REQ-005 |

## Acceptance Criteria
- `AC-1` (REQ-001): The pending-marker inventory is reproducible with `rg -n "Current Decision Approval \(pending\)|Withdrawn By" docs/10_adr/` and every hit is classified.
- `AC-2` (REQ-002): Each ADR-004 Exception has an approval reference or an NC ID, `## Known Deviations` cites the Known Issue IDs, and `tools/check_known_deviation_sync.py` and `tools/check_needs_confirmation_inventory.py` report no ERROR.
- `AC-3` (REQ-003): ADR-010 cites CSC-001 and its first Status line is still `Withdrawn`.
- `AC-4` (REQ-004, REQ-005, REQ-006, REQ-007): `governance_01`, `governance_02`, `governance_03`, and `governance_05` define the ledger, the pending form, Withdrawn, and the reviewer mapping, and the change is merged only with the maintainer's approval; no approval text was written by the implementer.
- `AC-5` (REQ-008): No Accepted ADR contains unapproved decision text unless it is in the defined pending form, and every pending bullet cites a ledger ID that resolves.
- `AC-6` (REQ-009): `tools/check_adr_structure.py` rejects an unknown Status value (test).
- `AC-7` (REQ-010): `tools/check_adr_structure.py` rejects a pending bullet without a ledger ID or with an unresolved ID (test).
- `AC-8` (REQ-004 to REQ-010): The docs checkers listed in `routing.md` for the changed files report no ERROR.

## Tests
- `REQ-009`: unit tests in `tests/tools/test_check_adr_structure.py` for an unknown Status value, each allowed value, and a Status body with a trailing paragraph (ADR-010 shape).
- `REQ-010`: unit tests for a pending bullet with a resolving ID, without an ID, and with an unresolved ID, and for a `Withdrawn By` bullet that is not subject to the pending check.
- `REQ-001` to `REQ-008`: documentation-only; verified by the checkers in the Validation plan and by the `rg` inventory in AC-1.

## Documentation Impact
Yes. Governance documents change (`REQ-004` to `REQ-007`) and each ADR in the inventory changes (`REQ-008`); `governance_04` and `tools/TOOL_DESCRIPTIONS.md` change as fallout of the checker change. The target docs are named in `Implementation Target Files`.

## Assumptions
- The ADR approval ledger lives in a new part of `governance_03` (proposed default, see UNK-01). A ledger entry is created only for a pending amendment or the pending withdrawal, never for a past approval. Entry fields: ID, ADR, decision, approver, date, scope; approver and date stay `Not recorded` until the maintainer states them. This is falsifiable by the maintainer's decision at the Phase 2 gate.
- The pending form stays a bullet under `### Approval Record` and the ADR Status line stays `Accepted`, because `tools/check_canonical_source_registry.py` rejects a non-`Accepted` first Status line for an ADR-sourced entry. The form in the Issue's example (`Accepted (Amendment pending)`) would break that check for ADR-004.
- `Withdrawn` is defined as a governed status (UNK-02 holds the alternative of removing ADR-010).
- The ledger ID prefix is outside the Known Issue ID-prefix convention of `governance_03` Part 1, so `tools/check_known_deviation_sync.py` does not parse ledger IDs as Known Issue IDs.
- ADR-013 holds no pending marker: the Step 2 search for `Current Decision Approval (pending)` matched ten ADRs and not ADR-013. The inventory is re-run in Phase 1 before any ADR edit.
- Two files outside the Issue's Target Files list (`docs/00_governance/governance_04_documentation-checks.md`, `tools/TOOL_DESCRIPTIONS.md`) are fallout of the checker change; they are reported to the owner as a scope amendment per the Issue's Constraints.
- Sign-off channel for the Phase 2 decisions (`rules/coding.md` Explicit sign-off gates): a maintainer comment on this Plan.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Ledger location, format, and ID prefix (Issue: `不明`) | Maintainer decision | Maintainer confirms or replaces the proposed default (new part of `governance_03`) at the Phase 2 gate; a different location is a Plan amendment (`tools/amend_plan.py`, scope change needs approval) | False |
| UNK-02 | Whether ADR-010 stays a governed `Withdrawn` ADR or leaves the active set | Maintainer decision; `governance_02` and the Current-Specification-Only policy favor removal, CSC-001 and `adr_01_index.md` assume `Withdrawn` | Maintainer decision at the Phase 2 gate; removal is a Plan amendment (adds index and inbound-link rows) | False |
| UNK-03 | Reviewer mapping content: `Security Reviewer` has no RACI role of the same function | Maintainer decision | The proposal maps only where a RACI role of the same function exists and records the gap otherwise; the maintainer fills it at the Phase 2 gate | False |
| UNK-04 | Whether the spawn-failure, overlay-only fail-open, and warning-only exceptions of ADR-004 fall under the 2026-10-13 task-level approval | When each exception was added versus the approval date | `git log -S` on each exception text in `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` in Phase 1; a covered exception needs no Known Issue | False |
| UNK-05 | Whether an archived issue (`adrrev013`) may be corrected as the Issue asks | Archived files under `issues/done/` were not read (`rules/workflow-lifecycle.md` Target Validation) | Owner decides; the Plan does not target the file | False |
| UNK-06 | CSC-001 Validation evidence cites `rmcompat003` under `issues/`; it exists only under `issues/done/` | Owner decision on the CSC-001 correction | Follow-up outside this Plan | False |
| UNK-07 | Substance of the RAG-related ADR-004 Exception | Decision in `issues/20261117-123006_adrchk006_rag-failure-policy.md` (open) | That issue decides the substance; this Plan only registers and references it; it does not block this Plan | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/00_governance/governance_01_documentation-policy.md` | Modify | High | 4 | High (single author) | not applicable (rsynced) |
| `docs/00_governance/governance_02_documentation-metadata.md` | Modify | Low | 4 | High (single author) | not applicable (rsynced) |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | High | 13 | High (single author) | not applicable (rsynced) |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Modify | Medium | 6 | High (single author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Modify | Medium | 12 | High (single author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | Modify | Medium | 9 | High (single author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify | Low | 11 | High (single author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Modify | Low | 6 | High (single author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Low | 16 | High (single author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify | Low | 17 | High (single author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Modify | Low | 3 | High (single author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Modify | Low | 5 | High (single author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | Modify | Low | 6 | High (single author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Modify | Low | 4 | High (single author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Modify | Low | 6 | High (single author) | not applicable (rsynced) |
| `tools/check_adr_structure.py` | Modify | Medium | 1 | High (single author) | not applicable (rsynced) |
| `tests/tools/test_check_adr_structure.py` | Modify | Low | 3 | High (single author) | not applicable (rsynced) |
| `docs/00_governance/governance_04_documentation-checks.md` | Modify | Low | 21 | High (single author) | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | 74 | High (single author) | not applicable (rsynced) |

## Design
- **Classification**: Path B (more than 3 files; adds a check rule). Baseline: `radon cc tools/check_adr_structure.py -s` peaks at grade B (`check_section_headings`, 9); `vulture` and `bandit` report findings only outside the targets; `lint-imports` keeps all contracts. Consumer scan: not run, because no persisted schema, public API, or shared constant changes; the allowed Status set is local to `tools/check_adr_structure.py` and its consumers are listed in `Reference Files` (checked in Step 3). Persisted schema check: not applicable.
- **D1 Ledger**: a new part of `governance_03` after Part 4, named "ADR approval ledger" to keep it distinct from the Known Issue ledger that `tools/check_known_deviation_sync.py` calls a ledger. Alternative: a new `governance_06` document (adds a document and index entries). Chosen: the existing tracker, so no new file path is needed. Compatibility: the part sits after the Part 2 boundary that `tools/check_known_deviation_sync.py` stops scanning at, and its ID prefix is not in the Known Issue prefix list.
- **D2 Pending form**: the existing bullet shape, formalized: `- **Current Decision Approval (pending)**: {changed text} ... Ledger: {ID}` under `### Approval Record`; the ADR Status line stays `Accepted`. Alternative: a Status variant (rejected: breaks `tools/check_canonical_source_registry.py`). A pending bullet is removed when the approval is recorded.
- **D3 Withdrawn**: a governed status with a required `### Withdrawal Approval Record` and a rule that the Status first line is exactly `Withdrawn`; surviving present-tense wording is tracked as a Canonical Source Conflict (CSC-001). Alternative (UNK-02): remove ADR-010 from the active set.
- **D4 Reviewer mapping**: a table in `governance_05` `## RACI Model`, derived only from roles defined there; gaps recorded, not invented.
- **D5 Known Deviations**: `tools/check_known_deviation_sync.py` accepts only Part 1 Known Issue IDs, so the ADR-004 Exceptions are registered as Known Issue entries and listed by ID; NC-001 stays the owner of the `path_denylist` rationale.
- **D6 Checkers**: one allowed-Status constant in `tools/check_adr_structure.py` that mirrors `governance_01` `## ADR Status Definitions`; Status is read as the first non-empty line after `## Status` (the rule `tools/check_canonical_source_registry.py` uses). The pending check is scoped to bullets under `### Approval Record` and resolves ledger IDs against the ledger part of `governance_03`. A drift test asserts each allowed value appears in `governance_01`.
- **Approval boundary**: the implementer prepares Phase 2 as a proposal and writes no approval text; `tools/check_adr_preservation.py` is expected to report the Approval-section edits of Phase 3 and each report is reviewed, not suppressed.

## Implementation steps
1. **Phase 1: Registration that needs no decision**
   - [ ] Re-run the inventory (`rg -n "Current Decision Approval \(pending\)|Withdrawn By" docs/10_adr/`), classify every hit, and report the list (REQ-001; all ADR rows of `Implementation Target Files`)
   - [ ] Resolve UNK-04 with `git log -S` on each ADR-004 exception text, then add Known Issue entries in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` for the exceptions that lack approval (REQ-002)
   - [ ] In `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, list the Known Issue IDs in `## Known Deviations` and cite an approval reference or NC ID on each Exception (REQ-002)
   - [ ] In `docs/10_adr/adr_02_06_010_rag-fallback.md`, add the CSC-001 reference to the Status body (REQ-003)
2. **Phase 2: Maintainer decision gate and governance proposal**
   - [ ] Present D1 to D4 and UNK-01 to UNK-03 to the maintainer and record the answers as a maintainer comment on this Plan; stop until they exist (REQ-004 to REQ-007)
   - [ ] Edit `docs/00_governance/governance_01_documentation-policy.md` (Status set, pending form, Withdrawn rules, ledger citation format) (REQ-004, REQ-005, REQ-006)
   - [ ] Edit `docs/00_governance/governance_02_documentation-metadata.md` (front matter `status` sentence) (REQ-006)
   - [ ] Edit `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (ledger part and a pending entry per inventory item, none for past approvals) (REQ-004)
   - [ ] Edit `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` (reviewer mapping) (REQ-007)
   - [ ] Hold the merge until the maintainer approves the governance change; write no approval text
3. **Phase 3: Apply the forms to the ADRs**
   - [ ] Add the ledger ID to every pending bullet in `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`, `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`, `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`, `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`, and `docs/10_adr/adr_02_07_016_adr-authority-model.md` (REQ-008)
   - [ ] Apply the defined form to `### Withdrawal Approval Record` in `docs/10_adr/adr_02_06_010_rag-fallback.md` (REQ-006, REQ-008)
4. **Phase 4: Checker enforcement and sync**
   - [ ] Add the Status value check and the pending-form check to `tools/check_adr_structure.py`, and the tests to `tests/tools/test_check_adr_structure.py` (REQ-009, REQ-010)
   - [ ] Update `docs/00_governance/governance_04_documentation-checks.md` and the two rows of `tools/TOOL_DESCRIPTIONS.md` (REQ-009, REQ-010)
5. **Phase 5: Validation and hand-off**
   - [ ] Run the Validation plan commands and report each result; no deploy step, because no `scripts/` or `config/` file changes (`skills/deploy/SKILL.md` is not invoked)
   - [ ] Report the two fallout files to the owner as a scope amendment

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_adr_structure.py`, `tests/tools/test_check_adr_structure.py` | Unit | `uv run pytest tests/tools/test_check_adr_structure.py` | New tests pass |
| `tools/check_adr_structure.py` | Lint, type, security, size | `uv run ruff format tools/check_adr_structure.py`, `uv run ruff check tools/check_adr_structure.py`, `uv run mypy tools/check_adr_structure.py`, `uv run bandit tools/check_adr_structure.py`, `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | No findings; size under 24576 B |
| `tools/TOOL_DESCRIPTIONS.md`, `tools/check_adr_structure.py` | Sync | `uv run python tools/check_tool_descriptions_sync.py` | No findings |
| `tools/check_adr_structure.py` | Coverage | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At least 90% on changed lines (the target is under `tools/`, so `--cov=scripts` may report no changed Python lines; record that result) |
| `docs/00_governance/*.md`, `docs/10_adr/*.md` | Documentation checks | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py` | No ERROR |
| `docs/10_adr/*.md` | ADR checks | `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_authority.py`, `uv run python tools/generate_adr_authority.py --check`, `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_preservation.py` | No ERROR except the reviewed Approval-section reports of `check_adr_preservation.py` |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Registration checks | `uv run python tools/check_known_deviation_sync.py`, `uv run python tools/check_needs_confirmation_inventory.py` | No ERROR |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_02_06_010_rag-fallback.md` | Status-line constraint | `uv run python tools/check_canonical_source_registry.py` | No ERROR |
| `plans/`, `issues/` | Work item checks | `uv run python tools/check_workitem_structure.py --file __CHANGED_FILES__`, `uv run python tools/check_workitem_traceability.py --active-only` | No findings |

## Risks
- **Risk**: The governance change needs the maintainer's approval and the implementer cannot write approval text → **Mitigation**: Phase 2 is a proposal gated on a recorded maintainer comment; ledger entries are pending only; the merge is held until approval (likelihood: certain).
- **Risk**: The ledger term collides with the Known Issue ledger used by `tools/check_known_deviation_sync.py` → **Mitigation**: the part is named "ADR approval ledger", sits after the Part 2 boundary, and uses an ID prefix outside the Known Issue prefix list; a test covers the ID resolution.
- **Risk**: The pending-form check flags unrelated "pending" prose, for example `Withdrawn By: Pending maintainer statement` → **Mitigation**: the check is scoped to `### Approval Record` bullets whose text starts with `Current Decision Approval (pending)`, and Phase 3 conforms every ADR before Phase 4 enables it.
- **Risk**: Other issues edit the same ADR files and `docs/10_adr/adr_01_index.md` (adrchk001, 005, 008, 009, 012, 013, 015, 016, 021, 022) → **Mitigation**: this Plan lands first; re-run the inventory before each edit; `tools/check_plan_target_overlaps.py` reports overlaps when those Plans freeze; the order is the owner's call.
- **Risk**: A Status check that reads the whole Status body rejects ADR-010, which has a paragraph after the value → **Mitigation**: read the first non-empty line only (the rule used by `tools/check_canonical_source_registry.py`); a test covers the ADR-010 shape.
- **Risk**: Choosing UNK-02 removal invalidates the ADR-010 row and adds index and link rows → **Mitigation**: amend the Plan through `tools/amend_plan.py` before Phase 3; a removed row needs approval.
- **Risk**: `tools/TOOL_DESCRIPTIONS.md` has the highest churn of the targets → **Mitigation**: edit only the two rows and sync through `skills/git-commit-and-sync/SKILL.md` before committing.
- **Risk**: `tools/check_adr_preservation.py` reports the Approval-section edits as ERROR → **Mitigation**: each report is reviewed and justified in the commit message; the decision text is unchanged.
- **Risk**: New governance text violates the docs content policy (counts, concrete values) → **Mitigation**: run `tools/check_docs_content_policy.py` and name items instead of counting them.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Registration that needs no decision: inventory, ADR-004 Exceptions, CSC-001 reference | Pending | — | — | |
| 2 | Maintainer decision gate and governance proposal | Pending | — | — | |
| 3 | Apply the forms to the ADRs | Pending | — | — | |
| 4 | Checker enforcement and sync | Pending | — | — | |
| 5 | Validation and hand-off | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123011_adrchk011_adr-approval-governance.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261118-092611
- **Related target files**: `docs/00_governance/governance_01_documentation-policy.md`; `docs/00_governance/governance_02_documentation-metadata.md`; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`; `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`; `docs/10_adr/adr_02_06_010_rag-fallback.md`; `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`; `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`; `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`; `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`; `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`; `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`; `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`; `docs/10_adr/adr_02_07_016_adr-authority-model.md`; `tools/check_adr_structure.py`; `tests/tools/test_check_adr_structure.py`; `docs/00_governance/governance_04_documentation-checks.md`; `tools/TOOL_DESCRIPTIONS.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (inventory); Step 2 `rg` of pending markers | N/A: the inventory is reported, not stored in a file | Phase 1 | AC-1 | `rg` inventory command in AC-1 | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (ADR-004 Exceptions); Step 2 reading of ADR-004 and `tools/check_known_deviation_sync.py` | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Phase 1 | AC-2 | `tools/check_known_deviation_sync.py`, `tools/check_needs_confirmation_inventory.py` | Derived from confirmed evidence |
| REQ-002 | Same | `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Phase 1 | AC-2 | `tools/check_known_deviation_sync.py`, `tools/check_needs_confirmation_inventory.py` | Derived from confirmed evidence |
| REQ-003 | Issue Required Changes (CSC-001 from ADR-010); Step 2 grep of `CSC-001` | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Phase 1 | AC-3 | `tools/check_adr_structure.py`, `tools/check_canonical_source_registry.py` | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes (ledger decision); no ledger in governance (Step 2) | `docs/00_governance/governance_01_documentation-policy.md` | Phase 2 | AC-4 | `tools/check_docs_quality.py`, `tools/check_docs_content_policy.py` | Needs confirmation |
| REQ-004 | Same | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Phase 2 | AC-4 | `tools/check_known_deviation_sync.py`, `tools/check_docs_quality.py` | Needs confirmation |
| REQ-005 | Issue Required Changes (pending form); Status-line constraint in `tools/check_canonical_source_registry.py` | `docs/00_governance/governance_01_documentation-policy.md` | Phase 2 | AC-4 | `tools/check_docs_quality.py`, `tools/check_canonical_source_registry.py` | Derived from confirmed evidence |
| REQ-006 | Issue Required Changes (Withdrawn); ADR-010 Status, `governance_02` `### status` | `docs/00_governance/governance_01_documentation-policy.md` | Phase 2 | AC-4 | `tools/check_docs_quality.py` | Needs confirmation |
| REQ-006 | Same | `docs/00_governance/governance_02_documentation-metadata.md` | Phase 2 | AC-4 | `tools/check_docs_quality.py` | Needs confirmation |
| REQ-006 | Same | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Phase 3 | AC-5 | `tools/check_adr_structure.py` | Needs confirmation |
| REQ-007 | Issue Required Changes (reviewer mapping); `governance_05` RACI Model | `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Phase 2 | AC-4 | `tools/check_docs_quality.py` | Needs confirmation |
| REQ-008 | Issue Required Changes (apply the forms); Step 2 pending-marker inventory | `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Phase 3 | AC-5 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-008 | Same | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Phase 3 | AC-5 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-008 | Same | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Phase 3 | AC-5 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-008 | Same | `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Phase 3 | AC-5 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-008 | Same | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Phase 3 | AC-5 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-008 | Same | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Phase 3 | AC-5 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-008 | Same | `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Phase 3 | AC-5 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-008 | Same | `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Phase 3 | AC-5 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-008 | Same | `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | Phase 3 | AC-5 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-008 | Same | `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Phase 3 | AC-5 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-008 | Same | `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Phase 3 | AC-5 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-009 | Issue Required Changes (Status validation); `check_section_headings` checks the heading only (Step 3) | `tools/check_adr_structure.py` | Phase 4 | AC-6 | `tests/tools/test_check_adr_structure.py` | Confirmed by repository evidence |
| REQ-009 | Same | `tests/tools/test_check_adr_structure.py` | Phase 4 | AC-6 | `uv run pytest tests/tools/test_check_adr_structure.py` | Confirmed by repository evidence |
| REQ-009 | Same; `AGENTS.md` Global Rule 9 | `docs/00_governance/governance_04_documentation-checks.md` | Phase 4 | AC-6 | `tools/check_docs_quality.py` | Derived from confirmed evidence |
| REQ-009 | Same; `AGENTS.md` Global Rule 9 | `tools/TOOL_DESCRIPTIONS.md` | Phase 4 | AC-6 | `tools/check_tool_descriptions_sync.py` | Derived from confirmed evidence |
| REQ-010 | Issue Implementation Intent (checkers enforce the pending form) and Acceptance Criteria (ledger IDs resolve) | `tools/check_adr_structure.py` | Phase 4 | AC-7 | `tests/tools/test_check_adr_structure.py` | Derived from confirmed evidence |
| REQ-010 | Same | `tests/tools/test_check_adr_structure.py` | Phase 4 | AC-7 | `uv run pytest tests/tools/test_check_adr_structure.py` | Derived from confirmed evidence |
| REQ-010 | Same; `AGENTS.md` Global Rule 9 | `docs/00_governance/governance_04_documentation-checks.md` | Phase 4 | AC-7 | `tools/check_docs_quality.py` | Derived from confirmed evidence |
| REQ-010 | Same; `AGENTS.md` Global Rule 9 | `tools/TOOL_DESCRIPTIONS.md` | Phase 4 | AC-7 | `tools/check_tool_descriptions_sync.py` | Derived from confirmed evidence |
