# Implementation: Remove backward-compat tests for /v1/search from test_mcp_rag_pipeline.py

Steps covered: Plan 20260626-095914 — Steps 1-4

---

## Goal

Remove tests that covered the deleted `/v1/search` endpoint and add canonical-path coverage and a 404 guard test.

---

## Scope

- **In scope**: `tests/test_mcp_rag_pipeline.py` — remove `/v1/search` tests, add 404 guard
- **Out of scope**: production code changes (plans 71-72 must be completed first)

---

## Assumptions

- Tests covering `/v1/search` will fail after server.py deletion (correct behavior).
- The 404 guard test ensures the endpoint stays removed.

---

## Implementation

### Target file
`tests/test_mcp_rag_pipeline.py`

### Procedure
1. Read the test file — find `/v1/search` test functions.
2. Step 1: Delete each test that calls `POST /v1/search`.
3. Step 2: Verify canonical `/v1/call_tool` coverage exists (from plan 71 step 3-1) — add if missing.
4. Step 3: Add 404 guard (regression prevention):
   ```python
   async def test_v1_search_permanently_removed(client):
       r = await client.post("/v1/search", json={"query": "x"})
       assert r.status_code == 404, "POST /v1/search must remain removed"
   ```
5. Step 4: Add a static import test to ensure `RagSearchRequest`/`RagSearchResponse` are gone:
   ```python
   def test_rag_search_models_removed():
       import importlib
       mod = importlib.import_module("mcp.rag_pipeline.models")
       assert not hasattr(mod, "RagSearchRequest")
       assert not hasattr(mod, "RagSearchResponse")
   ```

### Method
Test refactor. Add regression guards that prevent re-introduction of deleted APIs.

---

## Validation plan

- Run: `uv run pytest tests/test_mcp_rag_pipeline.py -x -v` — all tests pass.
- Run: `uv run pytest tests/ -x` — no regressions.
