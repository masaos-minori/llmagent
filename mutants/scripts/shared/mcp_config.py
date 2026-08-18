#!/usr/bin/env python3
"""scripts/shared/mcp_config.py

Transport configuration for MCP servers.
Placed in shared/ so tool_executor.py can reference it without depending on agent/.
"""

from __future__ import annotations

import fnmatch
import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from urllib.parse import urlparse

from shared.mcp_health import (  # noqa: F401
    McpServerHealthRegistry,
    McpServerHealthState,
)

logger = logging.getLogger(__name__)

_ENV_KEY_DENYLIST: tuple[str, ...] = ("LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH")


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


class TransportType(StrEnum):
    """MCP server transport protocol."""

    HTTP = "http"


class StartupMode(StrEnum):
    """MCP server startup lifecycle mode."""

    NONE = "none"  # no subprocess spawn, no health check; server is unusable
    PERSISTENT = "persistent"
    SUBPROCESS = "subprocess"


class SecurityProfile(StrEnum):
    """Deployment security profile for MCP auth enforcement."""

    LOCAL = "local"
    PRODUCTION = "production"


@dataclass
class McpServerConfig:
    """Transport configuration for one MCP server."""

    transport: TransportType
    url: str  # base URL (transport=HTTP)
    startup_mode: StartupMode = StartupMode.NONE
    call_timeout_sec: float = 60.0  # per-call timeout for HttpTransport; 0 = no timeout
    health_timeout: float | None = None  # per-server health-check timeout; None → 5.0
    startup_timeout_sec: int = 30  # subprocess startup health-poll timeout in seconds
    tool_names: list[str] = field(default_factory=list)
    auth_token: str = ""  # Bearer token sent by ToolExecutor
    role: str = ""  # human-readable role label
    cmd: list[str] = field(
        default_factory=list
    )  # launch command for startup_mode=subprocess
    env: dict[str, str] = field(default_factory=dict)  # extra env vars for subprocess
    key: str = field(
        default="", compare=False, repr=False
    )  # server key from config; compare=False keeps equality unaffected
    startup_stagger_delay_sec: float = (
        0.0  # stagger delay between consecutive server starts
    )
    max_stderr_log_size_mb: float = 100.0  # max size in MB before rotation
    max_stderr_log_files: int = 3  # number of rotated files to keep

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

    def _validate_cross_fields(self) -> None:
        """Validate cross-field constraints such as required URLs and timeouts."""
        key_prefix = f"McpServerConfig[{self.key!r}]" if self.key else "McpServerConfig"

        self._validate_startup_requirements(key_prefix)
        self._validate_timeouts(key_prefix)
        self._validate_tool_names(key_prefix)
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

    def _validate_tool_names(self, key_prefix: str) -> None:
        """Validate that tool_names entries are non-empty strings with no duplicates."""
        for i, name in enumerate(self.tool_names):
            if not isinstance(name, str) or not name:
                raise ValueError(
                    f"{key_prefix}: tool_names[{i}] must be a non-empty string, got {name!r}"
                )
        if len(self.tool_names) != len(set(self.tool_names)):
            dupes = sorted({n for n in self.tool_names if self.tool_names.count(n) > 1})
            raise ValueError(f"{key_prefix}: duplicate tool_names: {dupes}")

    def _validate_auth_token(self, key_prefix: str) -> None:
        """Validate that auth_token is a str."""
        if not isinstance(self.auth_token, str):
            raise ValueError(
                f"{key_prefix}: auth_token must be str, got {type(self.auth_token).__name__}"
            )

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
mutants_x_get_effective_health_timeout__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_get_effective_health_timeout__mutmut)
def get_effective_health_timeout(cfg: McpServerConfig) -> float:
    """Return the effective health timeout for a given server config.

    Returns the configured ``health_timeout`` if set, otherwise falls back
    to the global default of 5.0 seconds.

    Raises:
        ValueError: If ``health_timeout`` is set to a negative value.
    """
    if cfg.health_timeout is None:
        return 5.0
    if cfg.health_timeout < 0:
        raise ValueError(f"health_timeout must be >= 0, got {cfg.health_timeout}")
    return cfg.health_timeout


