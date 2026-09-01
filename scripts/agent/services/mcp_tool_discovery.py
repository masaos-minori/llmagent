"""scripts/agent/services/mcp_tool_discovery.py

McpToolDiscoveryService — discover live MCP tools at startup and build a
`RuntimeToolRegistry`.

This service fetches every HTTP-transport MCP server's `/v1/tools` endpoint,
validates each entry's shape (richer than `repl_health.py`'s existing
name-only check), normalizes valid entries into `shared.runtime_tool.RuntimeTool`
instances via `build_runtime_tool()`, detects cross-server duplicate tool
names, validates live tool lists against the static `ToolRegistry` for drift,
absorbs `_check_tool_definitions` startup validation, and reads optional
`schema_version`/`capabilities` keys on the response body and per-tool entries.
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
the registry entirely** in both `local` and `production` security profiles —
the safer of the two options considered (the alternative, first-wins-with-a-
warning, risks silently routing calls to an arbitrary server). Unlike the
other findings emitted by this service, a duplicate is **always** reported as
`FATAL`, regardless of `security_profile` or `strict` — a duplicated tool is
unusable in either profile, so there is no WARNING-only case.

Unified severity scheme (drift, tool-definitions, malformed-capabilities):
`is_fatal = strict or (security_profile == PRODUCTION)`. Duplicate-tool
findings are the one exception to this scheme — they are always FATAL.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from logging import getLogger
from typing import TYPE_CHECKING

import httpx
from shared.mcp_config import (
    McpServerConfig,
    SecurityProfile,
    TransportType,
    get_effective_health_timeout,
)
from shared.resource_scope import validate_tool_schema_v2
from shared.runtime_tool import RuntimeTool, build_runtime_tool
from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.tool_routing_validation import validate_routing_against_live

from agent.services.tool_validation import _check_tool_definitions
from agent.shared.health_models import StartupCheckOutcome, StartupCheckStatus

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = getLogger(__name__)

_SOURCE = "mcp_tool_discovery"

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


class McpToolDiscoveryService:
    """Discover live MCP tools and build a `RuntimeToolRegistry`."""

    def __init__(self, ctx: AgentContext) -> None:
        self._ctx = ctx

    async def discover_all(self) -> DiscoveryResult:
        """Fetch tools from every HTTP-transport MCP server and build a registry."""
        entries: list[_RawEntry] = []
        findings: list[StartupCheckOutcome] = []
        unreachable: list[str] = []
        for key, cfg in self._ctx.cfg.mcp.mcp_servers.items():
            if cfg.transport != TransportType.HTTP or not cfg.url:
                continue
            fetched, server_findings, is_unreachable = await self._fetch_server_tools(
                key, cfg
            )
            if is_unreachable:
                is_required = cfg.required
                new_findings = []
                for o in server_findings:
                    new_status = (
                        StartupCheckStatus.FATAL
                        if is_required
                        else StartupCheckStatus.WARNING
                    )
                    new_findings.append(
                        StartupCheckOutcome(
                            source=o.source,
                            status=new_status,
                            message=o.message,
                            remediation=o.remediation,
                        )
                    )
                server_findings = new_findings

            findings.extend(server_findings)
            if is_unreachable:
                unreachable.append(key)
            entries.extend(fetched)
        registry, dedup_findings = self._dedupe_and_build(entries)
        findings.extend(dedup_findings)
        drift_findings = self._build_drift_findings(entries)
        findings.extend(drift_findings)
        tool_defs_finding = await self._check_tool_definitions_finding()
        if tool_defs_finding is not None:
            findings.append(tool_defs_finding)
        unavailable_keys = frozenset(unreachable)
        filtered_registry = RuntimeToolRegistry(
            tools=dict(registry._tools),
            unavailable_servers=unavailable_keys,
        )
        return DiscoveryResult(
            registry=filtered_registry,
            findings=findings,
            unreachable=unreachable,
        )

    async def _fetch_server_tools(
        self, key: str, cfg: McpServerConfig
    ) -> tuple[list[_RawEntry], list[StartupCheckOutcome], bool]:
        """Fetch and validate one server's /v1/tools response.

        Returns (entries, findings, is_unreachable). `is_unreachable` is True
        only for whole-server failures (connection error, non-200, invalid
        JSON, or malformed top-level shape) — not for individual malformed
        tool entries, which are reported as per-entry findings while the
        server's remaining, valid entries are still discovered. All findings
        here are WARNING, not FATAL — consistent with `repl_health.py`'s
        existing behavior of logging and continuing rather than raising.
        """
        try:
            resp = await self._ctx.services_required.http.get(
                f"{cfg.url}/v1/tools",
                timeout=httpx.Timeout(timeout=get_effective_health_timeout(cfg)),
            )
        except (httpx.HTTPError, OSError) as e:
            return _warning_fetch_result(
                f"{key} unreachable at {cfg.url}/v1/tools: {e}"
            )

        if resp.status_code != HTTPStatus.OK:
            return _warning_fetch_result(
                f"{key} /v1/tools returned HTTP {resp.status_code}"
            )

        try:
            body: object = resp.json()
        except ValueError as e:
            return _warning_fetch_result(
                f"{key}: /v1/tools response is not valid JSON: {e}"
            )

        if not isinstance(body, dict):
            return _warning_fetch_result(
                f"{key}: /v1/tools response is not a JSON object (got {type(body).__name__})"
            )

        schema_version = body.get("schema_version")
        if schema_version is not None:
            logger.debug(
                "mcp_tool_discovery: server_key=%s schema_version=%s",
                key,
                schema_version,
            )
        elif schema_version is None:
            logger.warning(
                "mcp_tool_discovery: server_key=%s missing schema_version in /v1/tools response",
                key,
            )

        tools = body.get("tools")
        if not isinstance(tools, list):
            return _warning_fetch_result(
                f"{key}: /v1/tools 'tools' field must be a list (got {type(tools).__name__})"
            )

        entries: list[_RawEntry] = []
        entry_findings: list[StartupCheckOutcome] = []
        for raw_entry in tools:
            normalized, finding = self._validate_and_normalize_entry(
                key, cfg.url, raw_entry
            )
            if finding is not None:
                entry_findings.append(finding)
            if normalized is not None:
                entries.append((key, cfg.url, normalized))

        return entries, entry_findings, False

    def _validate_and_normalize_entry(
        self, server_key: str, server_url: str, entry: object
    ) -> tuple[dict[str, object] | None, StartupCheckOutcome | None]:
        """Validate one raw /v1/tools entry.

        Rules: entry is a dict; `name` is a non-empty string; `description`
        is present and is a str (empty string allowed); `inputSchema` is a dict; `is_write`, `requires_serial`,
        `resource_scope_kind`, `resource_scope_keys` are REQUIRED — a missing
        field, or one that fails `validate_tool_schema_v2()`'s schema-2.0
        contract (type/known-kind/scope-key-vs-inputSchema.properties
        checks), rejects the entry with a per-tool finding; it is never
        silently defaulted. Optional `status`/`resource_scope` (legacy
        singular)/`enabled`/`capabilities` remain type-checked only if
        present. Schema errors are per-tool WARNING findings, not FATAL.
        """
        if not isinstance(entry, dict):
            return _warning_entry(
                f"{server_key}: /v1/tools tool entry is not an object (got {type(entry).__name__})"
            )

        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            return _warning_entry(
                f"{server_key}: /v1/tools entry has invalid name {name!r}"
            )

        description = entry.get("description")
        if not isinstance(description, str):
            return _warning_entry(
                f"{server_key}: tool {name!r} has invalid description {description!r}"
            )

        input_schema = entry.get("inputSchema")
        if not isinstance(input_schema, dict):
            return _warning_entry(
                f"{server_key}: tool {name!r} has invalid inputSchema {input_schema!r}"
            )

        missing_fields = [f for f in _REQUIRED_SCHEMA_V2_FIELDS if f not in entry]
        if missing_fields:
            return _warning_entry(
                f"{server_key}: tool {name!r} missing required schema-2.0 field(s): "
                f"{', '.join(missing_fields)}"
            )

        schema_errors = validate_tool_schema_v2(entry)
        if schema_errors:
            return _warning_entry(
                f"{server_key}: tool {name!r} failed schema-2.0 validation: "
                f"{'; '.join(schema_errors)}"
            )

        for field_name, expected_type in (
            ("status", str),
            ("enabled", bool),
        ):
            if field_name in entry and not isinstance(entry[field_name], expected_type):
                return _warning_entry(
                    f"{server_key}: tool {name!r} has invalid {field_name} "
                    f"{entry[field_name]!r} (expected {expected_type.__name__})"
                )

        capabilities = entry.get("capabilities")
        if capabilities is not None and not isinstance(capabilities, list):
            return _warning_entry(
                f"{server_key}: tool {name!r} on server {server_key!r}: "
                "capabilities must be a list"
            )

        return entry, None

    def _dedupe_and_build(
        self, entries: list[_RawEntry]
    ) -> tuple[RuntimeToolRegistry, list[StartupCheckOutcome]]:
        """Group entries by tool name, build RuntimeTools, and exclude duplicates.

        Names reported by exactly one server become a RuntimeTool. Names
        reported by more than one distinct server are excluded from the
        registry entirely (per this module's docstring), each producing one
        FATAL finding — tool is unusable when duplicated across servers.

        Every entry reaching this method has already passed
        `_validate_and_normalize_entry()`'s hard schema-2.0 requirement, so
        `is_write`/`requires_serial`/`resource_scope_kind`/`resource_scope_keys`
        are guaranteed present — they are indexed directly (`entry[...]`), not
        defaulted via `.get()`.
        """
        by_name: dict[str, list[_RawEntry]] = {}
        for server_key, server_url, entry in entries:
            name = str(entry["name"])
            by_name.setdefault(name, []).append((server_key, server_url, entry))

        findings: list[StartupCheckOutcome] = []
        built: dict[str, RuntimeTool] = {}
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
            built[name] = build_runtime_tool(
                name=name,
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
        return RuntimeToolRegistry(tools=built), findings

    def _is_strict(self) -> bool:
        """Return True when strict mode is enabled."""
        return bool(getattr(self._ctx.cfg.tool, "tool_definitions_strict", False))

    def _is_fatal_severity(self) -> bool:
        """Return True when findings should be FATAL per the unified severity scheme.

        `is_fatal = strict or (security_profile == PRODUCTION)` — applies to all
        findings emitted by this service (duplicates, drift, tool-definitions,
        malformed-capabilities).
        """
        return self._is_strict() or (
            self._ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION
        )

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
        status = (
            StartupCheckStatus.FATAL
            if self._is_fatal_severity()
            else StartupCheckStatus.WARNING
        )
        return [
            StartupCheckOutcome(
                source=_SOURCE,
                status=status,
                message=f"Live routing drift [{sk}]: {msgs}",
            )
            for sk, msgs in drift.items()
        ]

    async def _check_tool_definitions_finding(self) -> StartupCheckOutcome | None:
        """Wrap `_check_tool_definitions` to surface failures as data, not exceptions.

        Converts any RuntimeError raised by the helper into a
        StartupCheckOutcome with the unified severity instead of letting it
        propagate — this resolves the old quirk where strict-mode drift
        detection was silently downgraded to "skipped" by an unrelated
        exception handler.
        """
        try:
            result = await _check_tool_definitions(self._ctx, strict=self._is_strict())
            if result.has_issues:
                status = (
                    StartupCheckStatus.FATAL
                    if self._is_fatal_severity()
                    else StartupCheckStatus.WARNING
                )
                return StartupCheckOutcome(
                    source=_SOURCE,
                    status=status,
                    message="; ".join(result.warning_messages()),
                )
            return None
        except RuntimeError as exc:
            status = (
                StartupCheckStatus.FATAL
                if self._is_fatal_severity()
                else StartupCheckStatus.WARNING
            )
            return StartupCheckOutcome(source=_SOURCE, status=status, message=str(exc))
