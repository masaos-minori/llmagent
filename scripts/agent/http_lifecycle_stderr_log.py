"""scripts/agent/http_lifecycle_stderr_log.py

Stderr log management for HTTP subprocess MCP servers.

Owns stderr log rotation logic currently inline in HttpServerLifecycleManager.start().
Enables independent unit testing of log management behavior.
"""

from __future__ import annotations

import logging
import os
from typing import IO

logger = logging.getLogger(__name__)

_DEFAULT_STDERR_TAIL_BYTES: int = 64 * 1024


class StderrLogManager:
    """Manages stderr log files for HTTP subprocess MCP servers."""

    def __init__(
        self,
        *,
        stderr_tail_bytes: int | None = None,
    ) -> None:
        self._stderr_tail_bytes = stderr_tail_bytes or _DEFAULT_STDERR_TAIL_BYTES
        self._log_files: dict[str, IO[bytes]] = {}
        self._log_paths: dict[str, str] = {}

    def open_log(self, server_key: str, cfg: object) -> IO[bytes]:
        """Open a stderr log file for the given server key.

        Args:
            server_key: Unique identifier for the server.
            cfg: Server configuration object (must have 'server_key', 'cmd', etc.)

        Returns:
            Open file handle in append mode.

        Raises:
            HttpStartupError: If the log directory cannot be created or opened.
        """
        # Determine log directory and filename based on server_key
        log_dir = f"/tmp/mcp_server_logs/{server_key}"
        log_file_path = f"{log_dir}/stderr.log"

        try:
            os.makedirs(log_dir, mode=0o700, exist_ok=True)
        except OSError as e:
            from agent.http_lifecycle_errors import HttpStartupError, StartupFailure

            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=f"Cannot create log directory '{log_dir}': {e}",
                    stderr_full="",
                )
            )

        log_file = open(log_file_path, "ab")
        self._log_files[server_key] = log_file
        self._log_paths[server_key] = log_file_path
        return log_file

    def read_tail(self, server_key: str) -> bytes:
        """Read the last N bytes of the stderr log for the given server key.

        Args:
            server_key: Unique identifier for the server.

        Returns:
            Last N bytes of the log file.
        """
        if server_key not in self._log_paths:
            return b""

        log_file_path = self._log_paths[server_key]
        try:
            with open(log_file_path, "rb") as f:
                f.seek(0, 2)  # Seek to end
                file_size = f.tell()
                if file_size <= self._stderr_tail_bytes:
                    f.seek(0)
                    return f.read()
                else:
                    f.seek(file_size - self._stderr_tail_bytes)
                    return f.read()
        except OSError:
            return b""

    def rotate_log(self, server_key: str, max_bytes: int) -> bool:
        """Rotate the stderr log if it exceeds max_bytes.

        Args:
            server_key: Unique identifier for the server.
            max_bytes: Maximum log file size before rotation.

        Returns:
            True if rotation occurred, False otherwise.
        """
        if server_key not in self._log_paths:
            return False

        log_file_path = self._log_paths[server_key]
        try:
            if os.path.getsize(log_file_path) > max_bytes:
                # Rotate: rename current log, create new one
                rotated_path = f"{log_file_path}.old"
                os.rename(log_file_path, rotated_path)
                # Keep the old log file around for debugging
                logger.info("Rotated stderr log for %s", server_key)
                return True
        except OSError:
            pass
        return False
