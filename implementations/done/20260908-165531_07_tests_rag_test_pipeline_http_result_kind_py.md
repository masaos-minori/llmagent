# Implementation Procedure: Update test_pipeline_http_result_kind.py for New Structure

## Goal

Update `tests/rag/test_pipeline_http_result_kind.py` to construct/patch the new `RagPipeline` structure after extracting private SQLite/refiner attributes to separate modules, per UNK-01's preferred resolution (rewrite tests directly rather than preserving via forwarding properties).

## Scope

- Replace direct assignment of `pipeline._rag_db_path`/`_sqlite_vec_so`/`_sqlite_timeout`/`_sqlite_busy_timeout_ms`/`_augment_refiner` with constructing/patching the new structure
- Align with Phase 4 (DB connection extraction) and Phase 6 (AugmentRefiner decoupling)

## Assumptions

- The Issue states `__init__` "stores five SQLite-related attributes" but names only four (`_rag_db_path`, `_sqlite_vec_so`, `_sqlite_timeout`, `_sqlite_busy_timeout_ms`); direct code reading confirms exactly these four exist.
- After Phase 4, `RagPipeline.__init__` accepts optional `RagDatabaseConnection` parameter; after Phase 6, `AugmentRefiner` is optional constructor parameter (default `None`).
- Tests must be rewritten to use the new structure directly, not preserved via forwarding properties on `RagPipeline`.

## Design decisions

1. **Rewrite tests directly** — matches the Issue's stated intent to decouple the constructor.
2. **Use `RagDatabaseConnection` where applicable** — tests that need database access should instantiate `RagDatabaseConnection` and pass it to `RagPipeline`.
3. **Pass `AugmentRefiner` as constructor parameter** — tests that need refiner behavior should pass it directly.

## Alternatives considered

- Preserving via forwarding properties on `RagPipeline`: rejected because it defeats the purpose of decoupling the constructor (Issue's stated intent).
- Mocking `RagPipeline` internals: rejected because it obscures the real behavior being tested.

## Implementation

### Target file

`tests/rag/test_pipeline_http_result_kind.py`

### Procedure

1. Read current test file to identify all direct private attribute assignments (lines 31-42 confirmed: 5 direct-assignment lines).
2. For each test that assigns `pipeline._rag_db_path`/`_sqlite_vec_so`/`_sqlite_timeout`/`_sqlite_busy_timeout_ms`:
   - Create a `RagDatabaseConnection` instance with the same parameters.
   - Pass it to `RagPipeline` constructor (or set as attribute if constructor doesn't accept it yet).
3. For each test that assigns `pipeline._augment_refiner`:
   - Pass `AugmentRefiner` as constructor parameter (per Phase 6: optional constructor parameter, default `None`).
4. Remove all direct private attribute assignments from the test file.
5. Verify tests pass against the new structure.

### Method

Test rewrite: replace private attribute assignments with proper construction patterns.

### Details

- Current direct-assignment lines: `tests/rag/test_pipeline_http_result_kind.py:31-42` (5 lines)
- Private attributes affected: `_rag_db_path`, `_sqlite_vec_so`, `_sqlite_timeout`, `_sqlite_busy_timeout_ms`, `_augment_refiner`
- After Phase 4: `RagPipeline` may accept `RagDatabaseConnection` as constructor parameter
- After Phase 6: `AugmentRefiner` is optional constructor parameter (default `None`)

## Compatibility considerations

- Tests must pass against the new structure; behavior must remain identical.
- If constructor doesn't accept `RagDatabaseConnection` yet, use attribute setting on the pipeline instance (less ideal but functional).

## Security considerations

- Test file changes have no security impact.

## Rollback considerations

- Revert: restore original private attribute assignments.
- Low risk: test changes are reversible.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/rag/test_pipeline_http_result_kind.py` | Integration | `uv run pytest tests/rag/test_pipeline_http_result_kind.py -v` | All tests pass against the new structure |

## Completion criteria

- No direct private attribute assignments remain in the test file.
- Tests pass against the new `RagPipeline` structure.
- Behavior unchanged from before refactor.

## Out of scope

- Modifying test assertions or adding new tests.
- Changing test coverage requirements.
- Updating other test files (handled separately).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Identify all direct private attribute assignments | Completed | — | — | Found 5 lines (31-34: DB attrs + 42-49: AugmentRefiner) |
| 2 | Rewrite DB-related assignments using `RagDatabaseConnection` | Completed | — | — | Removed; constructor handles DB via `RagDatabaseConnection` |
| 3 | Rewrite AugmentRefiner assignment using constructor parameter | Completed | — | — | Removed; constructor accepts `augment_refiner` param |
| 4 | Remove all direct private attribute assignments | Completed | — | — | All removed; `_make_pipeline()` simplified |
| 5 | Verify tests pass | Completed | — | — | 4/4 passed; ruff/mypy clean |

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
- **Requirement ID**: REQ-005, REQ-007 — update test file for new DB/connection structure
- **Source issue**: issues/20260908-105318_refactor_rag_pipeline_complexity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-165531_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-165531
- **Related target files**: tests/rag/test_pipeline_http_result_kind.py
