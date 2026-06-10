"""mcp/installer_validation.py
Server name validation and name-to-identifier conversion helpers.
"""

from __future__ import annotations

import re

# Allowed server name pattern: lowercase letters, digits, hyphens; starts with a letter.
_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def validate_server_name(server_name: str) -> str:
    """Return server_name when valid; raise ValueError with a clear message if not."""
    if not server_name:
        raise ValueError("Server name must not be empty.")
    if not _NAME_RE.match(server_name):
        raise ValueError(
            f"Invalid server name {server_name!r}. "
            "Use lowercase letters, digits, and hyphens; must start with a letter."
        )
    return server_name


def name_to_module(server_name: str) -> str:
    """Convert service name (hyphens allowed) to Python module identifier.

    Raises ValueError if server_name fails validation.
    """
    validate_server_name(server_name)
    return re.sub(r"[^a-z0-9]", "_", server_name.lower())


def name_to_class(server_name: str) -> str:
    """Convert service name to PascalCase class name prefix.

    Raises ValueError if server_name fails validation.
    """
    validate_server_name(server_name)
    return "".join(w.capitalize() for w in re.split(r"[-_]+", server_name))
