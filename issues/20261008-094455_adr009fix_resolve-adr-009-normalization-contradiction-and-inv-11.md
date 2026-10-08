# Resolve ADR-009 normalization contradiction and INV-11

## Priority
Medium

## Summary
Reconcile ADR-009 Rationale 3 with INV-05 and the Fail-Fast condition, add INV-11 for sentences whose normalization yields empty text, and remove a stale Completion Checklist note.

## Background
Source: local investigation notes (memo2.md, ADR-009 section; review findings G07, G06). The file rename is handled in a separate issue.

## Problem
- Rationale 3 says normalization never loses original text, but INV-05 and the Fail-Fast condition drop all chunks of a file whose normalization fails.
- RAG-002 (a sentence whose normalized text is empty is dropped together with its original text) has no invariant it violates.
- The Completion Checklist keeps a stale "not registered" note.

## Reason for Change
- The ADR's rationale and invariants disagree, so neither can be verified; RAG-002 needs a stated invariant (INV-11).
- Decision content changes, so an approval record is required.

## Implementation Intent
- Narrow the meaning to "normalized text never replaces content" and state that ingestion is abandoned per file.
- Apply Decision Details 6 and 11, Rationale 3, the Consequences replacement, INV-05 and INV-11, the RAG-002 Known Deviation, and the checklist change from memo2.md.

## Target Files or Areas
- `docs/10_adr/ADR-009-rag-ft5-text-separation.md` (filename may change under the rename issue)

## Required Changes
- Apply every ADR-009 replacement listed in memo2.md.
- Record a new Approval Record in the same change.

## Constraints
- governance_01 ADR Change Protocol applies.
- RAG-002 wording is updated in the ledger by the kiupd01 issue; keep both consistent.

## Acceptance Criteria
- Rationale 3, INV-05, and the Fail-Fast condition agree.
- INV-11 exists and RAG-002 is cited as its violation.
- Doc checkers pass.

## Testing Expectations
Run the doc checkers listed in `routing.md`. No code change.

## Documentation Impact
Documentation only: ADR-009 Decision Details, Rationale, Consequences, Invariants, Known Deviations, Completion Checklist, Approval Record.

## Out of Scope
- Fixing RAG-002 in code.
- Renaming the file.

## Dependencies
- Related: `issues/20261007-154050_regtest01_add-inv-02-regression-test-and-keep-original-japanese-text-on-empty-normalization.md`, the adr009ren issue, and the kiupd01 issue.

## Unresolved Questions
- N/A: none recorded in memo2.md.

## AI Implementation Instruction
Edit only the listed sections. Apply this issue before or after the rename issue, but not mixed in one commit. Run the doc checkers before finishing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-094455
- **Related target files**: `docs/10_adr/ADR-009-rag-ft5-text-separation.md`
