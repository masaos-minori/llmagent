# Implementation: Add canonical path tests to test_rag_pipeline_service.py

Steps covered: Plan 20260626-095913 — Steps 3-1, 3-2

---

## Goal

Add tests verifying that `pipeline_service.py` uses the canonical `POST /v1/call_tool` call, and that it correctly handles the wrapped response format.

---

## Scope

- **In scope**: `tests/test_rag_pipeline_service.py` (or equivalent) — add/update tests
- **Out of scope**: production code changes (steps 2-1 to 2-3 must be completed first)

---

## Implementation

### Target file
`tests/test_rag_pipeline_service.py`

### Procedure
1. Read existing tests to understand mock patterns.
2. Step 3-1: Mock `httpx.AsyncClient.post` and assert it is called with `/v1/call_tool` (not `/v1/search`):
   ```python
   async def test_pipeline_service_uses_call_tool_endpoint(mocker):
       mock_post = mocker.patch("httpx.AsyncClient.post")
       mock_post.return_value.json.return_value = {"result": {"results": []}}
       mock_post.return_value.status_code = 200
       
       await pipeline_service.run_pipeline(query="test", top_k=5)
       
       call_url = mock_post.call_args.args[0]
       assert "/v1/call_tool" in call_url
       assert "/v1/search" not in call_url
   ```
3. Step 3-2: Assert response parsing handles `{"result": {...}}` wrapper:
   ```python
   async def test_pipeline_service_parses_call_tool_response(mocker):
       mock_post.return_value.json.return_value = {
           "result": {"results": [{"id": "1", "score": 0.9}]}
       }
       results = await pipeline_service.run_pipeline(query="test", top_k=5)
       assert results[0]["id"] == "1"
   ```

---

## Validation plan

- Run: `uv run pytest tests/test_rag_pipeline_service.py -x -v` — pass.
- Run: `uv run pytest tests/ -x` — no regressions.
