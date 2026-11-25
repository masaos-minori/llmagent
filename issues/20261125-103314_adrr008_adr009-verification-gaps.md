# Register and test the ADR-009 FTS text-separation invariants

## Priority
Medium

## Summary
ADR-009 INV-05, INV-06, INV-08, and INV-11 have no dedicated automated test and are absent from the coverage index and manifest; register them honestly and add failure-focused tests.

## Background
Verified against master on 2026-11-25 (source: local note `memo-issue.md`, issue 014):
- Confirmed: the ADR states "INV-05, INV-06, INV-08, INV-11 have no dedicated automated test" (`docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md:250`); the index lists only ADR-009 INV-07 and INV-10 (`adr_01_index.md:224-225`) and the manifest only those two (INV-07 and INV-10).
- Not found: tests for a normalization failure producing no chunks, for empty normalized output stored as NULL (INV-11), or for tokenizer independence; a search of `tests/rag` for such cases returned nothing.
- ADR-009 states "INV-09 is not used" (`:169`); that notation is the subject of issues/20261125-103317_adrr011_adr-stable-decision-ids.md, not this issue.

## Problem
Data-integrity invariants of the canonical/derived text boundary are unregistered and untested.

## Reason for Change
A regression could silently overwrite original chunk text with normalized text.

## Implementation Intent
Register each invariant with its honest status first (Manual or Not Verified), then add tests and update the evidence after they pass.

## Target Files or Areas
- `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`, `docs/10_adr/adr_01_index.md`, `registry/manifests/invariant_coverage.yaml`
- the RAG normalization, chunk-splitting, and FTS code and tests under `scripts/rag/ingestion/` and `tests/rag/`

## Required Changes
- Register INV-05, INV-06, INV-08, and INV-11 in the index and manifest.
- Add tests: a normalization failure creates no new chunk and leaves existing chunks unchanged; original text is not reconstructed from normalized text; a tokenizer change does not change `content`; an empty normalization result is stored as NULL.
- Update the ADR evidence and statuses after the tests pass.

## Constraints
- Do not claim `Confirmed` without a passing test; keep status vocabulary as the matrix checker defines it.

## Acceptance Criteria
- Each invariant appears in the coverage inventory with an accurate status (Automated, Manual, or Not Verified).
- Tests cover failure atomicity and source/derived separation.

## Testing Expectations
The four test groups above, the ADR matrix and generation checks, the cited-test gate, and the whole suite.

## Documentation Impact
ADR-009 evidence, the index, and the manifest.

## Out of Scope
- Changing the chunking or normalization behavior.

## Dependencies
- N/A: none.

## Unresolved Questions
- `不明`: the exact current implementation paths for normalization and chunk writing (to be read during implementation; `scripts/rag/ingestion/chunk_splitter.py` and `chunk_japanese.py` are the starting points).

## AI Implementation Instruction
Add tests that assert the ADR contract; if the code violates an invariant, report it instead of changing behavior in this issue.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-103314
- **Related target files**: `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`, `docs/10_adr/adr_01_index.md`, `registry/manifests/invariant_coverage.yaml`, `scripts/rag/ingestion/chunk_splitter.py`
