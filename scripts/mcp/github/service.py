"""mcp/github/service.py -- Re-export stub for backward compatibility.

This module re-exports all public symbols from the split sub-modules so that
existing imports continue to work without changes:

    from mcp.github.service import GitHubService, build_service, _GITHUB_TOKEN

New code should import directly from the sub-modules:

    from mcp.github.service_business import GitHubService  # business methods
    from mcp.github.service_dispatch import GitHubService  # with dispatch formatters
    from mcp.github.service_init import build_service       # client init + singleton
"""

from __future__ import annotations

# Re-export public symbols for backward compatibility
# Use service_dispatch.GitHubService (extends service_business with fmt_* methods)
from mcp.github.service_dispatch import GitHubService  # noqa: F401
from mcp.github.service_init import _GITHUB_TOKEN, build_service  # noqa: F401

__all__ = ["GitHubService", "build_service", "_GITHUB_TOKEN"]
