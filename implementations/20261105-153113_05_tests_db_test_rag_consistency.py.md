## Goal

Add regression tests for the fail-closed RAG consistency contract: probe errors and
`sqlite-vec` unavailability produce explicit failures, unknown probe values never aggregate
as healthy zeros, and the schema/FK/embedding checks run independently when one raises. Also
update the in-memory test fixtures so a healthy database verifies clean under the new
per-probe guard (seq 01).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The report carries per-dimension unverified flags (`fk_unverified`, `embedding_unverified`,
  `schema_unverified`; `scripts/db/models.py`, seq 03) and the orchestrator records each
  probe's `sqlite3.Error` (seq 01). Tests assert on these.
- The embedding dimension contract is 1024 dims / 4096 bytes (`rules/env.md`). A valid
  `embedding` blob in the fixture must be 4096 bytes so `_check_embedding_dimension` returns
  clean.
- UNK-04 resolution: a missing embedding column (or unloaded vec0 extension) is treated as
  **unverified (fail closed)**, not clean. Therefore the fixtures must expose a `vec0`-
  compatible `chunks_vec` (an `embedding` column plus a valid vector) so healthy databases
  verify while a genuinely broken table still fails closed.

## Design decisions

- Fixtures first: add an `embedding BLOB` column to `chunks_vec` and a helper that inserts a
  4096-byte vector, so the embedding probe passes on healthy fixtures. Without this, the
  per-probe guard (seq 01) would mark every existing fixture's embedding dimension
  unverified and break the current green suite.
- Error injection via a fake `SQLiteHelper` whose `execute` raises `sqlite3.Error` for a
  targeted query, so each probe's propagation is exercised in isolation.
- Assert the structured contract (unverified flags, `diagnostic_errors`), not just
  `is_consistent == False`, so a future refactor cannot silently drop the fail-closed signal.

## Alternatives considered

- Skipping the embedding probe on non-`vec0` fixtures versus providing a valid vector. Chose
  providing a valid vector: it exercises the real probe path and keeps the suite representative
  of production (which always ships vec0). Skipping would leave the fail-closed embedding path
  untested.
- Asserting only `is_consistent()` versus asserting the per-dimension flags. Chose the flags:
  they pin WHICH dimension failed, matching AC-003's independence requirement.

## Implementation
### Target file
`tests/db/test_rag_consistency.py`

### Procedure
1. **Update the fixtures** so a healthy database verifies clean under the per-probe guard:
   - Add an `embedding BLOB` column to `chunks_vec` in `_RAG_SCHEMA`.
   - Add a helper `_insert_vec(db, chunk_id)` that inserts a 4096-byte (`1024 * 4`)
     `embedding` blob alongside the `chunk_id`, and route the existing raw
     `INSERT INTO chunks_vec (chunk_id)` calls through it (or otherwise supply a valid
     embedding). This makes `_check_embedding_dimension` return clean instead of raising on
     the missing column.
2. **Probe-error tests**: for each of FK, embedding, schema, build a fake helper whose
   `execute` raises `sqlite3.Error` for that probe's query and assert the corresponding
   flag (`fk_unverified` / `embedding_unverified` / `schema_unverified`) is set and
   `diagnostic_errors` is populated. No probe may return a silent empty/zero result on error
   (AC-001).
3. **Independence test**: force one probe (e.g. embedding) to raise and assert the other two
   still execute and report their real results (`fk_inconsistency_count`, `unknown_schema`),
   i.e. one failure does not cancel the others (AC-003).
4. **Zero-vs-unknown test**: construct a `RagConsistencyReport` with an unverified flag set
   and assert `is_consistent(report)` is `False` even when all numeric counts are zero, so an
   unknown value never aggregates as healthy (AC-002).
5. **Regression**: confirm the existing suite still passes after the fixture change, so a
   healthy database remains verified.

### Method
Fixture augmentation plus new test classes covering error injection, independence, and
zero-vs-unknown. Uses the existing `_FakeSQLiteHelper` extended to raise on a targeted query.

### Details
- Current `_RAG_SCHEMA` defines `chunks_vec` as `(chunk_id INTEGER PRIMARY KEY)` with no
  `embedding` column. On that schema `_check_embedding_dimension` raises `sqlite3.Error`
  (no such column), which the current combined `try`/`except` swallows. After the split
  (seq 01) the same raise marks the embedding dimension unverified, so the fixture must supply
  a valid embedding or the healthy-path tests regress.
- `_check_embedding_dimension` treats an empty `chunks_vec` (no rows) as clean; the failing
  case is specifically "rows present but embedding column absent/unloadable". The fixture
  change targets that case.
- Assert `report.embedding_unverified is True` (not merely `not is_consistent()`) so the test
  pins the structured contract.

## Compatibility considerations
Test-only change. The fixture change keeps healthy databases verifying clean, so no production
behavior changes. The consumer regression suite (`tests/agent/`, `tests/rag/`) is unaffected
by test-file edits.

## Security considerations
N/A: tests only; in-memory SQLite fixtures under `tmp_path`/module scope.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_rag_consistency.py` — full module green, including the new
  error-path, independence, and zero-vs-unknown cases.
- `uv run pytest tests/db/test_rag_consistency.py -k "probe or error or unverified"` — the new
  fail-closed cases explicitly.
- `uv run lint-imports` (0 broken contracts), `uv run ruff check .`, `uv run mypy scripts/`.

## Completion criteria
- Fixtures expose a `vec0`-compatible `chunks_vec` so a healthy database verifies clean.
- Tests exist for probe error, extension unavailability, partial-check independence, and
  zero-vs-unknown, and they fail if the fail-closed behavior regresses (AC-005).
- Existing suite stays green.

## Out of Scope
The orchestrator split (seq 01), the report status field (seq 03), consumer propagation
(seq 04), and the drill tests (seq 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Fixture update + new test classes. |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document. |
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
- **Requirement ID**: `REQ-005` (tests cover probe errors, extension unavailability, partial checks, zero-value ambiguity)
- **Source issue**: issues/20261104-143443_ragverify001_complete-fail-closed-rag-consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-230307_ragverify001_complete-fail-closed-rag-consistency.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-153113
- **Related target files**: tests/db/test_rag_consistency.py
