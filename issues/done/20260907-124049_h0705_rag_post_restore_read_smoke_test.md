# Add a RAG read smoke test to post-restore logical verification

## Priority
Medium

## Summary
Post-restore verification in `scripts/db/recovery.py` (`_run_logical_verification`) already
re-runs physical integrity checking and domain-specific logical consistency checks for both
`rag` and `session` targets after a restore, and `session`'s consistency report already
includes a read smoke test and a write smoke test (`_check_read_smoke_test`/
`_check_write_smoke_test` in `scripts/db/session_consistency.py`). `scripts/db/rag_consistency.py`
has no equivalent smoke-test function — RAG's post-restore verification checks table/
index/relationship counts but never actually executes a read query representative of
application usage (e.g. a search).

## Background
Confirmed by direct read: `scripts/db/session_consistency.py` lines 56-95 define
`_check_read_smoke_test()`/`_check_write_smoke_test()`, both wired into
`check_session_consistency()`'s result and consumed by `is_consistent()`. `scripts/db/rag_consistency.py`
has no function matching `smoke`/`read_`/`write_` (confirmed by `grep`) —
`check_rag_consistency()` only computes counts (`_collect_basic_counts`,
`_collect_document_checks`, `_collect_url_counts_and_mismatches`,
`_collect_affected_identifiers`).

## Problem
memo2.md's Issue H-07-07 (already implemented per
`issues/done/20260903-110305_h0707_add-rag-session-recovery-verification.md`) required
"Read-only search smoke test succeeds" as one of the RAG verification requirements. The
count-based checks (`fts_gap`, orphan counts, etc.) can all report zero/healthy while a
structural issue outside what they measure (e.g. a broken FTS query due to a subtly wrong
virtual-table configuration) still causes an actual search query to fail — the counts alone do
not prove the database is usable for its actual read path the way `session`'s
`_check_read_smoke_test` proves session/message reads work.

## Reason for Change
`recover_corruption()`'s success predicate for `rag` currently depends only on structural
counts, not on demonstrating that a representative read (matching what `session` already
does) succeeds — this is a narrower guarantee than what the domain policy intends and than
what `session` already provides for its own domain.

## Implementation Intent
Add a `_check_read_smoke_test`-equivalent to `scripts/db/rag_consistency.py` that runs a
minimal, representative read query (e.g. an FTS or vector search against a small/empty result
set, or a `SELECT 1 FROM documents LIMIT 1`-style existence check appropriate to what "search
smoke test" means for this schema) and wire its boolean result into `RagConsistencyReport`/
`is_consistent()`, mirroring the pattern `session_consistency.py` already establishes. Do not
add a write smoke test for RAG unless the domain policy (per H-07-01) explicitly permits
mutation during RAG verification — confirm this before adding one.

## Target Files or Areas
- `scripts/db/rag_consistency.py` (`check_rag_consistency()`, `is_consistent()`, a new
  smoke-test helper)
- `scripts/db/models.py` (`RagConsistencyReport` — new field)
- `tests/db/test_db_recovery.py` (or a dedicated RAG-consistency test file, if one exists —
  confirm before adding)

## Required Changes
- Add a read-smoke-test helper to `scripts/db/rag_consistency.py` following the same shape as
  `session_consistency.py`'s `_check_read_smoke_test` (try/except around a representative
  query, boolean result, error recorded in `diagnostic_errors` on failure).
- Add the new field to `RagConsistencyReport` and fold it into `is_consistent()`'s aggregate
  check.
- Confirm with H-07-01's recovery policy matrix whether a RAG write smoke test is also
  required/permitted; if not required, do not add one.
- Add a test case: read smoke test failure causes `is_consistent()` to report `False` /
  `recover_corruption()`'s `logical_verify_failed` action, mirroring the existing
  `test_recover_rag_fts_gap`/`test_recover_rag_fts_orphan` pattern in
  `tests/db/test_db_recovery.py`.

## Constraints
- Keep the smoke test read-only and lightweight — do not implement a full
  search-quality/relevance test, only an existence/executability check.
- Do not add a write smoke test for RAG without confirming the domain policy permits mutation
  during verification (per H-07-01).

## Acceptance Criteria
- [ ] `RagConsistencyReport` includes a read-smoke-test result, mirroring
      `SessionConsistencyReport`'s existing `read_smoke_test_ok` field.
- [ ] `is_consistent()` for RAG returns `False` when the smoke test fails, even if all
      count-based checks are healthy.
- [ ] A failing RAG smoke test causes `recover_corruption()` to return
      `action="logical_verify_failed"`, consistent with the existing count-based failure
      paths.
- [ ] Existing RAG consistency tests (`test_recover_rag_fts_gap`,
      `test_recover_rag_missing_table`, `test_recover_rag_fts_orphan`,
      `test_recover_rag_vector_orphan`) continue to pass unchanged.

## Testing Expectations
`uv run pytest tests/db/test_db_recovery.py -v` (or the dedicated RAG consistency test file,
once located); add the new smoke-test failure case described above.

## Documentation Impact
If a canonical recovery/RAG verification specification under `docs/` enumerates RAG's
post-restore checks, add the read smoke test there — this closes a gap already flagged as a
requirement in `issues/done/20260903-110305_h0707_add-rag-session-recovery-verification.md`.

## Out of Scope
- Do not implement a RAG write smoke test unless the domain policy explicitly
  requires/permits it.
- Do not change `session_consistency.py`'s existing smoke-test implementation.
- Do not alter the atomic-replace or WAL/SHM handling paths (tracked separately in this
  batch).

## Dependencies
Depends on `issues/done/20260903-110304_h0701_define-recovery-policy-per-sqlite-persistence-domain.md`
(H-07-01, for confirming write-smoke-test policy) and
`issues/done/20260903-110305_h0707_add-rag-session-recovery-verification.md` (H-07-07, which
already required this smoke test but did not implement it).

## Unresolved Questions
Whether the RAG domain policy (per H-07-01) permits or requires a write smoke test analogous
to session's — confirm before deciding whether to add one; default to read-only if
unconfirmed.

## AI Implementation Instruction
Follow `session_consistency.py`'s existing smoke-test pattern exactly (try/except, boolean
result, error appended to `diagnostic_errors`) rather than inventing a different shape for
RAG. Do not touch `scripts/db/recovery.py`'s control flow beyond what's needed to consume the
new report field — the dispatch logic (`_run_logical_verification`) already calls
`check_rag_consistency`/`is_consistent` generically.
