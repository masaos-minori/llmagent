"""mcp_servers/github -- GitHub MCP server package.

Sub-modules:
    service_init   — client init + build_service()
    service_business — GitHubService core business operations
    service_dispatch — GitHubService dispatch formatters (extends service_business)
    github_models  — Pydantic request/response models
    mapper         — issue/PR to info mappers
    github_tools   — MCP tool definitions
    formatter      — GitHub-specific formatting helpers
"""

from __future__ import annotations

__all__ = ["server"]

from . import github_server as server
