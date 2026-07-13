#!/usr/bin/env python3
"""mcp_servers/mdq/auth.py

Path authorization for mdq-mcp — fail-closed allowlist enforcement."""

from __future__ import annotations

import os
from pathlib import Path


def authorize_path(path: Path, allowed_dirs: list[str]) -> bool:
    """Authorize access to a file path based on the allowlist.

    Returns True if the path is within an allowed directory, False otherwise.

    An empty allowlist means fail-closed (deny all).
    Symlink escape attempts are prevented by resolving paths before checking.
    """
    if not allowed_dirs:
        return False

    try:
        resolved = path.resolve()
    except (OSError, ValueError):
        return False

    for root in allowed_dirs:
        try:
            resolved_root = Path(root).resolve()
            if str(resolved).startswith(str(resolved_root) + os.sep) or str(
                resolved
            ) == str(resolved_root):
                return True
        except (OSError, ValueError):
            continue

    return False
