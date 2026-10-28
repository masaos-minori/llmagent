"""scripts/agent/services/mcp_tool_discovery_registry.py — duplicate exclusion and RuntimeToolRegistry building.

Registry-building layer for agent/services/mcp_tool_discovery.py. Once the raw
`(server_key, server_url, entry)` tuples are in hand, this module owns the two steps that
turn them into a registry:
  _detect_duplicates: separate unique entries and emit the FATAL finding for a tool name
    reported by more than one server
  _build_runtime_tools: build each RuntimeTool and apply the unavailable-server and
    Security Posture allowlist filters
  _dedupe_and_build: the pair above in order, returning `(registry, dedup_findings)`

Fetching, severity escalation, drift findings and required-tool checks stay on the service
side. Nothing here contacts a server or reads configuration.
"""

from __future__ import annotations

from shared.runtime_tool import RuntimeTool, build_runtime_tool
from shared.runtime_tool_registry import RuntimeToolRegistry

from agent.services.mcp_tool_discovery_fetch import _SOURCE, _RawEntry
from agent.shared.health_models import StartupCheckOutcome, StartupCheckStatus


def _detect_duplicates(
    entries: list[_RawEntry],
) -> tuple[list[_RawEntry], list[StartupCheckOutcome]]:
    """Detect duplicate tool names and separate unique entries.

    Returns (unique_entries, dedup_findings). Duplicate tool names produce
    FATAL findings regardless of strict mode per `mcp_tool_discovery.py`'s documented
    exception to the severity scheme.
    """
    by_name: dict[str, list[_RawEntry]] = {}
    for server_key, server_url, entry in entries:
        name = str(entry["name"])
        by_name.setdefault(name, []).append((server_key, server_url, entry))

    findings: list[StartupCheckOutcome] = []
    unique_entries: list[_RawEntry] = []
    for name, group in by_name.items():
        server_keys = sorted({server_key for server_key, _, _ in group})
        if len(server_keys) > 1:
            # Always fatal — tool is unusable when duplicated across servers
            msg = (
                f"duplicate tool name {name!r} reported by multiple servers: "
                f"{', '.join(server_keys)} — excluded from registry"
            )
            findings.append(
                StartupCheckOutcome(
                    source=_SOURCE, status=StartupCheckStatus.FATAL, message=msg
                )
            )
            continue
        unique_entries.append(group[0])
    return unique_entries, findings


def _build_runtime_tools(
    unique_entries: list[_RawEntry],
    unavailable_servers: frozenset[str],
    allowed_servers: frozenset[str],
) -> RuntimeToolRegistry:
    """Build RuntimeToolRegistry from unique entries with unavailable and posture filtering.

    `allowed_servers` is the posture-derived allowlist (row `19`): a `frozenset` lets only its
    members through, and an empty `frozenset` registers nothing.
    """
    built: dict[str, RuntimeTool] = {}
    for server_key, server_url, entry in unique_entries:
        if server_key in unavailable_servers:
            continue
        name = str(entry["name"])
        built[name] = build_runtime_tool(
            name=name,
            server_key=server_key,
            server_url=server_url,
            description=str(entry.get("description", "")),
            # Every field below is `object`-typed in `_RawEntry`; the fetch layer's
            # `_validate_entry()` has already verified the concrete type of each one, which
            # is why these suppressions narrow an argument rather than hide a missing check.
            input_schema=entry.get("inputSchema"),  # type: ignore[arg-type]  # — dict, verified by _entry_schema_error()
            raw_definition=entry,
            status=str(entry.get("status", "active")),
            is_write=entry["is_write"],  # type: ignore[arg-type]  # — bool, verified by validate_tool_schema_v2()
            requires_serial=entry["requires_serial"],  # type: ignore[arg-type]  # — bool, verified by validate_tool_schema_v2()
            resource_scope_kind=str(entry["resource_scope_kind"]),
            resource_scope_keys=tuple(entry["resource_scope_keys"]),  # type: ignore[arg-type]  # — list, verified by validate_tool_schema_v2()
            enabled_for_llm=bool(entry.get("enabled", True)),
            capabilities=tuple(entry.get("capabilities", []) or []),  # type: ignore[arg-type]  # — list when present, verified by _entry_optional_field_error()
        )
    return RuntimeToolRegistry(tools=built, allowed_servers=allowed_servers)


def _dedupe_and_build(
    entries: list[_RawEntry],
    unavailable_servers: frozenset[str],
    allowed_servers: frozenset[str],
) -> tuple[RuntimeToolRegistry, list[StartupCheckOutcome]]:
    """Group entries by tool name, build RuntimeTools, and exclude duplicates.

    Names reported by exactly one server become a RuntimeTool. Names
    reported by more than one distinct server are excluded from the
    registry entirely (per this module's docstring), each producing one
    FATAL finding — tool is unusable when duplicated across servers.

    Every entry reaching this function has already passed `_validate_entry()`'s hard
    schema-2.0 requirement, so `is_write`/`requires_serial`/`resource_scope_kind`/
    `resource_scope_keys` are guaranteed present — they are indexed directly
    (`entry[...]`), not defaulted via `.get()`.

    `allowed_servers` travels exactly like `unavailable_servers` and reaches the registry unchanged:
    this module transports the gate, it does not decide it.
    """
    unique_entries, dedup_findings = _detect_duplicates(entries)
    registry = _build_runtime_tools(
        unique_entries, unavailable_servers, allowed_servers=allowed_servers
    )
    return registry, dedup_findings
