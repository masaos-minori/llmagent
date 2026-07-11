## Goal

Update and extend `tests/test_rag_pipeline_mcp_service.py::TestFmtDeleteDocument` so the test suite locks in the new cache-invalidation behavior of `fmt_delete_document()`: the existing found-case test must keep passing now that the success path accesses `self._pipeline`, and two new tests must assert the invalidate-on-success / no-invalidate-on-not-found contract.

## Scope

**In-Scope:**
- `tests/test_rag_pipeline_mcp_service.py`, class `TestFmtDeleteDocument`:
  - Update `test_found_returns_deleted` to set a mock `_pipeline` on the service before calling `fmt_delete_document()`.
  - Add `test_found_invalidates_cache`.
  - Add `test_not_found_does_not_invalidate_cache`.
  - (No change needed to `test_missing_url_returns_error` — it returns before `delete_document()` is called, so no `_pipeline` is required.)

**Out-of-Scope:**
- Any other test class in this file.
- Production code changes (covered by the Phase 1 and Phase 2 docs).

## Assumptions

- Without this update, `test_found_returns_deleted` would start failing with a `RuntimeError` once `fmt_delete_document()`'s success path calls `self._pipeline_or_raise()` (Phase 2's change), because the test currently constructs `RagPipelineMCPService()` without calling `start()`, leaving `_pipeline` unset (confirmed by direct read of `tests/test_rag_pipeline_mcp_service.py:588-593` in the plan's Assumption 4).
- Setting `service._pipeline = MagicMock()` directly (bypassing `start()`) is an established, low-risk test-double pattern already used elsewhere in this test file (per other `TestFmt*` classes' monkeypatch/mock style).
- `MagicMock()` auto-creates the `invalidate_cache` attribute on access, so no explicit spec is required for the mock to support `.invalidate_cache()` and `.invalidate_cache.assert_called_once()` / `.assert_not_called()`.

## Implementation

### Target file

`tests/test_rag_pipeline_mcp_service.py`

### Procedure

1. Locate the `TestFmtDeleteDocument` class.
2. Modify `test_found_returns_deleted`: after constructing `service = RagPipelineMCPService()`, add `service._pipeline = MagicMock()` before the `monkeypatch.setattr(...)` / call to `fmt_delete_document`.
3. Add a new test `test_found_invalidates_cache`: construct the service with a mock `_pipeline`, monkeypatch `delete_document` to return `True`, call `fmt_delete_document`, then assert `service._pipeline.invalidate_cache.assert_called_once()`.
4. Add a new test `test_not_found_does_not_invalidate_cache`: construct the service with a mock `_pipeline` present (to prove it is deliberately *not* touched), monkeypatch `delete_document` to return `False`, call `fmt_delete_document`, then assert `service._pipeline.invalidate_cache.assert_not_called()`.
5. Leave `test_not_found_returns_not_found` and `test_missing_url_returns_error` as-is — neither needs a `_pipeline` mock (the not-found path never calls `_pipeline_or_raise()`; the missing-url path returns before `delete_document()` is invoked).
6. Confirm `MagicMock` is already imported in this test file (used elsewhere); add the import if not already present.

### Method

Target end-state for the class (per the plan's Design section), to be reflected in the actual test file:

```python
class TestFmtDeleteDocument:
    async def test_found_returns_deleted(self, monkeypatch: Any) -> None:
        service = RagPipelineMCPService()
        service._pipeline = MagicMock()
        monkeypatch.setattr(service._doc_mgr, "delete_document", lambda url: True)
        result = await service.fmt_delete_document({"url": "file:///a.md"})
        assert "Deleted" in result

    async def test_found_invalidates_cache(self, monkeypatch: Any) -> None:
        service = RagPipelineMCPService()
        service._pipeline = MagicMock()
        monkeypatch.setattr(service._doc_mgr, "delete_document", lambda url: True)
        await service.fmt_delete_document({"url": "file:///a.md"})
        service._pipeline.invalidate_cache.assert_called_once()

    async def test_not_found_returns_not_found(self, monkeypatch: Any) -> None:
        service = RagPipelineMCPService()
        monkeypatch.setattr(service._doc_mgr, "delete_document", lambda url: False)
        result = await service.fmt_delete_document({"url": "file:///a.md"})
        assert "Not found" in result

    async def test_not_found_does_not_invalidate_cache(self, monkeypatch: Any) -> None:
        service = RagPipelineMCPService()
        service._pipeline = MagicMock()  # present but must not be touched
        monkeypatch.setattr(service._doc_mgr, "delete_document", lambda url: False)
        await service.fmt_delete_document({"url": "file:///a.md"})
        service._pipeline.invalidate_cache.assert_not_called()

    async def test_missing_url_returns_error(self) -> None:
        service = RagPipelineMCPService()
        result = await service.fmt_delete_document({})
        assert "Error" in result or "required" in result.lower()
```

### Details

- `test_found_returns_deleted` and `test_found_invalidates_cache` are deliberately separate: one locks the string-return contract, the other locks the cache side-effect contract — keep them as independent assertions rather than merging, to keep failures diagnostic (a broken invalidation call should not fail the "Deleted" string assertion, and vice versa).
- `test_not_found_does_not_invalidate_cache` must still set `service._pipeline = MagicMock()` even though the not-found path should never touch it — this is what proves the mock is deliberately untouched (an unset `_pipeline` would make the assertion vacuous, since `_pipeline_or_raise()` would raise before reaching any invalidate call, masking a possible bug where invalidation incorrectly also fires on not-found).
- Do not use `AsyncMock` for `_pipeline` unless `fmt_delete_document` awaits `invalidate_cache()` — per the plan's Design, `invalidate_cache()` is synchronous (`-> None`, no `async def`), so a plain `MagicMock()` is correct.
- Keep all test code and any new comments in English only (per `rules/coding.md`).

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to `tests/test_rag_pipeline_mcp_service.py`:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_rag_pipeline_mcp_service.py` | 0 errors |
| Tests | `uv run pytest tests/test_rag_pipeline_mcp_service.py -v` | All pass, including the 2 new tests; `test_found_returns_deleted` passes with the mock pipeline set |
| Regression | `uv run pytest tests/test_rag_pipeline.py tests/test_mcp_rag_pipeline.py -q` | No new failures |
