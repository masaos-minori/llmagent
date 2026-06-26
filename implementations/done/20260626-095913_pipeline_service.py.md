# Implementation: Migrate pipeline_service.py callers to canonical MCP tool call

Steps covered: Plan 20260626-095913 — Steps 2-1, 2-2, 2-3

---

## Goal

Migrate callers in `scripts/rag/pipeline_service.py` from the deprecated `POST /v1/search` HTTP call to the canonical `POST /v1/call_tool + {"name": "rag_run_pipeline"}` MCP tool call pattern.

---

## Scope

- **In scope**: `scripts/rag/pipeline_service.py` — HTTP call migration at line ~105
- **In scope**: `scripts/rag/pipeline.py` — any additional caller sites
- **Out of scope**: rag_pipeline MCP server changes (plan 71); tests (step 3-x)

---

## Assumptions

- `pipeline_service.py:105` calls `POST /v1/search` via `httpx` or similar.
- Canonical replacement: `POST /v1/call_tool` with body `{"name": "rag_run_pipeline", "args": {...}}`.
- The base URL (`rag_service_url`) is configured and still valid.

---

## Implementation

### Target files
`scripts/rag/pipeline_service.py`, `scripts/rag/pipeline.py`

### Procedure
1. Read `scripts/rag/pipeline_service.py` lines 95-120 — find `POST /v1/search` call.
2. Step 2-1: Change URL and body:
   ```python
   # Before:
   response = await client.post(f"{rag_service_url}/v1/search", json={"query": query, ...})
   
   # After:
   response = await client.post(
       f"{rag_service_url}/v1/call_tool",
       json={"name": "rag_run_pipeline", "args": {"query": query, ...}},
   )
   ```
3. Step 2-2: Update response parsing — `/v1/call_tool` returns `{"result": {...}}` wrapping; extract `response.json()["result"]`.
4. Step 2-3: Check `scripts/rag/pipeline.py` for any additional `/v1/search` calls and apply same migration.

### Method
HTTP call migration. Response shape may differ — validate response parsing.

---

## Validation plan

- Run: `uv run pytest tests/test_rag_pipeline_service.py -x -v` — pass.
- Confirm: `grep -rn "v1/search" scripts/rag/` returns 0.
- Pre-commit: `pre-commit run --all-files` — ruff + mypy must pass.
