"""mcp/audit.py
Structured audit logging helper extracted from mcp/server.py.
"""

from __future__ import annotations

import logging

from shared.logger import Logger as _SharedLogger


def _audit_log(
    server_logger: logging.Logger | _SharedLogger,
    session_id: str,
    request_id: str,
    action: str,
    target: str,
    outcome: str,
    detail: str = "",
    server_key: str = "",
    error_type: str = "",
) -> None:
    """Emit one structured AUDIT log line with who/what/where context."""
    server_logger.info(
        f"AUDIT session={session_id or '-'} request={request_id or '-'} "
        f"action={action} target={target} outcome={outcome} detail={detail} "
        f"server_key={server_key} error_type={error_type}"
    )
