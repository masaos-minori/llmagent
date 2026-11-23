"""
tests/integration/test_standard_config_integration.py

Integration coverage for the reduced (standard) configuration files: the values the agent
process uses must arrive from config/ through the normal startup path, not from a
hand-built dictionary (agentcfg006 REQ-001, AC-1, AC-2, AC-3, AC-5).

The tests read the real files under config/ and read them again through the loader the
startup path uses, so an assertion compares the shipped file against the behaviour the
code produces from it. Where a test claims that a value "comes from the file", it first
shows the file's value differs from the code default; a test cannot pass by reading the
default. Writable state paths are moved into pytest's tmp_path before any database object
is constructed, so nothing is written to production state and no test opens a network
connection.
"""

from __future__ import annotations

import sqlite3
import tomllib
from pathlib import Path
from typing import Any

import pytest
from agent.config_builders import build_agent_config, load_config
from agent.config_dataclasses import LLMConfig, MemoryConfig
from agent.memory.config_path import resolve_memory_jsonl_dir
from agent.production_config_validator import ProductionConfigValidator
from agent.services.config_validators import check_agent_refiner_keys
from agent.tool_enums import RiskLevel
from agent.tool_policy import check_allowed_root, classify_risk, is_plan_mode_blocked
from db.config import build_db_config
from db.helper import SQLiteHelper
from db.maintenance import (
    DbMaintenanceConfig,
    MaintenanceMode,
    RetentionConfig,
    prune_old_memories,
    purge_old_sessions,
)
from db.schema_sql import build_session_schema_sql
from db.store_protocols import get_embedding_dims
from shared.config_loader import ConfigLoader
from shared.config_validator import RagConfigValidator
from shared.runtime_tool_registry import RuntimeToolRegistry

from tests.integration.conftest import apply_session_schema
from tests.shared.runtime_tool_factory import build_fixture_runtime_tool

pytestmark = pytest.mark.integration

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"

# Keys the RAG Pipeline MCP server owns in its own file (ADR-002); none of them is an
# Agent setting, so the merged agent config must not carry them.
_RAG_PIPELINE_OWNED_KEYS = (
    "use_mqe",
    "use_rrf",
    "use_rerank",
    "use_refiner",
    "refiner_max_tokens",
    "refiner_max_chars_per_chunk",
    "refiner_timeout",
    "mqe_n_queries",
    "top_k_search",
    "top_k_rerank",
    "rag_top_k",
    "rag_min_score",
    "max_chunks_per_doc",
    "rrf_k",
)

# The paths a runtime object writes to; moved into tmp_path so the tests never touch
# production state. Only the database paths are validated for existence, so only those
# are moved.
_DB_PATH_KEYS = ("rag_db_path", "session_db_path", "workflow_db_path")

_TEST_SERVER = "standard_config_integration"


def _real_file(name: str) -> dict[str, Any]:
    """Read one real config/ file without merging, as its owning process reads it."""
    return tomllib.loads((CONFIG_DIR / name).read_text(encoding="utf-8"))


def _startup_mapping() -> dict[str, Any]:
    """Read config/ through the same loader and merge order the startup path uses."""
    return ConfigLoader().load_all(strict=True)


def _db_paths_in_tmp(cfg: dict[str, Any], root: Path) -> dict[str, Any]:
    """Copy a mapping with the writable database paths moved under a temp root."""
    mapping = dict(cfg)
    for key in _DB_PATH_KEYS:
        mapping[key] = str(root / Path(str(cfg[key])).name)
    return mapping


def _field_default(cls: Any, name: str) -> Any:
    """The documented code default for a typed-configuration field."""
    return cls.__dataclass_fields__[name].default


def _assert_from_file(
    actual: Any, file_value: Any, default_value: Any, key: str
) -> None:
    """Assert the value came from the file: the file must differ from the code default."""
    assert file_value != default_value, (
        f"{key}: the file's value equals the code default, so this test cannot show "
        "the file is the source"
    )
    assert actual == file_value, f"{key}: runtime value does not match config/"


def _fixture_registry(tool_name: str, tier: str, **kwargs: Any) -> RuntimeToolRegistry:
    """Build a registry with one declared tool, so a policy reads a declaration."""
    tool = build_fixture_runtime_tool(
        tool_name, _TEST_SERVER, agent_safety_tier=tier, **kwargs
    )
    return RuntimeToolRegistry(
        tools={tool_name: tool}, allowed_servers=frozenset({_TEST_SERVER})
    )


