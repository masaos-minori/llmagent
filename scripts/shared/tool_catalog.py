"""scripts/shared/tool_catalog.py — Shared `config/tool_catalog.toml` reader.

The catalog is DATA: it crosses no import boundary, so it is read at runtime rather
than imported as a module. Both the Agent lifecycle (which needs the server's
`required_capability` for report-based readiness) and MCP tool discovery read it
through this one reader, so the file path and the shape of the `[server.<key>]`
entry are defined once.

`shared` is a leaf layer, so this module performs no logging and imports nothing from
`agent`, `mcp_servers`, `rag`, or `db`.
"""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from shared.runtime_paths import resolve_config_dir

TOOL_CATALOG_FILENAME = "tool_catalog.toml"


def load_tool_catalog(config_dir: str | Path | None = None) -> dict[str, Any]:
    """Load `config/tool_catalog.toml`.

    Args:
        config_dir: Optional config directory; resolved the same way every other
            config-directory reader does when omitted.

    Returns:
        The parsed catalog.

    Raises:
        OSError: The file is missing or unreadable.
        tomllib.TOMLDecodeError: The file is not valid TOML.
    """
    path = resolve_config_dir(config_dir) / TOOL_CATALOG_FILENAME
    return tomllib.loads(path.read_text(encoding="utf-8"))


def required_capability_for(catalog: Mapping[str, Any], server_key: str) -> str | None:
    """Return the catalog `required_capability` declared for *server_key*.

    Returns None when the server has no `[server.<key>]` entry or declares no
    `required_capability`, which is the shape the readiness helpers read as the
    legacy `ready` fallback (D-6).
    """
    entry = catalog.get("server", {}).get(server_key)
    if not isinstance(entry, Mapping):
        return None
    value = entry.get("required_capability")
    return value if isinstance(value, str) else None
