# Implementation: RAG Regression Test File Creation

## Goal

Add two missing cross-cutting RAG regression test files (`test_rag_http_mode.py` and `test_rag_refiner.py`) that cover HTTP mode `remote_empty`/`in_process_fallback` invariants and Refiner fallback diagnostics, complementing the three existing partial test files.

## Scope

- **In-Scope**:
  - Create `tests/test_rag_http_mode.py` — `remote_empty` vs `in_process_fallback` invariants in `RagPipeline.augment()`
  - Create `tests/test_rag_refiner.py` — `refine_context()` fallback paths and diagnostics from `rag/pipeline_refiner.py`
  - Audit `tests/test_rag_ingestion_pipeline.py` for missing invariants (crawler → ChunkSplitter → RagIngester `.json` lifecycle, SHA-256 re-ingestion)
  - Audit `tests/test_rag_quality_regression.py` for missing `use_rrf=False` diagnostics and ranking degradation coverage
  - Audit `tests/test_rag_consistency.py` for missing `/db rebuild-fts` repair flow coverage
  - Verify RAG schema does not reference Agent session tables
- **Out-of-Scope**:
  - Large-scale retrieval benchmarks
  - Network-dependent integration tests against real external services
  - Performance benchmarking
  - Changes to production source code in `scripts/`

## Assumptions

- `tests/test_rag_ingestion_pipeline.py` (411 lines), `tests/test_rag_quality_regression.py` (394 lines), and `tests/test_rag_consistency.py` (334 lines) already exist with partial coverage; they may need additional test cases appended.
- `tests/test_pipeline_http_result_kind.py` (existing) tests `_http_result_kind` attribute but does NOT test `remote_empty` as a documented success case (empty string = valid remote response) vs `in_process_fallback` as fallback; `test_rag_http_mode.py` will test the `SearchDiagnostics` fields (`result_source`, `http_result_kind`, `fallback_reason`) and the `augment()` return contract.
- `tests/test_pipeline_refiner_fallback.py` (existing, 78 lines) tests `refine_context()` directly; `test_rag_refiner.py` will test the integration path through `augment()` and `get_diagnostics()` pipeline-level reporting.

## Implementation

### Target file: `tests/test_rag_http_mode.py` (new)

#### Procedure

Create new test file covering HTTP mode invariants at the `SearchDiagnostics` level.

#### Method

Create new file — add test classes following the pattern established in `tests/test_pipeline_http_result_kind.py`.

#### Details

**Test classes to create:**

1. **`TestRemoteEmpty`:**
   - Mock `call_rag_service` returning `""` (empty string, 200 status)
   - Assert `SearchDiagnostics.result_source == "REMOTE"`
   - Assert `SearchDiagnostics.http_result_kind == "remote_empty"`
   - Assert `augment()` returns `""` (not fallback to in-process pipeline)

2. **`TestInProcessFallback`:**
   - Mock `call_rag_service` returning `None` with `set_fallback_reason("connection error")`
   - Assert `SearchDiagnostics.result_source == "FALLBACK"`
   - Assert `SearchDiagnostics.http_result_kind == "in_process_fallback"`
   - Assert `augment()` returns non-empty string from in-process pipeline
   - Assert `pipeline.get_diagnostics()["fallback_count"] >= 1`

3. **`TestRemoteNonempty`:**
   - Mock `call_rag_service` returning non-empty string (200 status)
   - Assert `SearchDiagnostics.result_source == "REMOTE"`
   - Assert `SearchDiagnostics.http_result_kind == "remote_nonempty"`
   - Assert `augment()` returns the remote string directly

4. **`TestNoHttpMode`:**
   - Set `rag_service_url=""` (no HTTP mode)
   - Assert `SearchDiagnostics.result_source == "IN_PROCESS"`
   - Assert `SearchDiagnostics.http_result_kind is None` or `"not_used"`
   - Assert in-process pipeline runs normally

### Target file: `tests/test_rag_refiner.py` (new)

#### Procedure

Create new test file covering Refiner fallback diagnostics at the pipeline level.

