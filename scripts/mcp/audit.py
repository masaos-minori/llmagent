"""mcp/audit.py
Structured audit logging helper extracted from mcp/server.py.
"""

from __future__ import annotations

from typing import Any


def _audit_log(
    server_logger: Any,  # logging.Logger or shared.logger.Logger (duck-type compatible)
    session_id: str,
    request_id: str,
    action: str,
    target: str,
    outcome: str,
    detail: str = "",
) -> None:
    """Emit one structured AUDIT log line with who/what/where context."""
    server_logger.info(
        "AUDIT session=%s request=%s action=%s target=%s outcome=%s detail=%s",
        session_id or "-",
        request_id or "-",
        action,
        target,
        outcome,
        detail,
    )
