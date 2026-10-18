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

This is an independent HTTP round-trip from `repl_health.py`'s existing
drift-check fetch (`_collect_server_tool_names_per_server()`) — the two are
*not* unified in this pass, per the design decision to keep this module's
fetch pattern self-contained. Because each fetch is a separate HTTP call, the
two could theoretically observe different tool sets if a server's state
changes between the two calls; this is a known, accepted limitation.

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
from http import HTTPStatus
from logging import getLogger
from typing import TYPE_CHECKING

import httpx
from mcp_servers.server import MCP_TOOL_SCHEMA_VERSION
from shared.mcp_config import (
    McpServerConfig,
    TransportType,
    get_effective_health_timeout,
)
from shared.resource_scope import validate_tool_schema_v2
from shared.runtime_tool import RuntimeTool, build_runtime_tool
from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.tool_routing_validation import validate_routing_against_live

from agent.services.mcp_health import PostureGate, allowed_server_keys
from agent.services.tool_validation import _check_tool_definitions
from agent.shared.health_models import StartupCheckOutcome, StartupCheckStatus
from agent.tool_policy import check_write_classification

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = getLogger(__name__)

_SOURCE = "mcp_tool_discovery"

_TOOLS_ENDPOINT = "/v1/tools"

# Raw tool entry as received from a server's /v1/tools response, tagged with
# the owning server's key and base URL: (server_key, server_url, entry).
_RawEntry = tuple[str, str, dict[str, object]]

# Schema-2.0 fields every discovered tool entry MUST declare. A missing field is a hard
# rejection (per-tool WARNING/FATAL finding), not silently defaulted by build_runtime_tool().
_REQUIRED_SCHEMA_V2_FIELDS = (
    "is_write",
    "requires_serial",
    "resource_scope_kind",
    "resource_scope_keys",
)


class McpToolsHttpClient:
    """Handles HTTP fetching and top-level response validation."""

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http_client = http_client

    async def fetch_tools(
        self, server_key: str, cfg: McpServerConfig
    ) -> tuple[list[_RawEntry], list[StartupCheckOutcome], bool]:
        """Fetch one server's /v1/tools response. Returns (entries, findings, is_unreachable)."""
        try:
            resp = await self._http_client.get(
                f"{cfg.url}{_TOOLS_ENDPOINT}",
                timeout=httpx.Timeout(timeout=get_effective_health_timeout(cfg)),
            )
        except (httpx.HTTPError, OSError) as e:
            return _warning_fetch_result(
                f"{server_key} unreachable at {cfg.url}{_TOOLS_ENDPOINT}: {e}"
            )

        if resp.status_code != HTTPStatus.OK:
            return _warning_fetch_result(
                f"{server_key} {_TOOLS_ENDPOINT} returned HTTP {resp.status_code}"
            )

        try:
            body: object = resp.json()
        except ValueError as e:
            return _warning_fetch_result(
                f"{server_key}: {_TOOLS_ENDPOINT} response is not valid JSON: {e}"
            )

        if not isinstance(body, dict):
            return _warning_fetch_result(
                f"{server_key}: {_TOOLS_ENDPOINT} response is not a JSON object "
                f"(got {type(body).__name__})"
            )

        schema_error = _schema_version_error(server_key, body)
        if schema_error is not None:
            return _warning_fetch_result(schema_error)

        tools = body.get("tools")
        if not isinstance(tools, list):
            return _warning_fetch_result(
                f"{server_key}: {_TOOLS_ENDPOINT} 'tools' field must be a list "
                f"(got {type(tools).__name__})"
            )

        entries, entry_findings = _normalize_entries(server_key, cfg.url, tools)
        return entries, entry_findings, False


