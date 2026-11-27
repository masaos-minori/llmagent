# Add Approval Ledger integrity regression checks

## Priority
Low

## Summary
Add automated checks for Approval Ledger integrity that existing ADR structure and issue-inventory tooling do not cover.

## Background
Source: bundle item L-01. Verified against master on 2026-11-27:
- `Explicit in code`: `tools/check_adr_structure.py` already requires every ledger ID cited by an ADR pending bullet to have an entry (stated in the ledger section of `docs/00_governance/governance_03_issue-and-uncertainty-management.md`); `tools/check_issue_inventory_conformance.py` and `tests/tools/` exist.
- `Needs confirmation`: which of the checks below are already covered by those tools; the source claims they are not.

## Problem
Field completeness, duplicate IDs, ordering, reverse references from ledger entries to ADR pending bullets, and approved entries that remain active may not be validated, so governance drift can pass CI.

## Reason for Change
Independent of runtime implementation and not release-critical; a Low-priority hardening follow-up to issues/20261127-085938_amem010_final-validation-gate.md.

## Implementation Intent
Fail documentation CI when ledger structure or bidirectional consistency is broken, without inferring approval evidence or deleting entries.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- `tools/check_issue_inventory_conformance.py`, `tools/check_adr_structure.py`, `tests/tools/`, documentation CI workflow (`Unknown`)

## Required Changes
- Validate required ledger fields, duplicate `AAL` IDs, and ordering where policy requires it.
- Validate ADR pending bullets against active entries and active entries against ADR pending bullets; detect approved entries that remain active.
- Add valid and invalid fixtures, integrate the check into documentation CI, and document the checker and remediation. A tool change also needs its `tools/TOOL_DESCRIPTIONS.md` row and the lighter tool validation in `routing.md` "Adding a new tool".

## Constraints
- Do not infer approval evidence, delete ledger entries automatically, or change existing ADR decisions.

## Acceptance Criteria
- Broken ledger entries fail CI.
- ADR pending bullets and active entries are bidirectionally consistent.
- Duplicate and malformed `AAL` entries are detected and approved entries cannot remain active unnoticed.

## Testing Expectations
Unit tests with valid and invalid fixtures under `tests/tools/`; a smoke run of the checker against the live governance document; `rules/toolchain.md` checks for `tools/` changes.

## Documentation Impact
Checker description in `tools/TOOL_DESCRIPTIONS.md` and remediation guidance; Needs Confirmation items for any gap already covered.

## Out of Scope
- Changing ledger content or ADR decisions.

## Dependencies
- Depends on issues/20261127-085938_amem010_final-validation-gate.md.

## Unresolved Questions
- `不明`: the documentation CI workflow file and which checks already exist.

## AI Implementation Instruction
Extend existing checkers where possible. Stop and report if a requested check duplicates an existing one.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-085939
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `tools/check_issue_inventory_conformance.py`, `tools/check_adr_structure.py`, `tests/tools/`
