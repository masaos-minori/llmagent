#!/usr/bin/env python3
"""mcp/github/tools.py
MCP tool schema definitions for github-mcp server (inputSchema format).

Dependency direction: tools_repository/file/issues/pull_requests -> tools

Split layout:
  tools_repository.py        — Repository operation tools (6 tools)
  tools_file.py              — File operation tools (4 tools)
  tools_issues.py            — Issues operation tools (5 tools)
  tools_pull_requests.py     — Pull request operation tools (6 tools)
  tools.py                   — Re-export stub combining all domain lists

TOOL_LIST is the canonical export; _MCP_TOOLS is kept for backward compatibility.
"""

from .tools_file import TOOL_LIST as _file_tools
from .tools_issues import TOOL_LIST as _issue_tools
from .tools_pull_requests import TOOL_LIST as _pr_tools
from .tools_repository import TOOL_LIST as _repo_tools

_MCP_TOOLS = (
    _repo_tools + _file_tools + _issue_tools + _pr_tools
)

# Canonical export — server.py imports TOOL_LIST, not _MCP_TOOLS directly.
TOOL_LIST: list[dict] = _MCP_TOOLS
