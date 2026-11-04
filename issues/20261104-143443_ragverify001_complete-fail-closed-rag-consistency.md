# Make RAG consistency verification complete and fail closed

## Priority
High

## Summary
Unify RAG diagnostic error handling and embedding validation so a failed or incomplete check cannot be reported as a healthy index.

## Background
Verified against current source on 2026-11-04 (confirmed by repository evidence):

- `_safe_url_count_query` in `scripts/db/rag_consistency_queries.py` catches `Exception` and returns `{}` with no error recorded; `check_rag_consistency` (`scripts/db/rag_consistency.py`) states that this stage has no error left to report.
- `check_rag_consistency` runs `_check_fk_consistency`, `_check_embedding_dimension`, and `_check_schema_recognition` in one `try` that ends in `except sqlite3.Error: pass`; an early failure skips the later checks and leaves their healthy defaults (`0`), and no diagnostic is added.
- `_check_embedding_dimension` reads `SELECT length(embedding) FROM chunks_vec LIMIT 1`, so only one row is validated.
- `_embedding_dimension_issue` formats `expected={report.dimension_mismatch}`, where `dimension_mismatch` is a 0/1 flag, so the message can show `expected=1` instead of the configured dimension.

## Problem
Both a query failure and an unexamined malformed embedding row can produce a clean report. `diagnostic_errors`, unexecuted checks, and dimension fields have inconsistent meanings, so a healthy result does not mean every required check completed.

## Reason for Change
Data-integrity and operational risk: this report gates recovery verification and startup consistency decisions, so a false healthy result hides a damaged index.

## Implementation Intent
Define a strict verification contract: every mandatory check ends as pass, fail, or an explicit unverified state (never a healthy zero default); query errors are preserved; all embeddings are validated against the canonical 1024-dimension, 4096-byte float32 contract; independent checks run under independent exception boundaries. Implement the report-model and query-contract change together so the meanings stay consistent.

## Target Files or Areas
- `scripts/db/rag_consistency.py`
- `scripts/db/rag_consistency_queries.py`
- `scripts/db/models.py` (`RagConsistencyReport`)
- `scripts/db/recovery_verification.py` (`_rag_inconsistency_detail` consumes the report)
- `tests/db/test_rag_consistency.py`, `tests/db/test_embedding_dimension.py`

## Required Changes
- Return URL-query errors with their results and append them to `diagnostic_errors`.
- Catch the expected `sqlite3` exceptions rather than a broad `Exception` where practical.
- Run foreign-key, schema-recognition, and embedding checks under independent exception boundaries.
- Represent unexecuted checks as `None` or an explicit enum; any failed or unverified mandatory check makes `is_consistent()` false.
- Validate the length of every `chunks_vec` row against 4096 bytes; report the mismatch count, the observed length/dimension distribution, and at most 10 affected chunk IDs.
- Separate `expected_embedding_dims`, the observed dimensions, and the mismatch count in the report and messages.

## Constraints
- Preserve existing public interfaces unless an acceptance criterion requires a contract change; report-field changes must be handled in every consumer (recovery verification, startup, CLI).
- Read-only queries only.
- Messages contain counts and chunk IDs only, no row content.
- Full-table embedding validation must stay acceptable for the representative RAG database size (size: unknown).

## Acceptance Criteria
- No failed SQL query is represented as an unqualified empty healthy result.
- One failed fatal check does not prevent later independent checks from running.
- An unexecuted mandatory check cannot produce a healthy result.
- An embedding whose length is not 4096 bytes is detected, including malformed rows after the first.
- Messages read like `expected=1024, observed=768`, never `expected=1`.
- Tests fail the chunks, FTS, vector, foreign-key, schema, and embedding queries independently.

## Testing Expectations
- Unit tests for each changed branch; fault-injection tests per query; integration tests with a production-equivalent schema (sqlite-vec where available).
- Run `uv run pytest tests/db/test_rag_consistency.py tests/db/test_embedding_dimension.py -q`, ruff, and mypy.

## Documentation Impact
Update the RAG consistency design document and runbook for the pass/fail/unverified contract and the new report fields (failure behavior, intent).

## Out of Scope
- Repair actions and index rebuild logic.
- Session-domain consistency checks.

## Dependencies
- `issues/20261104-143443_drillmetrics001_strengthen-recovery-drills-and-rpo-rto.md` depends on this issue (the drill runs the full RAG verification).
- `issues/20261104-143443_sqliterec001_atomic-fail-closed-sqlite-recovery.md` consumes the report.

## Unresolved Questions
- sqlite-vec installation/loading specification for CI: unknown.
- Representative RAG database size for performance testing: unknown.
- Whether an unverified check is FATAL or WARNING for startup (versus recovery): unknown.

## AI Implementation Instruction
Change the report model first, then update every consumer. Do not report a check as passed when it did not run. Keep messages free of row content.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261104-143443
- **Related target files**: `scripts/db/rag_consistency.py`, `scripts/db/rag_consistency_queries.py`, `scripts/db/models.py`, `scripts/db/recovery_verification.py`, `tests/db/test_rag_consistency.py`