def _session_db(tmp_path: Path, db_config: Any) -> Path:
    """Create a session database from the real DDL and return its path.

    sqlite-vec is not present on every runner, so the vec0 table may be absent; the
    memory delete store clears that table too, so a plain stand-in with the same name is
    created when it is missing (the convention the memory tests already use).
    """
    db_path = Path(db_config.session_db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        apply_session_schema(conn, build_session_schema_sql(get_embedding_dims()))
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE name = 'memories_vec'"
        ).fetchone()
        if row is None:
            conn.execute(
                "CREATE TABLE memories_vec (memory_id TEXT PRIMARY KEY, embedding BLOB)"
            )
        conn.commit()
    finally:
        conn.close()
    return db_path


def _known_tools() -> set[str]:
    """The ownership expected set the drift check reads: the catalog's owned_tools."""
    catalog = _real_file("tool_catalog.toml")
    return {
        name
        for server in catalog["server"].values()
        for name in server.get("owned_tools", [])
    }


# ---------------------------------------------------------------------------
# AC-1: the standard config is accepted by the startup validation path
# ---------------------------------------------------------------------------


def test_standard_config_passes_strict_validation_through_the_startup_path(
    tmp_path: Path,
) -> None:
    """The real config/agent.toml is accepted by the production validator, and the startup
    builder assembles the typed configuration from it without error."""
    cfg = _startup_mapping()
    result = ProductionConfigValidator().validate(cfg, known_tools=_known_tools())
    assert result.errors == [], f"the real config must not be rejected: {result.errors}"
    assert result.ok is True

    runtime = build_agent_config(cfg_override=_db_paths_in_tmp(cfg, tmp_path))
    defaults = LLMConfig()
    # Each key below carries a value in the file that differs from the code default, so a
    # passing assertion shows the value arrived from config/.
    _assert_from_file(
        runtime.llm.http_timeout,
        cfg["http_timeout"],
        defaults.http_timeout,
        "http_timeout",
    )
    _assert_from_file(
        runtime.llm.llm_max_tokens,
        cfg["llm_max_tokens"],
        defaults.llm_max_tokens,
        "llm_max_tokens",
    )
    _assert_from_file(
        runtime.llm.history_protect_turns,
        cfg["history_protect_turns"],
        defaults.history_protect_turns,
        "history_protect_turns",
    )
    _assert_from_file(
        runtime.llm.sse_reconnect_max,
        cfg["sse_reconnect_max"],
        defaults.sse_reconnect_max,
        "sse_reconnect_max",
    )
    _assert_from_file(
        runtime.memory.memory_min_importance,
        cfg["memory_min_importance"],
        _field_default(MemoryConfig, "memory_min_importance"),
        "memory_min_importance",
    )


# ---------------------------------------------------------------------------
# AC-2 / AC-5: the agent reads only the settings it owns
# ---------------------------------------------------------------------------


def test_agent_carries_only_the_settings_the_agent_owns() -> None:
    """The merged agent config carries no key the RAG Pipeline MCP server owns in its own
    file, and the refiner keys the Agent must not carry are absent (ADR-002)."""
    cfg = _startup_mapping()

    carried = [key for key in _RAG_PIPELINE_OWNED_KEYS if key in cfg]
    assert carried == [], f"Agent-side keys owned by the RAG server file: {carried}"
    assert check_agent_refiner_keys(cfg) == []

    # The RAG server's own file is its config source; the agent-side entry carries only
    # transport fields.
    own = _real_file("rag_pipeline_mcp_server.toml")
    assert own["use_mqe"] is True
    assert own["refiner_max_tokens"] == 512

    server = cfg["mcp_servers"]["rag_pipeline"]
    transport_fields = {"transport", "url", "startup_mode", "auth_token", "role", "cmd"}
    extra = set(server) - transport_fields
    assert extra == set(), f"non-transport keys in the agent-side entry: {extra}"
    assert server["role"] == "query"


def test_rag_pipeline_config_is_validated_by_its_own_owner() -> None:
    """The RAG Pipeline MCP server starts from config/rag_pipeline_mcp_server.toml, and the
    same fail-fast validation its service runs at startup accepts the real file."""
    own = ConfigLoader().load("rag_pipeline_mcp_server.toml")
    result = RagConfigValidator().validate(own)
    assert result.ok is True, (
        f"the RAG server's own config must validate: {result.errors}"
    )