class ToolEntryValidator:
    """Validates individual /v1/tools entries."""

    def validate_entry(
        self,
        server_key: str,
        server_url: str,
        entry: object,
        required_server: bool,
    ) -> tuple[dict[str, object] | None, StartupCheckOutcome | None]:
        """Validate one raw /v1/tools entry. Returns (normalized_entry_or_None, finding_or_None)."""
        if not isinstance(entry, dict):
            return _warning_entry(
                f"{server_key}: {_TOOLS_ENDPOINT} tool entry is not an object "
                f"(got {type(entry).__name__})"
            )

        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            return _warning_entry(
                f"{server_key}: {_TOOLS_ENDPOINT} entry has invalid name {name!r}"
            )

        schema_error = _entry_schema_error(server_key, name, entry)
        if schema_error is not None:
            return _warning_entry(schema_error)

        field_error = _entry_optional_field_error(server_key, server_url, name, entry)
        if field_error is not None:
            return _warning_entry(field_error)

        return entry, None


class SeverityClassifier:
    """Consolidated severity classification logic."""

    def __init__(self, strict: bool, is_duplicate: bool = False) -> None:
        self._strict = strict
        self._is_duplicate = is_duplicate

    @property
    def is_fatal(self) -> bool:
        """Return True when findings should be FATAL per the unified severity scheme.

        For non-duplicate findings: is_fatal = strict.
        For duplicate findings: always True (exception to the scheme).
        """
        if self._is_duplicate:
            return True
        return self._strict


@dataclass(frozen=True)
class DiscoveryResult:
    """Result of discovering tools across all configured MCP servers."""

    registry: RuntimeToolRegistry
    findings: list[StartupCheckOutcome]
    unreachable: list[str]


def _warning_fetch_result(
    msg: str,
) -> tuple[list[_RawEntry], list[StartupCheckOutcome], bool]:
    """Build a (no entries, one WARNING finding, unreachable=True) fetch result."""
    return (
        [],
        [
            StartupCheckOutcome(
                source=_SOURCE, status=StartupCheckStatus.WARNING, message=msg
            )
        ],
        True,
    )


def _warning_entry(msg: str) -> tuple[None, StartupCheckOutcome]:
    """Build a (rejected entry, one WARNING finding) validation result."""
    return None, StartupCheckOutcome(
        source=_SOURCE, status=StartupCheckStatus.WARNING, message=msg
    )


def _schema_version_error(server_key: str, body: dict[str, object]) -> str | None:
    """Return the response-level schema_version error, or None when it is accepted.

    Logs a WARNING for a missing or unsupported `schema_version` and a DEBUG line
    when it matches `mcp_servers.server.MCP_TOOL_SCHEMA_VERSION`.
    """
    schema_version = body.get("schema_version")
    if schema_version is None:
        logger.warning(
            "mcp_tool_discovery: server_key=%s missing schema_version in %s response",
            server_key,
            _TOOLS_ENDPOINT,
        )
        return (
            f"{server_key}: {_TOOLS_ENDPOINT} response is missing schema_version "
            f"(expected {MCP_TOOL_SCHEMA_VERSION!r})"
        )
    if schema_version != MCP_TOOL_SCHEMA_VERSION:
        logger.warning(
            "mcp_tool_discovery: server_key=%s unsupported schema_version=%s",
            server_key,
            schema_version,
        )
        return (
            f"{server_key}: {_TOOLS_ENDPOINT} response has unsupported schema_version "
            f"{schema_version!r} (expected {MCP_TOOL_SCHEMA_VERSION!r})"
        )
    logger.debug(
        "mcp_tool_discovery: server_key=%s schema_version=%s",
        server_key,
        schema_version,
    )
    return None


def _normalize_entries(
    server_key: str, server_url: str, tools: list[object]
) -> tuple[list[_RawEntry], list[StartupCheckOutcome]]:
    """Validate one server's raw tool entries into (accepted entries, findings)."""
    entries: list[_RawEntry] = []
    findings: list[StartupCheckOutcome] = []
    validator = ToolEntryValidator()
    for raw_entry in tools:
        normalized, finding = validator.validate_entry(
            server_key, server_url, raw_entry, required_server=False
        )
        if finding is not None:
            findings.append(finding)
        if normalized is not None:
            entries.append((server_key, server_url, normalized))
    return entries, findings


