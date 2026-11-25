"""scripts/agent/http_lifecycle_launch_spec.py — Immutable launch specification for HTTP subprocess MCP servers.

One frozen object carries everything a subprocess spawn may use: the validated
executable path, the fixed process options, the minimal per-server environment, and
the file identity captured at validation time. `LaunchSpec.popen_kwargs` is the only
source of `Popen` keywords, so no configuration value can reach the spawn (cliplc006
REQ-001, REQ-002).
"""

from __future__ import annotations

import fnmatch
import logging
import os
import subprocess
from dataclasses import dataclass
from typing import IO, Any

from shared.mcp_config import (
    _ENV_KEY_DENYLIST,
    McpServerConfig,
    validate_server_key,
)

from .http_lifecycle_command_validator import (
    _DEFAULT_ALLOWED_ENV_VARS,
    _DEFAULT_PROTECTED_ENV_VARS,
)

logger = logging.getLogger(__name__)

# REQ-006: the only variables a child may inherit from the Agent process. The set is defined
# once, as the validator's env-policy constant `_DEFAULT_ALLOWED_ENV_VARS`; this alias names it
# for the environment builder. Server tokens are not in it: they are derived per server key, and
# an unrelated parent credential is never admitted.
_FIXED_RUNTIME_PATTERNS: frozenset[str] = _DEFAULT_ALLOWED_ENV_VARS


@dataclass(frozen=True)
class LaunchSpec:
    """Everything one subprocess spawn may use, fixed at one construction site.

    The type cannot express `shell`, `preexec_fn`, `cwd`, `stdout`, a
    `start_new_session=False`, or an inherited environment: `popen_kwargs()` emits the
    fixed keyword set and nothing else. Every field is a tuple or a scalar, so the
    specification cannot be mutated after construction.
    """

    server_key: str
    argv: tuple[str, ...]
    env_items: tuple[tuple[str, str], ...]
    stderr: IO[bytes]
    expected_identity: tuple[int, int]

    def popen_kwargs(self) -> dict[str, Any]:
        """Return the fixed `Popen` keyword set for this launch."""
        return {
            "start_new_session": True,
            "stdout": subprocess.DEVNULL,
            "stderr": self.stderr,
            "env": dict(self.env_items),
        }

    def verify_identity(self) -> str | None:
        """Re-check the validated file identity immediately before the spawn.

        Returns `None` when the target is still the same file, else a reason naming the
        server key and the path (REQ-003, AC-1). The caller turns that reason into a
        `StartupFailure` and does not spawn.
        """
        target = self.argv[0]
        try:
            st = os.stat(target)
        except OSError as exc:
            return (
                f"Server '{self.server_key}': launch target '{target}' is not "
                f"statable before spawn ({exc.strerror or exc})."
            )
        if (st.st_dev, st.st_ino) != self.expected_identity:
            return (
                f"Server '{self.server_key}': launch target '{target}' changed between "
                "validation and spawn."
            )
        return None


def build_launch_spec(
    server_key: str,
    cfg: McpServerConfig,
    resolved_path: str,
    expected_identity: tuple[int, int],
    stderr_fh: IO[bytes],
) -> LaunchSpec:
    """Build the one specification a server's spawn may use.

    `resolved_path` is the path the command validator returned and replaces `cfg.cmd[0]`;
    the remaining arguments are taken from the configuration as-is. The server key is
    validated before anything is derived from it, and `argv[0]` must be absolute.
    """
    validate_server_key(server_key, context=f"launch spec for server key {server_key}")
    if not os.path.isabs(resolved_path):
        raise ValueError(
            f"launch argv[0] for server '{server_key}' must be an absolute path: "
            f"{resolved_path!r}"
        )

    tail = list(cfg.cmd[1:]) if cfg.cmd else []
    for index, arg in enumerate(tail):
        if not isinstance(arg, str):
            raise ValueError(
                f"launch argument {index + 1} for server '{server_key}' must be str, "
                f"got {type(arg).__name__}"
            )

    return LaunchSpec(
        server_key=server_key,
        argv=(resolved_path, *tail),
        env_items=tuple(build_child_env(server_key, cfg).items()),
        stderr=stderr_fh,
        expected_identity=expected_identity,
    )


def build_child_env(server_key: str, cfg: McpServerConfig) -> dict[str, str]:
    """Build one server's minimal child environment.

    The child receives the fixed runtime set present in the parent, the two tokens
    derived from its own server key, the credential names its config declares in
    `credential_env`, and its configured `env` under the denylist and protected-variable
    rules (REQ-006, REQ-007). A declared name absent from the parent is simply not added.
    The audit line records key names only, never a value.
    """
    parent = os.environ
    env: dict[str, str] = {
        name: value
        for name, value in parent.items()
        if any(fnmatch.fnmatch(name, pattern) for pattern in _FIXED_RUNTIME_PATTERNS)
    }

    for name in _derived_token_names(server_key):
        if name in parent:
            env[name] = parent[name]

    for name in cfg.credential_env:
        if name in parent:
            env[name] = parent[name]

    for name, value in (cfg.env or {}).items():
        if any(fnmatch.fnmatch(name, pattern) for pattern in _ENV_KEY_DENYLIST):
            logger.warning(
                "Blocked denylisted env var from server config: %s",
                name,
            )
        elif name in _DEFAULT_PROTECTED_ENV_VARS:
            logger.warning("Blocked protected env var override: %s", name)
        else:
            env[name] = value

    logger.info(
        "Launch environment for server %s: keys=%s",
        server_key,
        sorted(env),
    )
    return env


def _derived_token_names(server_key: str) -> tuple[str, str]:
    """The auth and control token names derived from one server key."""
    upper = server_key.upper()
    return (f"MCP_{upper}_AUTH_TOKEN", f"MCP_{upper}_CONTROL_TOKEN")