def test_tool_catalog_is_the_single_owner_of_tool_facts() -> None:
    """Every server the agent config declares is required by default (ADR-004) and has a
    matching catalog table with the capability whose absence is fatal at startup and the
    ownership set the drift check reads; the reduced agent config no longer carries the
    per-tool maps the catalog owns."""
    cfg = _startup_mapping()
    catalog = _real_file("tool_catalog.toml")

    for key, server in cfg["mcp_servers"].items():
        entry = catalog["server"].get(key)
        assert entry is not None, f"{key}: server absent from config/tool_catalog.toml"
        assert entry.get("required_capability"), f"{key}: no required_capability"
        assert entry.get("owned_tools"), f"{key}: no owned_tools"
        assert server.get("required", True) is True, (
            f"{key}: a required server cannot be weakened"
        )

    for removed in ("tool_safety_tiers", "tool_names", "tool_definitions"):
        assert removed not in cfg, f"{removed} is owned by config/tool_catalog.toml"


# ---------------------------------------------------------------------------
# Plan mode and approval decisions driven by the real config
# ---------------------------------------------------------------------------


def test_plan_mode_blocks_the_configured_denylist() -> None:
    """Plan mode uses the shipped denylist as an operational exception on top of the
    declared tier: a tool whose declaration is READ_ONLY is still denied because the real
    config names it, and a tool the denylist does not name is allowed."""
    runtime = build_agent_config(cfg_override=_startup_mapping())
    denylist = runtime.tool.plan_blocked_tools
    assert denylist, "the real config must name the operational denylist"

    # A READ_ONLY declaration would pass the tier rule, so the denylist entry is what
    # denies the call here.
    listed = denylist[0]
    registry = _fixture_registry(listed, "READ_ONLY")
    assert is_plan_mode_blocked(runtime, listed, registry)

    not_listed = "list_directory"
    assert not_listed not in denylist, "the control tool must not be in the denylist"
    assert not is_plan_mode_blocked(
        runtime, not_listed, _fixture_registry(not_listed, "READ_ONLY")
    )
    # A tool with no declaration fails closed.
    assert is_plan_mode_blocked(
        runtime, "unknown_tool", _fixture_registry(listed, "READ_ONLY")
    )


def test_approval_escalation_uses_the_real_protected_paths_and_jail() -> None:
    """A declared MEDIUM path tool is escalated only by the shipped protected paths, and
    the shipped allowed_root still denies a path outside the jail."""
    runtime = build_agent_config(cfg_override=_startup_mapping())
    protected = runtime.approval.approval_protected_paths
    assert protected, "the real config must name the protected paths"

    tool = "delete_file"
    registry = _fixture_registry(
        tool,
        "WRITE_DANGEROUS",
        resource_scope_keys={"path": "path"},
        resource_scope_kind="path",
    )
    inside = str(Path(runtime.approval.allowed_root) / "db" / "row")
    assert inside.startswith(protected[0]), (
        "the allowed root must sit inside a protected path"
    )
    assert classify_risk(runtime, tool, {"path": inside}, registry) == RiskLevel.HIGH

    outside = "/tmp/standard-config-integration/row"
    assert not any(outside.startswith(prefix) for prefix in protected), (
        "the control path must sit outside every protected path"
    )
    assert classify_risk(runtime, tool, {"path": outside}, registry) == RiskLevel.MEDIUM
    assert not check_allowed_root(runtime, tool, {"path": outside}, registry)


# ---------------------------------------------------------------------------
# Reload path
# ---------------------------------------------------------------------------


