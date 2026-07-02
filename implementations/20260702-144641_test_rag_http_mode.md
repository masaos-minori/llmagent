# Implementation Procedure: tests/test_rag_http_mode.py

## Goal

Extend `test_remote_empty_sets_result_source_remote` in `tests/test_rag_http_mode.py` with
full `SearchDiagnostics` field assertions, and add a new test confirming that `remote_empty`
does not trigger the in-process fallback pipeline (Plan 142136 Phase 3).

## Scope

**In scope:**
- Extend `test_remote_empty_sets_result_source_remote`: add assertions for `result_source`,
  `remote_status_code`, `remote_latency_ms`, `fallback_reason`
- Add `test_remote_empty_does_not_trigger_in_process`: confirm `pipeline.run` is NOT called

**Out of scope:**
- Changes to production code
- Modifications to other test files

## Assumptions

1. `test_remote_empty_sets_result_source_remote` patches `call_rag_service` to return
   `("", 200, 30.0)` (empty string result, 200 status, 30ms latency).
2. The `pipeline.run` method is the in-process search trigger; it should NOT be called when
   `call_rag_service` returns a non-None result (even empty string).
3. `monkeypatch.setattr(pipeline, "run", AsyncMock())` is the correct pattern (consistent
   with existing test patterns in this file).
4. `augment()` returns the empty string directly (not `None`) when remote returns empty —
   confirming `remote_empty` is a success path.

## Implementation

### Target file

`tests/test_rag_http_mode.py`

### Procedure

1. Read `tests/test_rag_http_mode.py` to locate `test_remote_empty_sets_result_source_remote`
   and understand the mock setup (especially the latency value passed to `call_rag_service`).
2. Add assertions to the existing test:

```python
# Additions to test_remote_empty_sets_result_source_remote:
diag = pipeline.last_search_diagnostics
assert diag.result_source == ResultSource.REMOTE
assert diag.remote_status_code == 200
assert diag.remote_latency_ms == 30.0
assert diag.fallback_reason is None
```

3. Add new test method:

```python
@pytest.mark.asyncio
async def test_remote_empty_does_not_trigger_in_process(self, monkeypatch, pipeline):
    """remote_empty (status 200, empty result) must NOT fall back to in-process pipeline."""
    monkeypatch.setattr(
        "scripts.rag.pipeline_service.call_rag_service",
        AsyncMock(return_value=("", 200, 5.0)),
    )
    run_mock = AsyncMock()
    monkeypatch.setattr(pipeline, "run", run_mock)

    result = await pipeline.augment("test query")

    assert result == ""                  # empty string, not None
    run_mock.assert_not_called()         # in-process was NOT triggered
```

**Notes:**
- Verify the `monkeypatch.setattr` target path for `call_rag_service` by reading the
  `pipeline.py` import of `pipeline_service`.
- Replace `30.0` in the assertions with whatever value the existing test mock returns.

## Validation plan

| Step | Command | Expected result |
|------|---------|----------------|
| Run this test file | `uv run pytest tests/test_rag_http_mode.py -v` | all PASSED |
| Full suite (related) | `uv run pytest tests/test_rag_pipeline_service.py tests/test_pipeline_http_result_kind.py tests/test_rag_http_mode.py -v` | all PASSED |
| Lint | `ruff check tests/test_rag_http_mode.py` | 0 errors |
| Type check | `mypy tests/test_rag_http_mode.py` | no new errors |
