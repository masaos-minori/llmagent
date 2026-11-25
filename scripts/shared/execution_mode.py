#!/usr/bin/env python3
"""scripts/shared/execution_mode.py — Execution-mode vocabulary and resolver.

One closed vocabulary shared by the Agent and every MCP server: the mode is
decided from validated arguments plus the tool's declared preview capability,
never from the text a handler printed. Values are closed so a producer cannot
declare a mode no consumer can interpret.

``no_op`` belongs to the vocabulary but is never returned by the resolver: it
is a dispatcher outcome (no handler ran), not an input-derived mode.

The resolver is pure and total over its inputs: it raises only for a malformed
``dry_run`` on a preview-capable tool, so a caller never has to catch I/O
errors. The module imports nothing from ``agent`` or ``mcp_servers``: ``shared``
stays an import-linter leaf and both sides read the same rule.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

ExecutionMode = Literal["preview", "applied", "no_op"]
EXECUTION_MODES: frozenset[str] = frozenset({"preview", "applied", "no_op"})


def resolve_execution_mode(
    tool: str, args: Mapping[str, object], preview_capable: bool
) -> ExecutionMode:
    """Derive the execution mode from validated arguments and declared capability.

    ``preview`` is returned only when the tool declares the dry-run capability
    and its ``dry_run`` argument is exactly ``True``. A tool without the
    capability never previews: ``dry_run`` stays an ordinary argument handled by
    argument validation. An absent or ``None`` ``dry_run`` means applied.

    Raises:
        ValueError: ``dry_run`` is present on a preview-capable tool but is not
            a ``bool``. The message names the tool and the offending type only;
            the value is never echoed because arguments can carry secrets.
    """
    if not preview_capable:
        return "applied"

    dry_run = args.get("dry_run")
    if dry_run is None:
        return "applied"
    if not isinstance(dry_run, bool):
        raise ValueError(
            f"tool {tool} declares dry-run preview capability but its "
            f"dry_run argument is of type {type(dry_run).__name__}"
        )
    return "preview" if dry_run else "applied"
