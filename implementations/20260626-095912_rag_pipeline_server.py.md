# Implementation: Remove POST /v1/search from rag-pipeline-mcp server.py

Steps covered: Plan 20260626-095912 — Step 2-1

---

## Goal

Delete the `@app.post("/v1/search")` route and its handler from `scripts/mcp/rag_pipeline/server.py`. This endpoint is superseded by the canonical `POST /v1/call_tool` + `{"name": "rag_run_pipeline"}` MCP tool call.

---

## Scope

- **In scope**: `scripts/mcp/rag_pipeline/server.py` — delete `/v1/search` route
- **Out of scope**: service.py (step 2-2); models.py (step 2-3); tests (step 3-x)

---

## Assumptions

- Callers have been migrated to canonical MCP tool call (plan 72 prerequisite).
- `@app.post("/v1/search")` calls into `service.py` via a handler function.
- Removing the route will cause `404` for any remaining old callers (intended).

---

## Implementation

### Target file
`scripts/mcp/rag_pipeline/server.py`

### Procedure
1. Read `scripts/mcp/rag_pipeline/server.py` — find `@app.post("/v1/search")`.
2. Delete the route decorator and handler function.
3. Delete any `from .models import RagSearchRequest, RagSearchResponse` imports that are no longer used after model deletion (step 2-3).
4. Verify: `grep -n "v1/search" scripts/mcp/rag_pipeline/server.py` returns 0.

### Method
Dead code removal.

---

## Validation plan

- Run: `uv run pytest tests/test_mcp_rag_pipeline.py -x -v` — pass (after compat tests removed in plan 73).
- Confirm: `grep -n "v1/search" scripts/mcp/rag_pipeline/server.py` returns 0.
- Pre-commit: `pre-commit run --all-files` — ruff + mypy must pass.
