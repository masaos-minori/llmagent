"""scripts/agent/services/mcp_tool_discovery.py

McpToolDiscoveryService — discover live MCP tools at startup and build a
`RuntimeToolRegistry`.

This service fetches every HTTP-transport MCP server's `/v1/tools` endpoint,
validates each entry's shape (richer than `repl_health.py`'s existing
name-only check), normalizes valid entries into `shared.runtime_tool.RuntimeTool`
instances via `build_runtime_tool()`, detects cross-server duplicate tool
names, validates live tool lists against the static `ToolRegistry` for drift,
absorbs `_check_tool_definitions` startup validation, and reads
`schema_version`/`capabilities` keys on the response body and per-tool
entries. A response body missing `schema_version`, or declaring one other
than `mcp_servers.server.MCP_TOOL_SCHEMA_VERSION`, is rejected outright (all
of that server's tools excluded, one WARNING/FATAL finding) — the server and
this discovery client must speak the same tool-schema version.
Returns a built `shared.runtime_tool_registry.RuntimeToolRegistry` plus a list
of findings the startup pipeline can report.

The `/v1/tools` round-trip and the response- and entry-level validation live in
`mcp_tool_discovery_fetch.py`; cross-server duplicate exclusion and `RuntimeToolRegistry`
building live in `mcp_tool_discovery_registry.py`; this module keeps the orchestration —
severity escalation, drift, write-classification and tool-definition findings.

This is an independent HTTP round-trip from `repl_health.py`'s existing
drift-check fetch (`_collect_server_tool_names_per_server()`) — the two are
*not* unified in this pass, per the design decision to keep the discovery fetch
pattern (`mcp_tool_discovery_fetch.py`) self-contained. Because each fetch is a
separate HTTP call, the two could theoretically observe different tool sets if a
server's state changes between the two calls; this is a known, accepted limitation.

Duplicate-tool-name handling (concrete decision, stated explicitly per the
requirement's "avoid automatic priority selection" constraint): when the same
tool name is reported by more than one server, the tool is **excluded from
the registry entirely** — the safer of the two options considered (the
alternative, first-wins-with-a-warning, risks silently routing calls to an
arbitrary server). Unlike the other findings emitted by this service, a
duplicate is **always** reported as `FATAL`, regardless of `strict` — a
duplicated tool is unusable, so there is no WARNING-only case.

Unified severity scheme (drift, tool-definitions, malformed-capabilities):
`is_fatal = strict`. Duplicate-tool findings are the one exception to this
scheme — they are always FATAL.

Security Posture gating: when the caller supplies `posture_gates`, this service
reduces them to a server-key allowlist with
`agent.services.mcp_health.allowed_server_keys()` and hands that allowlist to
`RuntimeToolRegistry`, so a server whose posture the Agent rejected contributes no
tool. `posture_gates=None` means no gate was supplied and every reachable server's
tools are registered as before. This module never probes `/health` and never
decides a gate itself.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from shared.mcp_config import TransportType
from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.tool_routing_validation import validate_routing_against_live

from agent.services.mcp_health import PostureGate, allowed_server_keys
from agent.services.mcp_tool_discovery_fetch import (
    _SOURCE,
    _fetch_server_tools,
    _RawEntry,
    _unified_findings,
)
from agent.services.mcp_tool_discovery_registry import _dedupe_and_build
from agent.services.tool_validation import _check_tool_definitions
from agent.shared.health_models import StartupCheckOutcome, StartupCheckStatus
from agent.tool_policy import check_write_classification

if TYPE_CHECKING:
    from agent.context import AgentContext


@dataclass(frozen=True)
class DiscoveryResult:
    """Result of discovering tools across all configured MCP servers."""

    registry: RuntimeToolRegistry
    findings: list[StartupCheckOutcome]
    unreachable: list[str]


class McpToolDiscoveryService:
    """Discover live MCP tools and build a `RuntimeToolRegistry`."""

    def __init__(
        self,
        ctx: AgentContext,
        posture_gates: Mapping[str, PostureGate] | None = None,
    ) -> None:
        """Build the discovery service, optionally carrying the Security Posture gate.

        `posture_gates` is the gate row `18` (`agent.services.mcp_health`) produced at readiness. `None`
        means no gate was supplied and today's behavior is kept; it is the migration-window value, and the
        only production caller passes real gates.
        """
        self._ctx = ctx
        self._posture_gates = posture_gates

    async def discover_all(self) -> DiscoveryResult:
        """Fetch tools from every HTTP-transport MCP server and build a registry."""
        entries, findings, unreachable = await self._fetch_all_server_entries()
        unavailable_keys = frozenset(unreachable)
        allowed_servers = (
            None
            if self._posture_gates is None
            else frozenset(allowed_server_keys(self._posture_gates))
        )
        registry, dedup_findings = _dedupe_and_build(
            entries, unavailable_keys, allowed_servers=allowed_servers
        )
        findings.extend(dedup_findings)
        findings = self._check_required_tools(findings, registry)
        findings.extend(self._build_drift_findings(entries))
        findings.extend(self._build_write_classification_findings(registry))
        tool_defs_finding = await self._check_tool_definitions_finding()
        if tool_defs_finding is not None:
            findings.append(tool_defs_finding)
        return DiscoveryResult(
            registry=registry,
            findings=findings,
            unreachable=unreachable,
        )

    async def _fetch_all_server_entries(
        self,
    ) -> tuple[list[_RawEntry], list[StartupCheckOutcome], list[str]]:
        """Fetch every HTTP-transport server's tools and collect its findings.

        Returns `(entries, findings, unreachable)`. A server's findings are escalated
        to FATAL when that server is `required` (ADR-004), whether the fetch failed or
        it returned per-tool findings; the server key is recorded in `unreachable` only
        when the fetch itself failed.
        """
        entries: list[_RawEntry] = []
        findings: list[StartupCheckOutcome] = []
        unreachable: list[str] = []
        http_client = self._ctx.services_required.http
        for key, cfg in self._ctx.cfg.mcp.mcp_servers.items():
            if cfg.transport != TransportType.HTTP or not cfg.url or cfg.is_disabled:
                continue
            fetched, server_findings, is_unreachable = await _fetch_server_tools(
                http_client, key, cfg
            )
            findings.extend(
                self._escalate_unreachable_findings(server_findings, cfg.required)
            )
            if is_unreachable:
                unreachable.append(key)
            entries.extend(fetched)
        return entries, findings, unreachable

    def _is_strict(self) -> bool:
        """Return True when strict mode is enabled."""
        return bool(getattr(self._ctx.cfg.tool, "tool_definitions_strict", False))

    def _unified_status(self) -> StartupCheckStatus:
        """Return the severity a non-duplicate finding takes under the current strict mode.

        Single place where the unified severity scheme (`is_fatal = strict`) is decided, so
        every finding builder in this service agrees. Duplicate-tool findings are the one
        exception, and `mcp_tool_discovery_registry._detect_duplicates()` builds them as
        FATAL directly.
        """
        if self._is_strict():
            return StartupCheckStatus.FATAL
        return StartupCheckStatus.WARNING

    def _build_drift_findings(
        self, entries: list[_RawEntry]
    ) -> list[StartupCheckOutcome]:
        """Build drift findings by comparing live tool lists against the static ToolRegistry.

        Reuses `discover_all()`'s already-fetched `(server_key, server_url, entry)` tuples
        to build `{server_key: [tool_name, ...]}` shape without a second fetch.
        """
        per_server: dict[str, list[str]] = {}
        for server_key, _url, entry in entries:
            per_server.setdefault(server_key, []).append(str(entry["name"]))
        drift = validate_routing_against_live(live_tool_lists=per_server)
        if not drift:
            return []
        return _unified_findings(
            (f"Live routing drift [{sk}]: {msgs}" for sk, msgs in drift.items()),
            self._unified_status(),
        )

    def _build_write_classification_findings(
        self, registry: RuntimeToolRegistry
    ) -> list[StartupCheckOutcome]:
        """Report tools whose RuntimeTool write flag disagrees with the static tool sets (ADR-003 INV-03)."""
        messages = check_write_classification(registry)
        if not messages:
            return []
        return _unified_findings(
            (f"Write classification mismatch: {msg}" for msg in messages),
            self._unified_status(),
        )

    async def _check_tool_definitions_finding(self) -> StartupCheckOutcome | None:
        """Wrap `_check_tool_definitions` to surface failures as data, not exceptions.

        Converts any RuntimeError raised by the helper into a
        StartupCheckOutcome with the unified severity instead of letting it
        propagate — this resolves the old quirk where strict-mode drift
        detection was silently downgraded to "skipped" by an unrelated
        exception handler.
        """
        status = self._unified_status()
        try:
            result = await _check_tool_definitions(self._ctx, strict=self._is_strict())
            if result.has_issues:
                return StartupCheckOutcome(
                    source=_SOURCE,
                    status=status,
                    message="; ".join(result.warning_messages()),
                )
            return None
        except RuntimeError as exc:
            return StartupCheckOutcome(source=_SOURCE, status=status, message=str(exc))

    def _escalate_unreachable_findings(
        self, server_findings: list[StartupCheckOutcome], is_required: bool
    ) -> list[StartupCheckOutcome]:
        """Escalate one server's findings to FATAL when that server is required.

        Each finding keeps its `source`, `message`, and `remediation`; only `status`
        changes — FATAL for a required server, WARNING otherwise. Applies to both an
        unreachable server and a reachable server that returned per-tool findings.
        Returns a new list; the caller appends it to the findings collected so far.
        """
        status = StartupCheckStatus.FATAL if is_required else StartupCheckStatus.WARNING
        return [
            StartupCheckOutcome(
                source=o.source,
                status=status,
                message=o.message,
                remediation=o.remediation,
            )
            for o in server_findings
        ]

    def _check_required_tools(
        self,
        findings: list[StartupCheckOutcome],
        registry: RuntimeToolRegistry,
    ) -> list[StartupCheckOutcome]:
        """Check that all required tools are present in the discovery results."""
        discovered_names = {tool.name for tool in registry.all_tools()}
        for srv_key, srv_cfg in self._ctx.cfg.mcp.mcp_servers.items():
            if not srv_cfg.required or not srv_cfg.tool_names:
                continue
            for tool_name in srv_cfg.tool_names:
                if tool_name in discovered_names:
                    continue
                findings.append(
                    StartupCheckOutcome(
                        source=_SOURCE,
                        status=StartupCheckStatus.FATAL,
                        message=(
                            f"{srv_key}: required tool {tool_name!r} not found in discovery results"
                        ),
                        remediation="Verify the server's /v1/tools response includes this tool.",
                    )
                )
        return findings
