## 1. Goal
- Expand `tests/test_mdq_routing.py` to comprehensively cover tests ensuring MDQ tool names are consistent across tool_constants, tool_registry, `/v1/tools` HTTP response, LLM tool definitions, and safety tiers.

## 2. Scope
- **In-Scope**:
  - Reorganize `MDQ_TOOLS` count test to include distinction of 7 (production) / 9 (total)
  - Add tool name consistency tests via `/v1/tools` HTTP endpoint
  - Add safety tier classification tests (read-only vs write/admin per-tool verification)
  - Verify production tool filtering by `_MCP_TOOLS` status field
- **Out-of-Scope**:
  - Changing `MDQ_TOOLS` definition (not reducing 9 → 7)
  - Changing tool definitions in `tools.py`
  - Changing `agent.toml`

## 3. Requirements
### Functional
- `MDQ_TOOLS` count test maintains 9 total tools; separate test verifies 7 production tools
- `/v1/tools` HTTP endpoint returns tool names matching `MDQ_TOOLS`
- Safety tier tests verify `_WRITE_TOOLS` contains only `index_paths` and `refresh_index`
- Read-only tools (`search_docs`, `get_chunk`, `outline`, `stats`, `grep_docs`) are NOT in `_WRITE_TOOLS`

### Non-functional
- Tests use FastAPI `TestClient` (not real server) to avoid DB dependency
- No changes to tool definitions or config files

## 4. Architecture
### Component Boundaries
```
tests/test_mdq_routing.py
  ├── TestMdqToolsCount
  │     ├── test_mdq_tools_count → verify MDQ_TOOLS == 9 (unchanged)
  │     └── test_mdq_production_tools_count → verify _MCP_TOOLS status=="production" == 7
  ├── TestMdqToolsConsistency
  │     └── test_v1_tools_matches_mdq_tools → TestClient GET /v1/tools, verify tools[].name matches MDQ_TOOLS
  ├── TestMdqSafetyTiers
  │     ├── test_write_tools_contains_expected → _WRITE_TOOLS == {"index_paths", "refresh_index"}
  │     └── test_read_only_not_in_write_tools → search_docs, get_chunk, outline, stats, grep_docs NOT in _WRITE_TOOLS
  └── TestMdqToolRegistryConsistency
        └── test_registry_matches_mcp_tools → verify tool registry entries match _MCP_TOOLS
```

## 5. Module Design
No changes to dependency direction. All tests within `test_mdq_routing.py` — imports from `mdq.tools`, `mdq.server`, `shared.tool_constants`.

## 6. Interface Design
### Test Classes and Methods

```python
# test_mdq_routing.py

class TestMdqToolsCount:
    def test_mdq_tools_count(self):
        """MDQ_TOOLS should have 9 tools (7 production + 2 admin)."""
        from mcp.mdq.tools import MDQ_TOOLS
        assert len(MDQ_TOOLS) == 9

    def test_mdq_production_tools_count(self):
        """_MCP_TOOLS should have exactly 7 production-status tools."""
        from mcp.mdq.tools import _MCP_TOOLS
        production_tools = [t for t in _MCP_TOOLS if t.get("status") == "production"]
        assert len(production_tools) == 7

class TestMdqToolsConsistency:
    def test_v1_tools_matches_mdq_tools(self):
        """GET /v1/tools should return tool names matching MDQ_TOOLS."""
        from mcp.mdq.tools import MDQ_TOOLS
        from fastapi.testclient import TestClient
        from mcp.mdq.server import MdqMCPServer

        server = MdqMCPServer()
        # Initialize service to avoid DB errors in test
        server.service = server._get_service()  # or mock

        client = TestClient(server.app)
        response = client.get("/v1/tools")
        assert response.status_code == 200

        tool_names = {t["name"] for t in response.json()["tools"]}
        expected_names = set(MDQ_TOOLS)
        assert tool_names == expected_names, f"Missing: {expected_names - tool_names}, Extra: {tool_names - expected_names}"

class TestMdqSafetyTiers:
    def test_write_tools_contains_expected(self):
        """_WRITE_TOOLS should contain only index_paths and refresh_index."""
        from mcp.mdq.tools import _WRITE_TOOLS
        assert _WRITE_TOOLS == frozenset({"index_paths", "refresh_index"})

    def test_read_only_not_in_write_tools(self):
        """Read-only tools should NOT be in _WRITE_TOOLS."""
        from mcp.mdq.tools import _WRITE_TOOLS
        read_only_tools = {"search_docs", "get_chunk", "outline", "stats", "grep_docs"}
        assert read_only_tools.isdisjoint(_WRITE_TOOLS), f"Read-only tools found in _WRITE_TOOLS: {read_only_tools & _WRITE_TOOLS}"

class TestMdqToolRegistryConsistency:
    def test_registry_matches_mcp_tools(self):
        """Tool registry entries should match _MCP_TOOLS definitions."""
        from mcp.mdq.tools import _MCP_TOOLS, MDQ_TOOLS
        # Verify each tool in MDQ_TOOLS has a corresponding entry in _MCP_TOOLS
        mcp_tool_names = {t["name"] for t in _MCP_TOOLS}
        assert set(MDQ_TOOLS) == mcp_tool_names, f"MDQ_TOOLS not matching _MCP_TOOLS names: missing={set(MDQ_TOOLS) - mcp_tool_names}, extra={mcp_tool_names - set(MDQ_TOOLS)}"
```

