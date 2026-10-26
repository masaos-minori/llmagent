# GitMCPServer missing http_host attribute

## Priority
Low

## Summary
`GitMCPServer` in `git_server.py` does not define the `http_host` attribute, unlike other MCP server subclasses that explicitly set it to `"127.0.0.1"`.

## Background
The `MCPServer` base class in `server.py` uses `http_host` to determine which network interface to bind to. The `MdqMCPServer` subclass explicitly sets `http_host = "127.0.0.1"` (mdq_server.py, line 451).

However, `GitMCPServer` (git_server.py, lines 376-384) does not define `http_host`:

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
Without an explicit `http_host` attribute, the server may bind to all interfaces (`0.0.0.0`) instead of localhost only, depending on the `MCPServer` base class's default behavior. This is a security concern because:
1. The server should only be accessible locally (like other MCP servers).
2. Binding to all interfaces exposes the server to external network access.
3. The inconsistency with other MCP server subclasses makes the codebase harder to reason about.

## Reason for Change
The missing `http_host` attribute creates a potential security issue where the server could bind to all interfaces instead of localhost only.

## Implementation Intent
Add `http_host = "127.0.0.1"` to `GitMCPServer` to match the pattern used by other MCP server subclasses.

## Target Files or Areas
- `scripts/mcp_servers/git/git_server.py` — `GitMCPServer` class (lines 376-384)

## Required Changes
- Add `http_host = "127.0.0.1"` to `GitMCPServer`
- Ensure the attribute is documented in the class docstring

## Constraints
- Must not change the existing port binding behavior
- Must preserve backward compatibility with existing deployment configurations

## Acceptance Criteria
- `GitMCPServer` binds to `127.0.0.1` only
- Consistent with other MCP server subclasses
- No security regression from binding to all interfaces

## Testing Expectations
- Integration test: verify server binds to `127.0.0.1` only
- Regression test: ensure existing port binding behavior is unchanged

## Documentation Impact
Update `GitMCPServer` docstring to document the `http_host` attribute.

## Out of Scope
- Changes to the `MCPServer` base class's default `http_host` behavior
- Changes to how the server binds to network interfaces

## Dependencies
N/A: none

## Unresolved Questions
- What is the default `http_host` value in `MCPServer` if not specified?
- Are there any deployment configurations that rely on the current behavior?

## AI Implementation Instruction
In `scripts/mcp_servers/git/git_server.py`, add `http_host = "127.0.0.1"` to `GitMCPServer`. Do not modify any other MCP server's host configuration.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-220730
- **Related target files**: scripts/mcp_servers/git/git_server.py
