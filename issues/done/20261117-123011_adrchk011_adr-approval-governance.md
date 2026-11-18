# Establish ADR approval, status, and exception governance

## Priority
High

## Summary
Governance does not define the approval ledger, the pending-amendment form, the Withdrawn status, or the reviewer roles, so several ADRs are in states the rules do not allow. Define the mechanics and enforce them.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-H11`; merged from ADRCHK-H13, H14, H15, M03, L20 (review findings N1, N2, N4, N8, N25, M18, H8)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
Re-verified on 2026-11-18 against current docs and tools (adversarial pass; labels follow `skills/DESIGN.md` Evidence labels).
- Confirmed (`Explicit in code`): `governance_01` ADR Status Definitions define only `Proposed` and `Accepted`; ADR-010 `## Status` is `Withdrawn`; `tools/check_adr_structure.py` checks only that the `## Status` heading exists (`check_section_headings`), not its value.
- Confirmed (`Documentation only`): no governance document defines an approval ledger (pending bullets in ADR-001, 004, 005, 006, 008, 012, 014, 015, 016 cite "the ADR approval ledger" by name, and no ledger ID is cited anywhere); no governance document maps the Required Reviewer names (Architecture Owner, Affected Component Owner, Security Reviewer, Ops Reviewer, Data Owner) to the `governance_05` RACI roles.
- Corrected: a de facto pending form already exists as `- **Current Decision Approval (pending)**:` bullets under `### Approval Record` in ADR-001, 004, 005, 006, 008, 009, 012, 014, 015, and 016, and ADR-010 uses `### Withdrawal Approval Record` with `Pending maintainer statement`. Governance does not define the form. The pending changes are already applied in the ADR text (for example the ADR-001 INV-02 row and the `ADR Dependency Graph` section name in `adr_01_index.md`).
- Corrected: the ADR-004 dedup fail-open and warning-only exceptions already carry a written rationale. Only their approval is missing (`Maintainer approval record: written by a maintainer; not fabricated here.`, with no NC or ledger reference). The subprocess spawn-failure exception states no approval. The `path_denylist` rationale is PENDING and tracked as NC-001. ADR-004 `## Known Deviations` is `Not applicable`.
- Corrected: `tools/check_known_deviation_sync.py` parses only Part 1 Known Issue IDs in Known Deviations bullets (Part 2 `NC-` headings are excluded, and a bullet without a Known Issue ID is an ERROR). Exceptions listed in Known Deviations therefore need Known Issue entries; an NC entry alone does not satisfy the listing.
- Constraint found: `tools/check_canonical_source_registry.py` and `tools/check_canonical_source_conflicts.py` require the first line of an ADR-sourced entry's Status to equal `Accepted`, so the pending form must not alter the Status line.
- Constraint found: `governance_02` `status` rule removes a deprecated or superseded document from the active set instead of marking it with a historical status, which is in tension with a governed `Withdrawn` status and with the Current-Specification-Only policy in `governance_01`. CSC-001 is in `governance_03` Part 3; ADR-010 does not reference it.
- Path corrections: `adrrev013` and `rmcompat003` exist only under `issues/done/`; CSC-001 Validation evidence still cites `rmcompat003` as an open `issues/` path.

## Reason for Change
- Pending changes are already in Accepted text: examples are ADR-001 INV-02 Blocking=No, the ADR-016 section rename, the ADR-006 INV-13 wording, the ADR-010 withdrawal (Withdrawn By: Pending), and the ADR-004 Decision Group 10 amendment. governance_01 and governance_05 treat an unapproved decision change as a Blocking merge condition.
- The approval ledger is undefined: many ADRs cite an ADR approval ledger, but no governance document defines its location, format, or owner.
- Withdrawn is not a governed status: governance defines only Proposed and Accepted, ADR-010 is Withdrawn but keeps present-tense decision text, and `tools/check_adr_structure.py` only checks that a Status heading exists. CSC-001 covers this but ADR-010 does not reference it.
- ADR-004 Exceptions are untracked: the `path_denylist` rationale is marked PENDING, the dedup fail-open and warning-only exceptions have a rationale but no approval reference, only `path_denylist` is an NC item, and Known Deviations says Not applicable.
- Reviewer names do not map to roles: Required Reviewers do not match the RACI handles.

