# Establish ADR approval, status, and exception governance

## Priority
High

## Summary
Governance does not define the approval ledger, the pending-amendment form, the Withdrawn status, or the reviewer roles, so several ADRs are in states the rules do not allow. Define the mechanics and enforce them.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-H11`; merged from ADRCHK-H13, H14, H15, M03, L20 (review findings N1, N2, N4, N8, N25, M18, H8)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
Claims come from the review (`Documentation only` until re-verified).

## Reason for Change
- Pending changes are already in Accepted text: examples are ADR-001 INV-02 Blocking=No, the ADR-016 section rename, the ADR-006 INV-13 wording, the ADR-010 withdrawal (Withdrawn By: Pending), and the ADR-004 Decision Group 10 amendment. governance_01 and governance_05 treat an unapproved decision change as a Blocking merge condition.
- The approval ledger is undefined: many ADRs cite an ADR approval ledger, but no governance document defines its location, format, or owner.
- Withdrawn is not a governed status: governance defines only Proposed and Accepted, ADR-010 is Withdrawn but keeps present-tense decision text, and `tools/check_adr_structure.py` only checks that a Status heading exists. CSC-001 covers this but ADR-010 does not reference it.
- ADR-004 Exceptions are untracked: the `path_denylist` rationale is marked PENDING, dedup fail-open and warning-only continuation have no rationale or approval, only `path_denylist` is an NC item, and Known Deviations says Not applicable.
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
- The memo names `adrrev013` under `issues/`; it exists only under `issues/done/`.

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
