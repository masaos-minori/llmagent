# Give ADR decision details stable identifiers

## Priority
Low

## Summary
Approval records cite ADR Decision Details by position ("Decision Detail 22"), which can drift when list items are inserted; introduce stable decision ids and checker validation. The note's second claim, a generator formatting defect, is not reproducible.

## Background
Verified against master on 2026-11-25 (source: local note `memo-issue.md`, issues 018 and 020):
- Confirmed: ADR-008 approval and ledger text cite positional numbers (`adr_02_05_008_db-six-sqlite-store-separation.md:411-417`, for example "Decision Detail 22"); ADR-009 uses "INV-09 is not used" for a gap (`:169`) while other ADRs use other notation.
- Refuted: the note says generated index output has prose concatenated with the first ADR edge. In `docs/10_adr/adr_01_index.md` the generated blocks start with a separate "Generated from ..." line, a blank line, and the code fence (lines 72-76, 101-106, 140-144), and `uv run python tools/generate_adr_authority.py --check` reports no drift. No generator change is justified by current evidence.
- This is a proposal, not a defect: no drift or wrong approval scope has been observed.

## Problem
Positional references make approval scope fragile under reordering, and gap notation is inconsistent.

## Reason for Change
Stable ids prevent an approval from silently covering a different decision after an edit; the cost is a migration across ADRs, so timing matters.

## Implementation Intent
Define the id convention (for example `DD-###` and a reserved or retired invariant notation) in the ADR guide, migrate ADR-008 references first while preserving history, and validate dangling, duplicate, reused, and reserved ids in the ADR checkers.

## Target Files or Areas
- `docs/10_adr/adr_00_document-guide.md`, `docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md`, `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`
- `tools/check_adr_structure.py`, `tools/check_adr_reference.py`
- the checker tests under `tests/tools/`

## Required Changes
- Define and document the id convention and reserved notation.
- Migrate ADR-008 approval references to stable ids; add checker rules and tests for dangling, duplicate, reused, and reserved ids.

## Constraints
- Preserve approval history; do not change any decision or approval wording beyond the id references; generated sections stay generated.

## Acceptance Criteria
- Every approval reference resolves to one stable id; reordering list items does not change approval scope.
- Reserved ids cannot be reused silently; ADR checks pass and generation stays idempotent.

## Testing Expectations
Dangling, duplicate, and reserved-id tests, plus `generate_adr_authority.py --check` and the ADR checkers.

## Documentation Impact
The ADR guide and ADR-008 references.

## Out of Scope
- Any change to the index generator's output format (no defect found).

## Dependencies
- Perform after the higher-priority ADR content edits (issues/20261125-103309_adrr003_adr013-invariant-coverage.md, issues/20261125-103312_adrr006_adr010-withdrawn-history.md, issues/20261125-103313_adrr007_adr002-inv04-coverage.md, issues/20261125-103314_adrr008_adr009-verification-gaps.md) to avoid merge conflicts in the guide and index.

## Unresolved Questions
- `不明`: whether the maintainer wants a repository-wide id migration or ADR-008 only.

## AI Implementation Instruction
Migrate ADR-008 first, keep history intact, and stop if a reference cannot be mapped to one decision.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-103317
- **Related target files**: `docs/10_adr/adr_00_document-guide.md`, `tools/check_adr_structure.py`, `tools/check_adr_reference.py`
