"""scripts/mcp_servers/file/__init__.py — File MCP server package."""

from __future__ import annotations

# Sibling servers must not be imported here: each server process may read only its own
# config file (config isolation).
