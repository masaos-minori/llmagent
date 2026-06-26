# Implementation: Remove /v1/search handler from rag_pipeline service.py

Steps covered: Plan 20260626-095912 — Step 2-2

---

## Goal

Remove the `/v1/search` handler function from `scripts/mcp/rag_pipeline/service.py`. This is the business logic called by the deleted `server.py` route.

---

## Scope

- **In scope**: `scripts/mcp/rag_pipeline/service.py` — delete `search()` or equivalent handler
- **Out of scope**: server.py (step 2-1); models.py (step 2-3); tests

---

## Assumptions

- `service.py` has a `search(request: RagSearchRequest) -> RagSearchResponse` method or function.
- The canonical path is `run_pipeline()` or equivalent, which is called via MCP tool call.
- The `search()` function is NOT called by the canonical path.

---

## Implementation

### Target file
`scripts/mcp/rag_pipeline/service.py`

### Procedure
1. Read `scripts/mcp/rag_pipeline/service.py` — find the `search()` function (or equivalent).
2. Verify it is ONLY called from the deleted `/v1/search` route (not from any canonical path).
3. Delete the `search()` function and any `RagSearchRequest`/`RagSearchResponse` usages.
4. Run: `grep -rn "search\b" scripts/mcp/rag_pipeline/service.py` to confirm no stale references.

### Method
Dead code removal.

---

## Validation plan

- Run: `uv run pytest tests/test_mcp_rag_pipeline.py -x -v` — pass.
- Type check: `mypy scripts/mcp/rag_pipeline/service.py` — 0 errors.
- Pre-commit: `pre-commit run --all-files` — pass.
