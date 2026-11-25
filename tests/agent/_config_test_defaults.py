"""tests/agent/_config_test_defaults.py

Shared overrides for tests that call build_agent_config()/ProductionConfigValidator
against a minimal config dict. ProductionConfigValidator unconditionally requires
a non-empty allowed_tools, a non-empty allowed_root, and a non-empty sqlite_vec_so
(scripts/agent/production_config_validator.py), so any minimal test config dict
must merge these in unless the test specifically exercises the missing/empty
error path (see tests/agent/test_config_builders.py's _MIN_CFG, which
intentionally omits them).

agentcfg003 (REQ-005): the per-tool config maps (approval_risk_rules,
tool_safety_tiers, approval_resource_keys) are removed from the shipped
config/agent.toml, so their fixture mirrors (ALL_APPROVAL_RISK_RULES,
ALL_TOOL_SAFETY_TIERS, GIT_RISK_FLOOR) are removed with them. Tier, risk-floor,
and resource-key inputs now come from the producers' declared tool metadata,
seeded through tests/agent/_producer_registry.py (make_producer_registry /
PRODUCER_TIERS). Only SHIPPED_APPROVAL_PROTECTED_PATHS keeps a shipped-config
mirror for the agent tool policy: approval_protected_paths is a config list the
plan keeps. Config mirrors that other plans still require are kept separately:
SHIPPED_DB_PATH_KEYS and SHIPPED_MEMORY_EMBED_URL mirror the shipped
config/agent.toml for the typed-config contract (Plan agentcfg004).
"""

from typing import Any

from agent.config_builders import agent_config_payload, build_agent_config
from agent.config_dataclasses import AgentConfig, MCPConfig
from db.config import DbConfig
from db.maintenance import DbMaintenanceConfig
from shared.mcp_config import _build_mcp_servers
from shared.tool_registry import get_registry

# A non-empty allowed_root that contains every absolute test path, so the
# path jail (tool_policy.check_allowed_root) passes by default; tests that
# exercise the jail pass their own root. An empty allowed_root now denies
# every path-bearing tool call.
PERMISSIVE_ALLOWED_ROOT: str = "/"

# Mirrors config/agent.toml's sqlite_vec_so. ProductionConfigValidator now
# requires a non-empty sqlite_vec_so (the sqlite-vec library path) for any
# config that reaches build_agent_config(), so minimal test configs must merge
# this in. Tests that exercise the empty/absent error path pass their own value.
PERMISSIVE_SQLITE_VEC_SO: str = "/opt/llm/sqlite-vec/vec0.so"

# Mirrors config/agent.toml's approval_protected_paths. Approval-path
# characterization tests (tests/agent/test_tool_approval_paths.py, Plan row 14)
# must build escalation configs from this mirror instead of a local copy of the
# list, so a shipped-config edit surfaces as fixture drift.
SHIPPED_APPROVAL_PROTECTED_PATHS: list[str] = [
    "/opt/",
    "/etc/",
    "/boot/",
    "/usr/",
    "/bin/",
    "/sbin/",
]

# Every registered tool name, so tests that don't care about allowlist
# restriction aren't accidentally denied a tool call: an empty allowed_tools
# now disables every tool at runtime (RuntimeToolRegistry.apply_policy) in
# explicit_allowlist mode, and is mode-dependent (valid in discovered mode).
ALL_TOOL_NAMES: list[str] = sorted(get_registry().get_all_tool_names())

# Mirrors config/agent.toml's memory_embed_url. The Memory section owns the embedding
# endpoint, and MemoryConfig rejects an empty endpoint while embedding is enabled
# (scripts/agent/config_dataclasses.py), so a fixture that builds a Memory section with
# embedding on must supply a value; tests that exercise the empty-value error path pass
# their own.
SHIPPED_MEMORY_EMBED_URL: str = "http://192.168.11.228:8081"

# Mirrors config/agent.toml's DB path keys. build_db_config() now takes the mapping
# from the process that owns the file, so a minimal config dict must supply the paths
# itself; DbConfig rejects empty paths and an empty sqlite-vec path.
SHIPPED_DB_PATH_KEYS: dict[str, str] = {
    "rag_db_path": "/opt/llm/db/rag.sqlite",
    "session_db_path": "/opt/llm/db/session.sqlite",
    "workflow_db_path": "/opt/llm/db/workflow.sqlite",
    "sqlite_vec_so": PERMISSIVE_SQLITE_VEC_SO,
}

# The typed configuration those mirrored keys resolve to, for tests that construct
# AgentConfig directly instead of through build_agent_config(). conftest.py redirects
# the mirrored paths into the isolation root, so these are valid test paths.
MIN_DB_CONFIG: DbConfig = DbConfig(
    rag_db_path=SHIPPED_DB_PATH_KEYS["rag_db_path"],
    session_db_path=SHIPPED_DB_PATH_KEYS["session_db_path"],
    workflow_db_path=SHIPPED_DB_PATH_KEYS["workflow_db_path"],
    sqlite_vec_so=SHIPPED_DB_PATH_KEYS["sqlite_vec_so"],
)

