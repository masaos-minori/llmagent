## Goal

- Keep the corpus-index generation suite aligned with both ragrev015 production rules: its chunk payloads must use an in-domain `chunk_type`, and its fake embeddings must use the fixed production dimension (`REQ-001`, `REQ-002`).

## Scope
**Release unit**: ragrev015-core (Plan `### Release units`; owner-declared batch unit 20261110)

- `tests/rag/ingestion/test_ingester_index_generation.py` only.

## Assumptions

- Measured at HEAD `02f3143e2` in a scratch worktree: this file fails under each patch independently, and the same 2 tests fail under both, so both fixture causes hit the same tests.
- Failing names (measured, both patches): `TestIngestAllIndexGenerationBump::test_completed_ingest_advances_generation_by_one`, `TestIngestAllIndexGenerationBump::test_skipped_only_run_leaves_generation_unchanged`.
- Under the `chunk_type` domain check alone the cause is the payload fixtures `"chunk_type": ""` (current L140 in `_write_chunk` and current L168 in `_write_chunk_pair`): an empty value is rejected by `read_chunk_json`, so no group is ingested and the corpus generation never advances.
- Under the embedding-size check alone the cause is the 4 fake-embedding stubs `return_value=[0.1] * 128`, which produce a 512-byte BLOB the validator rejects.

## Design decisions

- Fix both causes in one document because the same two tests are affected by both production changes; splitting them would leave the file red between two implementation steps.
- Derive the fake embedding length from `get_embedding_dims()` in `scripts/db/store_protocols.py` rather than hard-coding `1024`, matching the seq-10 decision so the two files stay consistent.
- Use `"text"` for the payload fixtures: it is the schema default (`scripts/db/schema_sql.py` L41 `chunk_type TEXT NOT NULL DEFAULT 'text'`) and the value `ChunkSplitter` produces for prose chunks.

## Alternatives considered

- Marking the two tests `xfail` until the production change lands: rejected — the suite is green at HEAD, and the failure is a fixture mismatch, not an unresolved behavior question.

## Implementation
### Target file
- `tests/rag/ingestion/test_ingester_index_generation.py`

### Procedure
- Align the two chunk payload fixtures and the four fake-embedding stubs with the production contracts.

### Method
- Add `from db.store_protocols import get_embedding_dims` to the import block.
- Replace both `"chunk_type": "",` fixture values (current L140 and current L168) with `"chunk_type": "text",`.
- Replace all four occurrences of `return_value=[0.1] * 128` with `return_value=[0.1] * get_embedding_dims()`.

### Details
- `_write_chunk_pair` (current L152-175) intentionally writes two files with an identical generation signature and a duplicated `chunk_index` to trigger `GROUP_VALIDATION_FAILED`; only the `chunk_type` value changes, so the duplicate-index mechanism the test depends on is untouched.
- The file's own `chunks` table fixture declares `chunk_type TEXT` with no `CHECK` constraint (current L85), so the `chunk_type` failures here are read-time rejections, not schema rejections.

## Compatibility considerations

- Fixture-only change; no assertion changes.

## Security considerations
N/A: test data only.

## Rollback considerations
N/A: revert the single commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_ingester_index_generation.py -q` — the 2 measured failures are green after both production changes land; the fixture edits are behavior-neutral on HEAD (green before and after the fixture change alone).
- `uv run pytest tests/rag/ingestion -q` regression.

## Completion criteria

- Both `TestIngestAllIndexGenerationBump` tests pass with the real `chunk_type` domain rule and the real embedding-size validator active (AC-1, AC-2).

## Out of Scope

- Production validation logic (seq-1, seq-2 documents).
- Corpus index generation semantics themselves (documented in `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md`, unchanged by this plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261110-120906 | Test-only procedure: no production change end-of-unit gate: tests/rag/ingestion 337 passed; full suite 12133 passed; diff-cover 100%; ruff/mypy/lint-imports pass |
| 2 | Add or update tests per Validation plan | Completed | — | 20261110-120906 | end-of-unit gate: tests/rag/ingestion 337 passed; full suite 12133 passed; diff-cover 100%; ruff/mypy/lint-imports pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261110-120906 | end-of-unit gate: tests/rag/ingestion 337 passed; full suite 12133 passed; diff-cover 100%; ruff/mypy/lint-imports pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261110-120924 | N/A: not in scope |

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
- **Requirement ID**: `REQ-001` (reject wrong-size embeddings before the transaction), `REQ-002` (reject out-of-schema `chunk_type` at read time)
- **Source issue**: issues/20261108-131234_ragrev015_poison-chunk-groups-retried.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-232810
- **Related target files**: `tests/rag/ingestion/test_ingester_index_generation.py`