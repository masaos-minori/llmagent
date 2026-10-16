## Goal
- Pin the `updated_at` condition of the memory delete store with query assertions and a real in-memory SQLite case.

## Scope
- `tests/db/test_db_store_impl.py` only: additions to the memory delete store tests. The source change is the previous document.

## Assumptions
- The existing `TestSQLiteMemoryDeleteStore` tests use a `MagicMock` database and read the SQL from `mock_db.fetchall.call_args`.
- The file's `_FakeDB` wraps a real SQLite connection with `execute`, `fetchall`, and `commit` only; `delete_memories_before` also needs `begin_immediate`, which the real-database test adds locally.

## Design decisions
- Mock-based tests assert the SQL text; one real-database test proves the behavior with rows whose `created_at` and `updated_at` differ.
- The real-database test builds the minimal tables the delete store touches: `memories`, `memories_fts`, `memories_vec`, and `memory_links` (plain tables are enough).

## Alternatives considered
N/A: asserting SQL text alone was rejected because it does not prove retention behavior.

## Implementation
### Target file
`tests/db/test_db_store_impl.py`

### Procedure
- `test_collect_prunable_ids_uses_updated_at` (new): with a mock database, assert the SQL contains `updated_at < datetime('now', ?)` and `pinned = 0` and does not contain `created_at`.
- `test_delete_memories_before_selects_by_updated_at` (new): same assertion for the select in `delete_memories_before`.
- `TestMemoryDeleteStoreRealSqlite` (new) with a helper that wraps the real connection and adds a `begin_immediate` context manager (BEGIN IMMEDIATE and COMMIT) over `_FakeDB`'s methods: insert four memories (old `updated_at` and old `created_at`; old `created_at` and recent `updated_at`; old and pinned; recent), run `collect_prunable_ids(30)` and `delete_memories_before(30)`, and assert only the first memory is returned and deleted, that the recent-update and pinned rows remain, and that rows in the fts, vec, and link tables of the deleted id are gone.

### Method
- Use ISO timestamps built with `datetime` arithmetic relative to now (for example 90 days and 1 day ago) written as `YYYY-MM-DD HH:MM:SS` so SQLite's `datetime('now', ?)` comparison is unambiguous.
- Keep new names only in this Procedure section; refer to them elsewhere by description.

### Details
- Run the new tests against the unmodified source first: the two SQL tests and the real-database test are expected to fail.
- Do not change the existing mock-based tests.

## Compatibility considerations
N/A: additive tests.

## Security considerations
N/A: in-memory databases only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_db_store_impl.py -v` (new tests fail before the source change and pass after)
- `uv run ruff format tests/db/test_db_store_impl.py`, `uv run ruff check tests/db/test_db_store_impl.py`, `uv run mypy --no-namespace-packages tests/db/test_db_store_impl.py` (compare with the baseline)
- `uv run python tools/check_mock_patch_targets.py`

## Completion criteria
- The new tests exist and pass after the source change; the three that depend on `updated_at` fail beforehand.
- Existing tests pass unchanged and mypy has no new error in the file.

## Out of scope
- The store source, maintenance tests, and the `/memory` handler tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the two SQL assertion tests and the real SQLite test class | Pending | — | — | |
| 2 | Run the new tests against the unmodified source and record the result | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) after the source change | Pending | — | — | |

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
- **Requirement ID**: REQ-008 (prune by updated_at)
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-143248_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-145841
- **Related target files**: tests/db/test_db_store_impl.py
