"""scripts/agent/http_lifecycle_stderr_log_manager.py

Stderr log management for HTTP subprocess MCP servers.

HttpServerLifecycleManager delegates all stderr log operations to this module.
Owning stderr log rotation logic enables independent unit testing of log management behavior.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from typing import IO

from shared.mcp_config import validate_server_key

from agent.http_lifecycle_errors import HttpStartupError, StartupFailure

logger = logging.getLogger(__name__)

_DEFAULT_STDERR_TAIL_BYTES: int = 64 * 1024
# REQ-006: enforcement defaults. They mirror the config defaults in
# scripts/shared/mcp_config.py (max_stderr_log_size_mb, max_stderr_log_files) and are
# held as plain values here, so no agent module imports the MCP server config model.
_DEFAULT_MAX_LOG_SIZE_BYTES: int = 100 * 1024 * 1024
_DEFAULT_MAX_LOG_FILES: int = 3


class StderrLogManager:
    """Manages stderr log files for HTTP subprocess MCP servers."""

    def __init__(
        self,
        *,
        stderr_tail_bytes: int | None = None,
        max_log_size_bytes: int | None = None,
        max_log_files: int | None = None,
    ) -> None:
        self._stderr_tail_bytes = stderr_tail_bytes or _DEFAULT_STDERR_TAIL_BYTES
        self._max_log_size_bytes = max_log_size_bytes or _DEFAULT_MAX_LOG_SIZE_BYTES
        self._max_log_files = max_log_files or _DEFAULT_MAX_LOG_FILES
        self._log_paths: dict[str, str] = {}
        # Generation counter per server key, kept in the manager rather than derived
        # from the filesystem state.
        self._generations: dict[str, int] = {}

    def open_log(self, server_key: str, cfg: object) -> IO[bytes]:
        """Open a stderr log file for the given server key.

        Args:
            server_key: Unique identifier for the server.
            cfg: Server configuration object (must have 'server_key', 'cmd', etc.)

        Returns:
            Open file handle in append mode.

        Raises:
            HttpStartupError: If the server key is not a valid identifier, or the log
                directory cannot be created or opened.
        """
        # REQ-005 (AC-4): the key becomes a path component below, so an invalid one is
        # rejected before any directory or file is touched.
        try:
            validate_server_key(
                server_key,
                context=f"stderr log path for server key {server_key}",
            )
        except ValueError as e:
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=str(e),
                    stderr_full="",
                )
            ) from e

        # Determine log directory and filename based on the validated server_key
        log_dir = f"{tempfile.gettempdir()}/mcp_server_logs/{server_key}"
        log_file_path = f"{log_dir}/stderr.log"

        try:
            os.makedirs(log_dir, mode=0o700, exist_ok=True)
        except OSError as e:
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=f"Cannot create log directory '{log_dir}': {e}",
                    stderr_full="",
                )
            )

        # REQ-006 (AC-3): stderr content can carry credentials, so the log file is
        # created with mode 0o600; the directory stays 0o700.
        fd = os.open(log_file_path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        log_file = os.fdopen(fd, "ab")
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

    def rotate_log(self, server_key: str, max_bytes: int | None = None) -> bool:
        """Rotate the stderr log if it exceeds the size limit.

        Copy-and-truncate (Plan D2): the content is copied to the rotated generation and
        the active file is truncated in place, so the writer fd and `read_tail()` keep
        pointing at the same active path. `os.rename()` is not usable here because the
        writer fd would follow the renamed inode while `read_tail()` read the new empty
        path.

        Args:
            server_key: Unique identifier for the server.
            max_bytes: Size limit for this call; the configured default is used when it
                is not supplied.

        Returns:
            True if rotation occurred, False otherwise.
        """
        if server_key not in self._log_paths:
            return False

        log_file_path = self._log_paths[server_key]
        limit = max_bytes if max_bytes is not None else self._max_log_size_bytes
        try:
            if os.path.getsize(log_file_path) <= limit:
                return False

            generation = self._generations.get(server_key, 0) + 1
            self._generations[server_key] = generation
            rotated_path = f"{log_file_path}.{generation}"
            with open(log_file_path, "rb") as src, open(rotated_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            os.truncate(log_file_path, 0)
            logger.info("Rotated stderr log for %s", server_key)
            self.purge_generations(server_key)
            return True
        except OSError:
            return False

    def purge_generations(self, server_key: str) -> int:
        """Remove rotated generations beyond `max_log_files`, oldest first.

        Args:
            server_key: Unique identifier for the server.

        Returns:
            Number of generation files removed.
        """
        if server_key not in self._log_paths:
            return 0

        log_file_path = self._log_paths[server_key]
        prefix = f"{os.path.basename(log_file_path)}."
        directory = os.path.dirname(log_file_path)
        try:
            names = os.listdir(directory)
        except OSError:
            return 0

        generations = sorted(
            (n for n in names if n.startswith(prefix) and n[len(prefix) :].isdigit()),
            key=lambda n: int(n[len(prefix) :]),
        )
        removed = 0
        for name in generations[: max(0, len(generations) - self._max_log_files)]:
            try:
                os.remove(os.path.join(directory, name))
                removed += 1
            except OSError:
                pass
        return removed

    def get_log_path(self, server_key: str) -> str | None:
        """Return the tracked stderr log path for a server key, or None if untracked."""
        return self._log_paths.get(server_key)

    def forget(self, server_key: str) -> None:
        """Remove the tracked stderr log path for a server key, if present."""
        self._log_paths.pop(server_key, None)
        self._generations.pop(server_key, None)

    def clear(self) -> None:
        """Remove all tracked stderr log paths."""
        self._log_paths.clear()
        self._generations.clear()
