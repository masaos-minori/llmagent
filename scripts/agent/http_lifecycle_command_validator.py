"""scripts/agent/http_lifecycle_command_validator.py

Command validation for HTTP subprocess MCP servers.

HttpServerLifecycleManager delegates all command validation operations to this module.
Owning allowlist/symlink-resolution/regular-file checks enables independent unit testing of
security-critical validation logic.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import stat
from pathlib import Path

from .http_lifecycle_errors import HttpStartupError, StartupFailure

logger = logging.getLogger(__name__)

_DEFAULT_ALLOWED_COMMANDS: frozenset[str] = frozenset(
    {"node", "npm", "npx", "uvx", "python", "pipx", "uvicorn", "uv"}
)
_DEFAULT_PROTECTED_ENV_VARS: frozenset[str] = frozenset(
    {"PATH", "PYTHONPATH", "LD_LIBRARY_PATH", "HOME", "USER"}
)
# The fixed runtime set a child may inherit from the Agent process (REQ-006), in the same
# fnmatch form the previous allowlist used so locale variables behave unchanged. It is the
# canonical definition: `http_lifecycle_launch_spec.build_child_env` builds every child
# environment from it. Server tokens are deliberately absent: they are derived per server key
# there, so one server's token can no longer reach another server. `LLMAGENT_BINARY_DIR` and
# `LLMAGENT_COMMAND_MODE` are parent-only controls a child never reads, and unrelated parent
# credentials, proxy variables, and interpreter toolchain variables are absent for the same
# reason.
_DEFAULT_ALLOWED_ENV_VARS: frozenset[str] = frozenset(
    {
        "PATH",
        "HOME",
        "USER",
        "LOGNAME",
        "SHELL",
        "TMPDIR",
        "TMP",
        "TEMP",
        "LANG",
        "LC_*",
        "LLMAGENT_CONFIG_DIR",
        "LLMAGENT_SUDACHI_DICT",
    }
)
_INTERPRETER_BASENAME_RE = re.compile(r"python3(?:\.\d+)?")

# The only opt-out from strict command confinement (REQ-004). Exactly the literal value
# `permissive` opts in; anything else, including `PERMISSIVE` or a padded value, keeps the
# strict default, so a mistyped control fails closed.
_COMMAND_MODE_ENV_VAR = "LLMAGENT_COMMAND_MODE"
_PERMISSIVE_MODE_VALUE = "permissive"


def _permissive_mode() -> bool:
    """True only when the parent process sets `LLMAGENT_COMMAND_MODE=permissive`."""
    return os.environ.get(_COMMAND_MODE_ENV_VAR) == _PERMISSIVE_MODE_VALUE


class CommandValidator:
    """Validates commands for HTTP subprocess MCP servers.

    Command confinement is strict by default (REQ-004):

    - Strict (default): a command is accepted only when its resolved path is inside the
      trusted binary directory, that directory and the file are owned by root or the Agent
      user, and the file is neither group- nor world-writable. The basename allowlist does
      not apply, so a binary found elsewhere on ``PATH`` is rejected whatever its name.
    - Permissive (opt-in): the basename allowlist applies in addition to the trusted
      directory. Set ``LLMAGENT_COMMAND_MODE=permissive`` in the Agent process to restore
      it; only that literal value opts in, and any other value keeps the strict default.

    The trusted binary directory is ``LLMAGENT_BINARY_DIR`` when set, else
    ``/opt/llm/bin``. A command is inside it only when it is a regular file
    directly in that directory and the directory is neither group- nor
    world-writable. Symlinks are resolved before the check, so the directory
    must hold real files: a symlink in it that points elsewhere is rejected.

    ``validate`` returns the resolved path together with its ``(st_dev, st_ino)``
    identity, which the launch specification re-checks immediately before the spawn
    (REQ-003). Building the child environment is not this class's job: it belongs to
    ``http_lifecycle_launch_spec.build_child_env``, which builds it per server key.
    """

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
        self._permissive = _permissive_mode()

    def validate(self, server_key: str, cmd_name: str) -> tuple[str, tuple[int, int]]:
        """Validate a command name and return its path with its file identity.

        Performs five security checks in order:
        1. Resolve via shutil.which (PATH lookup)
        2. Resolve symlinks via os.path.realpath
        3. Verify resolved path exists and is a regular file
        4. Strict (default): require the resolved path inside the allowed binary
           directory (regular file, exact real-path parent, directory not
           group/world-writable); the allowlist is ignored. Permissive: accept when the
           basename is on the allowlist OR the path satisfies that directory rule.
        5. Strict only: the file and the directory are owned by root or the Agent user,
           and the file is neither group- nor world-writable.

        Raises HttpStartupError with a descriptive StartupFailure on any failure.
        Returns ``(resolved_path, (st_dev, st_ino))``: the identity is what the launch
        specification re-checks before spawning.
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

        # Check 4 (strict, the default): only the allowed binary directory is trusted.
        if not self._permissive:
            if not self._inside_allowed_binary_dir(cmd_path):
                raise HttpStartupError(
                    StartupFailure(
                        server_key=server_key,
                        reason=(
                            f"Command '{cmd_name}' (resolved to '{cmd_path}') "
                            "is outside the trusted binary directory "
                            f"'{self._allowed_binary_dir()}' "
                            "(strict command confinement)."
                        ),
                        stderr_full="",
                    )
                )
            # Check 5: the trusted directory and the file must be owned and moded so
            # that untrusted users cannot swap or edit what the Agent is about to run.
            self._trusted_ownership_and_mode(server_key, cmd_path)
            return cmd_path, _file_identity(cmd_path)

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

        return cmd_path, _file_identity(cmd_path)

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

    def _trusted_ownership_and_mode(self, server_key: str, cmd_path: str) -> None:
        """Reject a validated path whose ownership or mode the Agent cannot trust.

        The file and the trusted directory must be owned by root or the Agent user, and
        the file must be neither group- nor world-writable: a name inside the trusted
        directory is only safe while untrusted users cannot replace or edit it.
        """
        allowed_dir = os.path.realpath(self._allowed_binary_dir())
        trusted_uids = {0, os.geteuid()}

        file_st = os.stat(cmd_path)
        if file_st.st_uid not in trusted_uids:
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=(
                        f"Command '{cmd_path}' is owned by uid {file_st.st_uid}, "
                        "which is neither root nor the Agent user."
                    ),
                    stderr_full="",
                )
            )
        if file_st.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=(
                        f"Command '{cmd_path}' is group- or world-writable, "
                        "so its contents are not trusted."
                    ),
                    stderr_full="",
                )
            )

        dir_st = os.stat(allowed_dir)
        if dir_st.st_uid not in trusted_uids:
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=(
                        f"Trusted binary directory '{allowed_dir}' is owned by uid "
                        f"{dir_st.st_uid}, which is neither root nor the Agent user."
                    ),
                    stderr_full="",
                )
            )


def _file_identity(path: str) -> tuple[int, int]:
    """Return the ``(st_dev, st_ino)`` pair that identifies this exact file."""
    st = os.stat(path)
    return (st.st_dev, st.st_ino)
