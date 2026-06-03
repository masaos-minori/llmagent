"""mcp/installer_validation.py
Server name validation and name-to-identifier conversion helpers.
"""

from __future__ import annotations

import re

# Allowed server name pattern: lowercase letters, digits, hyphens; starts with a letter.
_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def validate_server_name(server_name: str) -> str | None:
    """Return None if valid, or an error message string if invalid."""
    if not server_name:
        return "Server name must not be empty."
    if not _NAME_RE.match(server_name):
        return (
            f"Invalid server name {server_name!r}. "
            "Use lowercase letters, digits, and hyphens; must start with a letter."
        )
    return None


def name_to_module(server_name: str) -> str:
    """Convert service name (hyphens allowed) to Python module identifier."""
    return re.sub(r"[^a-z0-9]", "_", server_name.lower())


def name_to_class(server_name: str) -> str:
    """Convert service name to PascalCase class name prefix."""
    return "".join(w.capitalize() for w in re.split(r"[-_]+", server_name))