## Implementation Intent
- Governance defines the ledger, the pending-amendment form, the allowed status values, and the reviewer mapping.
- Every ADR either has approved text, or shows its pending amendment in the defined form.
- Checkers enforce the status set and the pending form.

## Target Files or Areas
- `docs/00_governance/governance_01_documentation-policy.md`
- `docs/00_governance/governance_02_documentation-metadata.md`
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`
- `tools/check_adr_structure.py`
- `docs/10_adr/adr_02_06_010_rag-fallback.md`
- `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
- `docs/10_adr/adr_01_index.md`
- issues/done/20261109-113123_adrrev013_rag-consistency-policy.md (Exceptions statement only; path now under done/)
- Every ADR that contains a pending marker

## Required Changes
- (no decision needed) Inventory every Pending approval marker in the ADRs and attach the list to the PR.
- (no decision needed) Register each unapproved ADR-004 Exception as an NC item, list the items in Known Deviations, and correct `adrrev013`.
- (no decision needed) Reference CSC-001 from ADR-010.
- (decision) Define the ledger path, its entry fields (ID, ADR, decision, approver, date, scope), and the citation format.
- (decision) Define the pending-amendment form, for example Accepted (Amendment pending) with a link.
- (decision) Define Withdrawn and its content rules, or move ADR-010 out of the active set.
- (decision) Add a mapping table from Required Reviewer names to RACI roles.
- Add Status value validation to `check_adr_structure.py` and apply the forms to every ADR in the inventory.

## Constraints
- Never write approval text, and never create ledger entries for past approvals.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- No Accepted ADR contains unapproved decision text unless it is in the defined pending form.
- Every ledger ID cited in an ADR resolves, or is tracked as a Needs Confirmation item.
- `check_adr_structure.py` rejects an unknown Status value (test).
- Each ADR-004 Exception has an approval reference or an NC ID.

## Testing Expectations
Test for Status validation under `tests/tools/`; run `tools/check_adr_structure.py`, `tools/check_needs_confirmation_inventory.py`, `tools/check_known_deviation_sync.py`, and the docs checkers. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. governance_01/02/03/05 and each affected ADR: ledger, pending form, Withdrawn, reviewer mapping, Known Deviations.

## Out of Scope
- Approving any pending decision.
- Deciding the substance of ADR-004 Exceptions.

## Dependencies
- Blocks `issues/20261117-123001_adrchk001_mcp-auth-contract.md`, `issues/20261117-123005_adrchk005_startup-fail-closed.md`, `issues/20261117-123009_adrchk009_plan-code-reconcile.md`, and `issues/20261117-123013_adrchk013_invariant-matrix-checks.md` (they use the pending form).
- `issues/20261117-123006_adrchk006_rag-failure-policy.md` decides the substance of the RAG-related ADR-004 Exception.

## Unresolved Questions
- The ledger location is `不明`; ask the maintainer for the path.
- The memo names `adrrev013` under `issues/`; it exists only under `issues/done/`. Whether an archived issue may be edited is `不明`; the plan does not target it.
- Whether ADR-010 stays as a governed `Withdrawn` ADR or leaves the active set is a maintainer decision (`governance_02` and the Current-Specification-Only policy favor removal; CSC-001 and `adr_01_index.md` currently assume `Withdrawn`).

## AI Implementation Instruction
- Never write approval text, and never create ledger entries for past approvals.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123011
- **Related target files**: `docs/00_governance/governance_01_documentation-policy.md`; `docs/00_governance/governance_02_documentation-metadata.md`; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`; `tools/check_adr_structure.py`; `docs/10_adr/adr_02_06_010_rag-fallback.md`; `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`; `docs/10_adr/adr_01_index.md`; `issues/done/20261109-113123_adrrev013_rag-consistency-policy.md (Exceptions statement only; path now under done/)`; Every ADR that contains a pending marker
