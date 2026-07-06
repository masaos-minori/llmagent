#!/usr/bin/env python3
"""shared/mcp_config.py
Transport configuration for MCP servers.
Placed in shared/ so tool_executor.py can reference it without depending on agent/.
"""

from __future__ import annotations

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


class TransportType(StrEnum):
    """MCP server transport protocol."""

    HTTP = "http"


class StartupMode(StrEnum):
    """MCP server startup lifecycle mode."""

    PERSISTENT = "persistent"
    SUBPROCESS = "subprocess"


class HealthcheckMode(StrEnum):
    """MCP server health-check strategy."""

    HTTP = "http"


class SecurityProfile(StrEnum):
    """Deployment security profile for MCP auth enforcement."""

    LOCAL = "local"
    PRODUCTION = "production"


@dataclass
class McpServerConfig:
    """Transport configuration for one MCP server."""

    transport: TransportType
    url: str  # base URL (transport=HTTP)
    startup_mode: StartupMode = StartupMode.PERSISTENT
    healthcheck_mode: HealthcheckMode = (
        HealthcheckMode.HTTP
    )  # resolved in __post_init__
    call_timeout_sec: float = 60.0  # per-call timeout for HttpTransport; 0 = no timeout
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

    def __post_init__(self) -> None:
        self._validate_enum_types()
        self._validate_cross_fields()

    def _validate_enum_types(self) -> None:
        if not isinstance(self.transport, TransportType):
            raise ValueError(f"{self.transport!r} is not a valid TransportType")
        if self.startup_mode is not None and not isinstance(
            self.startup_mode, StartupMode
        ):
            raise ValueError(f"{self.startup_mode!r} is not a valid StartupMode")
        if self.healthcheck_mode is not None and not isinstance(
            self.healthcheck_mode, HealthcheckMode
        ):
            raise ValueError(
                f"{self.healthcheck_mode!r} is not a valid HealthcheckMode"
            )

    def _validate_cross_fields(self) -> None:
        key_prefix = f"McpServerConfig[{self.key!r}]" if self.key else "McpServerConfig"

        if self.transport == TransportType.HTTP and not self.url:
            raise ValueError(
                f"{key_prefix}: url must not be empty when transport='http'"
            )
        if self.startup_mode == StartupMode.SUBPROCESS and not self.cmd:
            raise ValueError(
                f"{key_prefix}: cmd must not be empty when startup_mode='subprocess'"
            )

        if self.call_timeout_sec < 0:
            raise ValueError(
                f"{key_prefix}: call_timeout_sec must be >= 0, got {self.call_timeout_sec}"
            )
        if self.startup_timeout_sec < 0:
            raise ValueError(
                f"{key_prefix}: startup_timeout_sec must be >= 0, got {self.startup_timeout_sec}"
            )

        for i, name in enumerate(self.tool_names):
            if not isinstance(name, str) or not name:
                raise ValueError(
                    f"{key_prefix}: tool_names[{i}] must be a non-empty string, got {name!r}"
                )
        if len(self.tool_names) != len(set(self.tool_names)):
            dupes = sorted({n for n in self.tool_names if self.tool_names.count(n) > 1})
            raise ValueError(f"{key_prefix}: duplicate tool_names: {dupes}")

        if not isinstance(self.auth_token, str):
            raise ValueError(
                f"{key_prefix}: auth_token must be str, got {type(self.auth_token).__name__}"
            )

        for k, v in self.env.items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise ValueError(
                    f"{key_prefix}: env must be dict[str, str]; got key={k!r} value={v!r}"
                )

        if self.transport == TransportType.HTTP and self.url:
            parsed = urlparse(self.url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValueError(
                    f"{key_prefix}: url must be a valid HTTP/HTTPS URL, got {self.url!r}"
                )


def _build_mcp_servers(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from [mcp_servers.<key>] sections in *_mcp_server.toml files."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "Add [mcp_servers.<key>] to the server's config/*_mcp_server.toml."
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


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
    # Resolve healthcheck_mode with auto-inference from transport.
    raw_hc = v.get("healthcheck_mode", "")
    if not isinstance(raw_hc, str):
        raise ValueError(
            f"mcp_servers[{key!r}].healthcheck_mode must be str, got {type(raw_hc).__name__}"
        )
    if not raw_hc:
        healthcheck_mode = HealthcheckMode.HTTP
    else:
        healthcheck_mode = HealthcheckMode(raw_hc)
    cmd = list(v.get("cmd", []))
    env = dict(v.get("env", {}))
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        startup_mode=StartupMode(v.get("startup_mode", "persistent")),
        healthcheck_mode=healthcheck_mode,
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        call_timeout_sec=float(v.get("call_timeout_sec", 60.0)),
        role=v.get("role", ""),
        cmd=cmd,
        env=env,
        key=key,
    )