## 7. Data Model & Serialization
No changes to data models. Tests verify consistency of existing tool definitions across multiple sources.

## 8. Error Handling & Resource Lifecycle
### Failure Modes
- `TestClient` HTTP tests may fail due to DB initialization in `MdqService.__init__` → **Mitigation**: Use `tmp_path` fixture or monkeypatch `MdqService._get_service()` to return a mock service

### Resource Lifecycle
- No connection pooling changes; each test uses isolated TestClient instance

## 9. Configuration
No config changes needed. Tests verify existing tool definitions — no config file modifications.

## 10. Test Strategy
### Unit Tests
- `test_mdq_tools_count`: Verify MDQ_TOOLS has 9 tools (unchanged)
- `test_mdq_production_tools_count`: Verify 7 production-status tools from _MCP_TOOLS
- `test_v1_tools_matches_mdq_tools`: TestClient GET /v1/tools, verify tool names match
- `test_write_tools_contains_expected`: _WRITE_TOOLS == {"index_paths", "refresh_index"}
- `test_read_only_not_in_write_tools`: Read-only tools NOT in _WRITE_TOOLS
- `test_registry_matches_mcp_tools`: MDQ_TOOLS matches _MCP_TOOLS names

### Regression Tests
- Full mdq regression: `uv run pytest tests/test_mdq_routing.py -x -q`

## 11. Implementation Plan
### Phase 1: Tool Count Test Fix
- Maintain `test_mdq_tools_count` with 9 tools; add separate test for 7 production tools

### Phase 2: /v1/tools HTTP Test Addition
- Add TestClient-based tests to verify GET /v1/tools returns tool names matching MDQ_TOOLS

### Phase 3: Safety Tier Per-Tool Tests
- Add `_WRITE_TOOLS` verification tests (only index_paths and refresh_index)
- Verify read-only tools are NOT in _WRITE_TOOLS

### Phase 4: Verification
- Run `uv run pytest tests/test_mdq_routing.py -x -q`
- Run lint/type check: `uv run ruff check tests/test_mdq_routing.py && uv run mypy tests/test_mdq_routing.py`

## 12. Risks / Open Questions
- **UNK-01**: TestClient vs real server for `/v1/tools` HTTP tests → **Resolution**: Use FastAPI `TestClient` (pytest fixture) — no existing HTTP test precedent in routing tests, but TestClient is standard for FastAPI testing.
- **UNK-02**: Per-tool safety tier configuration in `agent.toml` — current test only checks mdq overall tier → **Resolution**: Analyze agent.toml; per-tool settings already defined via `_WRITE_TOOLS` frozenset in tools.py.
- **Risk**: TestClient HTTP tests may fail due to DB initialization in `MdqService.__init__` → **Mitigation**: Use `tmp_path` fixture or monkeypatch `MdqService._get_service()` to return a mock service.
- **Risk**: `_MCP_TOOLS` admin tools returned by `/v1/tools` — test must account for this (server.py:L221 returns all tools) → **Mitigation**: Design test to expect all 9 tools from `/v1/tools`, not just production tools.
