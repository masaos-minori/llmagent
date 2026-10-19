"""scripts/agent/services/mcp_tool_discovery_fetch.py — per-server /v1/tools fetch and entry validation.

Fetch and validation layer for agent/services/mcp_tool_discovery.py. One HTTP round-trip
per HTTP-transport MCP server, plus every response-level and entry-level rejection that a
round-trip can produce:
  _fetch_server_tools: one server's /v1/tools round-trip, returning entries, findings and
    an unreachable flag
  _schema_version_error: response-level schema_version acceptance
  _normalize_entries: response body to raw (server_key, server_url, entry) tuples
  _validate_entry / _entry_schema_error / _entry_optional_field_error: the schema-2.0
    contract check for a single tool entry
  _warning_fetch_result / _warning_entry: WARNING findings for a rejected fetch or entry
  _SOURCE / _unified_findings: the startup source id and StartupCheckOutcome construction
    shared with the service

Severity escalation, duplicate exclusion, registry building and drift findings stay on the
service side. Nothing here probes `/health` (`shared/mcp_config.py`'s
`get_effective_health_timeout()` is used only as the request timeout), it never decides a
Security Posture gate, and it never contacts a server other than the one it was given.
"""

from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus
from logging import getLogger

import httpx
from mcp_servers.server import MCP_TOOL_SCHEMA_VERSION
from shared.mcp_config import McpServerConfig, get_effective_health_timeout
from shared.resource_scope import validate_tool_schema_v2

from agent.shared.health_models import StartupCheckOutcome, StartupCheckStatus

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


async def _fetch_server_tools(
    http_client: httpx.AsyncClient, server_key: str, cfg: McpServerConfig
) -> tuple[list[_RawEntry], list[StartupCheckOutcome], bool]:
    """Fetch one server's /v1/tools response. Returns (entries, findings, is_unreachable)."""
    try:
        resp = await http_client.get(
            f"{cfg.url}{_TOOLS_ENDPOINT}",
            headers=cfg.auth_headers(),
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


def _validate_entry(
    server_key: str, server_url: str, entry: object
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


def _unified_findings(
    messages: Iterable[str], status: StartupCheckStatus
) -> list[StartupCheckOutcome]:
    """Wrap already-formatted messages as findings carrying the unified severity status."""
    return [
        StartupCheckOutcome(source=_SOURCE, status=status, message=message)
        for message in messages
    ]


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
    for raw_entry in tools:
        normalized, finding = _validate_entry(server_key, server_url, raw_entry)
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