def x_get_effective_health_timeout__mutmut_orig(cfg: McpServerConfig) -> float:
    """Return the effective health timeout for a given server config.

    Returns the configured ``health_timeout`` if set, otherwise falls back
    to the global default of 5.0 seconds.

    Raises:
        ValueError: If ``health_timeout`` is set to a negative value.
    """
    if cfg.health_timeout is None:
        return 5.0
    if cfg.health_timeout < 0:
        raise ValueError(f"health_timeout must be >= 0, got {cfg.health_timeout}")
    return cfg.health_timeout


def x_get_effective_health_timeout__mutmut_1(cfg: McpServerConfig) -> float:
    """Return the effective health timeout for a given server config.

    Returns the configured ``health_timeout`` if set, otherwise falls back
    to the global default of 5.0 seconds.

    Raises:
        ValueError: If ``health_timeout`` is set to a negative value.
    """
    if cfg.health_timeout is not None:
        return 5.0
    if cfg.health_timeout < 0:
        raise ValueError(f"health_timeout must be >= 0, got {cfg.health_timeout}")
    return cfg.health_timeout


def x_get_effective_health_timeout__mutmut_2(cfg: McpServerConfig) -> float:
    """Return the effective health timeout for a given server config.

    Returns the configured ``health_timeout`` if set, otherwise falls back
    to the global default of 5.0 seconds.

    Raises:
        ValueError: If ``health_timeout`` is set to a negative value.
    """
    if cfg.health_timeout is None:
        return 6.0
    if cfg.health_timeout < 0:
        raise ValueError(f"health_timeout must be >= 0, got {cfg.health_timeout}")
    return cfg.health_timeout


def x_get_effective_health_timeout__mutmut_3(cfg: McpServerConfig) -> float:
    """Return the effective health timeout for a given server config.

    Returns the configured ``health_timeout`` if set, otherwise falls back
    to the global default of 5.0 seconds.

    Raises:
        ValueError: If ``health_timeout`` is set to a negative value.
    """
    if cfg.health_timeout is None:
        return 5.0
    if cfg.health_timeout <= 0:
        raise ValueError(f"health_timeout must be >= 0, got {cfg.health_timeout}")
    return cfg.health_timeout


def x_get_effective_health_timeout__mutmut_4(cfg: McpServerConfig) -> float:
    """Return the effective health timeout for a given server config.

    Returns the configured ``health_timeout`` if set, otherwise falls back
    to the global default of 5.0 seconds.

    Raises:
        ValueError: If ``health_timeout`` is set to a negative value.
    """
    if cfg.health_timeout is None:
        return 5.0
    if cfg.health_timeout < 1:
        raise ValueError(f"health_timeout must be >= 0, got {cfg.health_timeout}")
    return cfg.health_timeout


def x_get_effective_health_timeout__mutmut_5(cfg: McpServerConfig) -> float:
    """Return the effective health timeout for a given server config.

    Returns the configured ``health_timeout`` if set, otherwise falls back
    to the global default of 5.0 seconds.

    Raises:
        ValueError: If ``health_timeout`` is set to a negative value.
    """
    if cfg.health_timeout is None:
        return 5.0
    if cfg.health_timeout < 0:
        raise ValueError(None)
    return cfg.health_timeout

