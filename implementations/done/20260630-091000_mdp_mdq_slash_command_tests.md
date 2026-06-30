## Goal
- Add unit tests for all 7 MDQ slash commands in `scripts/agent/commands/cmd_mdq.py` as `tests/test_cmd_mdq.py`, verifying that MDQ slash commands work correctly through MCP tool calls.

## Scope
- **In-Scope**:
  - Create new `tests/test_cmd_mdq.py`
  - Tests for each command (status, index, refresh, search, outline, get, grep)
  - Unit tests using MCP tool executor (`ctx.services.tools.execute`) mock
  - Output verification for error responses (`is_error=True`)
  - Error output verification when MCP tools are unavailable
- **Out-of-Scope**:
  - Implementation changes to `cmd_mdq.py` (all commands already implemented)
  - Integration tests with actual MDQ MCP server
  - Major CLI argument parser refactoring

## Assumptions
1. All 7 commands in `cmd_mdq.py` are already implemented and registered with CommandRegistry
2. Can build mocks by referencing existing command test patterns (e.g., `test_agent_rag.py`)
3. `ctx.services.tools.execute(tool_name, args)` returns a `DispatchResult(is_error, output)`-like object
4. Each command only makes MCP tool calls and does not read `mdq.sqlite` directly (confirmed by inspecting `cmd_mdq.py`)

## Implementation

### Target file
`tests/test_cmd_mdq.py` — new file

### Procedure
1. Review existing command test mock patterns in `tests/test_agent_rag.py`
2. Create `tests/test_cmd_mdq.py` with test classes for each command
3. Add error response tests for each command
4. Add test for error output when `ctx.services is None`

### Method
- Use `MagicMock(spec=...)` to minimize AgentContext dependency complexity
- Mock `ctx.services.tools.execute` to return `DispatchResult(is_error=False, output="...")` for success paths
- Mock `ctx.services.tools.execute` to return `DispatchResult(is_error=True, output="error message")` for error paths

### Details

```python
# tests/test_cmd_mdq.py

class TestMdqStatusCommand:
    def test_status_calls_stats_tool(self):
        """`/mdq status` calls `stats` MCP tool."""
        ctx = MagicMock(spec=AgentContext)
        ctx.services.tools.execute = AsyncMock(return_value=DispatchResult(is_error=False, output="stats output"))
        # Execute command and verify stats tool was called with empty args

class TestMdqIndexCommand:
    def test_index_calls_index_paths_tool(self):
        """`/mdq index <path>` calls `index_paths` MCP tool."""
        ctx = MagicMock(spec=AgentContext)
        ctx.services.tools.execute = AsyncMock(return_value=DispatchResult(is_error=False, output="indexed output"))
        # Execute command and verify index_paths tool was called with path arg

    def test_index_calls_with_force_flag(self):
        """`/mdq index <path> --force` passes force=True."""
        ctx = MagicMock(spec=AgentContext)
        ctx.services.tools.execute = AsyncMock(return_value=DispatchResult(is_error=False, output="indexed output"))
        # Execute command and verify force=True was passed

class TestMdqRefreshCommand:
    def test_refresh_calls_refresh_index_tool(self):
        """`/mdq refresh <path>` calls `refresh_index` MCP tool."""
        ctx = MagicMock(spec=AgentContext)
        ctx.services.tools.execute = AsyncMock(return_value=DispatchResult(is_error=False, output="refreshed output"))
        # Execute command and verify refresh_index tool was called

class TestMdqSearchCommand:
    def test_search_calls_search_docs_tool(self):
        """`/mdq search <query>` calls `search_docs` MCP tool."""
        ctx = MagicMock(spec=AgentContext)
        ctx.services.tools.execute = AsyncMock(return_value=DispatchResult(is_error=False, output="search results"))
        # Execute command and verify search_docs tool was called

    def test_search_with_limit(self):
        """`/mdq search <query> --limit N` passes limit=N."""
        ctx = MagicMock(spec=AgentContext)
        ctx.services.tools.execute = AsyncMock(return_value=DispatchResult(is_error=False, output="search results"))
        # Execute command and verify limit param was passed

class TestMdqOutlineCommand:
    def test_outline_calls_outline_tool(self):
        """`/mdq outline <path>` calls `outline` MCP tool."""
        ctx = MagicMock(spec=AgentContext)
        ctx.services.tools.execute = AsyncMock(return_value=DispatchResult(is_error=False, output="outline output"))
        # Execute command and verify outline tool was called

class TestMdqGetCommand:
    def test_get_calls_get_chunk_tool(self):
        """`/mdq get <chunk_id>` calls `get_chunk` MCP tool."""
        ctx = MagicMock(spec=AgentContext)
        ctx.services.tools.execute = AsyncMock(return_value=DispatchResult(is_error=False, output="chunk content"))
        # Execute command and verify get_chunk tool was called

    def test_get_with_neighbors(self):
        """`/mdq get <chunk_id> --with-neighbors` passes neighbors=True."""
        ctx = MagicMock(spec=AgentContext)
        ctx.services.tools.execute = AsyncMock(return_value=DispatchResult(is_error=False, output="chunk content"))
        # Execute command and verify neighbors param was passed

class TestMdqGrepCommand:
    def test_grep_calls_grep_docs_tool(self):
        """`/mdq grep <pattern>` calls `grep_docs` MCP tool."""
        ctx = MagicMock(spec=AgentContext)
        ctx.services.tools.execute = AsyncMock(return_value=DispatchResult(is_error=False, output="grep results"))
        # Execute command and verify grep_docs tool was called

    def test_grep_with_path_prefix(self):
        """`/mdq grep <pattern> --path PATH` passes path_prefix."""
        ctx = MagicMock(spec=AgentContext)
        ctx.services.tools.execute = AsyncMock(return_value=DispatchResult(is_error=False, output="grep results"))
        # Execute command and verify path_prefix param was passed

class TestMdqErrorHandling:
    def test_error_response_output(self):
        """Error responses (is_error=True) display error message."""
        ctx = MagicMock(spec=AgentContext)
        ctx.services.tools.execute = AsyncMock(return_value=DispatchResult(is_error=True, output="error occurred"))
        # Execute any command and verify error message is displayed

    def test_no_services_error(self):
        """When ctx.services is None, display error about MCP tools."""
        ctx = MagicMock(spec=AgentContext)
        ctx.services = None
        # Execute any command and verify appropriate error output
```

## Validation plan
- Run `uv run pytest tests/test_cmd_mdq.py -x -q` to confirm all tests pass
- Run lint: `ruff check tests/test_cmd_mdq.py` for 0 errors
- Run type check: `mypy tests/test_cmd_mdq.py` for no new errors