def test_config_loader_has_no_cache_and_the_reload_path_rebuilds_from_the_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`load_config()` is documented as always fresh, so a change written to a copy of the
    real config is seen by the next call, and the `/reload` path assembles the typed
    configuration from the values it is given."""
    copy = tmp_path / "config"
    copy.mkdir()
    source = (CONFIG_DIR / "agent.toml").read_text(encoding="utf-8")
    (copy / "agent.toml").write_text(source, encoding="utf-8")
    monkeypatch.setenv("LLMAGENT_CONFIG_DIR", str(copy))

    first = load_config()
    assert first["max_tool_turns"] == _real_file("agent.toml")["max_tool_turns"]

    changed = source.replace("max_tool_turns = 5", "max_tool_turns = 7")
    assert changed != source, "the shipped file must carry the value the test changes"
    (copy / "agent.toml").write_text(changed, encoding="utf-8")

    second = load_config()
    assert second["max_tool_turns"] == 7, "a reload must pick up the changed file"
    assert first["max_tool_turns"] != second["max_tool_turns"]

    runtime = build_agent_config(cfg_override=_db_paths_in_tmp(second, tmp_path))
    assert runtime.tool.max_tool_turns == 7


# ---------------------------------------------------------------------------
# Memory path
# ---------------------------------------------------------------------------


def test_memory_path_uses_the_real_memory_section(tmp_path: Path) -> None:
    """The typed memory configuration and the JSONL resolver read the same file through the
    same loader path, and the shipped retention value is the window the prune applies."""
    cfg = _startup_mapping()
    runtime = build_agent_config(cfg_override=_db_paths_in_tmp(cfg, tmp_path))

    _assert_from_file(
        runtime.memory.memory_min_importance,
        cfg["memory_min_importance"],
        _field_default(MemoryConfig, "memory_min_importance"),
        "memory_min_importance",
    )
    # The resolver resolves the same key through the same helper the builder uses.
    assert resolve_memory_jsonl_dir() == runtime.memory.memory_jsonl_dir

    db_path = _session_db(tmp_path, runtime.db)
    with sqlite3.connect(str(db_path)) as conn:
        for memory_id, age_days in (("recent", 1), ("expired", 120)):
            conn.execute(
                "INSERT INTO memories (memory_id, memory_type, content, importance, updated_at) "
                "VALUES (?, 'semantic', 'entry', 0.6, strftime('%Y-%m-%dT%H:%M:%SZ', 'now', ?))",
                (memory_id, f"-{age_days} days"),
            )
        conn.commit()

    with SQLiteHelper("session", db_config=runtime.db).open(write_mode=True) as db:
        result = prune_old_memories(db, runtime.memory.memory_retention_days)

    assert result.success is True
    assert cfg["memory_retention_days"] == 90, (
        "the shipped window is the value the prune applies"
    )
    data = result.data
    assert data is not None, "the prune reports its counts"
    # Only the entry older than that window is removed.
    assert data["deleted"] == 1
    assert data["pruned_ids"] == ["expired"]


# ---------------------------------------------------------------------------
# Database maintenance path
# ---------------------------------------------------------------------------


def test_database_maintenance_applies_the_real_retention_policy(tmp_path: Path) -> None:
    """The typed maintenance configuration is built from the real mapping by its owning
    module, and the session purge applies exactly those limits (the shipped age rule is 30
    days, not the 90-day default)."""
    cfg = _startup_mapping()
    mapping = _db_paths_in_tmp(cfg, tmp_path)
    maintenance = DbMaintenanceConfig.from_mapping(cfg)
    runtime = build_agent_config(cfg_override=mapping)

    # Both typed configurations are the ones the owning modules build from the mapping.
    assert maintenance == runtime.maintenance, (
        "the builder must produce the same typed values"
    )
    assert build_db_config(mapping) == runtime.db, (
        "the typed DB configuration must come from the same mapping the builder used"
    )

    # A default-built configuration shows the file's value is what the test is reading.
    _assert_from_file(
        maintenance.retention_max_age_days,
        cfg["sqlite_retention_max_age_days"],
        _field_default(DbMaintenanceConfig, "retention_max_age_days"),
        "sqlite_retention_max_age_days",
    )

    retention = RetentionConfig.from_typed(runtime.maintenance)
    assert retention.max_age_days == 30 and retention.max_sessions == 100

    db_path = _session_db(tmp_path, runtime.db)
    with sqlite3.connect(str(db_path)) as conn:
        for _ in range(101):
            conn.execute(
                "INSERT INTO sessions (created_at) VALUES (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))"
            )
        conn.execute(
            "INSERT INTO sessions (created_at) VALUES (strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-40 days'))"
        )
        conn.commit()

    with SQLiteHelper("session", db_config=runtime.db).open(write_mode=True) as db:
        result = purge_old_sessions(db, retention, MaintenanceMode.STRICT)

    assert result.success is True
    data = result.data
    assert data is not None, "the purge reports its counts"
    # One session is older than the shipped 30-day window, then one more is beyond the
    # 100-session limit: both rules come from the file rather than from the defaults.
    assert data["age_deleted"] == 1
    assert data["count_deleted"] == 1
    with sqlite3.connect(str(db_path)) as conn:
        remaining = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    assert remaining == 100
