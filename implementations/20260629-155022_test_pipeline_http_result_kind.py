# Implementation: HTTP RAG Remote Empty Semantics Verification

## Goal

Verify and lock `remote_empty` HTTP RAG semantics (success, no fallback, no in-process execution) by fixing two failing tests in `test_pipeline_http_result_kind.py`, then confirm the stale known-issue entry is absent from the docs.

## Scope

- **In-Scope**:
  - Fix `test_in_process_fallback` and `test_no_http_mode` in `tests/test_pipeline_http_result_kind.py` (both fail due to missing DB mock for SQLite vec extension)
  - Verify the three semantic assertions for `remote_empty`: `status=="success"`, `fallback_reason is None`, `http_result_kind=="remote_empty"`
  - Verify `remote_empty` does NOT trigger the in-process pipeline (SQLiteHelper must not be called)
  - Confirm `docs/03_rag_90_inconsistencies_and_known_issues.md` "Active Issues" section has no stale `remote_empty` ambiguity entry
  - Add explicit assertion that in-process pipeline (`SQLiteHelper.open`) is NOT called when `remote_empty` is returned
- **Out-of-Scope**:
  - Changing `call_rag_service` contract or remote API shape
  - Changing fallback policy for HTTP errors (4xx/5xx)
  - Renaming `test_pipeline_http_result_kind.py` to `test_rag_http_mode.py`

## Assumptions

- The implementation in `scripts/rag/pipeline.py` is already correct for `remote_empty`: the `augment()` method returns `result` (empty string `""`) directly without calling `SQLiteHelper().open()` or `self.run()`.
- The two failing tests fail only due to a missing mock for `SQLiteHelper.open()` / sqlite-vec extension, not due to a semantic bug.
- `docs/03_rag_90_inconsistencies_and_known_issues.md` "Active Issues" section is already empty — no removal needed unless inspection reveals a hidden entry.

## Implementation

### Target file: `tests/test_pipeline_http_result_kind.py`

#### Procedure

1. **Fix `test_in_process_fallback`** — add SQLiteHelper mock to prevent sqlite-vec load
2. **Fix `test_no_http_mode`** — add same SQLiteHelper mock
3. **Add assertion in `test_remote_empty`** — verify in-process pipeline is NOT called

#### Method

Direct file edit — add `patch("rag.pipeline.SQLiteHelper.open")` context manager to the two failing tests, and add `assert_not_called()` assertion in `test_remote_empty`.

#### Details

**1. Fix `test_in_process_fallback` (add SQLiteHelper mock):**

Add a patch for `rag.pipeline.SQLiteHelper.open` alongside the existing `pipeline.run` mock:

```python
with patch("rag.pipeline.call_rag_service", mock_call_rag_service):
    with patch("rag.pipeline.SQLiteHelper.open"):
        monkeypatch.setattr(
            pipeline,
            "run",
            AsyncMock(
                return_value=PipelineRunResult(
                    queries=["query"],
                    search_results=[],
                    merged=[],
                    reranked=[],
                    stage_results=[],
                    diagnostics=SearchDiagnostics(),
                )
            ),
        )
        await pipeline.augment("query")
```

**2. Fix `test_no_http_mode` (add SQLiteHelper mock):**

```python
with patch("rag.pipeline.SQLiteHelper.open"):
    monkeypatch.setattr(
        pipeline,
        "run",
        AsyncMock(
            return_value=PipelineRunResult(
                queries=["query"],
                search_results=[],
                merged=[],
                reranked=[],
                stage_results=[],
                diagnostics=SearchDiagnostics(),
            )
        ),
    )
    await pipeline.augment("query")
```

**3. Add assertion in `test_remote_empty` (verify no DB call):**

Add after the existing assertions:

```python
# Verify in-process pipeline is NOT executed for remote_empty
with patch("rag.pipeline.SQLiteHelper.open") as mock_open:
    pass  # Already patched above; assert_not_called will be added below

# Add assertion at end of test_remote_empty:
# Note: Since we're not patching SQLiteHelper.open in this test (it should NOT be called),
# we add a separate assertion using unittest.mock.patch to verify it's not called.
```

Actually, the cleanest approach is to add a patch context at the end of `test_remote_empty`:

```python
    # Verify in-process pipeline is NOT executed for remote_empty
    with patch("rag.pipeline.SQLiteHelper.open") as mock_open:
        pass  # Already patched above; we need to assert it wasn't called
```

Wait, that won't work because the patch would be applied after the test already ran. The correct approach is to add the patch at the beginning of the test:

```python
@pytest.mark.asyncio
async def test_remote_empty(monkeypatch) -> None:
    """Empty remote result ('') -> http_result_kind='remote_empty', fallback_reason=None."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(
        http,
        rag_url,
        query,
        history_context,
        *,
        auth_token="",
        set_fetch_result=None,
        set_fallback_reason=None,
    ):
        return "", 200, 30.0

    with patch("rag.pipeline.call_rag_service", mock_call_rag_service):
        with patch("rag.pipeline.SQLiteHelper.open") as mock_open:
            await pipeline.augment("query")

    # Verify in-process pipeline is NOT executed for remote_empty
    mock_open.assert_not_called()

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] == "remote_empty"
    http_sr = next(
        r for r in pipeline.last_stage_results if r["stage_name"] == "HttpAugment"
    )
    assert http_sr["status"] == "success"
    assert http_sr["fallback_reason"] is None
```

### Target file: `docs/03_rag_90_inconsistencies_and_known_issues.md`

#### Procedure

Verify "Active Issues" section is stale-entry-free (already confirmed empty from earlier inspection).

#### Method

Read-only verification — no changes expected.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/test_pipeline_http_result_kind.py::test_remote_empty` | Unit — mock `call_rag_service` returning `("", 200, 30.0)`, assert no DB call | `.venv/bin/pytest tests/test_pipeline_http_result_kind.py::test_remote_empty -v` | PASSED; status=success, fallback_reason=None, http_result_kind=remote_empty |
| `tests/test_pipeline_http_result_kind.py::test_remote_nonempty` | Unit — mock returning non-empty string | `.venv/bin/pytest tests/test_pipeline_http_result_kind.py::test_remote_nonempty -v` | PASSED (already passing) |
| `tests/test_pipeline_http_result_kind.py::test_in_process_fallback` | Unit — mock returning None + patch SQLiteHelper | `.venv/bin/pytest tests/test_pipeline_http_result_kind.py::test_in_process_fallback -v` | PASSED after SQLiteHelper mock fix |
| `tests/test_pipeline_http_result_kind.py::test_no_http_mode` | Unit — no rag_service_url + patch SQLiteHelper | `.venv/bin/pytest tests/test_pipeline_http_result_kind.py::test_no_http_mode -v` | PASSED after SQLiteHelper mock fix |
| `docs/03_rag_90_inconsistencies_and_known_issues.md` | Manual inspection | Read file, search for "remote_empty" | No stale ambiguity entry in Active Issues |
