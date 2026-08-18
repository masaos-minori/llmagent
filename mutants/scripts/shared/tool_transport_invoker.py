#!/usr/bin/env python3
"""scripts/shared/tool_transport_invoker.py — MCP transport invocation layer."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any

import httpx

from shared.http_transport import HttpTransport, TransportError
from shared.mcp_config import (
    McpServerConfig,
    McpServerHealthRegistry,
    McpServerHealthState,
)
from shared.tool_lifecycle import LifecycleProtocol, ServerCooldownError
from shared.transport_dto import ToolCallResult

logger = logging.getLogger(__name__)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁToolTransportInvokerǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolTransportInvokerǁset_lifecycle__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolTransportInvokerǁset_health_registry__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolTransportInvokerǁset_session_id__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolTransportInvokerǁ_ensure_semaphores__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolTransportInvokerǁ_maybe_semaphore__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolTransportInvokerǁ_error_result__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolTransportInvokerǁ_check_health__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolTransportInvokerǁ_increment_counter__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolTransportInvokerǁ_record_success__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolTransportInvokerǁinvoke__mutmut: MutantDict = {}  # type: ignore


class ToolTransportInvoker:
    """Handles transport-level MCP invocation: health, lifecycle, semaphore, call, and recording."""

    @_mutmut_mutated(mutants_xǁToolTransportInvokerǁ__init____mutmut)
    def __init__(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_orig(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_1(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = None
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_2(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = ""
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_3(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = None
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_4(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = None
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_5(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = None
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_6(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(None)
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_7(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits and {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_8(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = ""

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_9(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = None
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_10(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(None)
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_11(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = None
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_12(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) + known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_13(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(None) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_14(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                None,
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_15(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                None,
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_16(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_17(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_18(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "XXtool_concurrency_limits: unknown server key(s) %r;XX"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_19(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "TOOL_CONCURRENCY_LIMITS: UNKNOWN SERVER KEY(S) %R;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_20(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                "XX Semaphore will not be applied for these server keys.XX",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_21(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_22(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " SEMAPHORE WILL NOT BE APPLIED FOR THESE SERVER KEYS.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_23(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(None),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_24(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = None
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_25(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = None
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_26(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = None

    def xǁToolTransportInvokerǁ__init____mutmut_27(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                None, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_28(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, None, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_29(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, None, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_30(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, None, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_31(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=None
            )

    def xǁToolTransportInvokerǁ__init____mutmut_32(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_33(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, key, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_34(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, cfg, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_35(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, timeout_sec=timeout_sec
            )

    def xǁToolTransportInvokerǁ__init____mutmut_36(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, )

    @_mutmut_mutated(mutants_xǁToolTransportInvokerǁset_lifecycle__mutmut)
    def set_lifecycle(self, lifecycle: LifecycleProtocol | None) -> None:
        """Attach a lifecycle protocol for pre-call readiness checks."""
        self._lifecycle = lifecycle

    def xǁToolTransportInvokerǁset_lifecycle__mutmut_orig(self, lifecycle: LifecycleProtocol | None) -> None:
        """Attach a lifecycle protocol for pre-call readiness checks."""
        self._lifecycle = lifecycle

    def xǁToolTransportInvokerǁset_lifecycle__mutmut_1(self, lifecycle: LifecycleProtocol | None) -> None:
        """Attach a lifecycle protocol for pre-call readiness checks."""
        self._lifecycle = None

    @_mutmut_mutated(mutants_xǁToolTransportInvokerǁset_health_registry__mutmut)
    def set_health_registry(self, registry: McpServerHealthRegistry | None) -> None:
        """Attach a health registry for post-call success/failure tracking."""
        self._health_registry = registry

    def xǁToolTransportInvokerǁset_health_registry__mutmut_orig(self, registry: McpServerHealthRegistry | None) -> None:
        """Attach a health registry for post-call success/failure tracking."""
        self._health_registry = registry

    def xǁToolTransportInvokerǁset_health_registry__mutmut_1(self, registry: McpServerHealthRegistry | None) -> None:
        """Attach a health registry for post-call success/failure tracking."""
        self._health_registry = None

    @_mutmut_mutated(mutants_xǁToolTransportInvokerǁset_session_id__mutmut)
    def set_session_id(self, session_id: str) -> None:
        """Propagate the current session ID to all transports."""
        for transport in self._transports.values():
            if isinstance(transport, HttpTransport):
                transport.set_session_id(session_id)

    def xǁToolTransportInvokerǁset_session_id__mutmut_orig(self, session_id: str) -> None:
        """Propagate the current session ID to all transports."""
        for transport in self._transports.values():
            if isinstance(transport, HttpTransport):
                transport.set_session_id(session_id)

    def xǁToolTransportInvokerǁset_session_id__mutmut_1(self, session_id: str) -> None:
        """Propagate the current session ID to all transports."""
        for transport in self._transports.values():
            if isinstance(transport, HttpTransport):
                transport.set_session_id(None)

    @_mutmut_mutated(mutants_xǁToolTransportInvokerǁget_error_counters__mutmut)
    def get_error_counters(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, 0),
                "tool": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_orig(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, 0),
                "tool": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_1(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = None
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, 0),
                "tool": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_2(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) & set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, 0),
                "tool": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_3(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(None) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, 0),
                "tool": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_4(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(None)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, 0),
                "tool": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_5(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "XXtransportXX": self.stat_transport_errors.get(k, 0),
                "tool": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_6(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "TRANSPORT": self.stat_transport_errors.get(k, 0),
                "tool": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_7(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(None, 0),
                "tool": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_8(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, None),
                "tool": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_9(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(0),
                "tool": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_10(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, ),
                "tool": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_11(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, 1),
                "tool": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_12(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, 0),
                "XXtoolXX": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_13(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, 0),
                "TOOL": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_14(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, 0),
                "tool": self.stat_tool_errors.get(None, 0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_15(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, 0),
                "tool": self.stat_tool_errors.get(k, None),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_16(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, 0),
                "tool": self.stat_tool_errors.get(0),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_17(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, 0),
                "tool": self.stat_tool_errors.get(k, ),
            }
            for k in all_keys
        }

    def xǁToolTransportInvokerǁget_error_counters__mutmut_18(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, 0),
                "tool": self.stat_tool_errors.get(k, 1),
            }
            for k in all_keys
        }

    @_mutmut_mutated(mutants_xǁToolTransportInvokerǁ_ensure_semaphores__mutmut)
    def _ensure_semaphores(self) -> None:
        """Lazily create concurrency semaphores from configuration limits."""
        if self._semaphores is None and self._concurrency_limits:
            self._semaphores = {
                key: asyncio.Semaphore(n)
                for key, n in self._concurrency_limits.items()
                if n > 0
            }

    def xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_orig(self) -> None:
        """Lazily create concurrency semaphores from configuration limits."""
        if self._semaphores is None and self._concurrency_limits:
            self._semaphores = {
                key: asyncio.Semaphore(n)
                for key, n in self._concurrency_limits.items()
                if n > 0
            }

    def xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_1(self) -> None:
        """Lazily create concurrency semaphores from configuration limits."""
        if self._semaphores is None or self._concurrency_limits:
            self._semaphores = {
                key: asyncio.Semaphore(n)
                for key, n in self._concurrency_limits.items()
                if n > 0
            }

    def xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_2(self) -> None:
        """Lazily create concurrency semaphores from configuration limits."""
        if self._semaphores is not None and self._concurrency_limits:
            self._semaphores = {
                key: asyncio.Semaphore(n)
                for key, n in self._concurrency_limits.items()
                if n > 0
            }

    def xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_3(self) -> None:
        """Lazily create concurrency semaphores from configuration limits."""
        if self._semaphores is None and self._concurrency_limits:
            self._semaphores = None

    def xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_4(self) -> None:
        """Lazily create concurrency semaphores from configuration limits."""
        if self._semaphores is None and self._concurrency_limits:
            self._semaphores = {
                key: asyncio.Semaphore(None)
                for key, n in self._concurrency_limits.items()
                if n > 0
            }

    def xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_5(self) -> None:
        """Lazily create concurrency semaphores from configuration limits."""
        if self._semaphores is None and self._concurrency_limits:
            self._semaphores = {
                key: asyncio.Semaphore(n)
                for key, n in self._concurrency_limits.items()
                if n >= 0
            }

    def xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_6(self) -> None:
        """Lazily create concurrency semaphores from configuration limits."""
        if self._semaphores is None and self._concurrency_limits:
            self._semaphores = {
                key: asyncio.Semaphore(n)
                for key, n in self._concurrency_limits.items()
                if n > 1
            }

    @staticmethod
    @_mutmut_mutated(mutants_xǁToolTransportInvokerǁ_maybe_semaphore__mutmut)
    def _maybe_semaphore(
        sem: asyncio.Semaphore | None,
    ) -> contextlib.AbstractAsyncContextManager[None]:
        """Return the semaphore as an async context manager, or nullcontext if None."""
        if sem is not None:
            return sem
        return contextlib.nullcontext()

    @staticmethod
    def xǁToolTransportInvokerǁ_maybe_semaphore__mutmut_orig(
        sem: asyncio.Semaphore | None,
    ) -> contextlib.AbstractAsyncContextManager[None]:
        """Return the semaphore as an async context manager, or nullcontext if None."""
        if sem is not None:
            return sem
        return contextlib.nullcontext()

    @staticmethod
    def xǁToolTransportInvokerǁ_maybe_semaphore__mutmut_1(
        sem: asyncio.Semaphore | None,
    ) -> contextlib.AbstractAsyncContextManager[None]:
        """Return the semaphore as an async context manager, or nullcontext if None."""
        if sem is None:
            return sem
        return contextlib.nullcontext()

    def _transport_missing_msg(self, server_key: str) -> str:
        """Build an error message for a missing transport by server key."""
        return f"No transport configured for server {server_key!r}"

    @_mutmut_mutated(mutants_xǁToolTransportInvokerǁ_error_result__mutmut)
    def _error_result(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=True,
            request_id="",
            server_key=server_key,
            source="mcp",
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_orig(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=True,
            request_id="",
            server_key=server_key,
            source="mcp",
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_1(
        self,
        server_key: str,
        output: str,
        error_type: str = "XXtoolXX",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=True,
            request_id="",
            server_key=server_key,
            source="mcp",
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_2(
        self,
        server_key: str,
        output: str,
        error_type: str = "TOOL",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=True,
            request_id="",
            server_key=server_key,
            source="mcp",
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_3(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=None,
            is_error=True,
            request_id="",
            server_key=server_key,
            source="mcp",
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_4(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=None,
            request_id="",
            server_key=server_key,
            source="mcp",
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_5(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=True,
            request_id=None,
            server_key=server_key,
            source="mcp",
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_6(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=True,
            request_id="",
            server_key=None,
            source="mcp",
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_7(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=True,
            request_id="",
            server_key=server_key,
            source=None,
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_8(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=True,
            request_id="",
            server_key=server_key,
            source="mcp",
            error_type=None,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_9(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            is_error=True,
            request_id="",
            server_key=server_key,
            source="mcp",
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_10(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            request_id="",
            server_key=server_key,
            source="mcp",
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_11(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=True,
            server_key=server_key,
            source="mcp",
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_12(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=True,
            request_id="",
            source="mcp",
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_13(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=True,
            request_id="",
            server_key=server_key,
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_14(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=True,
            request_id="",
            server_key=server_key,
            source="mcp",
            )

    def xǁToolTransportInvokerǁ_error_result__mutmut_15(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=False,
            request_id="",
            server_key=server_key,
            source="mcp",
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_16(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=True,
            request_id="XXXX",
            server_key=server_key,
            source="mcp",
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_17(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=True,
            request_id="",
            server_key=server_key,
            source="XXmcpXX",
            error_type=error_type,
        )

    def xǁToolTransportInvokerǁ_error_result__mutmut_18(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=True,
            request_id="",
            server_key=server_key,
            source="MCP",
            error_type=error_type,
        )

    @_mutmut_mutated(mutants_xǁToolTransportInvokerǁ_check_health__mutmut)
    def _check_health(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_orig(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_1(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is not None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_2(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = None
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_3(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(None)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_4(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state != McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_5(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info(None, server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_6(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", None)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_7(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info(server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_8(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", )
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_9(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("XXHealth: %r is HALF_OPEN — allowing trial dispatchXX", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_10(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("health: %r is half_open — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_11(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("HEALTH: %R IS HALF_OPEN — ALLOWING TRIAL DISPATCH", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_12(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(None):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_13(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = None
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_14(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(None)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_15(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(None, msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_16(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, None, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_17(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type=None)
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_18(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(msg, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_19(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, error_type="tool")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_20(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, )
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_21(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="XXtoolXX")
        return None

    def xǁToolTransportInvokerǁ_check_health__mutmut_22(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="TOOL")
        return None

    @staticmethod
    @_mutmut_mutated(mutants_xǁToolTransportInvokerǁ_increment_counter__mutmut)
    def _increment_counter(counter: dict[str, int], key: str) -> None:
        """Increment the count for a key in a get-or-default error counter dict."""
        counter[key] = counter.get(key, 0) + 1

    @staticmethod
    def xǁToolTransportInvokerǁ_increment_counter__mutmut_orig(counter: dict[str, int], key: str) -> None:
        """Increment the count for a key in a get-or-default error counter dict."""
        counter[key] = counter.get(key, 0) + 1

    @staticmethod
    def xǁToolTransportInvokerǁ_increment_counter__mutmut_1(counter: dict[str, int], key: str) -> None:
        """Increment the count for a key in a get-or-default error counter dict."""
        counter[key] = None

    @staticmethod
    def xǁToolTransportInvokerǁ_increment_counter__mutmut_2(counter: dict[str, int], key: str) -> None:
        """Increment the count for a key in a get-or-default error counter dict."""
        counter[key] = counter.get(key, 0) - 1

    @staticmethod
    def xǁToolTransportInvokerǁ_increment_counter__mutmut_3(counter: dict[str, int], key: str) -> None:
        """Increment the count for a key in a get-or-default error counter dict."""
        counter[key] = counter.get(None, 0) + 1

    @staticmethod
    def xǁToolTransportInvokerǁ_increment_counter__mutmut_4(counter: dict[str, int], key: str) -> None:
        """Increment the count for a key in a get-or-default error counter dict."""
        counter[key] = counter.get(key, None) + 1

    @staticmethod
    def xǁToolTransportInvokerǁ_increment_counter__mutmut_5(counter: dict[str, int], key: str) -> None:
        """Increment the count for a key in a get-or-default error counter dict."""
        counter[key] = counter.get(0) + 1

    @staticmethod
    def xǁToolTransportInvokerǁ_increment_counter__mutmut_6(counter: dict[str, int], key: str) -> None:
        """Increment the count for a key in a get-or-default error counter dict."""
        counter[key] = counter.get(key, ) + 1

    @staticmethod
    def xǁToolTransportInvokerǁ_increment_counter__mutmut_7(counter: dict[str, int], key: str) -> None:
        """Increment the count for a key in a get-or-default error counter dict."""
        counter[key] = counter.get(key, 1) + 1

    @staticmethod
    def xǁToolTransportInvokerǁ_increment_counter__mutmut_8(counter: dict[str, int], key: str) -> None:
        """Increment the count for a key in a get-or-default error counter dict."""
        counter[key] = counter.get(key, 0) + 2

    @_mutmut_mutated(mutants_xǁToolTransportInvokerǁ_record_success__mutmut)
    def _record_success(self, server_key: str, result: ToolCallResult) -> None:
        """Record a successful call for health tracking; increment tool error counter on tool errors."""
        if self._health_registry is not None:
            self._health_registry.record_success(server_key)
        if result.is_error and result.error_type == "tool":
            self._increment_counter(self.stat_tool_errors, server_key)

    def xǁToolTransportInvokerǁ_record_success__mutmut_orig(self, server_key: str, result: ToolCallResult) -> None:
        """Record a successful call for health tracking; increment tool error counter on tool errors."""
        if self._health_registry is not None:
            self._health_registry.record_success(server_key)
        if result.is_error and result.error_type == "tool":
            self._increment_counter(self.stat_tool_errors, server_key)

    def xǁToolTransportInvokerǁ_record_success__mutmut_1(self, server_key: str, result: ToolCallResult) -> None:
        """Record a successful call for health tracking; increment tool error counter on tool errors."""
        if self._health_registry is None:
            self._health_registry.record_success(server_key)
        if result.is_error and result.error_type == "tool":
            self._increment_counter(self.stat_tool_errors, server_key)

    def xǁToolTransportInvokerǁ_record_success__mutmut_2(self, server_key: str, result: ToolCallResult) -> None:
        """Record a successful call for health tracking; increment tool error counter on tool errors."""
        if self._health_registry is not None:
            self._health_registry.record_success(None)
        if result.is_error and result.error_type == "tool":
            self._increment_counter(self.stat_tool_errors, server_key)

    def xǁToolTransportInvokerǁ_record_success__mutmut_3(self, server_key: str, result: ToolCallResult) -> None:
        """Record a successful call for health tracking; increment tool error counter on tool errors."""
        if self._health_registry is not None:
            self._health_registry.record_success(server_key)
        if result.is_error or result.error_type == "tool":
            self._increment_counter(self.stat_tool_errors, server_key)

    def xǁToolTransportInvokerǁ_record_success__mutmut_4(self, server_key: str, result: ToolCallResult) -> None:
        """Record a successful call for health tracking; increment tool error counter on tool errors."""
        if self._health_registry is not None:
            self._health_registry.record_success(server_key)
        if result.is_error and result.error_type != "tool":
            self._increment_counter(self.stat_tool_errors, server_key)

    def xǁToolTransportInvokerǁ_record_success__mutmut_5(self, server_key: str, result: ToolCallResult) -> None:
        """Record a successful call for health tracking; increment tool error counter on tool errors."""
        if self._health_registry is not None:
            self._health_registry.record_success(server_key)
        if result.is_error and result.error_type == "XXtoolXX":
            self._increment_counter(self.stat_tool_errors, server_key)

    def xǁToolTransportInvokerǁ_record_success__mutmut_6(self, server_key: str, result: ToolCallResult) -> None:
        """Record a successful call for health tracking; increment tool error counter on tool errors."""
        if self._health_registry is not None:
            self._health_registry.record_success(server_key)
        if result.is_error and result.error_type == "TOOL":
            self._increment_counter(self.stat_tool_errors, server_key)

    def xǁToolTransportInvokerǁ_record_success__mutmut_7(self, server_key: str, result: ToolCallResult) -> None:
        """Record a successful call for health tracking; increment tool error counter on tool errors."""
        if self._health_registry is not None:
            self._health_registry.record_success(server_key)
        if result.is_error and result.error_type == "tool":
            self._increment_counter(None, server_key)

    def xǁToolTransportInvokerǁ_record_success__mutmut_8(self, server_key: str, result: ToolCallResult) -> None:
        """Record a successful call for health tracking; increment tool error counter on tool errors."""
        if self._health_registry is not None:
            self._health_registry.record_success(server_key)
        if result.is_error and result.error_type == "tool":
            self._increment_counter(self.stat_tool_errors, None)

    def xǁToolTransportInvokerǁ_record_success__mutmut_9(self, server_key: str, result: ToolCallResult) -> None:
        """Record a successful call for health tracking; increment tool error counter on tool errors."""
        if self._health_registry is not None:
            self._health_registry.record_success(server_key)
        if result.is_error and result.error_type == "tool":
            self._increment_counter(server_key)

    def xǁToolTransportInvokerǁ_record_success__mutmut_10(self, server_key: str, result: ToolCallResult) -> None:
        """Record a successful call for health tracking; increment tool error counter on tool errors."""
        if self._health_registry is not None:
            self._health_registry.record_success(server_key)
        if result.is_error and result.error_type == "tool":
            self._increment_counter(self.stat_tool_errors, )

    @_mutmut_mutated(mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut)
    def _record_transport_error(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_orig(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_1(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(None, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_2(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, None)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_3(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_4(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, )
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_5(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_6(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = None
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_7(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(None)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_8(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                None, server_key, e, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_9(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", None, e, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_10(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, None, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_11(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, None
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_12(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                server_key, e, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_13(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", e, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_14(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_15(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_16(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "XXtransport failure for %r: %s (state=%s)XX", server_key, e, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_17(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "TRANSPORT FAILURE FOR %R: %S (STATE=%S)", server_key, e, state.value
            )
        return self._error_result(server_key, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_18(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(None, str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_19(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(server_key, None, error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_20(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(server_key, str(e), error_type=None)

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_21(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(str(e), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_22(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(server_key, error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_23(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(server_key, str(e), )

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_24(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(server_key, str(None), error_type="transport")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_25(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(server_key, str(e), error_type="XXtransportXX")

    def xǁToolTransportInvokerǁ_record_transport_error__mutmut_26(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and return an error result."""
        self._increment_counter(self.stat_transport_errors, server_key)
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return self._error_result(server_key, str(e), error_type="TRANSPORT")

    @_mutmut_mutated(mutants_xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut)
    async def _execute_with_semaphore(
        self,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute a transport call under optional concurrency semaphore."""
        async with self._maybe_semaphore(sem):
            return await transport.call(tool_name, args)

    async def xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_orig(
        self,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute a transport call under optional concurrency semaphore."""
        async with self._maybe_semaphore(sem):
            return await transport.call(tool_name, args)

    async def xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_1(
        self,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute a transport call under optional concurrency semaphore."""
        async with self._maybe_semaphore(None):
            return await transport.call(tool_name, args)

    async def xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_2(
        self,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute a transport call under optional concurrency semaphore."""
        async with self._maybe_semaphore(sem):
            return await transport.call(None, args)

    async def xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_3(
        self,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute a transport call under optional concurrency semaphore."""
        async with self._maybe_semaphore(sem):
            return await transport.call(tool_name, None)

    async def xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_4(
        self,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute a transport call under optional concurrency semaphore."""
        async with self._maybe_semaphore(sem):
            return await transport.call(args)

    async def xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_5(
        self,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute a transport call under optional concurrency semaphore."""
        async with self._maybe_semaphore(sem):
            return await transport.call(tool_name, )

    @_mutmut_mutated(mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut)
    async def _invoke_and_record(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(transport, tool_name, args, sem)
            self._record_success(server_key, result)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_orig(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(transport, tool_name, args, sem)
            self._record_success(server_key, result)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_1(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = None
            self._record_success(server_key, result)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_2(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(None, tool_name, args, sem)
            self._record_success(server_key, result)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_3(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(transport, None, args, sem)
            self._record_success(server_key, result)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_4(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(transport, tool_name, None, sem)
            self._record_success(server_key, result)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_5(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(transport, tool_name, args, None)
            self._record_success(server_key, result)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_6(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(tool_name, args, sem)
            self._record_success(server_key, result)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_7(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(transport, args, sem)
            self._record_success(server_key, result)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_8(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(transport, tool_name, sem)
            self._record_success(server_key, result)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_9(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(transport, tool_name, args, )
            self._record_success(server_key, result)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_10(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(transport, tool_name, args, sem)
            self._record_success(None, result)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_11(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(transport, tool_name, args, sem)
            self._record_success(server_key, None)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_12(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(transport, tool_name, args, sem)
            self._record_success(result)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_13(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(transport, tool_name, args, sem)
            self._record_success(server_key, )
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_14(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(transport, tool_name, args, sem)
            self._record_success(server_key, result)
            return result
        except TransportError as e:
            return self._record_transport_error(None, e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_15(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(transport, tool_name, args, sem)
            self._record_success(server_key, result)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, None)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_16(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(transport, tool_name, args, sem)
            self._record_success(server_key, result)
            return result
        except TransportError as e:
            return self._record_transport_error(e)

    async def xǁToolTransportInvokerǁ_invoke_and_record__mutmut_17(
        self,
        server_key: str,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
        try:
            result = await self._execute_with_semaphore(transport, tool_name, args, sem)
            self._record_success(server_key, result)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, )

    @_mutmut_mutated(mutants_xǁToolTransportInvokerǁinvoke__mutmut)
    async def invoke(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_orig(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_1(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(None):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_2(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_3(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(None)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_4(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = None
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_5(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(None)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_6(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(None)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_7(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(None, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_8(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, None, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_9(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type=None)

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_10(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_11(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_12(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, )

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_13(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="XXtransportXX")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_14(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="TRANSPORT")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_15(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = None
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_16(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(None)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_17(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is not None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_18(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = None
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_19(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(None)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_20(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(None)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_21(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(None, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_22(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, None, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_23(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type=None)

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_24(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_25(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_26(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_27(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="XXtoolXX")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_28(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="TOOL")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_29(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = None
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_30(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(None)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_31(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores and {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_32(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            None, transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_33(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, None, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_34(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, None, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_35(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, None, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_36(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, None
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_37(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            transport, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_38(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, tool_name, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_39(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, args, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_40(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, sem
        )

    async def xǁToolTransportInvokerǁinvoke__mutmut_41(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except ServerCooldownError as e:
                msg = str(e)
                logger.warning(msg)
                return self._error_result(server_key, msg, error_type="transport")

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, )

mutants_xǁToolTransportInvokerǁ__init____mutmut['_mutmut_orig'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_1'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_2'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_3'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_4'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_5'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_6'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_7'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_8'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_9'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_10'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_11'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_12'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_13'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_14'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_15'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_15 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_16'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_16 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_17'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_17 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_18'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_18 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_19'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_19 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_20'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_20 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_21'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_21 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_22'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_22 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_23'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_23 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_24'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_24 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_25'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_25 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_26'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_26 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_27'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_27 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_28'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_28 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_29'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_29 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_30'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_30 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_31'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_31 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_32'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_32 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_33'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_33 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_34'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_34 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_35'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_35 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ__init____mutmut['xǁToolTransportInvokerǁ__init____mutmut_36'] = ToolTransportInvoker.xǁToolTransportInvokerǁ__init____mutmut_36 # type: ignore # mutmut generated

mutants_xǁToolTransportInvokerǁset_lifecycle__mutmut['_mutmut_orig'] = ToolTransportInvoker.xǁToolTransportInvokerǁset_lifecycle__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁset_lifecycle__mutmut['xǁToolTransportInvokerǁset_lifecycle__mutmut_1'] = ToolTransportInvoker.xǁToolTransportInvokerǁset_lifecycle__mutmut_1 # type: ignore # mutmut generated

mutants_xǁToolTransportInvokerǁset_health_registry__mutmut['_mutmut_orig'] = ToolTransportInvoker.xǁToolTransportInvokerǁset_health_registry__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁset_health_registry__mutmut['xǁToolTransportInvokerǁset_health_registry__mutmut_1'] = ToolTransportInvoker.xǁToolTransportInvokerǁset_health_registry__mutmut_1 # type: ignore # mutmut generated

mutants_xǁToolTransportInvokerǁset_session_id__mutmut['_mutmut_orig'] = ToolTransportInvoker.xǁToolTransportInvokerǁset_session_id__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁset_session_id__mutmut['xǁToolTransportInvokerǁset_session_id__mutmut_1'] = ToolTransportInvoker.xǁToolTransportInvokerǁset_session_id__mutmut_1 # type: ignore # mutmut generated

mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['_mutmut_orig'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_1'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_2'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_3'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_4'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_5'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_6'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_7'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_8'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_9'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_10'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_11'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_12'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_13'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_14'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_15'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_15 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_16'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_16 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_17'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_17 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁget_error_counters__mutmut['xǁToolTransportInvokerǁget_error_counters__mutmut_18'] = ToolTransportInvoker.xǁToolTransportInvokerǁget_error_counters__mutmut_18 # type: ignore # mutmut generated

mutants_xǁToolTransportInvokerǁ_ensure_semaphores__mutmut['_mutmut_orig'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_ensure_semaphores__mutmut['xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_1'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_ensure_semaphores__mutmut['xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_2'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_ensure_semaphores__mutmut['xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_3'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_ensure_semaphores__mutmut['xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_4'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_ensure_semaphores__mutmut['xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_5'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_ensure_semaphores__mutmut['xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_6'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_ensure_semaphores__mutmut_6 # type: ignore # mutmut generated

mutants_xǁToolTransportInvokerǁ_maybe_semaphore__mutmut['_mutmut_orig'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_maybe_semaphore__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_maybe_semaphore__mutmut['xǁToolTransportInvokerǁ_maybe_semaphore__mutmut_1'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_maybe_semaphore__mutmut_1 # type: ignore # mutmut generated

mutants_xǁToolTransportInvokerǁ_error_result__mutmut['_mutmut_orig'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_1'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_2'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_3'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_4'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_5'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_6'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_7'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_8'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_9'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_10'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_11'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_12'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_13'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_14'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_15'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_15 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_16'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_16 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_17'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_17 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_error_result__mutmut['xǁToolTransportInvokerǁ_error_result__mutmut_18'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_error_result__mutmut_18 # type: ignore # mutmut generated

mutants_xǁToolTransportInvokerǁ_check_health__mutmut['_mutmut_orig'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_1'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_2'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_3'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_4'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_5'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_6'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_7'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_8'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_9'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_10'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_11'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_12'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_13'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_14'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_15'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_15 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_16'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_16 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_17'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_17 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_18'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_18 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_19'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_19 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_20'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_20 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_21'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_21 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_check_health__mutmut['xǁToolTransportInvokerǁ_check_health__mutmut_22'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_check_health__mutmut_22 # type: ignore # mutmut generated

mutants_xǁToolTransportInvokerǁ_increment_counter__mutmut['_mutmut_orig'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_increment_counter__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_increment_counter__mutmut['xǁToolTransportInvokerǁ_increment_counter__mutmut_1'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_increment_counter__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_increment_counter__mutmut['xǁToolTransportInvokerǁ_increment_counter__mutmut_2'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_increment_counter__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_increment_counter__mutmut['xǁToolTransportInvokerǁ_increment_counter__mutmut_3'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_increment_counter__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_increment_counter__mutmut['xǁToolTransportInvokerǁ_increment_counter__mutmut_4'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_increment_counter__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_increment_counter__mutmut['xǁToolTransportInvokerǁ_increment_counter__mutmut_5'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_increment_counter__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_increment_counter__mutmut['xǁToolTransportInvokerǁ_increment_counter__mutmut_6'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_increment_counter__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_increment_counter__mutmut['xǁToolTransportInvokerǁ_increment_counter__mutmut_7'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_increment_counter__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_increment_counter__mutmut['xǁToolTransportInvokerǁ_increment_counter__mutmut_8'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_increment_counter__mutmut_8 # type: ignore # mutmut generated

mutants_xǁToolTransportInvokerǁ_record_success__mutmut['_mutmut_orig'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_success__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_success__mutmut['xǁToolTransportInvokerǁ_record_success__mutmut_1'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_success__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_success__mutmut['xǁToolTransportInvokerǁ_record_success__mutmut_2'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_success__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_success__mutmut['xǁToolTransportInvokerǁ_record_success__mutmut_3'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_success__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_success__mutmut['xǁToolTransportInvokerǁ_record_success__mutmut_4'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_success__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_success__mutmut['xǁToolTransportInvokerǁ_record_success__mutmut_5'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_success__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_success__mutmut['xǁToolTransportInvokerǁ_record_success__mutmut_6'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_success__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_success__mutmut['xǁToolTransportInvokerǁ_record_success__mutmut_7'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_success__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_success__mutmut['xǁToolTransportInvokerǁ_record_success__mutmut_8'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_success__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_success__mutmut['xǁToolTransportInvokerǁ_record_success__mutmut_9'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_success__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_success__mutmut['xǁToolTransportInvokerǁ_record_success__mutmut_10'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_success__mutmut_10 # type: ignore # mutmut generated

mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['_mutmut_orig'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_1'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_2'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_3'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_4'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_5'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_6'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_7'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_8'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_9'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_10'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_11'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_12'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_13'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_14'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_15'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_15 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_16'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_16 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_17'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_17 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_18'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_18 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_19'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_19 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_20'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_20 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_21'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_21 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_22'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_22 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_23'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_23 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_24'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_24 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_25'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_25 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_record_transport_error__mutmut['xǁToolTransportInvokerǁ_record_transport_error__mutmut_26'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_record_transport_error__mutmut_26 # type: ignore # mutmut generated

mutants_xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut['_mutmut_orig'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut['xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_1'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut['xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_2'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut['xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_3'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut['xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_4'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut['xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_5'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_execute_with_semaphore__mutmut_5 # type: ignore # mutmut generated

mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['_mutmut_orig'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_1'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_2'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_3'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_4'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_5'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_6'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_7'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_8'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_9'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_10'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_11'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_12'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_13'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_14'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_15'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_15 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_16'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_16 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁ_invoke_and_record__mutmut['xǁToolTransportInvokerǁ_invoke_and_record__mutmut_17'] = ToolTransportInvoker.xǁToolTransportInvokerǁ_invoke_and_record__mutmut_17 # type: ignore # mutmut generated

mutants_xǁToolTransportInvokerǁinvoke__mutmut['_mutmut_orig'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_1'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_2'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_3'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_4'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_5'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_6'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_7'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_8'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_9'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_10'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_11'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_12'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_13'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_14'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_15'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_15 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_16'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_16 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_17'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_17 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_18'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_18 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_19'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_19 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_20'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_20 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_21'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_21 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_22'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_22 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_23'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_23 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_24'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_24 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_25'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_25 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_26'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_26 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_27'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_27 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_28'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_28 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_29'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_29 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_30'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_30 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_31'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_31 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_32'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_32 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_33'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_33 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_34'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_34 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_35'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_35 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_36'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_36 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_37'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_37 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_38'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_38 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_39'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_39 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_40'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_40 # type: ignore # mutmut generated
mutants_xǁToolTransportInvokerǁinvoke__mutmut['xǁToolTransportInvokerǁinvoke__mutmut_41'] = ToolTransportInvoker.xǁToolTransportInvokerǁinvoke__mutmut_41 # type: ignore # mutmut generated
