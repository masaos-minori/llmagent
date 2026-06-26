# Implementation: Add canonical MCP tool tests to test_mcp_rag_pipeline.py

Steps covered: Plan 20260626-095912 — Steps 3-1, 3-2

---

## Goal

Add tests for the canonical `POST /v1/call_tool + {"name": "rag_run_pipeline"}` path, and confirm `/v1/search` now returns 404.

---

## Scope

- **In scope**: `tests/test_mcp_rag_pipeline.py` — add canonical tests, add 404 test for /v1/search
- **Out of scope**: production code changes (steps 2-1 to 2-3 must be completed first)

---

## Implementation

### Target file
`tests/test_mcp_rag_pipeline.py`

### Procedure
1. Read existing tests to understand fixture patterns.
2. Step 3-1 (Canonical path test):
   ```python
   async def test_rag_run_pipeline_via_call_tool(client):
       r = await client.post("/v1/call_tool", json={
           "name": "rag_run_pipeline",
           "args": {"query": "test query", "top_k": 5},
       })
       assert r.status_code == 200
       data = r.json()
       assert "results" in data
   ```
3. Step 3-2 (404 test for deleted endpoint):
   ```python
   async def test_v1_search_returns_404(client):
       r = await client.post("/v1/search", json={"query": "test"})
       assert r.status_code == 404
   ```
4. Remove any test that was only testing `/v1/search` behavior (the deletion is covered in plan 73).

### Method
`pytest-asyncio` + `httpx.AsyncClient`.

---

## Validation plan

- Run: `uv run pytest tests/test_mcp_rag_pipeline.py -x -v` — all tests pass.
- Run: `uv run pytest tests/ -x` — no regressions.