#### Method

Create new file — add test classes following the pattern established in `tests/test_pipeline_refiner_fallback.py`.

#### Details

**Test classes to create:**

1. **`TestRefinerFallbackDiagnostics`:**
   - Patch `RagLLM.refine_context` to return `""`
   - Assert `augment()` returns raw chunks (fallback)
   - Assert `pipeline.get_diagnostics()["refiner_fallback_count"] >= 1`
   - Assert `pipeline.get_diagnostics()["refiner_returned_empty"] >= 1`

2. **`TestRefinerExceptionDiagnostics`:**
   - Patch `RagLLM.refine_context` to raise `httpx.RequestError`
   - Assert `augment()` returns raw chunks (fallback)
   - Assert `pipeline.get_diagnostics()["refiner_fallback_count"] >= 1`
   - Assert `pipeline.get_diagnostics()["refiner_exception_count"] >= 1`

3. **`TestRefinerNoRetry`:**
   - Patch `RagLLM.refine_context` to raise once
   - Assert `refine_context` was called exactly once (no retry)

4. **`TestRefinerDiagnosticsPipelineLevel`:**
   - Full `augment()` integration with refiner enabled
   - Assert all diagnostic fields (`refiner_fallback_count`, `refiner_returned_empty`, `refiner_exception_count`) are correctly aggregated

### Target file: `tests/test_rag_ingestion_pipeline.py` (audit)

#### Procedure

Read existing file to identify missing invariants. Based on earlier inspection of plan 20260629-095420, the following tests may be needed:
- Crawler output `.json` suffix assertion
- ChunkSplitter input `*.json` only (no `.txt`)
- Chunk output `.json` suffix
- RagIngester `_move_to_registered` preserves `.json` suffix
- `source_file` field preserves `.json` filename

### Target file: `tests/test_rag_quality_regression.py` (audit)

#### Procedure

Read existing file to verify `use_rrf=False` diagnostics coverage. Based on earlier inspection of plan 20260629-095101, the following may be needed:
- `fusion_mode == "dedup_only"` diagnostic assertion
- MQE ranking degradation log message when `use_rrf=False`

### Target file: `tests/test_rag_consistency.py` (audit)

#### Procedure

Read existing file to confirm `/db rebuild-fts` repair flow coverage. Based on earlier inspection, `test_summarize_issues_fts_gap_includes_rebuild_guidance` already exists — no changes expected.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/test_rag_http_mode.py` | Unit tests with mocked `call_rag_service`; in-memory DB | `uv run pytest tests/test_rag_http_mode.py -v` | All tests pass; `remote_empty`, `in_process_fallback`, `remote_nonempty`, no-HTTP invariants verified |
| `tests/test_rag_refiner.py` | Unit tests with mocked `RagLLM`; AsyncMock for LLM calls | `uv run pytest tests/test_rag_refiner.py -v` | All tests pass; fallback reasons, no-retry, pipeline-level diagnostics verified |
| `tests/test_rag_ingestion_pipeline.py` | Integration tests with in-memory SQLite and mocked `SQLiteHelper` | `uv run pytest tests/test_rag_ingestion_pipeline.py -v` | All 411+ lines pass; schema independence test added if missing |
| `tests/test_rag_quality_regression.py` | Async unit tests with patched `_search_all_queries` | `uv run pytest tests/test_rag_quality_regression.py -v` | All tests pass; `use_rrf=False` dedup-only ranking degradation covered |
| `tests/test_rag_consistency.py` | Unit tests with in-memory SQLite and real FTS5 virtual tables | `uv run pytest tests/test_rag_consistency.py -v` | All tests pass; rebuild-fts guidance assertion present |
| Full test suite | No regressions | `uv run pytest tests/ -x -q` | Exit 0, no failures |
| Lint | ruff clean | `uv run ruff check tests/test_rag_http_mode.py tests/test_rag_refiner.py` | No errors |
| Type check | mypy clean | `uv run mypy tests/test_rag_http_mode.py tests/test_rag_refiner.py --ignore-missing-imports` | No errors |