mutants_x_get_effective_health_timeout__mutmut['_mutmut_orig'] = x_get_effective_health_timeout__mutmut_orig # type: ignore # mutmut generated
mutants_x_get_effective_health_timeout__mutmut['x_get_effective_health_timeout__mutmut_1'] = x_get_effective_health_timeout__mutmut_1 # type: ignore # mutmut generated
mutants_x_get_effective_health_timeout__mutmut['x_get_effective_health_timeout__mutmut_2'] = x_get_effective_health_timeout__mutmut_2 # type: ignore # mutmut generated
mutants_x_get_effective_health_timeout__mutmut['x_get_effective_health_timeout__mutmut_3'] = x_get_effective_health_timeout__mutmut_3 # type: ignore # mutmut generated
mutants_x_get_effective_health_timeout__mutmut['x_get_effective_health_timeout__mutmut_4'] = x_get_effective_health_timeout__mutmut_4 # type: ignore # mutmut generated
mutants_x_get_effective_health_timeout__mutmut['x_get_effective_health_timeout__mutmut_5'] = x_get_effective_health_timeout__mutmut_5 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__build_mcp_servers__mutmut)
def _build_mcp_servers(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_orig(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_1(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = None
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_2(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get(None)
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_3(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("XXmcp_serversXX")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_4(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("MCP_SERVERS")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_5(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) and not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_6(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_7(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) or raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_8(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            None
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_9(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "XXmcp_servers config section is missing or empty. XX"
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_10(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "MCP_SERVERS CONFIG SECTION IS MISSING OR EMPTY. "
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_11(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "XXAdd [mcp_servers.<key>] to the server's config/*_mcp_server.toml.XX"
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_12(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_13(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "ADD [MCP_SERVERS.<KEY>] TO THE SERVER'S CONFIG/*_MCP_SERVER.TOML."
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_14(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(None, v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_15(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(key, None) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_16(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(v) for key, v in raw.items()}


def x__build_mcp_servers__mutmut_17(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(key, ) for key, v in raw.items()}

mutants_x__build_mcp_servers__mutmut['_mutmut_orig'] = x__build_mcp_servers__mutmut_orig # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_1'] = x__build_mcp_servers__mutmut_1 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_2'] = x__build_mcp_servers__mutmut_2 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_3'] = x__build_mcp_servers__mutmut_3 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_4'] = x__build_mcp_servers__mutmut_4 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_5'] = x__build_mcp_servers__mutmut_5 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_6'] = x__build_mcp_servers__mutmut_6 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_7'] = x__build_mcp_servers__mutmut_7 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_8'] = x__build_mcp_servers__mutmut_8 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_9'] = x__build_mcp_servers__mutmut_9 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_10'] = x__build_mcp_servers__mutmut_10 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_11'] = x__build_mcp_servers__mutmut_11 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_12'] = x__build_mcp_servers__mutmut_12 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_13'] = x__build_mcp_servers__mutmut_13 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_14'] = x__build_mcp_servers__mutmut_14 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_15'] = x__build_mcp_servers__mutmut_15 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_16'] = x__build_mcp_servers__mutmut_16 # type: ignore # mutmut generated
mutants_x__build_mcp_servers__mutmut['x__build_mcp_servers__mutmut_17'] = x__build_mcp_servers__mutmut_17 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__build_single_server__mutmut)
def _build_single_server(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_orig(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_1(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_2(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(None)
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_3(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(None).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_4(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = None
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_5(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get(None, "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_6(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", None)
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_7(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_8(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", )
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_9(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("XXtransportXX", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_10(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("TRANSPORT", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_11(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "XXhttpXX")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_12(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "HTTP")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_13(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_14(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            None
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_15(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(None).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_16(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = None
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_17(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(None)
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_18(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get(None, []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_19(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", None))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_20(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get([]))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_21(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", ))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_22(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("XXcmdXX", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_23(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("CMD", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_24(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = None
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_25(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(None)
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_26(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get(None, {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_27(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", None))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_28(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get({}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_29(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", ))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_30(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("XXenvXX", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_31(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("ENV", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_32(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = None
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_33(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get(None)
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_34(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("XXhealth_timeoutXX")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_35(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("HEALTH_TIMEOUT")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_36(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_37(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = None
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_38(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(None)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_39(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                None
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_40(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(None).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_41(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = ""
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_42(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=None,
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_43(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=None,
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_44(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=None,
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_45(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=None,
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_46(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=None,
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_47(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=None,
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_48(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=None,
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_49(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=None,
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_50(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=None,
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_51(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=None,
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_52(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=None,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_53(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=None,
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_54(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=None,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_55(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=None,
        key=key,
    )


def x__build_single_server__mutmut_56(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=None,
    )


def x__build_single_server__mutmut_57(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_58(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_59(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_60(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_61(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_62(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_63(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_64(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_65(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_66(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_67(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_68(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_69(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_70(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        key=key,
    )


def x__build_single_server__mutmut_71(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        )


def x__build_single_server__mutmut_72(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(None),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_73(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get(None, ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_74(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", None),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_75(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get(""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_76(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_77(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("XXurlXX", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_78(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("URL", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_79(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", "XXXX"),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_80(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(None),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_81(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get(None, "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_82(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", None)),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_83(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_84(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", )),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_85(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("XXstartup_modeXX", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_86(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("STARTUP_MODE", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_87(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "XXnoneXX")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_88(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "NONE")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_89(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(None),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_90(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get(None, 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_91(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", None)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_92(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get(30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_93(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", )),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_94(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("XXstartup_timeout_secXX", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_95(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("STARTUP_TIMEOUT_SEC", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_96(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 31)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_97(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(None),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_98(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get(None, 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_99(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", None)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_100(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get(0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_101(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", )),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_102(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("XXstartup_stagger_delay_secXX", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_103(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("STARTUP_STAGGER_DELAY_SEC", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_104(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 1.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_105(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(None),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_106(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get(None, 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_107(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", None)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_108(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get(100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_109(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", )),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_110(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("XXmax_stderr_log_size_mbXX", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_111(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("MAX_STDERR_LOG_SIZE_MB", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_112(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 101.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_113(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(None),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_114(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get(None, 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_115(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", None)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_116(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get(3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_117(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", )),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_118(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("XXmax_stderr_log_filesXX", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_119(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("MAX_STDERR_LOG_FILES", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_120(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 4)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_121(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(None),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_122(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get(None, [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_123(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", None)),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_124(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get([])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_125(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", )),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_126(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("XXtool_namesXX", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_127(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("TOOL_NAMES", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_128(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get(None, ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_129(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", None),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_130(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get(""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_131(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_132(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("XXauth_tokenXX", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_133(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("AUTH_TOKEN", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_134(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", "XXXX"),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_135(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(None),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_136(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get(None, 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_137(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", None)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_138(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get(60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_139(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", )),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_140(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("XXcall_timeout_secXX", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_141(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("CALL_TIMEOUT_SEC", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_142(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 61.0)),
        health_timeout=health_timeout,
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_143(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get(None, ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_144(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", None),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_145(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get(""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_146(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", ),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_147(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("XXroleXX", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_148(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("ROLE", ""),
        cmd=cmd,
        env=env,
        key=key,
    )


def x__build_single_server__mutmut_149(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults.

    All TOML string values are converted to enum types here so that
    McpServerConfig runtime instances use normalized enum values.
    """
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    health_timeout_raw = v.get("health_timeout")
    if health_timeout_raw is not None:
        try:
            health_timeout = float(health_timeout_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
                f"got {type(health_timeout_raw).__name__}"
            )
    else:
        health_timeout = None
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "none")),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        startup_stagger_delay_sec=float(v.get("startup_stagger_delay_sec", 0.0)),
        max_stderr_log_size_mb=float(v.get("max_stderr_log_size_mb", 100.0)),
        max_stderr_log_files=int(v.get("max_stderr_log_files", 3)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        health_timeout=health_timeout,
        role=v.get("role", "XXXX"),
        cmd=cmd,
        env=env,
        key=key,
    )

mutants_x__build_single_server__mutmut['_mutmut_orig'] = x__build_single_server__mutmut_orig # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_1'] = x__build_single_server__mutmut_1 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_2'] = x__build_single_server__mutmut_2 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_3'] = x__build_single_server__mutmut_3 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_4'] = x__build_single_server__mutmut_4 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_5'] = x__build_single_server__mutmut_5 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_6'] = x__build_single_server__mutmut_6 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_7'] = x__build_single_server__mutmut_7 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_8'] = x__build_single_server__mutmut_8 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_9'] = x__build_single_server__mutmut_9 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_10'] = x__build_single_server__mutmut_10 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_11'] = x__build_single_server__mutmut_11 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_12'] = x__build_single_server__mutmut_12 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_13'] = x__build_single_server__mutmut_13 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_14'] = x__build_single_server__mutmut_14 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_15'] = x__build_single_server__mutmut_15 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_16'] = x__build_single_server__mutmut_16 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_17'] = x__build_single_server__mutmut_17 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_18'] = x__build_single_server__mutmut_18 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_19'] = x__build_single_server__mutmut_19 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_20'] = x__build_single_server__mutmut_20 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_21'] = x__build_single_server__mutmut_21 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_22'] = x__build_single_server__mutmut_22 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_23'] = x__build_single_server__mutmut_23 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_24'] = x__build_single_server__mutmut_24 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_25'] = x__build_single_server__mutmut_25 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_26'] = x__build_single_server__mutmut_26 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_27'] = x__build_single_server__mutmut_27 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_28'] = x__build_single_server__mutmut_28 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_29'] = x__build_single_server__mutmut_29 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_30'] = x__build_single_server__mutmut_30 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_31'] = x__build_single_server__mutmut_31 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_32'] = x__build_single_server__mutmut_32 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_33'] = x__build_single_server__mutmut_33 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_34'] = x__build_single_server__mutmut_34 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_35'] = x__build_single_server__mutmut_35 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_36'] = x__build_single_server__mutmut_36 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_37'] = x__build_single_server__mutmut_37 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_38'] = x__build_single_server__mutmut_38 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_39'] = x__build_single_server__mutmut_39 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_40'] = x__build_single_server__mutmut_40 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_41'] = x__build_single_server__mutmut_41 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_42'] = x__build_single_server__mutmut_42 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_43'] = x__build_single_server__mutmut_43 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_44'] = x__build_single_server__mutmut_44 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_45'] = x__build_single_server__mutmut_45 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_46'] = x__build_single_server__mutmut_46 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_47'] = x__build_single_server__mutmut_47 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_48'] = x__build_single_server__mutmut_48 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_49'] = x__build_single_server__mutmut_49 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_50'] = x__build_single_server__mutmut_50 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_51'] = x__build_single_server__mutmut_51 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_52'] = x__build_single_server__mutmut_52 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_53'] = x__build_single_server__mutmut_53 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_54'] = x__build_single_server__mutmut_54 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_55'] = x__build_single_server__mutmut_55 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_56'] = x__build_single_server__mutmut_56 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_57'] = x__build_single_server__mutmut_57 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_58'] = x__build_single_server__mutmut_58 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_59'] = x__build_single_server__mutmut_59 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_60'] = x__build_single_server__mutmut_60 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_61'] = x__build_single_server__mutmut_61 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_62'] = x__build_single_server__mutmut_62 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_63'] = x__build_single_server__mutmut_63 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_64'] = x__build_single_server__mutmut_64 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_65'] = x__build_single_server__mutmut_65 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_66'] = x__build_single_server__mutmut_66 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_67'] = x__build_single_server__mutmut_67 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_68'] = x__build_single_server__mutmut_68 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_69'] = x__build_single_server__mutmut_69 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_70'] = x__build_single_server__mutmut_70 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_71'] = x__build_single_server__mutmut_71 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_72'] = x__build_single_server__mutmut_72 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_73'] = x__build_single_server__mutmut_73 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_74'] = x__build_single_server__mutmut_74 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_75'] = x__build_single_server__mutmut_75 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_76'] = x__build_single_server__mutmut_76 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_77'] = x__build_single_server__mutmut_77 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_78'] = x__build_single_server__mutmut_78 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_79'] = x__build_single_server__mutmut_79 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_80'] = x__build_single_server__mutmut_80 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_81'] = x__build_single_server__mutmut_81 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_82'] = x__build_single_server__mutmut_82 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_83'] = x__build_single_server__mutmut_83 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_84'] = x__build_single_server__mutmut_84 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_85'] = x__build_single_server__mutmut_85 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_86'] = x__build_single_server__mutmut_86 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_87'] = x__build_single_server__mutmut_87 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_88'] = x__build_single_server__mutmut_88 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_89'] = x__build_single_server__mutmut_89 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_90'] = x__build_single_server__mutmut_90 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_91'] = x__build_single_server__mutmut_91 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_92'] = x__build_single_server__mutmut_92 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_93'] = x__build_single_server__mutmut_93 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_94'] = x__build_single_server__mutmut_94 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_95'] = x__build_single_server__mutmut_95 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_96'] = x__build_single_server__mutmut_96 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_97'] = x__build_single_server__mutmut_97 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_98'] = x__build_single_server__mutmut_98 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_99'] = x__build_single_server__mutmut_99 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_100'] = x__build_single_server__mutmut_100 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_101'] = x__build_single_server__mutmut_101 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_102'] = x__build_single_server__mutmut_102 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_103'] = x__build_single_server__mutmut_103 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_104'] = x__build_single_server__mutmut_104 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_105'] = x__build_single_server__mutmut_105 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_106'] = x__build_single_server__mutmut_106 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_107'] = x__build_single_server__mutmut_107 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_108'] = x__build_single_server__mutmut_108 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_109'] = x__build_single_server__mutmut_109 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_110'] = x__build_single_server__mutmut_110 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_111'] = x__build_single_server__mutmut_111 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_112'] = x__build_single_server__mutmut_112 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_113'] = x__build_single_server__mutmut_113 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_114'] = x__build_single_server__mutmut_114 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_115'] = x__build_single_server__mutmut_115 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_116'] = x__build_single_server__mutmut_116 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_117'] = x__build_single_server__mutmut_117 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_118'] = x__build_single_server__mutmut_118 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_119'] = x__build_single_server__mutmut_119 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_120'] = x__build_single_server__mutmut_120 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_121'] = x__build_single_server__mutmut_121 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_122'] = x__build_single_server__mutmut_122 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_123'] = x__build_single_server__mutmut_123 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_124'] = x__build_single_server__mutmut_124 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_125'] = x__build_single_server__mutmut_125 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_126'] = x__build_single_server__mutmut_126 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_127'] = x__build_single_server__mutmut_127 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_128'] = x__build_single_server__mutmut_128 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_129'] = x__build_single_server__mutmut_129 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_130'] = x__build_single_server__mutmut_130 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_131'] = x__build_single_server__mutmut_131 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_132'] = x__build_single_server__mutmut_132 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_133'] = x__build_single_server__mutmut_133 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_134'] = x__build_single_server__mutmut_134 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_135'] = x__build_single_server__mutmut_135 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_136'] = x__build_single_server__mutmut_136 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_137'] = x__build_single_server__mutmut_137 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_138'] = x__build_single_server__mutmut_138 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_139'] = x__build_single_server__mutmut_139 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_140'] = x__build_single_server__mutmut_140 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_141'] = x__build_single_server__mutmut_141 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_142'] = x__build_single_server__mutmut_142 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_143'] = x__build_single_server__mutmut_143 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_144'] = x__build_single_server__mutmut_144 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_145'] = x__build_single_server__mutmut_145 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_146'] = x__build_single_server__mutmut_146 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_147'] = x__build_single_server__mutmut_147 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_148'] = x__build_single_server__mutmut_148 # type: ignore # mutmut generated
mutants_x__build_single_server__mutmut['x__build_single_server__mutmut_149'] = x__build_single_server__mutmut_149 # type: ignore # mutmut generated
