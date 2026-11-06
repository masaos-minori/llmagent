# Align invariant verification claims with actual evidence

## Priority
Medium

## Summary
Make each reviewed ADR verification claim reflect its actual evidence and coverage limits, add focused tests at the highest-risk unverified boundaries, and keep justified manual controls with explicit procedures and records.

## Background
Evidence already visible in the repository (Explicit in file):
- ADR-010 states INV-05 (full pipeline re-execution) is covered by a test where the in-process `run` is stubbed and "no test asserts the full stage sequence".
- ADR-008 states INV-16 (Dry Run) is covered without a test asserting byte-identity of a corrupt DB under Dry Run.
- ADR-004 INV-10 notes "the safety/integrity guarantee has no single crosscutting test", and the ADR index records the shared failure-policy review (ADR-004 INV-15/INV-16) as a deliberate Manual Review with a stated rationale and evidence.

These limits are recorded in places, but whether the index and every ADR present them consistently, and whether other claims are overstated, is not verified.

## Problem
A test that exists, especially a stub-based one, does not establish full architectural coverage. Accepted status and verification completion are separate dimensions. Overstated verification creates false confidence, while treating every manual check as defective would disregard deliberate decisions. Which claims are actually overstated is not yet established.

## Reason for Change
Verification reports must describe actual evidence, limits, and residual risk. It is Medium because it concerns testability and documentation accuracy rather than a confirmed runtime defect. Final mappings depend on the other ADR issues, so the work should be sequenced after them.

## Implementation Intent
Inventory existing invariant-to-evidence mappings in the ADR Invariant Verification Matrix without creating a duplicate registry. Inspect the referenced tests and assertions, classify each reviewed claim using existing repository conventions (full, partial, manual, absent, not executed), correct overstated claims in ADRs and the index, and add focused tests for high-risk gaps where feasible. Preserve justified manual controls and define their expected procedure and record.

## Target Files or Areas
- `docs/10_adr/adr_01_index.md` (Invariant Verification Matrix)
- Verification sections of affected ADRs, at least ADR-004, ADR-008, and ADR-010
- `tests/rag/test_rag_http_mode.py`, `tests/db/test_db_recovery.py`, and other tests identified during investigation
- CI configuration, only as identified during investigation

## Required Changes
- Inventory invariant-to-evidence mappings without creating a duplicate registry.
- Inspect referenced tests and assertions.
- Classify verification as full, partial, manual, absent, or not executed using existing conventions.
- Review RAG pipeline execution claims (ADR-010 INV-05) and database dry-run preservation claims (ADR-008 INV-16) specifically.
- Correct overstated claims in the ADRs and the index.
- Add focused tests for high-risk gaps where feasible (for example stage order on fallback, byte-identity under Dry Run).
- Preserve justified manual reviews, including the shared failure-policy review approach, and define expected procedures and records.
- Synchronize ADR and index entries.

## Constraints
- Do not mark an invariant verified solely because a test reference exists.
- Do not weaken an invariant to fit existing tests.
- Do not require universal automation.
- Do not treat Accepted status as evidence of implementation completion.
- Keep architectural policy changes in their dedicated issues.

## Acceptance Criteria
- Each reviewed claim identifies its actual evidence and coverage limits.
- Partial coverage and residual risks are visible.
- Added tests assert the intended boundary.
- Manual verification has a defined procedure and expected record.
- ADR and index statuses agree.
- Unexecuted tests are clearly distinguished from passing tests.

## Testing Expectations
- Run affected tests (`uv run pytest tests/rag tests/db` and any other affected area) and applicable CI checks; report skipped checks and environmental limitations explicitly.
- Run `check_adr_invariant_matrix.py`, `check_adr_reference.py`, `check_adr_preservation.py`, `check_docs_quality.py`, `check_docs_structure.py`, and the toolchain in `rules/toolchain.md` for added tests.

## Documentation Impact
Yes. ADR Verification sections and the index matrix: actual evidence, coverage limits, residual risk, and manual-verification procedures and records.

## Out of Scope
- Full test-suite redesign
- Mandatory automation of every architectural rule
- New authority or evidence registries

## Dependencies
- Depends on, for final mappings: `issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md`, `issues/20261107-050702_adrrag002_reconcile-adr-010-contract.md`, `issues/20261107-050703_adrdb001_clarify-adr-008-scope.md`, `issues/20261107-050704_adrcfg001_clarify-adr-002-isolation.md`.

## Unresolved Questions
- 不明: which claims beyond ADR-010 INV-05 and ADR-008 INV-16 are overstated; this needs the inspection above.
- 不明: the repository convention names for partial/not-executed status in the index; confirm before choosing labels.

## AI Implementation Instruction
Inspect each cited test's assertions before changing a claim. Keep changes minimal and add tests only for the identified high-risk gaps. Do not create new registries. Report skipped or unexecuted checks explicitly.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-050705
- **Related target files**: `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_02_06_010_rag-fallback.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `tests/rag/test_rag_http_mode.py`, `tests/db/test_db_recovery.py`
