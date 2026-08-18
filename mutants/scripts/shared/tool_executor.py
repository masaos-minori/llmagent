#!/usr/bin/env python3
"""scripts/shared/tool_executor.py

MCP tool execution layer.

Provides HttpTransport implementation for POST /v1/call_tool over httpx.

ToolExecutor routes tool calls to the appropriate server via ToolRouteResolver,
applies TTL caching on successful results, and delegates execution to the
configured transport.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import OrderedDict
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shared.runtime_tool_registry import RuntimeToolRegistry

import httpx

from shared.http_transport import (  # noqa: F401 -- re-exported: tests/shared/test_tool_executor.py imports TransportError from this module
    HttpTransport,
    TransportError,
)
from shared.json_utils import dumps as _json_dumps
from shared.mcp_config import (
    McpServerConfig,
    StartupMode,
)
from shared.route_resolver import ToolRouteResolver
from shared.tool_cache import CacheEntry
from shared.tool_executor_helpers import is_side_effect
from shared.tool_lifecycle import LifecycleProtocol
from shared.tool_transport_invoker import ToolTransportInvoker
from shared.transport_dto import ToolCallResult

logger = logging.getLogger(__name__)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁToolExecutorǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolExecutorǁapply_config__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolExecutorǁset_runtime_registry__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolExecutorǁ_check_startup_mode__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolExecutorǁ_resolve_transport__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolExecutorǁ_run_gate_chain__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolExecutorǁ_raw_execute__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolExecutorǁ_store_and_evict__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolExecutorǁexecute__mutmut: MutantDict = {}  # type: ignore


# ─────────────────────────────────────────────────────────────────────────────
# ToolExecutor
# ─────────────────────────────────────────────────────────────────────────────


class ToolExecutor(ToolTransportInvoker):
    """Routes tool calls to the appropriate MCP server transport with TTL caching; only successful results are cached."""

    @_mutmut_mutated(mutants_xǁToolExecutorǁ__init____mutmut)
    def __init__(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_orig(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_1(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 1,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_2(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(None, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_3(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, None, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_4(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, None, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_5(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, None)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_6(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_7(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_8(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_9(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, )
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_10(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = None
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_11(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = None
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_12(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = None
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_13(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = None
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_14(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = None
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_15(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 1
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_16(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = None

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_17(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = None

    def xǁToolExecutorǁ__init____mutmut_18(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            None, discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_19(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=None
        )

    def xǁToolExecutorǁ__init____mutmut_20(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            discovery_map=discovery_map or {}
        )

    def xǁToolExecutorǁ__init____mutmut_21(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, )

    def xǁToolExecutorǁ__init____mutmut_22(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize with HTTP client, cache settings, and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map and {}
        )

    @_mutmut_mutated(mutants_xǁToolExecutorǁapply_config__mutmut)
    def apply_config(self, *, cache_ttl: float | None = None) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        if cache_ttl is not None:
            self._cache_ttl = cache_ttl

    def xǁToolExecutorǁapply_config__mutmut_orig(self, *, cache_ttl: float | None = None) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        if cache_ttl is not None:
            self._cache_ttl = cache_ttl

    def xǁToolExecutorǁapply_config__mutmut_1(self, *, cache_ttl: float | None = None) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        if cache_ttl is None:
            self._cache_ttl = cache_ttl

    def xǁToolExecutorǁapply_config__mutmut_2(self, *, cache_ttl: float | None = None) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        if cache_ttl is not None:
            self._cache_ttl = None

    @_mutmut_mutated(mutants_xǁToolExecutorǁset_runtime_registry__mutmut)
    def set_runtime_registry(self, registry: RuntimeToolRegistry) -> None:
        """Wire RuntimeToolRegistry into the existing resolver after discovery completes."""
        self._resolver.set_runtime_registry(registry)

    def xǁToolExecutorǁset_runtime_registry__mutmut_orig(self, registry: RuntimeToolRegistry) -> None:
        """Wire RuntimeToolRegistry into the existing resolver after discovery completes."""
        self._resolver.set_runtime_registry(registry)

    def xǁToolExecutorǁset_runtime_registry__mutmut_1(self, registry: RuntimeToolRegistry) -> None:
        """Wire RuntimeToolRegistry into the existing resolver after discovery completes."""
        self._resolver.set_runtime_registry(None)

    @_mutmut_mutated(mutants_xǁToolExecutorǁ_check_startup_mode__mutmut)
    def _check_startup_mode(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is not None and cfg.startup_mode == StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolExecutorǁ_check_startup_mode__mutmut_orig(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is not None and cfg.startup_mode == StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolExecutorǁ_check_startup_mode__mutmut_1(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = None
        if cfg is not None and cfg.startup_mode == StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolExecutorǁ_check_startup_mode__mutmut_2(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(None)
        if cfg is not None and cfg.startup_mode == StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolExecutorǁ_check_startup_mode__mutmut_3(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is not None or cfg.startup_mode == StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolExecutorǁ_check_startup_mode__mutmut_4(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is None and cfg.startup_mode == StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolExecutorǁ_check_startup_mode__mutmut_5(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is not None and cfg.startup_mode != StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolExecutorǁ_check_startup_mode__mutmut_6(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is not None and cfg.startup_mode == StartupMode.NONE:
            msg = None
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolExecutorǁ_check_startup_mode__mutmut_7(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is not None and cfg.startup_mode == StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(None)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def xǁToolExecutorǁ_check_startup_mode__mutmut_8(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is not None and cfg.startup_mode == StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(msg)
            return self._error_result(None, msg, error_type="tool")
        return None

    def xǁToolExecutorǁ_check_startup_mode__mutmut_9(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is not None and cfg.startup_mode == StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(msg)
            return self._error_result(server_key, None, error_type="tool")
        return None

    def xǁToolExecutorǁ_check_startup_mode__mutmut_10(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is not None and cfg.startup_mode == StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type=None)
        return None

    def xǁToolExecutorǁ_check_startup_mode__mutmut_11(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is not None and cfg.startup_mode == StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(msg)
            return self._error_result(msg, error_type="tool")
        return None

    def xǁToolExecutorǁ_check_startup_mode__mutmut_12(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is not None and cfg.startup_mode == StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(msg)
            return self._error_result(server_key, error_type="tool")
        return None

    def xǁToolExecutorǁ_check_startup_mode__mutmut_13(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is not None and cfg.startup_mode == StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(msg)
            return self._error_result(server_key, msg, )
        return None

    def xǁToolExecutorǁ_check_startup_mode__mutmut_14(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is not None and cfg.startup_mode == StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="XXtoolXX")
        return None

    def xǁToolExecutorǁ_check_startup_mode__mutmut_15(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is not None and cfg.startup_mode == StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="TOOL")
        return None

    @_mutmut_mutated(mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut)
    async def _ensure_lifecycle_ready(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is None:
            return None
        try:
            await self._lifecycle.ensure_ready(server_key)
        except (OSError, RuntimeError) as e:
            msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
            logger.error(msg)
            if self._health_registry is not None:
                self._health_registry.record_failure(server_key)
            return self._error_result(server_key, msg, error_type="transport")
        return None

    async def xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_orig(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is None:
            return None
        try:
            await self._lifecycle.ensure_ready(server_key)
        except (OSError, RuntimeError) as e:
            msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
            logger.error(msg)
            if self._health_registry is not None:
                self._health_registry.record_failure(server_key)
            return self._error_result(server_key, msg, error_type="transport")
        return None

    async def xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_1(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is not None:
            return None
        try:
            await self._lifecycle.ensure_ready(server_key)
        except (OSError, RuntimeError) as e:
            msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
            logger.error(msg)
            if self._health_registry is not None:
                self._health_registry.record_failure(server_key)
            return self._error_result(server_key, msg, error_type="transport")
        return None

    async def xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_2(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is None:
            return None
        try:
            await self._lifecycle.ensure_ready(None)
        except (OSError, RuntimeError) as e:
            msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
            logger.error(msg)
            if self._health_registry is not None:
                self._health_registry.record_failure(server_key)
            return self._error_result(server_key, msg, error_type="transport")
        return None

    async def xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_3(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is None:
            return None
        try:
            await self._lifecycle.ensure_ready(server_key)
        except (OSError, RuntimeError) as e:
            msg = None
            logger.error(msg)
            if self._health_registry is not None:
                self._health_registry.record_failure(server_key)
            return self._error_result(server_key, msg, error_type="transport")
        return None

    async def xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_4(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is None:
            return None
        try:
            await self._lifecycle.ensure_ready(server_key)
        except (OSError, RuntimeError) as e:
            msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
            logger.error(None)
            if self._health_registry is not None:
                self._health_registry.record_failure(server_key)
            return self._error_result(server_key, msg, error_type="transport")
        return None

    async def xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_5(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is None:
            return None
        try:
            await self._lifecycle.ensure_ready(server_key)
        except (OSError, RuntimeError) as e:
            msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
            logger.error(msg)
            if self._health_registry is None:
                self._health_registry.record_failure(server_key)
            return self._error_result(server_key, msg, error_type="transport")
        return None

    async def xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_6(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is None:
            return None
        try:
            await self._lifecycle.ensure_ready(server_key)
        except (OSError, RuntimeError) as e:
            msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
            logger.error(msg)
            if self._health_registry is not None:
                self._health_registry.record_failure(None)
            return self._error_result(server_key, msg, error_type="transport")
        return None

    async def xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_7(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is None:
            return None
        try:
            await self._lifecycle.ensure_ready(server_key)
        except (OSError, RuntimeError) as e:
            msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
            logger.error(msg)
            if self._health_registry is not None:
                self._health_registry.record_failure(server_key)
            return self._error_result(None, msg, error_type="transport")
        return None

    async def xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_8(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is None:
            return None
        try:
            await self._lifecycle.ensure_ready(server_key)
        except (OSError, RuntimeError) as e:
            msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
            logger.error(msg)
            if self._health_registry is not None:
                self._health_registry.record_failure(server_key)
            return self._error_result(server_key, None, error_type="transport")
        return None

    async def xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_9(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is None:
            return None
        try:
            await self._lifecycle.ensure_ready(server_key)
        except (OSError, RuntimeError) as e:
            msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
            logger.error(msg)
            if self._health_registry is not None:
                self._health_registry.record_failure(server_key)
            return self._error_result(server_key, msg, error_type=None)
        return None

    async def xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_10(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is None:
            return None
        try:
            await self._lifecycle.ensure_ready(server_key)
        except (OSError, RuntimeError) as e:
            msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
            logger.error(msg)
            if self._health_registry is not None:
                self._health_registry.record_failure(server_key)
            return self._error_result(msg, error_type="transport")
        return None

    async def xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_11(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is None:
            return None
        try:
            await self._lifecycle.ensure_ready(server_key)
        except (OSError, RuntimeError) as e:
            msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
            logger.error(msg)
            if self._health_registry is not None:
                self._health_registry.record_failure(server_key)
            return self._error_result(server_key, error_type="transport")
        return None

    async def xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_12(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is None:
            return None
        try:
            await self._lifecycle.ensure_ready(server_key)
        except (OSError, RuntimeError) as e:
            msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
            logger.error(msg)
            if self._health_registry is not None:
                self._health_registry.record_failure(server_key)
            return self._error_result(server_key, msg, )
        return None

    async def xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_13(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is None:
            return None
        try:
            await self._lifecycle.ensure_ready(server_key)
        except (OSError, RuntimeError) as e:
            msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
            logger.error(msg)
            if self._health_registry is not None:
                self._health_registry.record_failure(server_key)
            return self._error_result(server_key, msg, error_type="XXtransportXX")
        return None

    async def xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_14(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is None:
            return None
        try:
            await self._lifecycle.ensure_ready(server_key)
        except (OSError, RuntimeError) as e:
            msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
            logger.error(msg)
            if self._health_registry is not None:
                self._health_registry.record_failure(server_key)
            return self._error_result(server_key, msg, error_type="TRANSPORT")
        return None

    @_mutmut_mutated(mutants_xǁToolExecutorǁ_resolve_transport__mutmut)
    def _resolve_transport(self, server_key: str) -> HttpTransport | None:
        """Resolve the transport for a server key; returns None if missing."""
        return self._transports.get(server_key)

    def xǁToolExecutorǁ_resolve_transport__mutmut_orig(self, server_key: str) -> HttpTransport | None:
        """Resolve the transport for a server key; returns None if missing."""
        return self._transports.get(server_key)

    def xǁToolExecutorǁ_resolve_transport__mutmut_1(self, server_key: str) -> HttpTransport | None:
        """Resolve the transport for a server key; returns None if missing."""
        return self._transports.get(None)

    @_mutmut_mutated(mutants_xǁToolExecutorǁ_run_gate_chain__mutmut)
    def _run_gate_chain(self, server_key: str) -> ToolCallResult | None:
        """Run the startup-mode and health gates in order; return the first error, or None if both pass.

        The lifecycle gate (_ensure_lifecycle_ready) is async and stays a separate
        await in _raw_execute immediately after this call, preserving call order.
        """
        if err := self._check_startup_mode(server_key):
            return err
        if err := self._check_health(server_key):
            return err
        return None

    def xǁToolExecutorǁ_run_gate_chain__mutmut_orig(self, server_key: str) -> ToolCallResult | None:
        """Run the startup-mode and health gates in order; return the first error, or None if both pass.

        The lifecycle gate (_ensure_lifecycle_ready) is async and stays a separate
        await in _raw_execute immediately after this call, preserving call order.
        """
        if err := self._check_startup_mode(server_key):
            return err
        if err := self._check_health(server_key):
            return err
        return None

    def xǁToolExecutorǁ_run_gate_chain__mutmut_1(self, server_key: str) -> ToolCallResult | None:
        """Run the startup-mode and health gates in order; return the first error, or None if both pass.

        The lifecycle gate (_ensure_lifecycle_ready) is async and stays a separate
        await in _raw_execute immediately after this call, preserving call order.
        """
        if err := self._check_startup_mode(None):
            return err
        if err := self._check_health(server_key):
            return err
        return None

    def xǁToolExecutorǁ_run_gate_chain__mutmut_2(self, server_key: str) -> ToolCallResult | None:
        """Run the startup-mode and health gates in order; return the first error, or None if both pass.

        The lifecycle gate (_ensure_lifecycle_ready) is async and stays a separate
        await in _raw_execute immediately after this call, preserving call order.
        """
        if err := self._check_startup_mode(server_key):
            return err
        if err := self._check_health(None):
            return err
        return None

    @_mutmut_mutated(mutants_xǁToolExecutorǁ_raw_execute__mutmut)
    async def _raw_execute(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_orig(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_1(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = None

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_2(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(None)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_3(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(None):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_4(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = None
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_5(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(None)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_6(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_7(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = None
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_8(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(None)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_9(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is not None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_10(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                None, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_11(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, None, error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_12(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type=None
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_13(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_14(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_15(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_16(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(None), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_17(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="XXtoolXX"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_18(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="TOOL"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_19(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = None
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_20(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(None)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_21(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores and {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_22(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            None, transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_23(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, None, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_24(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, None, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_25(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, None, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_26(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, None
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_27(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            transport, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_28(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, tool_name, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_29(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, args, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_30(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, sem
        )

    async def xǁToolExecutorǁ_raw_execute__mutmut_31(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, )

    @_mutmut_mutated(mutants_xǁToolExecutorǁ_execute_with_cache__mutmut)
    async def _execute_with_cache(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_orig(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_1(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = None
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_2(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(None)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_3(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(None)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_4(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_5(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = None
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_6(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() + cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_7(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age <= self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_8(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(None)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_9(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits = 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_10(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits -= 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_11(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 2
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_12(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info(None, tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_13(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", None, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_14(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, None)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_15(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info(tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_16(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_17(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, )
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_18(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("XXTool cache hit: %s (age=%.0fs)XX", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_19(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_20(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("TOOL CACHE HIT: %S (AGE=%.0FS)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_21(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=None,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_22(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=None,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_23(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id=None,
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_24(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=None,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_25(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source=None,
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_26(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type=None,
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_27(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_28(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_29(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_30(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_31(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_32(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_33(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="XXXX",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_34(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="XXcacheXX",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_35(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="CACHE",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_36(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="XXtoolXX" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_37(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="TOOL" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_38(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "XXXX",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_39(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = None
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_40(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            None, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_41(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, None, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_42(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, None
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_43(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_44(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_45(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_46(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_47(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(None, result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_48(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, None)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_49(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(result)
        return result

    async def xǁToolExecutorǁ_execute_with_cache__mutmut_50(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key=cached.server_key,
                    source="cache",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, )
        return result

    @_mutmut_mutated(mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut)
    async def _execute_with_stampede_protection(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_orig(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_1(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = None
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_2(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(None)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_3(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None or not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_4(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_5(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_6(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None or inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_7(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_8(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = None
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_9(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = None
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_10(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = None
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_11(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = None
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_12(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(None, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_13(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, None)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_14(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_15(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, )
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_16(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_17(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(None)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_18(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_19(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(None)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_20(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(None, None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_21(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(None)

    async def xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_22(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, )

    @_mutmut_mutated(mutants_xǁToolExecutorǁ_store_and_evict__mutmut)
    def _store_and_evict(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_orig(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_1(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = None
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_2(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=None,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_3(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=None,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_4(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=None,
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_5(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=None,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_6(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_7(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_8(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_9(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_10(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 or len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_11(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size >= 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_12(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 1 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_13(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) >= self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_14(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = None
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_15(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=None)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_16(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=True)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_17(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug(None, evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_18(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", None)

    def xǁToolExecutorǁ_store_and_evict__mutmut_19(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug(evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_20(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", )

    def xǁToolExecutorǁ_store_and_evict__mutmut_21(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("XXTool cache LRU evict: %rXX", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_22(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("tool cache lru evict: %r", evicted_key)

    def xǁToolExecutorǁ_store_and_evict__mutmut_23(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("TOOL CACHE LRU EVICT: %R", evicted_key)

    @_mutmut_mutated(mutants_xǁToolExecutorǁexecute__mutmut)
    async def execute(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool. Side-effecting tools bypass the cache and always
        re-execute; other tools use the cache."""
        if is_side_effect(tool_name):
            return await self._raw_execute(tool_name, args)
        return await self._execute_with_cache(tool_name, args)

    async def xǁToolExecutorǁexecute__mutmut_orig(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool. Side-effecting tools bypass the cache and always
        re-execute; other tools use the cache."""
        if is_side_effect(tool_name):
            return await self._raw_execute(tool_name, args)
        return await self._execute_with_cache(tool_name, args)

    async def xǁToolExecutorǁexecute__mutmut_1(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool. Side-effecting tools bypass the cache and always
        re-execute; other tools use the cache."""
        if is_side_effect(None):
            return await self._raw_execute(tool_name, args)
        return await self._execute_with_cache(tool_name, args)

    async def xǁToolExecutorǁexecute__mutmut_2(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool. Side-effecting tools bypass the cache and always
        re-execute; other tools use the cache."""
        if is_side_effect(tool_name):
            return await self._raw_execute(None, args)
        return await self._execute_with_cache(tool_name, args)

    async def xǁToolExecutorǁexecute__mutmut_3(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool. Side-effecting tools bypass the cache and always
        re-execute; other tools use the cache."""
        if is_side_effect(tool_name):
            return await self._raw_execute(tool_name, None)
        return await self._execute_with_cache(tool_name, args)

    async def xǁToolExecutorǁexecute__mutmut_4(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool. Side-effecting tools bypass the cache and always
        re-execute; other tools use the cache."""
        if is_side_effect(tool_name):
            return await self._raw_execute(args)
        return await self._execute_with_cache(tool_name, args)

    async def xǁToolExecutorǁexecute__mutmut_5(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool. Side-effecting tools bypass the cache and always
        re-execute; other tools use the cache."""
        if is_side_effect(tool_name):
            return await self._raw_execute(tool_name, )
        return await self._execute_with_cache(tool_name, args)

    async def xǁToolExecutorǁexecute__mutmut_6(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool. Side-effecting tools bypass the cache and always
        re-execute; other tools use the cache."""
        if is_side_effect(tool_name):
            return await self._raw_execute(tool_name, args)
        return await self._execute_with_cache(None, args)

    async def xǁToolExecutorǁexecute__mutmut_7(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool. Side-effecting tools bypass the cache and always
        re-execute; other tools use the cache."""
        if is_side_effect(tool_name):
            return await self._raw_execute(tool_name, args)
        return await self._execute_with_cache(tool_name, None)

    async def xǁToolExecutorǁexecute__mutmut_8(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool. Side-effecting tools bypass the cache and always
        re-execute; other tools use the cache."""
        if is_side_effect(tool_name):
            return await self._raw_execute(tool_name, args)
        return await self._execute_with_cache(args)

    async def xǁToolExecutorǁexecute__mutmut_9(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool. Side-effecting tools bypass the cache and always
        re-execute; other tools use the cache."""
        if is_side_effect(tool_name):
            return await self._raw_execute(tool_name, args)
        return await self._execute_with_cache(tool_name, )

    def clear_cache(self) -> None:
        """Evict all cached tool results."""
        self._cache.clear()

    def get_error_counters(self) -> dict[str, dict[str, int]]:
        """Return per-server error counters: {server_key: {"transport": N, "tool": N}}."""
        return super().get_error_counters()

mutants_xǁToolExecutorǁ__init____mutmut['_mutmut_orig'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_1'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_2'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_3'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_4'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_5'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_6'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_7'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_8'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_9'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_10'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_11'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_12'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_13'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_14'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_15'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_15 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_16'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_16 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_17'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_17 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_18'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_18 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_19'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_19 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_20'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_20 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_21'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_21 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ__init____mutmut['xǁToolExecutorǁ__init____mutmut_22'] = ToolExecutor.xǁToolExecutorǁ__init____mutmut_22 # type: ignore # mutmut generated

mutants_xǁToolExecutorǁapply_config__mutmut['_mutmut_orig'] = ToolExecutor.xǁToolExecutorǁapply_config__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolExecutorǁapply_config__mutmut['xǁToolExecutorǁapply_config__mutmut_1'] = ToolExecutor.xǁToolExecutorǁapply_config__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁapply_config__mutmut['xǁToolExecutorǁapply_config__mutmut_2'] = ToolExecutor.xǁToolExecutorǁapply_config__mutmut_2 # type: ignore # mutmut generated

mutants_xǁToolExecutorǁset_runtime_registry__mutmut['_mutmut_orig'] = ToolExecutor.xǁToolExecutorǁset_runtime_registry__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolExecutorǁset_runtime_registry__mutmut['xǁToolExecutorǁset_runtime_registry__mutmut_1'] = ToolExecutor.xǁToolExecutorǁset_runtime_registry__mutmut_1 # type: ignore # mutmut generated

mutants_xǁToolExecutorǁ_check_startup_mode__mutmut['_mutmut_orig'] = ToolExecutor.xǁToolExecutorǁ_check_startup_mode__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_check_startup_mode__mutmut['xǁToolExecutorǁ_check_startup_mode__mutmut_1'] = ToolExecutor.xǁToolExecutorǁ_check_startup_mode__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_check_startup_mode__mutmut['xǁToolExecutorǁ_check_startup_mode__mutmut_2'] = ToolExecutor.xǁToolExecutorǁ_check_startup_mode__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_check_startup_mode__mutmut['xǁToolExecutorǁ_check_startup_mode__mutmut_3'] = ToolExecutor.xǁToolExecutorǁ_check_startup_mode__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_check_startup_mode__mutmut['xǁToolExecutorǁ_check_startup_mode__mutmut_4'] = ToolExecutor.xǁToolExecutorǁ_check_startup_mode__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_check_startup_mode__mutmut['xǁToolExecutorǁ_check_startup_mode__mutmut_5'] = ToolExecutor.xǁToolExecutorǁ_check_startup_mode__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_check_startup_mode__mutmut['xǁToolExecutorǁ_check_startup_mode__mutmut_6'] = ToolExecutor.xǁToolExecutorǁ_check_startup_mode__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_check_startup_mode__mutmut['xǁToolExecutorǁ_check_startup_mode__mutmut_7'] = ToolExecutor.xǁToolExecutorǁ_check_startup_mode__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_check_startup_mode__mutmut['xǁToolExecutorǁ_check_startup_mode__mutmut_8'] = ToolExecutor.xǁToolExecutorǁ_check_startup_mode__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_check_startup_mode__mutmut['xǁToolExecutorǁ_check_startup_mode__mutmut_9'] = ToolExecutor.xǁToolExecutorǁ_check_startup_mode__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_check_startup_mode__mutmut['xǁToolExecutorǁ_check_startup_mode__mutmut_10'] = ToolExecutor.xǁToolExecutorǁ_check_startup_mode__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_check_startup_mode__mutmut['xǁToolExecutorǁ_check_startup_mode__mutmut_11'] = ToolExecutor.xǁToolExecutorǁ_check_startup_mode__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_check_startup_mode__mutmut['xǁToolExecutorǁ_check_startup_mode__mutmut_12'] = ToolExecutor.xǁToolExecutorǁ_check_startup_mode__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_check_startup_mode__mutmut['xǁToolExecutorǁ_check_startup_mode__mutmut_13'] = ToolExecutor.xǁToolExecutorǁ_check_startup_mode__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_check_startup_mode__mutmut['xǁToolExecutorǁ_check_startup_mode__mutmut_14'] = ToolExecutor.xǁToolExecutorǁ_check_startup_mode__mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_check_startup_mode__mutmut['xǁToolExecutorǁ_check_startup_mode__mutmut_15'] = ToolExecutor.xǁToolExecutorǁ_check_startup_mode__mutmut_15 # type: ignore # mutmut generated

mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut['_mutmut_orig'] = ToolExecutor.xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut['xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_1'] = ToolExecutor.xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut['xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_2'] = ToolExecutor.xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut['xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_3'] = ToolExecutor.xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut['xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_4'] = ToolExecutor.xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut['xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_5'] = ToolExecutor.xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut['xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_6'] = ToolExecutor.xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut['xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_7'] = ToolExecutor.xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut['xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_8'] = ToolExecutor.xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut['xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_9'] = ToolExecutor.xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut['xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_10'] = ToolExecutor.xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut['xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_11'] = ToolExecutor.xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut['xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_12'] = ToolExecutor.xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut['xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_13'] = ToolExecutor.xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut['xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_14'] = ToolExecutor.xǁToolExecutorǁ_ensure_lifecycle_ready__mutmut_14 # type: ignore # mutmut generated

mutants_xǁToolExecutorǁ_resolve_transport__mutmut['_mutmut_orig'] = ToolExecutor.xǁToolExecutorǁ_resolve_transport__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_resolve_transport__mutmut['xǁToolExecutorǁ_resolve_transport__mutmut_1'] = ToolExecutor.xǁToolExecutorǁ_resolve_transport__mutmut_1 # type: ignore # mutmut generated

mutants_xǁToolExecutorǁ_run_gate_chain__mutmut['_mutmut_orig'] = ToolExecutor.xǁToolExecutorǁ_run_gate_chain__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_run_gate_chain__mutmut['xǁToolExecutorǁ_run_gate_chain__mutmut_1'] = ToolExecutor.xǁToolExecutorǁ_run_gate_chain__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_run_gate_chain__mutmut['xǁToolExecutorǁ_run_gate_chain__mutmut_2'] = ToolExecutor.xǁToolExecutorǁ_run_gate_chain__mutmut_2 # type: ignore # mutmut generated

mutants_xǁToolExecutorǁ_raw_execute__mutmut['_mutmut_orig'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_1'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_2'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_3'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_4'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_5'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_6'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_7'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_8'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_9'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_10'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_11'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_12'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_13'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_14'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_15'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_15 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_16'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_16 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_17'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_17 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_18'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_18 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_19'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_19 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_20'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_20 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_21'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_21 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_22'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_22 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_23'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_23 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_24'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_24 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_25'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_25 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_26'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_26 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_27'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_27 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_28'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_28 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_29'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_29 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_30'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_30 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_raw_execute__mutmut['xǁToolExecutorǁ_raw_execute__mutmut_31'] = ToolExecutor.xǁToolExecutorǁ_raw_execute__mutmut_31 # type: ignore # mutmut generated

mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['_mutmut_orig'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_1'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_2'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_3'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_4'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_5'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_6'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_7'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_8'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_9'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_10'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_11'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_12'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_13'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_14'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_15'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_15 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_16'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_16 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_17'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_17 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_18'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_18 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_19'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_19 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_20'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_20 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_21'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_21 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_22'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_22 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_23'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_23 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_24'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_24 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_25'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_25 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_26'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_26 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_27'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_27 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_28'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_28 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_29'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_29 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_30'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_30 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_31'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_31 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_32'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_32 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_33'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_33 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_34'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_34 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_35'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_35 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_36'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_36 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_37'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_37 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_38'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_38 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_39'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_39 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_40'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_40 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_41'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_41 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_42'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_42 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_43'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_43 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_44'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_44 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_45'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_45 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_46'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_46 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_47'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_47 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_48'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_48 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_49'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_49 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_cache__mutmut['xǁToolExecutorǁ_execute_with_cache__mutmut_50'] = ToolExecutor.xǁToolExecutorǁ_execute_with_cache__mutmut_50 # type: ignore # mutmut generated

mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['_mutmut_orig'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_1'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_2'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_3'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_4'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_5'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_6'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_7'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_8'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_9'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_10'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_11'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_12'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_13'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_14'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_15'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_15 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_16'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_16 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_17'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_17 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_18'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_18 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_19'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_19 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_20'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_20 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_21'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_21 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_execute_with_stampede_protection__mutmut['xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_22'] = ToolExecutor.xǁToolExecutorǁ_execute_with_stampede_protection__mutmut_22 # type: ignore # mutmut generated

mutants_xǁToolExecutorǁ_store_and_evict__mutmut['_mutmut_orig'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_1'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_2'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_3'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_4'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_5'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_6'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_7'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_8'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_9'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_10'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_11'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_12'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_13'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_14'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_15'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_15 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_16'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_16 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_17'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_17 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_18'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_18 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_19'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_19 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_20'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_20 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_21'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_21 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_22'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_22 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁ_store_and_evict__mutmut['xǁToolExecutorǁ_store_and_evict__mutmut_23'] = ToolExecutor.xǁToolExecutorǁ_store_and_evict__mutmut_23 # type: ignore # mutmut generated

mutants_xǁToolExecutorǁexecute__mutmut['_mutmut_orig'] = ToolExecutor.xǁToolExecutorǁexecute__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolExecutorǁexecute__mutmut['xǁToolExecutorǁexecute__mutmut_1'] = ToolExecutor.xǁToolExecutorǁexecute__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁexecute__mutmut['xǁToolExecutorǁexecute__mutmut_2'] = ToolExecutor.xǁToolExecutorǁexecute__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁexecute__mutmut['xǁToolExecutorǁexecute__mutmut_3'] = ToolExecutor.xǁToolExecutorǁexecute__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁexecute__mutmut['xǁToolExecutorǁexecute__mutmut_4'] = ToolExecutor.xǁToolExecutorǁexecute__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁexecute__mutmut['xǁToolExecutorǁexecute__mutmut_5'] = ToolExecutor.xǁToolExecutorǁexecute__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁexecute__mutmut['xǁToolExecutorǁexecute__mutmut_6'] = ToolExecutor.xǁToolExecutorǁexecute__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁexecute__mutmut['xǁToolExecutorǁexecute__mutmut_7'] = ToolExecutor.xǁToolExecutorǁexecute__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁexecute__mutmut['xǁToolExecutorǁexecute__mutmut_8'] = ToolExecutor.xǁToolExecutorǁexecute__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolExecutorǁexecute__mutmut['xǁToolExecutorǁexecute__mutmut_9'] = ToolExecutor.xǁToolExecutorǁexecute__mutmut_9 # type: ignore # mutmut generated
