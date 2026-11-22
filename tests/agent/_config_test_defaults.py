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

from db.config import DbConfig
from db.maintenance import DbMaintenanceConfig
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
