# Implementation: Add list_documents and delete_document to rag-pipeline-mcp

## Goal

Move RAG document management operations (`list_documents`, `delete_document`) from `DbMaintenanceService` into `rag-pipeline-mcp`, exposing them as MCP tools `rag_list_documents` and `rag_delete_document`.

## Scope

- `scripts/mcp/rag_pipeline/tools.py` — add `rag_list_documents` and `rag_delete_document` tool schemas to `_MCP_TOOLS`
- `scripts/mcp/rag_pipeline/service.py` — implement `list_documents()`, `delete_document()` methods; add `fmt_list_documents()`, `fmt_delete_document()` handlers; register in `get_dispatch_table()`
- `scripts/mcp/rag_pipeline/server.py` — no change needed if tools are registered via `get_dispatch_table()` (confirm)

Out of scope:
- Agent-side wiring (`cmd_db.py`) — covered in Step 4 doc
- Removing methods from `DbMaintenanceService` — covered in Step 3 doc

## Assumptions

1. `RagPipelineMCPService.get_dispatch_table()` returns a dict of `tool_name → async handler`; adding entries there is sufficient for the server to expose the tools.
2. `SQLiteHelper("rag")` or `SQLiteHelper().open()` opens the RAG DB (verify which convention is used in existing `service.py` methods).
3. The SQL for `list_documents` comes from `DbMaintenanceService.list_documents()` (lines 108–135 of `db_maintenance_service.py`).
4. The SQL for `delete_document` comes from `DbMaintenanceService.delete_document()` (lines 136–end).
5. Tool output format: `rag_list_documents` returns JSON array; `rag_delete_document` returns a success/not-found message string.

## Implementation

### Target file

`scripts/mcp/rag_pipeline/service.py`

### Procedure

1. Add `rag_list_documents` and `rag_delete_document` schemas to `_MCP_TOOLS` in `tools.py`.
2. In `service.py`, add sync `list_documents(lang, limit)` and `delete_document(url)` methods that run the SQL.
3. Add `async fmt_list_documents(args: ToolArgs) -> str` and `async fmt_delete_document(args: ToolArgs) -> str` handlers.
4. Register both in `get_dispatch_table()`.

### Method

Follow the existing `fmt_run_pipeline` / `fmt_debug_pipeline` pattern. Use `SQLiteHelper` in the same way the existing service methods do.

### Details

**tools.py — append to `_MCP_TOOLS`:**
```python
{
    "name": "rag_list_documents",
    "description": "List indexed documents in the RAG store.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "lang": {"type": "string", "description": "Filter by language ('ja' or 'en')."},
            "limit": {"type": "integer", "description": "Max results (default 20)."},
        },
        "required": [],
    },
    "status": "production",
},
{
    "name": "rag_delete_document",
    "description": "Delete a document and all its chunks from the RAG store by URL.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Exact document URL to delete."},
        },
        "required": ["url"],
    },
    "status": "production",
},
```

**service.py — new sync methods (copy SQL from DbMaintenanceService):**
```python
def list_documents(self, lang: str | None = None, limit: int = 20) -> list[dict]:
    # Copy SQL body from db_maintenance_service.py::list_documents()
    ...

def delete_document(self, url: str) -> bool:
    # Copy SQL body from db_maintenance_service.py::delete_document()
    ...
```

**service.py — new async handlers:**
```python
async def fmt_list_documents(self, args: ToolArgs) -> str:
    lang = args.get("lang")
    limit = int(args.get("limit", 20))
    rows = self.list_documents(lang, limit)
    if not rows:
        return "No documents found."
    return "\n".join(f"{r['url']} [{r['lang']}] {r['chunk_count']} chunks" for r in rows)

async def fmt_delete_document(self, args: ToolArgs) -> str:
    url = str(args.get("url", "")).strip()
    if not url:
        return "Error: url is required."
    ok = self.delete_document(url)
    return f"Deleted: {url}" if ok else f"Not found: {url}"
```

**service.py — get_dispatch_table():**
```python
return {
    "rag_run_pipeline": self.fmt_run_pipeline,
    "rag_debug_pipeline": self.fmt_debug_pipeline,
    "rag_list_documents": self.fmt_list_documents,
    "rag_delete_document": self.fmt_delete_document,
}
```

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check scripts/mcp/rag_pipeline/` | 0 errors |
| Type check | `mypy scripts/mcp/rag_pipeline/` | 0 new errors |
| Architecture | `lint-imports` | 0 violations |
| Unit tests | `uv run pytest tests/ -k rag_pipeline -x -q` | all pass |
| Manual | Call `rag_list_documents` via MCP client | returns document list |
| Manual | Call `rag_delete_document` with a known URL | returns "Deleted: <url>" |
