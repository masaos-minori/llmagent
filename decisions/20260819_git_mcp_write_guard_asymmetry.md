## Title

Git-MCP Write Guard Asymmetry

### Context

Claim that git-mcp has write tools without proper `is_write` guards while github-mcp has them.

### Decision

**NO ISSUE FOUND.** Both servers enforce `is_write` guards consistently.

### Rationale

Investigation confirmed both MCP servers use `is_write` metadata on all tool definitions. No asymmetry exists.

### Evidence

- `scripts/mcp_servers/git/git_tools.py`: 5 write tools (`is_write: True`) + 10 read-only (`is_write: False`)
- `scripts/mcp_servers/github/tools_pull_requests.py`: 3 write tools (`is_write: True`) + 3 read-only (`is_write: False`)
- `scripts/mcp_servers/github/tools_issues.py`: 2 write tools (`is_write: True`) + 3 read-only (`is_write: False`)
- `scripts/mcp_servers/github/tools_file.py`: 2 write tools (`is_write: True`) + 2 read-only (`is_write: False`)
- `scripts/mcp_servers/github/tools_repository.py`: 0 write tools, all read-only

All write tools carry `"is_write": true` metadata. The claim is incorrect.

### Follow-up Actions

None required.
