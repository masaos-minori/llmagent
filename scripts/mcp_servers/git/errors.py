#!/usr/bin/env python3
"""scripts/mcp_servers/git/errors.py

Domain exceptions shared across the git-mcp modules.
"""

from __future__ import annotations


class GitServiceError(RuntimeError):
    """Raised on general git service errors."""
