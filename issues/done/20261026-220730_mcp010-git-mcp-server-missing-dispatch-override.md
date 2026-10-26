# GitMCPServer missing dispatch method override (NotImplementedError)

## Priority
Medium

## Summary
`GitMCPServer` in `git_server.py` does not override the `dispatch()` method from `MCPServer`, so calling `server.dispatch()` programmatically raises `NotImplementedError`.

## Background
The `MCPServer` base class in `server.py` defines a `dispatch()` method that raises `NotImplementedError`:

```python
async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
    raise NotImplementedError("Subclasses must implement dispatch")
```

Other MCP server subclasses override this method:
- `MdqMCPServer` (mdq_server.py, line 458): overrides `dispatch()`
- `WebSearchMCPServer` (web_search_server.py, line 326): overrides `dispatch()`
- `FileDeleteMCPServer` (delete_server.py, line 268): overrides `dispatch()`

But `GitMCPServer` (git_server.py, line 376) does NOT override `dispatch()`:

```python
class GitMCPServer(MCPServer):
    """MCPServer subclass for git-mcp."""
    server_name = "git-mcp"
    server_version = "1.0.0"
    http_port = 8014
    own_config_file = "git_mcp_server.toml"
    app_module = "mcp_servers.git.git_server:app"
    mcp_tools = TOOL_LIST
```

## Problem
If any code path calls `server.dispatch()` programmatically (e.g., via the MCPServer base class interface), it will raise `NotImplementedError`. This is a latent bug that only manifests when:
1. The server is instantiated programmatically (not via `__main__`).
2. The `dispatch()` method is called directly on the instance.

The risk is that:
1. Future refactoring could add a programmatic dispatch path.
2. Test code might instantiate `GitMCPServer` and call `dispatch()`.
3. The inconsistency with other MCP server subclasses makes the codebase harder to reason about.

## Reason for Change
The missing `dispatch()` override creates an inconsistency with other MCP server subclasses and introduces a latent bug that could surface during testing or future development.

## Implementation Intent
Add a `dispatch()` method to `GitMCPServer` that delegates to the git service's dispatch table, similar to how other MCP servers implement it.

## Target Files or Areas
- `scripts/mcp_servers/git/git_server.py` — `GitMCPServer` class (lines 376-384)

## Required Changes
- Add `dispatch()` method to `GitMCPServer` that delegates to `_service.get_dispatch_table()`
- Ensure the method signature matches the `MCPServer.dispatch()` contract
- Document the method in the class docstring

## Constraints
- Must not change the existing HTTP-based dispatch flow
- Must preserve the current git service dispatch behavior

## Acceptance Criteria
- `GitMCPServer.dispatch()` returns a `DispatchResult` without raising `NotImplementedError`
- The method delegates to the git service's dispatch table
- Other MCP server subclasses have consistent `dispatch()` implementations

## Testing Expectations
- Unit test: verify `GitMCPServer.dispatch()` does not raise `NotImplementedError`
- Integration test: verify programmatic dispatch works correctly
- Regression test: ensure existing HTTP dispatch behavior is unchanged

## Documentation Impact
Update `GitMCPServer` docstring to document the `dispatch()` method.

## Out of Scope
- Changes to the git service's dispatch table
- Changes to the HTTP-based dispatch flow

## Dependencies
N/A: none

## Unresolved Questions
- Are there any existing code paths that call `GitMCPServer.dispatch()` programmatically?
- Should the `dispatch()` method include idempotency key support?

## AI Implementation Instruction
In `scripts/mcp_servers/git/git_server.py`, add a `dispatch()` method to `GitMCPServer` that delegates to the git service's dispatch table. Do not modify any other MCP server's dispatch implementation.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-220730
- **Related target files**: scripts/mcp_servers/git/git_server.py
