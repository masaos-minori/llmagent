# Implementation Procedure: tests/test_pipeline_http_result_kind.py

## Goal

Extend the three existing test stubs in `tests/test_pipeline_http_result_kind.py` to assert
all five `SearchDiagnostics` fields (`result_source`, `http_result_kind`, `remote_status_code`,
`remote_latency_ms`, `fallback_reason`) for each HTTP result kind (Plan 142136 Phase 2).

## Scope

**In scope:**
- Extend `test_remote_nonempty`, `test_remote_empty`, `test_in_process_fallback` with
  `SearchDiagnostics` field assertions
- No new test methods needed; assertions are additive to existing stubs

**Out of scope:**
- Changes to production code
- New test classes

## Assumptions

1. `pipeline.last_search_diagnostics` is accessible after `await pipeline.augment(query)`.
2. `ResultSource` and `HttpResultKind` are importable from `scripts.rag.models_result` (or
   wherever they are defined — verify by reading the existing test file imports).
3. The mock latency values are deterministic (e.g., `50.0` for nonempty, `30.0` for empty,
   `None` or a fixed value for fallback) — read the existing mock setup to confirm values.
4. For `test_in_process_fallback`, `fallback_reason` is `not None` (a string starting with
   the retry prefix).

## Implementation

### Target file

`tests/test_pipeline_http_result_kind.py`

### Procedure

1. Read `tests/test_pipeline_http_result_kind.py` to see existing test structure, mock setup,
   and which assertions are currently present.
2. Identify the mock latency values used in each test.
3. Add assertions after the existing `augment()` call in each test:

```python
# test_remote_nonempty additions:
diag = pipeline.last_search_diagnostics
assert diag.result_source == ResultSource.REMOTE
assert diag.remote_status_code == 200
assert diag.remote_latency_ms == 50.0     # match mock latency
assert diag.fallback_reason is None

# test_remote_empty additions:
diag = pipeline.last_search_diagnostics
assert diag.result_source == ResultSource.REMOTE
assert diag.http_result_kind == HttpResultKind.EMPTY
assert diag.remote_status_code == 200
assert diag.remote_latency_ms == 30.0     # match mock latency
assert diag.fallback_reason is None

# test_in_process_fallback additions:
diag = pipeline.last_search_diagnostics
assert diag.result_source == ResultSource.FALLBACK
assert diag.http_result_kind == HttpResultKind.ERROR
assert diag.remote_status_code == 503
assert diag.fallback_reason is not None
```

**Notes:**
- Replace `50.0` and `30.0` with the actual latency values the mock returns.
- If `http_result_kind` is not set for `test_remote_nonempty`, assert `HttpResultKind.NONEMPTY`
  or skip that assertion (check the existing code path).
- Import `ResultSource`, `HttpResultKind` at the top of the file if not already imported.

## Validation plan

| Step | Command | Expected result |
|------|---------|----------------|
| Run this test file | `uv run pytest tests/test_pipeline_http_result_kind.py -v` | all PASSED |
| Run full suite | `uv run pytest tests/test_rag_pipeline_service.py tests/test_rag_http_mode.py -v` | no regressions |
| Lint | `ruff check tests/test_pipeline_http_result_kind.py` | 0 errors |
