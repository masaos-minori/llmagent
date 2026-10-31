"""tests/tools/test_generate_reference_table.py

Unit tests for tools/generate_reference_table.py: the agent/eventbus/memory
class/function reference generators, regression coverage for the pre-existing
rag/mcp/deployment generators, the manifest mode (schema validity, byte
determinism, two-way drift) and the --check output contract.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

import tools.generate_reference_table as grt
from tools import _contract_manifests as cm
from tools.generate_reference_table import (
    generate_agent_reference_table,
    generate_deployment_reference_table,
    generate_eventbus_reference_table,
    generate_mcp_reference_table,
    generate_memory_reference_table,
    generate_rag_config_table,
)

_FIXTURE_MODULE = '''"""Fixture module for reference-table generator tests."""


class Widget:
    """A small, well-behaved widget."""

    def _private_helper(self) -> None:
        """Must not appear in the generated table."""


def build_widget(name: str, count: int = 1) -> "Widget":
    """Build a Widget instance."""
    return Widget()


def _private_function() -> None:
    """Must not appear in the generated table."""
'''


def test_agent_reference_table_extracts_public_symbols(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "widget.py").write_text(_FIXTURE_MODULE, encoding="utf-8")
    monkeypatch.setattr("tools.generate_reference_table.AGENT_DIR", tmp_path)
    table = generate_agent_reference_table()
    assert "`Widget`" in table
    assert "Build a Widget instance." in table
    assert "class Widget" in table
    assert "def build_widget(name, count)" in table
    assert "_private_helper" not in table
    assert "_private_function" not in table


def test_eventbus_reference_table_extracts_public_symbols(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "widget.py").write_text(_FIXTURE_MODULE, encoding="utf-8")
    monkeypatch.setattr("tools.generate_reference_table.EVENTBUS_DIR", tmp_path)
    table = generate_eventbus_reference_table()
    assert "`Widget`" in table
    assert "`build_widget`" in table


def test_memory_reference_table_extracts_public_symbols(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "widget.py").write_text(_FIXTURE_MODULE, encoding="utf-8")
    monkeypatch.setattr("tools.generate_reference_table.MEMORY_DIR", tmp_path)
    table = generate_memory_reference_table()
    assert "`Widget`" in table
    assert "`build_widget`" in table


def test_agent_reference_table_empty_directory_returns_header_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("tools.generate_reference_table.AGENT_DIR", tmp_path)
    table = generate_agent_reference_table()
    assert table == "| File | Class/Function | Signature | Summary |\n|---|---|---|---|"


def test_agent_reference_table_skips_private_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "_internal.py").write_text(_FIXTURE_MODULE, encoding="utf-8")
    monkeypatch.setattr("tools.generate_reference_table.AGENT_DIR", tmp_path)
    table = generate_agent_reference_table()
    assert "Widget" not in table


def test_agent_reference_table_skips_class_with_no_docstring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "plain.py").write_text("class Plain:\n    pass\n", encoding="utf-8")
    monkeypatch.setattr("tools.generate_reference_table.AGENT_DIR", tmp_path)
    table = generate_agent_reference_table()
    assert "`Plain`" in table
    assert "class Plain" in table
    assert "| —" in table or " | — |" in table


# ---------------------------------------------------------------------------
# Regression: existing rag/mcp/deployment generators unaffected
# ---------------------------------------------------------------------------


def test_existing_generators_unaffected() -> None:
    assert generate_rag_config_table().startswith("| Key | Default | Description |")
    assert generate_mcp_reference_table().startswith(
        "| Server | Port | Tool Count | Tool Names |"
    )
    assert generate_deployment_reference_table().startswith(
        "| DB | Config key | Set in `agent.toml`? |"
    )


# ---------------------------------------------------------------------------
# Synthetic-repo fixtures (manifest mode sources; tmp paths only)
# ---------------------------------------------------------------------------

_DEPLOYMENT_SOURCES: dict[str, str] = {
    "config/agent.toml": 'session_db_path = "/var/lib/llm/session.sqlite"\n',
    "scripts/db/config.py": (
        "class DbConfig:\n"
        '    session_db_path: str = ""\n'
        "    history_db_path: str | None = None\n"
    ),
    "scripts/db/schema_sql.py": 'WORKFLOW_SCHEMA_VERSION = "1.1.0"\n',
    "scripts/eventbus/schema.sql": (
        "CREATE TABLE eventbus_events (id INTEGER);\nPRAGMA user_version = 5;\n"
    ),
}

_FULL_SOURCES: dict[str, str] = {
    **_DEPLOYMENT_SOURCES,
    "config/agent.toml": (
        'session_db_path = "/var/lib/llm/session.sqlite"\n\n'
        "[mcp_servers.alpha]\n"
        'url = "http://127.0.0.1:8101"\n\n'
        "[mcp_servers.demo]\n"
        'url = "http://127.0.0.1:8102"\n'
    ),
    "scripts/mcp_servers/alpha/alpha.py": (
        "TOOL_LIST = [\n"
        '    {"name": "alpha_one", "description": "x"},\n'
        '    {"name": "alpha_two", "description": "x"},\n'
        "]\n"
    ),
    "scripts/mcp_servers/demo/demo.py": (
        'TOOL_LIST = [\n    {"name": "demo_run", "description": "x"},\n]\n'
    ),
    "scripts/eventbus/auth.py": (
        "from enum import StrEnum\n\n\n"
        "class Role(StrEnum):\n"
        '    ADMIN = "admin"\n'
        '    CONSUMER = "consumer"\n\n\n'
        "_ROUTE_ROLE_MAP: dict[str, set[Role]] = {\n"
        '    "/publish": {Role.ADMIN},\n'
        '    "/events": {Role.ADMIN, Role.CONSUMER},\n'
        "}\n"
    ),
    "scripts/agent/services/config_field_registry.py": (
        "_FIELDS = [\n"
        '    ConfigFieldRegistry("theme", "ui", True, _validate_theme),\n'
        '    ConfigFieldRegistry("max_retries", "network", False),\n'
        "]\n"
    ),
    "scripts/shared/security/posture_contract.py": (
        'COMMON_CHECK_IDS = ("check_proc", "check_perms")\n\n'
        "REQUIRED_CHECK_IDS: dict[str, tuple[str, ...]] = {\n"
        '    "agent": COMMON_CHECK_IDS + ("check_agent_sandbox",),\n'
        '    "rag": COMMON_CHECK_IDS,\n'
        "}\n"
    ),
    "docs/10_adr/adr_01_index.md": (
        "# ADR Index\n\n"
        "## ADR Invariant Verification Matrix\n\n"
        "| ADR / Invariant | Invariant | Gate | Timing | Blocking | Verification Status |\n"
        "|---|---|---|---|---|---|\n"
        "| ADR-001 INV-01 | gate must run | Unit Test | CI | Blocking | "
        "Confirmed (`tests/tools/test_fake.py::test_gate`, passing) |\n"
        "| ADR-002 INV-02 | release review | Manual Review | Startup | Deployment Blocking | "
        "Manual — procedure: review scripts/. Cadence: nightly Expected evidence: "
        "a recorded review Owner: qa Exception: exc-002 |\n"
    ),
    "scripts/agent/widget.py": _FIXTURE_MODULE,
    "scripts/eventbus/widget.py": _FIXTURE_MODULE,
    "scripts/agent/memory/widget.py": _FIXTURE_MODULE,
}


def _synthetic_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sources: dict[str, str]
) -> None:
    """Write the fixture sources under tmp_path and repoint every generator
    constant the requested manifests read from."""
    for rel, text in sources.items():
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    monkeypatch.setattr(grt, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(grt, "MANIFEST_DIR", tmp_path / "registry" / "manifests")
    monkeypatch.setattr(grt, "AGENT_TOML", tmp_path / "config" / "agent.toml")
    monkeypatch.setattr(grt, "DB_CONFIG_SRC", tmp_path / "scripts" / "db" / "config.py")
    monkeypatch.setattr(
        grt, "DB_SCHEMA_SQL_SRC", tmp_path / "scripts" / "db" / "schema_sql.py"
    )
    monkeypatch.setattr(
        grt, "EVENTBUS_SCHEMA_SQL_SRC", tmp_path / "scripts" / "eventbus" / "schema.sql"
    )
    monkeypatch.setattr(
        grt, "EVENTBUS_AUTH_SRC", tmp_path / "scripts" / "eventbus" / "auth.py"
    )
    monkeypatch.setattr(
        grt,
        "CONFIG_FIELD_REGISTRY_SRC",
        tmp_path / "scripts" / "agent" / "services" / "config_field_registry.py",
    )
    monkeypatch.setattr(
        grt,
        "POSTURE_CONTRACT_SRC",
        tmp_path / "scripts" / "shared" / "security" / "posture_contract.py",
    )
    monkeypatch.setattr(grt, "MCP_SERVERS_DIR", tmp_path / "scripts" / "mcp_servers")
    monkeypatch.setattr(grt, "AGENT_DIR", tmp_path / "scripts" / "agent")
    monkeypatch.setattr(grt, "EVENTBUS_DIR", tmp_path / "scripts" / "eventbus")
    monkeypatch.setattr(grt, "MEMORY_DIR", tmp_path / "scripts" / "agent" / "memory")
    import tools.check_adr_invariant_matrix as matrix_mod

    monkeypatch.setattr(
        matrix_mod, "ADR_INDEX", tmp_path / "docs" / "10_adr" / "adr_01_index.md"
    )


def _write_committed_manifests(names: list[str]) -> None:
    for name in names:
        grt.write_manifest(grt.build_manifest(name), grt.MANIFEST_DIR)


# ---------------------------------------------------------------------------
# Manifest generation: schema validity, byte determinism, entry contents
# ---------------------------------------------------------------------------


class TestManifestGeneration:
    def test_all_manifests_schema_valid_and_deterministic(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _synthetic_repo(tmp_path, monkeypatch, _FULL_SOURCES)
        schema = json.loads(Path(cm.SCHEMA_PATH).read_text(encoding="utf-8"))
        for name in grt._MANIFEST_BUILDERS:
            first = grt.build_manifest(name)
            second = grt.build_manifest(name)
            assert cm.dump_manifest(first) == cm.dump_manifest(second)
            jsonschema.validate(first, schema)
            assert "generated_at" not in cm.dump_manifest(first)

    def test_manifest_entries_match_synthetic_sources(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _synthetic_repo(tmp_path, monkeypatch, _FULL_SOURCES)
        tools = [e["tool"] for e in grt.build_manifest("tool_ownership")["entries"]]
        assert tools == ["alpha_one", "alpha_two", "demo_run"]
        endpoints = grt.build_manifest("mcp_endpoints")["entries"]
        assert endpoints[0] == {
            "server": "alpha",
            "port": 8101,
            "tools": ["alpha_one", "alpha_two"],
        }
        roles = grt.build_manifest("eventbus_route_roles")["entries"]
        assert roles == [
            {"route": "/events", "roles": ["ADMIN", "CONSUMER"]},
            {"route": "/publish", "roles": ["ADMIN"]},
        ]
        db = grt.build_manifest("db_schema_versions")["entries"]
        assert [(e["kind"], e["name"]) for e in db] == [
            ("db_path", "history.sqlite"),
            ("db_path", "session.sqlite"),
            ("schema", "eventbus"),
            ("schema", "workflow"),
        ]
        fields = grt.build_manifest("config_ownership")["entries"]
        assert fields[0] == {
            "field": "max_retries",
            "section": "network",
            "hot_reloadable": False,
            "validator": None,
        }
        health = grt.build_manifest("health_contracts")["entries"]
        assert health[0]["server"] == "agent"
        assert health[0]["checks"] == [
            "check_agent_sandbox",
            "check_perms",
            "check_proc",
        ]
        assert health[0]["disposition"] == "fail-fast"
        coverage = grt.build_manifest("invariant_coverage")["entries"]
        assert [e["adr"] for e in coverage] == ["ADR-001", "ADR-002"]
        assert coverage[1]["exception"] == "exc-002"
        assert coverage[1]["cadence"] == "nightly"

    def test_unknown_manifest_name_rejected(self) -> None:
        with pytest.raises(cm.ManifestError):
            cm.envelope("bogus_manifest", ["config/agent.toml"], [])


# ---------------------------------------------------------------------------
# Two-way drift: manifest vs source, block vs manifest
# ---------------------------------------------------------------------------


class TestManifestDrift:
    def test_missing_manifest_is_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _synthetic_repo(tmp_path, monkeypatch, _DEPLOYMENT_SOURCES)
        doc = tmp_path / "doc.md"
        doc.write_text("# Doc\n", encoding="utf-8")
        monkeypatch.setattr(grt, "DOMAIN_DOCS", {"deployment": doc})
        doc.write_text(grt.render_updated_doc("deployment", doc.read_text()))
        assert grt.check_drift(["deployment"]) == [
            "registry/manifests/db_schema_versions.yaml (manifest missing)",
        ]

    def test_manifest_stale_vs_source(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _synthetic_repo(tmp_path, monkeypatch, _DEPLOYMENT_SOURCES)
        _write_committed_manifests(["db_schema_versions"])
        doc = tmp_path / "doc.md"
        doc.write_text("# Doc\n", encoding="utf-8")
        monkeypatch.setattr(grt, "DOMAIN_DOCS", {"deployment": doc})
        doc.write_text(grt.render_updated_doc("deployment", doc.read_text()))
        assert grt.check_drift(["deployment"]) == []

        (tmp_path / "scripts/eventbus/schema.sql").write_text(
            "CREATE TABLE eventbus_events (id INTEGER);\nPRAGMA user_version = 6;\n",
            encoding="utf-8",
        )
        assert grt.check_drift(["deployment"]) == [
            "registry/manifests/db_schema_versions.yaml (manifest stale)"
        ]

    def test_block_stale_vs_manifest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _synthetic_repo(tmp_path, monkeypatch, _DEPLOYMENT_SOURCES)
        _write_committed_manifests(["db_schema_versions"])
        doc = tmp_path / "doc.md"
        doc.write_text("# Doc\n", encoding="utf-8")
        monkeypatch.setattr(grt, "DOMAIN_DOCS", {"deployment": doc})
        doc.write_text(grt.render_updated_doc("deployment", doc.read_text()))
        assert grt.check_drift(["deployment"]) == []

        doc.write_text(
            doc.read_text().replace("| DB | Config key |", "| DB | HAND-EDIT |", 1),
            encoding="utf-8",
        )
        assert grt.check_drift(["deployment"]) == ["doc.md (--type deployment)"]


# ---------------------------------------------------------------------------
# --check output contract on the live docs
# ---------------------------------------------------------------------------


class TestCheckDrift:
    """--check detects hand edits and stale guarded blocks without writing.

    Fixtures are extended for the manifest-coupled check_drift (doc 05): a
    synthetic deployment repo stands in for the live sources; the reported
    DRIFT strings asserted here are the unchanged CLI contract.
    """

    def test_live_docs_have_no_drift(self) -> None:
        from tools.generate_reference_table import DOMAIN_DOCS, check_drift

        assert check_drift(list(DOMAIN_DOCS)) == []

    def test_hand_edit_inside_guard_is_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _synthetic_repo(tmp_path, monkeypatch, _DEPLOYMENT_SOURCES)
        doc = tmp_path / "doc.md"
        doc.write_text("# Doc\n", encoding="utf-8")
        monkeypatch.setattr(grt, "DOMAIN_DOCS", {"deployment": doc})
        doc.write_text(grt.render_updated_doc("deployment", doc.read_text()))
        _write_committed_manifests(["db_schema_versions"])
        assert grt.check_drift(["deployment"]) == []

        edited = doc.read_text().replace("| ", "| HAND-EDIT ", 1)
        doc.write_text(edited, encoding="utf-8")
        assert grt.check_drift(["deployment"]) == ["doc.md (--type deployment)"]
        assert doc.read_text() == edited  # --check never writes

    def test_missing_guard_is_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _synthetic_repo(tmp_path, monkeypatch, _DEPLOYMENT_SOURCES)
        _write_committed_manifests(["db_schema_versions"])
        doc = tmp_path / "doc.md"
        doc.write_text("# no guard\n", encoding="utf-8")
        monkeypatch.setattr(grt, "DOMAIN_DOCS", {"deployment": doc})
        assert grt.check_drift(["deployment"]) == ["doc.md (guarded block missing)"]
