"""scripts/agent/http_lifecycle_command_validator.py

Command validation for HTTP subprocess MCP servers.

HttpServerLifecycleManager delegates all command validation operations to this module.
Owning allowlist/symlink-resolution/regular-file checks enables independent unit testing of
security-critical validation logic.
"""

from __future__ import annotations

import fnmatch
import logging
import os
import re
import shutil
import stat
from pathlib import Path

from shared.mcp_config import _ENV_KEY_DENYLIST

from .http_lifecycle_errors import HttpStartupError, StartupFailure

logger = logging.getLogger(__name__)

_DEFAULT_ALLOWED_COMMANDS: frozenset[str] = frozenset(
    {"node", "npm", "npx", "uvx", "python", "pipx", "uvicorn", "uv"}
)
_DEFAULT_PROTECTED_ENV_VARS: frozenset[str] = frozenset(
    {"PATH", "PYTHONPATH", "LD_LIBRARY_PATH", "HOME", "USER"}
)
_INTERPRETER_BASENAME_RE = re.compile(r"python3(?:\.\d+)?")


class CommandValidator:
    """Validates commands and filters environment variables for HTTP subprocess MCP servers."""

    PROTECTED_ENV_VARS: frozenset[str] = frozenset(
        {"PATH", "PYTHONPATH", "LD_LIBRARY_PATH", "HOME", "USER"}
    )

    _DEFAULT_ALLOWED_BINARY_DIR: str = "/opt/llm/bin"

    def __init__(
        self,
        *,
        allowed_commands: frozenset[str] | None = None,
        protected_env_vars: frozenset[str] | None = None,
    ) -> None:
        self._allowed_commands = allowed_commands or _DEFAULT_ALLOWED_COMMANDS
        self._protected_env_vars = protected_env_vars or _DEFAULT_PROTECTED_ENV_VARS

    def validate(self, server_key: str, cmd_name: str) -> str:
        """Validate and resolve a command name to an absolute executable path.

        Performs five security checks in order:
        1. Resolve via shutil.which (PATH lookup)
        2. Resolve symlinks via os.path.realpath
        3. Verify resolved path exists and is a regular file
        4. Check basename against allowlist OR resolved path inside the allowed
           binary directory (regular file, exact real-path parent, not
           group/world-writable)

        Raises HttpStartupError with a descriptive StartupFailure on any failure.
        Returns the resolved absolute path on success.
        """
        # Check 1: PATH lookup
        cmd_executable = shutil.which(cmd_name)
        if cmd_executable is None:
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=f"Command '{cmd_name}' not found in PATH.",
                    stderr_full="",
                )
            )

        # Check 2: Symlink resolution
        cmd_path = os.path.realpath(cmd_executable)

        # Check 3: Regular file verification
        if not os.path.isfile(cmd_path):
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=f"Resolved command '{cmd_path}' is not a regular file.",
                    stderr_full="",
                )
            )

        # Check 4: Allowlist OR allowed-binary-directory rule. Reject only when
        # the command is outside BOTH controls; the directory branch is additive
        # and never weakens the existing basename allowlist.
        base_name = os.path.basename(cmd_path)
        in_allowlist = base_name in self._allowed_commands or bool(
            _INTERPRETER_BASENAME_RE.fullmatch(base_name)
        )
        if not in_allowlist and not self._inside_allowed_binary_dir(cmd_path):
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=(
                        f"Command '{cmd_name}' (resolved to '{cmd_path}') "
                        "is not in the allowed commands list."
                    ),
                    stderr_full="",
                )
            )

        return cmd_path

    def _allowed_binary_dir(self) -> str:
        """Return the allowed binary directory, overridable via LLMAGENT_BINARY_DIR."""
        return os.environ.get("LLMAGENT_BINARY_DIR") or self._DEFAULT_ALLOWED_BINARY_DIR

    def _inside_allowed_binary_dir(self, cmd_path: str) -> bool:
        """True if cmd_path is a regular file directly inside the allowed binary dir.

        Requires an exact realpath parent match (no subdirectories), a regular
        file (a symlink planted in the dir pointing elsewhere fails the isfile
        and parent checks), and a directory that is neither group- nor
        world-writable.
        """
        allowed = os.path.realpath(self._allowed_binary_dir())
        if not os.path.isfile(cmd_path):
            return False
        if Path(os.path.realpath(cmd_path)).parent != Path(allowed):
            return False
        # Directory writability, not the file's: the control is that untrusted
        # users cannot drop binaries into the allowed directory.
        mode = os.stat(allowed).st_mode
        return (mode & (stat.S_IWGRP | stat.S_IWOTH)) == 0

    def filter_env(self, env: dict[str, str] | None) -> dict[str, str] | None:
        """Filter environment variables, blocking protected ones.

        Returns a new dict with protected env vars excluded, or None if input is None.
        Logs warnings for blocked overrides.
        """
        if env is None:
            return None

        result = dict(os.environ)
        for key in list(result):
            if any(fnmatch.fnmatch(key, p) for p in _ENV_KEY_DENYLIST):
                del result[key]
        for key, value in env.items():
            if key in self._protected_env_vars:
                logger.warning("Blocked protected env var override: %s=%s", key, value)
            else:
                result[key] = value
        return result
