#!/usr/bin/env python3
"""scripts/shared/mcp_config.py

Transport configuration for MCP servers.
Placed in shared/ so tool_executor.py can reference it without depending on agent/.
"""

from __future__ import annotations

import fnmatch
import logging
import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from urllib.parse import urlparse

from shared.config_field_types import (
    reject_unknown_keys,
    strict_bool,
    strict_float,
    strict_int,
    strict_str,
    strict_str_list,
    strict_str_mapping,
)
from shared.config_utils import resolve_env_ref
from shared.logger import register_secret
from shared.mcp_call_state_contract import resolve_control_token

logger = logging.getLogger(__name__)

_ENV_KEY_DENYLIST: tuple[str, ...] = ("LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH")

# REQ-005: the only server-identifier shape that may become a path component or terminal text.
_SERVER_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
# A credential_env entry is a variable name, never a pattern (REQ-006).
_CREDENTIAL_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_server_key(key: str, *, context: str) -> str:
    """Return a server identifier unchanged, or reject it before it reaches a path.

    `context` names the section and field in the raised message. An empty key is allowed:
    it is the dataclass default for instances built without a config section.
    """
    if key == "":
        return key
    if not _SERVER_KEY_RE.fullmatch(key):
        raise ValueError(
            f"{context} is not a valid server identifier: {key!r} must match "
            "^[a-z0-9][a-z0-9_-]{0,63}$"
        )
    return key


# Declared key set of one [mcp_servers.<key>] table. A key outside this set is rejected by name
# instead of being dropped in silence.
_MCP_SERVER_KEYS: tuple[str, ...] = (
    "transport",
    "url",
    "startup_mode",
    "cmd",
    "env",
    "credential_env",
    "call_timeout_sec",
    "health_timeout",
    "startup_timeout_sec",
    "startup_stagger_delay_sec",
    "max_stderr_log_size_mb",
    "max_stderr_log_files",
    "auth_token",
    "control_auth_token",
    "role",
    "required",
)


class TransportType(StrEnum):
    """MCP server transport protocol."""

    HTTP = "http"


class StartupMode(StrEnum):
    """MCP server startup lifecycle mode.

    Per-mode required fields:
    - NONE: none of url/cmd/auth_token (server is unusable)
    - PERSISTENT: url (enforced via HTTP-transport check)
    - SUBPROCESS: cmd (enforced) and url
    """

    NONE = "none"  # no subprocess spawn, no health check; server is unusable
    PERSISTENT = "persistent"
    SUBPROCESS = "subprocess"

    @property
    def is_persistent(self) -> bool:
        """Whether this mode represents a persistent server."""
        return self == StartupMode.PERSISTENT

    @property
    def has_health_check(self) -> bool:
        """Whether this mode requires health checks."""
        return self != StartupMode.NONE

    @property
    def requires_subprocess(self) -> bool:
        """Whether this mode requires subprocess management."""
        return self == StartupMode.SUBPROCESS


