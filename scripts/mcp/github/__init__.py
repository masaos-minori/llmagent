"""mcp/github -- GitHub MCP server package.

Sub-modules:
    service_init   — client init + build_service()
    service_business — GitHubService core business operations
    service_dispatch — GitHubService dispatch formatters (extends service_business)
    service        — re-export stub for backward compatibility
    models         — Pydantic request/response models
    mapper         — issue/PR to info mappers
    tools          — MCP tool definitions
    formatter      — GitHub-specific formatting helpers
"""

from __future__ import annotations

# Re-export public symbols from the combined module for convenience
from mcp.github.service import _GITHUB_TOKEN, GitHubService, build_service  # noqa: F401

__all__ = ["GitHubService", "build_service", "_GITHUB_TOKEN"]
