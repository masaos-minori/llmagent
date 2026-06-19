# Implementation: Tests for rag_list_documents and rag_delete_document

## Goal

Add unit tests for the two new MCP tools (`rag_list_documents`, `rag_delete_document`) in `mcp/rag_pipeline/`, and remove tests for deleted `DbMaintenanceService` methods.

## Scope

- `tests/test_rag_pipeline_mcp.py` (new file or existing) — add tests for `fmt_list_documents`, `fmt_delete_document`
- `tests/test_db_maintenance.py` (existing) — remove tests for `list_documents()`, `delete_document()` methods

Out of scope:
- E2E/integration tests against running rag-pipeline-mcp server
- Tests for `_db_clean`/`_db_list_urls` command handlers (covered by existing cmd_db tests if they exist)

## Assumptions

1. Unit tests mock `SQLiteHelper` to avoid real DB access, consistent with existing `mcp/rag_pipeline/` test patterns.
2. `tests/test_db_maintenance.py` has tests for the deleted methods; locate them by `grep -n "list_documents\|delete_document" tests/test_db_maintenance.py`.
3. The test file for rag-pipeline-mcp may already exist; check `tests/` for `test_rag_pipeline*`.
4. `RagPipelineMCPService` can be instantiated without a running server for unit tests (verify `__init__` has no mandatory async startup).

## Implementation

### Target file

`tests/test_rag_pipeline_mcp.py` (new or existing)

### Procedure

1. Check for existing rag-pipeline MCP test file: `ls tests/ | grep rag_pipeline`.
2. Add test class or functions for `fmt_list_documents` and `fmt_delete_document`.
3. In `tests/test_db_maintenance.py`, delete the test methods for `list_documents` and `delete_document`.

### Method

Pytest with `unittest.mock.patch` or `pytest-mock` to mock `SQLiteHelper`. Each test verifies the handler returns the expected string.

### Details

**New tests — fmt_list_documents:**
```python
@pytest.mark.asyncio
async def test_fmt_list_documents_returns_rows(monkeypatch):
    service = RagPipelineMCPService()
    monkeypatch.setattr(
        service, "list_documents",
        lambda lang=None, limit=20: [
            {"url": "file:///a.md", "lang": "en", "chunk_count": 3}
        ]
    )
    result = await service.fmt_list_documents({"limit": 5})
    assert "file:///a.md" in result
    assert "3 chunks" in result

@pytest.mark.asyncio
async def test_fmt_list_documents_empty(monkeypatch):
    service = RagPipelineMCPService()
    monkeypatch.setattr(service, "list_documents", lambda **kw: [])
    result = await service.fmt_list_documents({})
    assert "No documents" in result
```

**New tests — fmt_delete_document:**
```python
@pytest.mark.asyncio
async def test_fmt_delete_document_found(monkeypatch):
    service = RagPipelineMCPService()
    monkeypatch.setattr(service, "delete_document", lambda url: True)
    result = await service.fmt_delete_document({"url": "file:///a.md"})
    assert "Deleted" in result

@pytest.mark.asyncio
async def test_fmt_delete_document_not_found(monkeypatch):
    service = RagPipelineMCPService()
    monkeypatch.setattr(service, "delete_document", lambda url: False)
    result = await service.fmt_delete_document({"url": "file:///a.md"})
    assert "Not found" in result

@pytest.mark.asyncio
async def test_fmt_delete_document_missing_url():
    service = RagPipelineMCPService()
    result = await service.fmt_delete_document({})
    assert "Error" in result or "required" in result.lower()
```

**tests/test_db_maintenance.py — removal:**
```bash
grep -n "list_documents\|delete_document" tests/test_db_maintenance.py
# Delete those test methods
```

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check tests/` | 0 errors |
| Type check | `mypy tests/` | 0 new errors |
| Unit tests | `uv run pytest tests/test_rag_pipeline_mcp.py -v` | all new tests pass |
| Full suite | `uv run pytest tests/ -x -q` | all pass |
