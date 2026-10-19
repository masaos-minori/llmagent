## Goal
Create real-database tests that exercise Memory vector write, replace, delete, count, KNN, and hybrid retrieval on a default-opened session connection, and that a missing extension fails visibly (`REQ-006`, `REQ-008`).

## Scope
- One new test module under `tests/agent/memory/` (the directory exists).
- Tests use a temporary session database and a patched `build_db_config`; production paths and the JSONL archive are not touched.

## Assumptions
- `/opt/llm/sqlite-vec/vec0.so` exists in the development environment (reproduction on 2026-10-19 loaded it); CI has no extension, so the module skips explicitly there, matching `tests/agent/memory/test_memory_retriever.py`.
- This module is written first and must fail on `no such module: vec0` before the helper change (Plan Phase 1).

## Design decisions
- Create the schema through a default-opened `SQLiteHelper("session")` (not `load_vec=True`), so the test itself fails if the default regresses.
- Patch `agent.memory.write_ops._emit_delete_event` so `delete` does not read `agent.toml` or write the real JSONL archive.

## Alternatives considered
Reusing the in-memory fixtures of `test_memory_store.py` was rejected: they model `memories_vec` as a plain table, which is exactly what hid the defect.

## Implementation
### Target file
`tests/agent/memory/test_memory_vec_session.py` (new)

### Procedure
1. Define `_VEC_SO` (new) and a module-level `pytestmark` skip when the file is missing, with an explicit reason string.
2. Add fixture `vec_session_db` (new): `tmp_path` database, `DbConfig` with `sqlite_vec_so` set, `monkeypatch.setattr("db.helper.build_db_config", ...)`, schema via `build_session_schema_sql(4)` through a default-opened helper.
3. Add the tests listed under Details.
4. Run the module before the helper change and confirm it fails with `no such module: vec0`; run it after and confirm it passes.

### Method
- Build entries with `MemoryEntry(memory_id=..., memory_type=..., source_type="decision", session_id=None, turn_id=None, project=..., repo=..., branch=..., content=..., summary=...)`; `source_type` must be one of conversation, decision, rule, failure.
- Embeddings are 4-element float lists with `embed_dim=4`.
- Import `write_ops`, `count_ops`, `HybridRetriever`, `VectorRetriever`, and `MemoryQuery` from `agent.memory`.

### Details
- `test_session_default_connection_loads_vec` (new): a default-opened session helper can run `SELECT COUNT(*) FROM memories_vec`.
- `test_add_and_count_vec` (new), `test_upsert_replaces_vec_row` (new) (count stays the same after upserting the same id), `test_delete_removes_vec_row` (new) (with `_emit_delete_event` patched).
- `test_knn_search_returns_nearest_with_filters` (new): nearest entry first; a `memory_type` filter and a `branch` filter exclude non-matching entries; fewer than `limit` rows is acceptable and asserted (Plan UNK-05).
- `test_hybrid_search_reports_hybrid_mode` (new): `HybridRetriever.search` with an embedding sets `last_retrieval_mode` to `hybrid`.
- `test_missing_extension_config_fails_visibly` (new): after creating the schema, patch the config to `sqlite_vec_so=""`; `add` with an embedding raises `sqlite3.OperationalError`, `count_vec` raises, and the `memories` table has no row from the failed write (whole transaction rolled back).

## Compatibility considerations
N/A: new test module.

## Security considerations
N/A: tests only; no production data or paths are used.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/memory/test_memory_vec_session.py -q` (fails before `scripts/db/helper.py` and `scripts/agent/memory/retriever.py` change, passes after)
- `uv run ruff format` and `uv run ruff check` on the file; `uv run python tools/check_mock_patch_targets.py`
- `uv run python tools/check_suppression_justification.py` if any suppression is added (none expected)

## Completion criteria
- Every test passes on a vec-enabled machine after the helper and retriever changes, and fails before them.
- On a machine without the extension the module is skipped with an explicit reason.

## Out of scope
- Rewriting `test_memory_store.py` or `test_import_ops.py`
- Testing `rebuild_ops` or `import_ops` beyond what the plan names

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the module with the skip guard and the fixture | Pending | — | — | |
| 2 | Add the tests and run them to confirm the expected failure before the code change | Pending | — | — | |
| 3 | Confirm they pass after the helper and retriever changes | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) for the test file | Pending | — | — | |

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
- **Requirement ID**: `REQ-006`, `REQ-008` (real-DB Memory vector tests)
- **Source issue**: issues/20261019-092704_mem001_session-sqlite-vec-not-loaded-at-runtime.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-094625_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-095521
- **Related target files**: tests/agent/memory/test_memory_vec_session.py