@dataclass
class McpServerConfig:
    """Transport configuration for one MCP server."""

    transport: TransportType
    url: str  # base URL (transport=HTTP)
    startup_mode: StartupMode = StartupMode.NONE
    call_timeout_sec: float = 60.0  # per-call timeout for HttpTransport; 0 = no timeout
    health_timeout: float | None = None  # per-server health-check timeout; None → 5.0
    startup_timeout_sec: int = 30  # subprocess startup health-poll timeout in seconds
    auth_token: str = ""  # Bearer token sent by ToolExecutor
    control_auth_token: str = ""  # Bearer token for the control API paths (mcpdl004)
    role: str = ""  # human-readable role label
    cmd: list[str] = field(
        default_factory=list
    )  # launch command for startup_mode=subprocess
    env: dict[str, str] = field(default_factory=dict)  # extra env vars for subprocess
    credential_env: tuple[str, ...] = field(
        default_factory=tuple
    )  # credential variable names this server's child receives (REQ-007)
    key: str = field(
        default="", compare=False, repr=False
    )  # server key from config; compare=False keeps equality unaffected
    startup_stagger_delay_sec: float = (
        0.0  # stagger delay between consecutive server starts
    )
    max_stderr_log_size_mb: float = 100.0  # max size in MB before rotation
    max_stderr_log_files: int = 3  # number of rotated files to keep
    required: bool = True  # Startup criticality: FATAL vs WARNING escalation at discovery. Effective value validated against `registry/component_mandatoriness.yaml` at startup; cannot weaken the approved classification (ADR-004 Group 3 item 13).

    @property
    def is_disabled(self) -> bool:
        """Whether this server is currently disabled (startup_mode=NONE)."""
        return self.startup_mode == StartupMode.NONE

    @property
    def needs_health_check(self) -> bool:
        """Whether this server requires health checks."""
        return self.startup_mode.has_health_check

    def auth_headers(self) -> dict[str, str]:
        """Return the Bearer Authorization header for this server, or {} when no token is set."""
        if not self.auth_token:
            return {}
        return {"Authorization": f"Bearer {self.auth_token}"}

    @property
    def requires_cmd(self) -> bool:
        """Whether this server has a launch command configured."""
        return len(self.cmd) > 0

    def __post_init__(self) -> None:
        """Validate enum types and cross-field constraints after initialization."""
        self._validate_enum_types()
        self._validate_cross_fields()

    def _validate_enum_types(self) -> None:
        """Ensure transport and startup_mode values are valid enum members."""
        if not isinstance(self.transport, TransportType):
            raise ValueError(f"{self.transport!r} is not a valid TransportType")
        if self.startup_mode is not None and not isinstance(
            self.startup_mode, StartupMode
        ):
            raise ValueError(f"{self.startup_mode!r} is not a valid StartupMode")

    def _validate_key(self) -> None:
        """Reject a server identifier that could become a path component (REQ-005)."""
        validate_server_key(self.key, context="McpServerConfig.key")

    def _validate_cross_fields(self) -> None:
        """Validate cross-field constraints such as required URLs and timeouts."""
        key_prefix = f"McpServerConfig[{self.key!r}]" if self.key else "McpServerConfig"

        self._validate_key()
        self._validate_startup_requirements(key_prefix)
        self._validate_timeouts(key_prefix)
        self._validate_auth_token(key_prefix)
        self._validate_env(key_prefix)
        self._validate_url_scheme(key_prefix)
        self._validate_startup_stagger_delay(key_prefix)
        self._validate_stderr_log_rotation(key_prefix)

    def _validate_startup_requirements(self, key_prefix: str) -> None:
        """Validate that url/cmd are present when required by transport/startup_mode."""
        if self.transport == TransportType.HTTP and not self.url:
            raise ValueError(
                f"{key_prefix}: url must not be empty when transport='http'"
            )
        if self.startup_mode == StartupMode.SUBPROCESS and not self.cmd:
            raise ValueError(
                f"{key_prefix}: cmd must not be empty when startup_mode='subprocess'"
            )
        # ADR-004 Exceptions: non-required subprocess servers are disallowed because a
        # subprocess server that fails to spawn must fail closed (cannot degrade gracefully).
        if self.startup_mode == StartupMode.SUBPROCESS and not self.required:
            raise ValueError(
                f"{key_prefix}: required=false is not supported when "
                f"startup_mode='subprocess' (ADR-004 Exceptions)"
            )

    def _validate_timeouts(self, key_prefix: str) -> None:
        """Validate that timeout fields are non-negative."""
        if self.call_timeout_sec < 0:
            raise ValueError(
                f"{key_prefix}: call_timeout_sec must be >= 0, got {self.call_timeout_sec}"
            )
        if self.health_timeout is not None and self.health_timeout < 0:
            raise ValueError(
                f"{key_prefix}: health_timeout must be >= 0, got {self.health_timeout}"
            )
        if self.startup_timeout_sec < 0:
            raise ValueError(
                f"{key_prefix}: startup_timeout_sec must be >= 0, got {self.startup_timeout_sec}"
            )

    def _validate_auth_token(self, key_prefix: str) -> None:
        """Validate that auth_token is a non-empty str, unless the server is disabled."""
        if not isinstance(self.auth_token, str):
            raise ValueError(
                f"{key_prefix}: auth_token must be str, got {type(self.auth_token).__name__}"
            )
        if not self.auth_token and not self.is_disabled:
            # Disabled servers do not require unused connection credentials
            raise ValueError(f"{key_prefix}: auth_token must not be empty")

    def _validate_env(self, key_prefix: str) -> None:
        """Validate env is dict[str, str] and contains no denylisted keys."""
        for k, v in self.env.items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise ValueError(
                    f"{key_prefix}: env must be dict[str, str]; got key={k!r} value={v!r}"
                )
            if any(fnmatch.fnmatch(k, p) for p in _ENV_KEY_DENYLIST):
                raise ValueError(
                    f"{key_prefix}: env key {k!r} matches denylisted pattern; "
                    "dangerous loader/interpreter env vars are not permitted"
                )

    def _validate_url_scheme(self, key_prefix: str) -> None:
        """Validate that an HTTP url has a valid http/https scheme and netloc."""
        if self.transport == TransportType.HTTP and self.url:
            parsed = urlparse(self.url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValueError(
                    f"{key_prefix}: url must be a valid HTTP/HTTPS URL, got {self.url!r}"
                )

    def _validate_startup_stagger_delay(self, key_prefix: str) -> None:
        """Validate that startup_stagger_delay_sec is non-negative."""
        if self.startup_stagger_delay_sec < 0:
            raise ValueError(
                f"{key_prefix}: startup_stagger_delay_sec must be >= 0, got {self.startup_stagger_delay_sec}"
            )

    def _validate_stderr_log_rotation(self, key_prefix: str) -> None:
        """Validate stderr log rotation size and file-count limits."""
        if self.max_stderr_log_size_mb <= 0:
            raise ValueError(
                f"{key_prefix}: max_stderr_log_size_mb must be > 0, got {self.max_stderr_log_size_mb}"
            )

        if self.max_stderr_log_files < 1:
            raise ValueError(
                f"{key_prefix}: max_stderr_log_files must be >= 1, got {self.max_stderr_log_files}"
            )


def get_effective_health_timeout(cfg: McpServerConfig) -> float | None:
    """Return the effective health timeout for a given server config.

    Returns None (no timeout) when health_timeout is 0, consistent with
    call_timeout_sec's "0 = no timeout" convention. Returns the configured
    health_timeout if set to a positive value, otherwise falls back to
    the global default of 5.0 seconds.

    Raises:
        ValueError: If ``health_timeout`` is set to a negative value.
    """
    if cfg.health_timeout is None:
        return 5.0
    if cfg.health_timeout == 0:
        return None  # No timeout, consistent with call_timeout_sec=0 convention
    if cfg.health_timeout < 0:
        raise ValueError(f"health_timeout must be >= 0, got {cfg.health_timeout}")
    return cfg.health_timeout


def _build_mcp_servers(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    servers: dict[str, McpServerConfig] = {}
    for key, value in raw.items():
        # Defensive second enforcement: a section name is the identifier the log
        # directory and the derived token names are built from (REQ-005).
        validate_server_key(key, context=f"mcp_servers.{key} section name")
        servers[key] = _build_single_server(key, value)
    return servers


_ABSENT = object()


def _read_str(v: dict[str, Any], name: str, section: str, *, default: str = "") -> str:
    """Read a str field; only an absent key takes the default."""
    raw = v.get(name, _ABSENT)
    if raw is _ABSENT:
        return default
    return strict_str(raw, f"{section}.{name}", allow_empty=True)


def _read_credential_env(v: dict[str, Any], section: str) -> tuple[str, ...]:
    """Read `credential_env`; an absent key takes the empty-tuple default (REQ-006/007).

    Entries are variable names: a glob metacharacter, whitespace, `=`, or a denylisted
    name is rejected, so the list can never widen a child environment by pattern.
    """
    raw = v.get("credential_env", _ABSENT)
    if raw is _ABSENT:
        return ()
    if isinstance(raw, tuple):
        # `agent_config_payload` renders the dataclass value back into a reload payload,
        # so the roundtrip must accept what startup produced. TOML and JSON input is a
        # list; every other type is rejected by the strict primitive below.
        raw = list(raw)
    names = strict_str_list(raw, f"{section}.credential_env", allow_empty=True)
    field_path = f"{section}.credential_env"
    for index, name in enumerate(names):
        item_path = f"{field_path}[{index}]"
        if not _CREDENTIAL_NAME_RE.match(name):
            raise ValueError(
                f"config key {item_path!r} is invalid: credential_env entries are "
                "variable names, not patterns, and may not contain whitespace or '='"
            )
        if name in _ENV_KEY_DENYLIST:
            raise ValueError(
                f"config key {item_path!r} is denylisted: {name!r} is a "
                "loader/interpreter variable and cannot be granted to a subprocess"
            )
    return tuple(names)


def _read_bool(v: dict[str, Any], name: str, section: str, *, default: bool) -> bool:
    """Read a bool field; a string or number is rejected, not coerced."""
    raw = v.get(name, _ABSENT)
    if raw is _ABSENT:
        return default
    return strict_bool(raw, f"{section}.{name}")


def _read_int(v: dict[str, Any], name: str, section: str, *, default: int) -> int:
    """Read an int field; a bool or a string is rejected, not coerced."""
    raw = v.get(name, _ABSENT)
    if raw is _ABSENT:
        return default
    return strict_int(raw, f"{section}.{name}")


def _read_float(v: dict[str, Any], name: str, section: str, *, default: float) -> float:
    """Read a float field; a bool or a string is rejected, not coerced."""
    raw = v.get(name, _ABSENT)
    if raw is _ABSENT:
        return default
    return strict_float(raw, f"{section}.{name}")


def _read_optional_float(v: dict[str, Any], name: str, section: str) -> float | None:
    """Read a float field that an explicit `null` clears."""
    raw = v.get(name, _ABSENT)
    if raw is _ABSENT or raw is None:
        return None
    return strict_float(raw, f"{section}.{name}")


def _read_cmd(v: dict[str, Any], section: str) -> list[str]:
    """Read the cmd sequence: a list of non-empty strings, never a split string.

    An absent key means "no launch command" and is the default; a key present with an
    empty sequence is rejected, because it says "launch something" and names nothing.
    """
    raw = v.get("cmd", _ABSENT)
    if raw is _ABSENT:
        return []
    return strict_str_list(raw, f"{section}.cmd")


def _read_enum[T: StrEnum](
    value: str, enum_type: type[T], name: str, section: str
) -> T:
    """Convert a declared string value to its enum member, naming the field on failure.

    The failure message lists the accepted values instead of echoing the configured one.
    """
    try:
        return enum_type(value)
    except ValueError as exc:
        accepted = ", ".join(repr(member.value) for member in enum_type)
        raise ValueError(f"{section}.{name} must be one of: {accepted}") from exc


def _build_single_server(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    Every value is read through the shared strict primitives (REQ-001), so this parser
    and the reload path accept exactly the same inputs. A present-but-wrong-typed value
    is rejected; only an absent key takes the default. A key outside `_MCP_SERVER_KEYS`
    is rejected by name rather than dropped. Raised messages name the server key and the
    field and never the value, because `auth_token` and `env` carry credentials.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    section = f"mcp_servers.{key}"
    reject_unknown_keys(v, list(_MCP_SERVER_KEYS), section=section)

    transport = _read_str(v, "transport", section, default="http")
    startup_mode = _read_str(v, "startup_mode", section, default="none")
    cmd = _read_cmd(v, section)
    env = strict_str_mapping(v.get("env", {}), f"{section}.env", allow_empty=True)
    health_timeout = _read_optional_float(v, "health_timeout", section)

    resolved_auth_token = resolve_env_ref(_read_str(v, "auth_token", section))
    register_secret(resolved_auth_token)
    # The control token is optional: an unset variable closes the control paths
    # instead of stopping the Agent (mcpdl004 REQ-002).
    resolved_control_token = resolve_control_token(
        _read_str(v, "control_auth_token", section)
    )
    if resolved_control_token:
        register_secret(resolved_control_token)

    return McpServerConfig(
        transport=_read_enum(transport, TransportType, "transport", section),
        url=_read_str(v, "url", section),
        startup_mode=_read_enum(startup_mode, StartupMode, "startup_mode", section),
        startup_timeout_sec=_read_int(v, "startup_timeout_sec", section, default=30),
        startup_stagger_delay_sec=_read_float(
            v, "startup_stagger_delay_sec", section, default=0.0
        ),
        max_stderr_log_size_mb=_read_float(
            v, "max_stderr_log_size_mb", section, default=100.0
        ),
        max_stderr_log_files=_read_int(v, "max_stderr_log_files", section, default=3),
        auth_token=resolved_auth_token,
        control_auth_token=resolved_control_token,
        call_timeout_sec=_read_float(v, "call_timeout_sec", section, default=60.0),
        health_timeout=health_timeout,
        role=_read_str(v, "role", section),
        cmd=cmd,
        env=env,
        credential_env=_read_credential_env(v, section),
        key=key,
        required=_read_bool(v, "required", section, default=True),
    )