# DbMaintenanceConfig validates only through from_mapping(); its defaults are the
# shipped values, so tests that construct AgentConfig directly use them.
MIN_MAINTENANCE_CONFIG: DbMaintenanceConfig = DbMaintenanceConfig()

# One declared MCP server. `shared.mcp_config._build_mcp_servers` rejects a missing
# or empty `mcp_servers` section, so any payload that reaches `build_agent_config`
# (including the reload candidate) must carry at least one server definition.
# Reload fixtures use this so the live section and the candidate agree.
MIN_MCP_SERVERS: dict[str, dict[str, object]] = {
    "fixture_server": {
        "transport": "http",
        "url": "http://mcp.local:8100",
        "cmd": ["/opt/llm/bin/fixture_server"],
    }
}


def min_mcp_config() -> MCPConfig:
    """Return the typed MCP section the fixture server resolves to."""
    return MCPConfig(mcp_servers=_build_mcp_servers({"mcp_servers": MIN_MCP_SERVERS}))


# A complete payload for a config-reload fixture. The reload candidate is built
# through `build_agent_config` (REQ-002), so a reload fixture's live config must be
# something the startup entry point itself produced; a hand-built partial
# AgentConfig is not a valid starting point.
RELOAD_FIXTURE_PAYLOAD: dict[str, object] = {
    "llm_url": "http://llm.local:8000",
    "http_timeout": 30.0,
    "llm_retry_base_delay": 1.0,
    "llm_temperature": 0.7,
    "llm_max_tokens": 1000,
    "sse_heartbeat_timeout": 30.0,
    "sse_malformed_retry": 1,
    "sse_reconnect_max": 5,
    "llm_stream_retry_on_heartbeat_timeout": True,
    "llm_stream_retry_on_malformed_chunk": False,
    "context_token_limit": 0,
    "context_char_limit": 8000,
    "context_compress_turns": 4,
    "max_tool_turns": 5,
    "tool_result_max_llm_chars": 4000,
    "serial_tool_calls": False,
    "tool_policy_mode": "discovered",
    "allowed_tools": ALL_TOOL_NAMES,
    "disabled_tools": [],
    "plan_blocked_tools": ["write_file"],
    "masked_fields": ["content", "old_text", "new_text"],
    "allowed_root": PERMISSIVE_ALLOWED_ROOT,
    "approval_protected_paths": SHIPPED_APPROVAL_PROTECTED_PATHS,
    "approval_high_risk_branches": ["main"],
    "approval_shell_safe_prefixes": ["ls"],
    "approval_github_allowed_repos": [],
    "use_memory_layer": True,
    "memory_embed_enabled": True,
    "memory_embed_url": SHIPPED_MEMORY_EMBED_URL,
    "memory_retention_days": 90,
    "memory_max_pinned": 10,
    "memory_local_only": False,
    "mcp_servers": MIN_MCP_SERVERS,
    **SHIPPED_DB_PATH_KEYS,
}


def reload_fixture_config(**overrides: object) -> AgentConfig:
    """Build a reload fixture's live config through the startup entry point.

    `overrides` apply on top of the complete fixture payload, so a test that names
    one field starts from a config the startup path would actually accept.
    """
    return build_agent_config(cfg_override={**RELOAD_FIXTURE_PAYLOAD, **overrides})


def reload_fixture_ctx(**overrides: object) -> Any:
    """Return a reload-test ctx whose live config is startup-built.

    The reload candidate is built through `build_agent_config` (REQ-002), so a
    reload test's ctx.cfg must be a real ``AgentConfig``; the service sync skips
    ``llm``, ``memory``, ``embedding`` and ``retriever`` (all None), while
    ``hist_mgr``, ``tools`` and ``lifecycle`` stay MagicMocks for tests that assert
    on those calls.
    """
    from unittest.mock import MagicMock

    ctx = MagicMock()
    ctx.cfg = reload_fixture_config(**overrides)
    ctx.conv.system_prompt_name = "default"
    ctx.conv.system_prompt_content = "fixture default prompt"
    ctx.conv.history = []
    services = MagicMock()
    for service in ("llm", "memory", "embedding", "retriever"):
        setattr(services, service, None)
    ctx.services_required = services
    return ctx


def reload_candidate(ctx: Any, **overrides: object) -> AgentConfig:
    """Build the candidate `apply_config_dict` would build for this payload (REQ-002)."""
    return build_agent_config(
        cfg_override={**agent_config_payload(ctx.cfg), **overrides}
    )
