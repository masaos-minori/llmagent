## Goal
Create `tests/db/test_session_consistency.py`: unit tests for
`check_session_consistency()`/`is_consistent()` (seq 03), mirroring
`tests/db/test_rag_consistency.py`'s existing structure (REQ-008).

## Scope
- In scope: new file `tests/db/test_session_consistency.py` only, covering the
  Session logical-corruption cases: missing table, orphaned message/invalid
  relationship, invalid memory-link, read smoke-test failure, write smoke-test
  failure where applicable, no content leaked in a failure result.
- Out of scope: `tests/integration/test_session_recovery.py` (seq 10, the
  `_restore_from_backup()`-level integration tests); `check_rag_consistency()`'s own
  tests (unchanged).

## Assumptions
- Seq 03 (`scripts/db/session_consistency.py`) lands before or together with this
  row — these tests exercise a function/dataclass that does not exist until that row
  is implemented.
- The in-memory SQLite fixture pattern (Design decisions below) can substitute a
  plain table for `memories_vec` (a `vec0` virtual table requiring the `sqlite-vec`
  extension), matching how `test_rag_consistency.py`'s own `_RAG_SCHEMA` already
  substitutes a plain table for `chunks_vec` — `check_session_consistency()`'s own
  checks (per seq 03's design) do not need to query `memories_vec`'s vector column
  itself, only confirm the table exists.

## Design decisions
- Mirror `test_rag_consistency.py`'s exact structure: a `_FakeSQLiteHelper` wrapper
  (`__init__(conn)`, `execute()`, `fetchall()`, `commit()`) around a real in-memory
  `sqlite3.Connection`, a local schema string (`_SESSION_SCHEMA` — a
  vec0-extension-free copy of `_SESSION_SCHEMA_TEMPLATE`), and one test class per
  concern group (matching `TestRagConsistency`/`TestRagConsistencySeverity`'s
  existing split).
- Use real SQLite inserts/deletes to construct each corruption scenario (e.g. insert
  a `messages` row with a `session_id` that does not exist in `sessions`) rather than
  mocking `db.execute()` — matches `test_rag_consistency.py`'s existing approach of
  exercising real SQL against a real (if minimal) schema.

## Alternatives considered
- Mock `SQLiteHelper.execute()` to return canned rows per query, avoiding a real
  SQLite connection: rejected — `test_rag_consistency.py`'s existing precedent uses
  real in-memory SQLite specifically so the SQL itself (joins, `NOT IN` subqueries) is
  exercised, not just the Python logic around it; this row follows the same
  precedent for consistency and because `check_session_consistency()`'s FK-orphan
  queries are exactly the kind of SQL a mock would risk mismatching silently.

## Implementation
### Target file
`tests/db/test_session_consistency.py`

### Procedure
1. Define `_SESSION_SCHEMA` in this test file: copy `_SESSION_SCHEMA_TEMPLATE`
   (`scripts/db/schema_sql.py:93-152`) with `memories_vec` replaced by a plain table
   (`CREATE TABLE memories_vec (memory_id TEXT PRIMARY KEY, embedding BLOB)` or
   similar), matching `test_rag_consistency.py`'s `_RAG_SCHEMA` substitution pattern
   for `chunks_vec`.
2. Define `_FakeSQLiteHelper` identically to `test_rag_consistency.py`'s existing
   class (or import/reuse it if this row's implementation finds it reusable as a
   shared test helper — confirm during implementation whether extracting it to a
   shared `tests/db/conftest.py` fixture is warranted, without over-engineering a
   two-user abstraction).
3. Add one test class covering: required tables exist (drop one table, assert
   `diagnostic_errors` is set); sessions readable; message→session referential
   validity (insert an orphaned `messages` row, assert
   `orphaned_message_count == 1` and the affected `message_id` appears in the
   report); memory/memory-link validity (insert an orphaned `memory_links` row,
   assert `orphaned_memory_link_count == 1`); session diagnostics readable; read
   smoke test (assert `read_smoke_test_ok is True` on a healthy DB, `False` if a
   required table is dropped); write smoke test (assert `write_smoke_test_ok is True`
   and the throwaway row is not left behind — assert row count unchanged
   before/after, matching the Plan's Risks mitigation for seq 03).
4. Add a test asserting `is_consistent()` returns `False` for every corruption case
   above and `True` for a healthy fixture DB.
5. Add a test asserting no report field or `diagnostic_errors` entry contains
   `messages.content`/`memories.content` string values — only counts/IDs (REQ-010).

### Method
Confirmed this cycle (2026-09-06) via direct read of
`tests/db/test_rag_consistency.py` (lines 1-50+): `_FakeSQLiteHelper` (lines 16-27)
wraps a real `sqlite3.Connection`; `_RAG_SCHEMA` (lines 32+) is a vec0-free copy of
the production schema; `TestRagConsistency`/`TestRagConsistencySeverity`/
`TestNewConsistencyChecks` (lines 141, 247, 457) are the existing per-concern test
class split this row's new file mirrors.

### Details
No change to `test_rag_consistency.py` itself — this is a new, separate file.

## Compatibility considerations
N/A: new test file, no existing test affected.

## Security considerations
Test fixtures must use synthetic placeholder content for `messages.content`/
`memories.content`, never realistic-looking user data, consistent with REQ-010's
no-content-leakage requirement being testable without ambiguity.

## Rollback considerations
New file — revert via `git rm tests/db/test_session_consistency.py` if seq 03's
actual report shape differs enough from this document's assumptions to require a
substantially different test structure.

## Validation plan
- `uv run pytest tests/db/test_session_consistency.py -v` — all new tests pass.
- `uv run pytest tests/db/test_rag_consistency.py -v` — regression check, unaffected
  (confirms no shared-fixture extraction broke the existing RAG tests, if step 2's
  extraction option was taken).

## Completion criteria
- Every Session logical-corruption case in the Issue's Testing Expectations has a
  corresponding passing test in this new file.
- `is_consistent()` is tested against both a healthy and each corrupted fixture.

## Out of scope
- `tests/integration/test_session_recovery.py` — tracked in seq 10.
- `scripts/db/session_consistency.py`'s own implementation — tracked in seq 03.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-008
- **Source issue**: issues/20260903-110305_h0707_add-rag-session-recovery-verification.md
- **Source plan**: plans/20260905-163508_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-144010
- **Related target files**: tests/db/test_session_consistency.py
