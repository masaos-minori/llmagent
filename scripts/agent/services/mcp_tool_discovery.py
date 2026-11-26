"""scripts/agent/services/mcp_tool_discovery.py

McpToolDiscoveryService — discover live MCP tools at startup and build a
`RuntimeToolRegistry`.

This service fetches every HTTP-transport MCP server's `/v1/tools` endpoint,
validates each entry's shape, normalizes valid entries into
`shared.runtime_tool.RuntimeTool` instances via `build_runtime_tool()`,
detects cross-server duplicate tool names, validates live tool lists against
the static `ToolRegistry` for drift, absorbs `_check_tool_definitions` startup
validation, and reads `schema_version`/`capabilities` keys on the response body
and per-tool entries. A response body missing `schema_version`, or declaring
one other than `mcp_servers.server.MCP_TOOL_SCHEMA_VERSION`, is rejected outright
(all of that server's tools excluded, one WARNING/FATAL finding) — the server
and this discovery client must speak the same tool-schema version.
Returns a built `shared.runtime_tool_registry.RuntimeToolRegistry` plus a list
of findings the startup pipeline can report.

The `/v1/tools` round-trip and the response- and entry-level validation live in
`mcp_tool_discovery_fetch.py`; cross-server duplicate exclusion and `RuntimeToolRegistry`
building live in `mcp_tool_discovery_registry.py`; this module keeps the orchestration —
severity escalation, drift, write-classification and tool-definition findings.

Discovery fetches `/v1/tools` once per server. Each fetch is a single, self-contained
HTTP call; this module performs no second cross-module fetch of the same data.

Duplicate-tool-name handling (concrete decision, stated explicitly per the
requirement's "avoid automatic priority selection" constraint): when the same
tool name is reported by more than one server, the tool is **excluded from
the registry entirely** — the safer of the two options considered (the
alternative, first-wins-with-a-warning, risks silently routing calls to an
arbitrary server). A duplicate is **always** reported as `FATAL` — a
duplicated tool is unusable, so there is no WARNING-only case.

Severity (strict-only): drift, write-classification and tool-definition
findings are always `FATAL`; per-server findings escalate by the server
`required` flag in `_escalate_unreachable_findings`.

Security Posture gating: when the caller supplies `posture_gates`, this service
reduces them to a server-key allowlist with
`agent.services.mcp_health.allowed_server_keys()` and hands that allowlist to
`RuntimeToolRegistry`, so a server whose posture the Agent rejected contributes no
tool. An empty gate mapping allows no server and adds no MCP tool to the registry.
This module never probes `/health` and never
decides a gate itself.

Required-capability proof (REQ-005): `config/tool_catalog.toml` is read through
`shared.tool_catalog` before the registry is built, and each `required` server's declared
capability is proven from the report its gate carries — a body without the capability block
falls back to `ready` (D-6). Optional capabilities reported `degraded` or `unavailable` are
collected per server into the map handed to the registry builder, so only the tools that
depend on them are excluded (REQ-006). Reading a gate's report is not deciding a gate.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from shared.mcp_config import TransportType
from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.tool_catalog import load_tool_catalog, required_capability_for
from shared.tool_routing_validation import validate_routing_against_live

from agent.services.mcp_health import (
    PostureGate,
    allowed_server_keys,
    classify_capabilities,
)
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
        posture_gates: Mapping[str, PostureGate],
    ) -> None:
        """Build the discovery service carrying the Security Posture gate.

        `posture_gates` is the gate row `18` (`agent.services.mcp_health`) produced at
        readiness and is required. An empty mapping is a valid explicit value and
        registers no MCP tool.
        """
        self._ctx = ctx
        self._posture_gates = posture_gates

    async def discover_all(self) -> DiscoveryResult:
        """Fetch tools from every HTTP-transport MCP server and build a registry."""
        entries, findings, unreachable = await self._fetch_all_server_entries()
        unavailable_keys = frozenset(unreachable)
        allowed_servers = frozenset(allowed_server_keys(self._posture_gates))
        try:
            # The catalog is read before the registry is built (D-9): the required-capability
            # proof and the degraded-capability map are both decided from it, so the registry
            # is published once, already excluding the tools of a degraded optional capability.
            tool_catalog = self._load_tool_catalog()
        except OSError as exc:
            # Fail-closed (REQ-005): a missing/unreadable manifest means no
            # required server can prove its declared capability, so block.
            findings.append(
                StartupCheckOutcome(
                    source=_SOURCE,
                    status=StartupCheckStatus.FATAL,
                    message=f"tool_catalog.toml unavailable: {exc}",
                    remediation="Ship config/tool_catalog.toml alongside agent.toml.",
                )
            )
            return DiscoveryResult(
                registry=RuntimeToolRegistry(allowed_servers=allowed_servers),
                findings=findings,
                unreachable=unreachable,
            )
        findings = self._check_required_tools(findings, tool_catalog)
        # The map is produced here and transported unchanged (REQ-006): the exclusion decision is
        # the registry's, so the registry is published once with the dependent tools already dropped.
        degraded = self._degraded_capability_map(tool_catalog)
        registry, dedup_findings = _dedupe_and_build(
            entries,
            unavailable_keys,
            allowed_servers=allowed_servers,
            degraded_capabilities=degraded,
        )
        findings.extend(dedup_findings)
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

    def _load_tool_catalog(self) -> dict[str, Any]:
        """Load config/tool_catalog.toml once per discovery (fail-closed).

        Reads through `shared.tool_catalog`, the one reader both Tool Discovery and the
        lifecycle readiness helpers use, so the file path and the entry shape are defined
        once. The manifest is DATA (it crosses no import boundary), so it is loaded at
        runtime rather than imported as a module. Raises ``OSError`` if the file
        is missing or unreadable so the caller can fail closed.
        """
        return load_tool_catalog()

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
            StartupCheckStatus.FATAL,
        )

    def _build_write_classification_findings(
        self, registry: RuntimeToolRegistry
    ) -> list[StartupCheckOutcome]:
        """Report tools whose declared write classification disagrees with the reference tool sets.

        ADR-003 INV-03 as a drift report (agentcfg003 REQ-007, AC-10): the value the
        tool's producer declared is the authority, the static tool sets are comparison
        data only, and the finding changes no decision in the policy layer.
        """
        messages = check_write_classification(registry)
        if not messages:
            return []
        return _unified_findings(
            (f"Declared write classification drift: {msg}" for msg in messages),
            StartupCheckStatus.FATAL,
        )

    async def _check_tool_definitions_finding(self) -> StartupCheckOutcome | None:
        """Wrap `_check_tool_definitions` to surface failures as data, not exceptions.

        Converts any RuntimeError raised by the helper into a
        `FATAL` StartupCheckOutcome instead of letting it propagate — this
        resolves the old quirk where drift detection was silently downgraded
        to "skipped" by an unrelated exception handler.
        """
        status = StartupCheckStatus.FATAL
        try:
            result = await _check_tool_definitions(self._ctx, strict=True)
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
        tool_catalog: Mapping[str, Any],
    ) -> list[StartupCheckOutcome]:
        """Check that every required server proves its declared required capability.

        Required-capability model (REQ-005, AC-3): the manifest
        (config/tool_catalog.toml) declares, per required server, the capability its tools
        must provide, and the parsed health report is the proof of it. A required server
        whose report does not prove that capability `ok` is FATAL. A server with no catalog
        entry, or a body without the capability block, is read through its `ready` flag
        (D-6), so the legacy shape still proves readiness. The check is no longer gated on a
        tool declaring a capability: required loss must block startup (REQ-005), so the
        earlier inert-until-declared guard was removed.
        """
        for srv_key, srv_cfg in self._ctx.cfg.mcp.mcp_servers.items():
            if not srv_cfg.required:
                continue
            required_cap = required_capability_for(tool_catalog, srv_key)
            gate = self._posture_gates.get(srv_key)
            if gate is None:
                findings.append(
                    StartupCheckOutcome(
                        source=_SOURCE,
                        status=StartupCheckStatus.FATAL,
                        message=(
                            f"{srv_key}: required server has no health gate, so its "
                            "required capability cannot be proven"
                        ),
                        remediation="Probe the server at readiness so its report is available.",
                    )
                )
                continue
            finding = classify_capabilities(gate, required_cap)
            if finding.required_proven:
                continue
            if required_cap:
                message = (
                    f"{srv_key}: required capability {required_cap!r} not proven "
                    "by the health report"
                )
            else:
                message = (
                    f"{srv_key}: required server's health report does not prove "
                    "readiness (no declared capability, legacy ready fallback)"
                )
            findings.append(
                StartupCheckOutcome(
                    source=_SOURCE,
                    status=StartupCheckStatus.FATAL,
                    message=message,
                    remediation=(
                        "Verify the server's /health report proves its declared "
                        "capability."
                    ),
                )
            )
        return findings

    def _degraded_capability_map(
        self, tool_catalog: Mapping[str, Any]
    ) -> dict[str, tuple[str, ...]]:
        """Per-server degraded or unavailable optional capabilities (REQ-006).

        Producer of the map Tool Discovery hands to the registry so only the tools that
        depend on the lost capability are excluded with reason `capability` (seq 11 wires
        the call site, seq 13 the exclusion itself). The required capability is not part of
        the map: its loss blocks startup instead of disabling tools.
        """
        degraded: dict[str, tuple[str, ...]] = {}
        for srv_key, gate in self._posture_gates.items():
            finding = classify_capabilities(
                gate, required_capability_for(tool_catalog, srv_key)
            )
            if finding.degraded_optional:
                degraded[srv_key] = finding.degraded_optional
        return degraded
