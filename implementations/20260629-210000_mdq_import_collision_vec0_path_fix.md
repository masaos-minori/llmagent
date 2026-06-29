# Implementation Design: mdq-mcp import collision and vec0.so path fix

## Goal

Fix the `mcp.mdq` package import collision with the external `mcp` SDK and the `vec0.so` path mismatch so that `python -m mcp.mdq.server` starts cleanly and all MDQ tests pass.

## Scope

- **In-Scope**:
  - Create `scripts/mcp/mdq/__main__.py` to enable `python -m mcp.mdq.server`
  - Fix hardcoded `vec0.so` path in `scripts/mcp/mdq/service.py` to use config_loader
  - Add graceful handling for `.so.so` double-extension issue
- **Out-of-Scope**:
  - Renaming `scripts/mcp/` to `scripts/mcpx/` (high blast radius)
  - Implementing hybrid/vector search (MDQ-02 — planned, not in this task)
  - Deploying to `/opt/llm/`

## Implementation Steps

### Phase 1: Create __main__.py

Create `scripts/mcp/mdq/__main__.py` with content:
```python
"""Entry point: python -m mcp.mdq.server"""
import sys
from mcp.mdq.server import MdqMCPServer

server = MdqMCPServer()
if "--stdio" in sys.argv:
    import asyncio
    asyncio.run(server.run_stdio())
else:
    server.run_http()
```

### Phase 2: Fix vec0.so path in service.py

- Change hardcoded `conn.load_extension("/opt/llm/sqlite-vec/vec0.so")` to use config_loader
- Add graceful handling for `.so.so` double-extension issue (try without `.so` suffix if load fails)
- Match the pattern used in `db/helper.py` which reads from `db_cfg.sqlite_vec_so`

### Phase 3: Verify

- All 9 tests in `tests/test_mdq_hybrid_search.py` pass
- `uv run pytest tests/ -k mdq -q` — 0 failures
- FastAPI routes registered (`/health`, `/v1/tools`, `/v1/call_tool`)

## Acceptance Criteria

- [ ] `__main__.py` created and module loads correctly
- [ ] vec0.so path read from config instead of hardcoded
- [ ] Graceful handling for `.so.so` double-extension issue
- [ ] All MDQ tests pass