def _entry_schema_error(
    server_key: str, name: str, entry: dict[str, object]
) -> str | None:
    """Return the first error for the entry's required fields and schema-2.0 contract."""
    for field_name, expected_type in (
        ("description", str),
        ("inputSchema", dict),
    ):
        value = entry.get(field_name)
        if not isinstance(value, expected_type):
            return f"{server_key}: tool {name!r} has invalid {field_name} {value!r}"

    missing_fields = [f for f in _REQUIRED_SCHEMA_V2_FIELDS if f not in entry]
    if missing_fields:
        return (
            f"{server_key}: tool {name!r} missing required schema-2.0 field(s): "
            f"{', '.join(missing_fields)}"
        )

    schema_errors = validate_tool_schema_v2(entry)
    if schema_errors:
        return (
            f"{server_key}: tool {name!r} failed schema-2.0 validation: "
            f"{'; '.join(schema_errors)}"
        )
    return None


def _entry_optional_field_error(
    server_key: str, server_url: str, name: str, entry: dict[str, object]
) -> str | None:
    """Return the first error for the entry's optional typed fields and capabilities."""
    for field_name, expected_type in (
        ("status", str),
        ("enabled", bool),
    ):
        if field_name in entry and not isinstance(entry[field_name], expected_type):
            return (
                f"{server_key}: tool {name!r} has invalid {field_name} "
                f"{entry[field_name]!r} (expected {expected_type.__name__})"
            )

    capabilities = entry.get("capabilities")
    if capabilities is not None and not isinstance(capabilities, list):
        return (
            f"{server_key}: tool {name!r} on server {server_url!r}: "
            "capabilities must be a list"
        )
    return None


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
        registry, dedup_findings = self._dedupe_and_build(
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
            client = McpToolsHttpClient(http_client)
            fetched, server_findings, is_unreachable = await client.fetch_tools(
                key, cfg
            )
            findings = self._escalate_unreachable_findings(
                findings, server_findings, cfg.required
            )
            if is_unreachable:
                unreachable.append(key)
            entries.extend(fetched)
        return entries, findings, unreachable

    def _detect_duplicates(
        self, entries: list[_RawEntry]
    ) -> tuple[list[tuple[str, str, dict[str, object]]], list[StartupCheckOutcome]]:
        """Detect duplicate tool names and separate unique entries.

        Returns (unique_entries, dedup_findings). Duplicate tool names produce
        FATAL findings regardless of strict mode per the module's documented
        exception to the severity scheme.
        """
        by_name: dict[str, list[_RawEntry]] = {}
        for server_key, server_url, entry in entries:
            name = str(entry["name"])
            by_name.setdefault(name, []).append((server_key, server_url, entry))

        findings: list[StartupCheckOutcome] = []
        unique_entries: list[tuple[str, str, dict[str, object]]] = []
        for name, group in by_name.items():
            server_keys = sorted({server_key for server_key, _, _ in group})
            if len(server_keys) > 1:
                # Always fatal — tool is unusable when duplicated across servers
                status = StartupCheckStatus.FATAL
                msg = (
                    f"duplicate tool name {name!r} reported by multiple servers: "
                    f"{', '.join(server_keys)} — excluded from registry"
                )
                findings.append(
                    StartupCheckOutcome(source=_SOURCE, status=status, message=msg)
                )
                continue
            server_key, server_url, entry = group[0]
            unique_entries.append((server_key, server_url, entry))
        return unique_entries, findings

    def _build_runtime_tools(
        self,
        unique_entries: list[tuple[str, str, dict[str, object]]],
        unavailable_servers: frozenset[str],
        allowed_servers: frozenset[str] | None = None,
    ) -> RuntimeToolRegistry:
        """Build RuntimeToolRegistry from unique entries with unavailable and posture filtering.

        `allowed_servers` is the posture-derived allowlist (row `19`): `None` registers every tool that
        survived the unavailable filter, a `frozenset` lets only its members through, and an empty
        `frozenset` registers nothing.
        """
        built: dict[str, RuntimeTool] = {}
        for server_key, server_url, entry in unique_entries:
            if server_key in unavailable_servers:
                continue
            built[str(entry["name"])] = build_runtime_tool(
                name=str(entry["name"]),
                server_key=server_key,
                server_url=server_url,
                description=str(entry.get("description", "")),
                input_schema=entry.get("inputSchema"),  # type: ignore[arg-type]
                raw_definition=entry,
                status=str(entry.get("status", "active")),
                is_write=entry["is_write"],  # type: ignore[arg-type]
                requires_serial=entry["requires_serial"],  # type: ignore[arg-type]
                resource_scope_kind=str(entry["resource_scope_kind"]),
                resource_scope_keys=tuple(entry["resource_scope_keys"]),  # type: ignore[arg-type]
                enabled_for_llm=bool(entry.get("enabled", True)),
                capabilities=tuple(entry.get("capabilities", []) or []),  # type: ignore[arg-type]
            )
        return RuntimeToolRegistry(tools=built, allowed_servers=allowed_servers)

    def _dedupe_and_build(
        self,
        entries: list[_RawEntry],
        unavailable_servers: frozenset[str],
        allowed_servers: frozenset[str] | None = None,
    ) -> tuple[RuntimeToolRegistry, list[StartupCheckOutcome]]:
        """Group entries by tool name, build RuntimeTools, and exclude duplicates.

        Names reported by exactly one server become a RuntimeTool. Names
        reported by more than one distinct server are excluded from the
        registry entirely (per this module's docstring), each producing one
        FATAL finding — tool is unusable when duplicated across servers.

        Every entry reaching this method has already passed
        ToolEntryValidator.validate_entry()'s hard schema-2.0 requirement, so
        `is_write`/`requires_serial`/`resource_scope_kind`/`resource_scope_keys`
        are guaranteed present — they are indexed directly (`entry[...]`), not
        defaulted via `.get()`.

        `allowed_servers` travels exactly like `unavailable_servers` and reaches the registry unchanged:
        this module transports the gate, it does not decide it.
        """
        unique_entries, dedup_findings = self._detect_duplicates(entries)
        registry = self._build_runtime_tools(
            unique_entries, unavailable_servers, allowed_servers=allowed_servers
        )
        return registry, dedup_findings

    def _is_strict(self) -> bool:
        """Return True when strict mode is enabled."""
        return bool(getattr(self._ctx.cfg.tool, "tool_definitions_strict", False))

    def _unified_status(self) -> StartupCheckStatus:
        """Return the severity a non-duplicate finding takes under the current strict mode.

        Single place where `SeverityClassifier` is consulted, so every finding builder in
        this service applies the same unified severity scheme.
        """
        classifier = SeverityClassifier(strict=self._is_strict(), is_duplicate=False)
        if classifier.is_fatal:
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
        status = self._unified_status()
        return [
            StartupCheckOutcome(
                source=_SOURCE,
                status=status,
                message=f"Live routing drift [{sk}]: {msgs}",
            )
            for sk, msgs in drift.items()
        ]

    def _build_write_classification_findings(
        self, registry: RuntimeToolRegistry
    ) -> list[StartupCheckOutcome]:
        """Report tools whose RuntimeTool write flag disagrees with the static tool sets (ADR-003 INV-03)."""
        messages = check_write_classification(registry)
        if not messages:
            return []
        status = self._unified_status()
        return [
            StartupCheckOutcome(
                source=_SOURCE,
                status=status,
                message=f"Write classification mismatch: {msg}",
            )
            for msg in messages
        ]

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
        self,
        current_findings: list[StartupCheckOutcome],
        server_findings: list[StartupCheckOutcome],
        is_required: bool,
    ) -> list[StartupCheckOutcome]:
        """Escalate one server's findings to FATAL when that server is required.

        Each finding keeps its `source`, `message`, and `remediation`; only `status`
        changes — FATAL for a required server, WARNING otherwise. Applies to both an
        unreachable server and a reachable server that returned per-tool findings.
        """
        status = StartupCheckStatus.FATAL if is_required else StartupCheckStatus.WARNING
        current_findings.extend(
            StartupCheckOutcome(
                source=o.source,
                status=status,
                message=o.message,
                remediation=o.remediation,
            )
            for o in server_findings
        )
        return current_findings

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
