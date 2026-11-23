"""tests/tools/test_generate_reference_table.py

Unit tests for tools/generate_reference_table.py: the agent/eventbus/memory
class/function reference generators, regression coverage for the pre-existing
rag/mcp/deployment generators, the manifest mode (schema validity, byte
determinism, two-way drift) and the --check output contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

import jsonschema
import pytest

import tools._agent_config_migration as acm
import tools.generate_reference_table as grt
from tools import _contract_manifests as cm
from tools.check_docs_structure import MAX_SIZE
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
    "scripts/eventbus/schema.sql": "CREATE TABLE eventbus_events (id INTEGER);\n",
    "scripts/shared/mcp_dedup_schema.py": (
        "_SCHEMA = 'CREATE TABLE IF NOT EXISTS dedup_call_state (key TEXT)'\n"
        "_USER_VERSION = 1\n"
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
    "scripts/eventbus/publish_route.py": (
        "from eventbus.auth import Role, require_role\n"
        "from fastapi import APIRouter, Depends\n\n"
        "router = APIRouter()\n\n\n"
        '@router.post("/publish")\n'
        "async def publish_event(\n"
        "    _principal=Depends(require_role(Role.PUBLISHER)),\n"
        ") -> dict:\n"
        '    return {"ok": True}\n'
    ),
    "scripts/eventbus/ack_route.py": (
        "from eventbus.auth import Role, require_role\n"
        "from fastapi import APIRouter, Depends\n\n"
        "router = APIRouter()\n\n\n"
        '@router.post("/events/{event_id}/ack")\n'
        "async def ack_event(\n"
        "    _principal=Depends(require_role(Role.CONSUMER)),\n"
        ") -> dict:\n"
        '    return {"ok": True}\n'
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
        "| ADR / Invariant | Invariant | Type | Timing | Gate | Verification Status |\n"
        "|---|---|---|---|---|---|\n"
        "| ADR-001 INV-01 | gate must run | Unit Test | CI | Blocking | "
        "Confirmed (`tests/tools/test_fake.py::test_gate`, passing) |\n"
        "| ADR-002 INV-02 | release review | Manual Review | Startup | Deployment Blocking | "
        "Manual — procedure: review scripts/. Cadence: nightly Expected evidence: "
        "a recorded review Owner: qa Exception: exc-002 |\n"
    ),
    "registry/component_mandatoriness.yaml": (
        "version: 1\n"
        "entries:\n"
        "  - component_id: alpha\n"
        "    classification: required\n"
        "    failure_category: safety-integrity\n"
        "    safety_role: Alpha server safety role\n"
        "    safely_disableable_functions: [fn_a]\n"
        "    startup_consequence: abort_startup\n"
        "    observability: [ServiceWarning, metric_drop]\n"
        "    owner: alpha-owner\n"
        "    authority_adr: ADR-004\n"
        "    rationale: Required because it touches safety-critical paths\n"
        "  - component_id: beta\n"
        "    classification: non_required\n"
        "    failure_category: availability\n"
        "    safety_role: Beta server safety role\n"
        "    safely_disableable_functions: []\n"
        "    startup_consequence: log_warning\n"
        "    observability: []\n"
        "    owner: beta-owner\n"
        "    authority_adr: ADR-004\n"
        "    rationale: Non-required optional helper\n"
    ),
    "scripts/agent/widget.py": _FIXTURE_MODULE,
    "scripts/eventbus/widget.py": _FIXTURE_MODULE,
    "scripts/agent/memory/widget.py": _FIXTURE_MODULE,
    "scripts/agent/production_config_validator.py": (
        "_REMOVED_KEY_REPLACEMENTS: dict[str, str] = {\n"
        '    "tool_safety_tiers": "the per-tool agent_safety_tier field in config/tool_catalog.toml",\n'
        '    "approval_risk_rules": "the declared agent_safety_tier (single risk source)",\n'
        "}\n"
    ),
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
        grt, "EVENTBUS_SCHEMA_SQL_SRC", tmp_path / "scripts" / "eventbus" / "schema.sql"
    )
    monkeypatch.setattr(
        grt, "DEDUP_SCHEMA_SRC", tmp_path / "scripts" / "shared" / "mcp_dedup_schema.py"
    )
    monkeypatch.setattr(
        grt,
        "_EVENTBUS_ROUTE_MODULES",
        tuple(
            tmp_path / "scripts" / "eventbus" / name
            for name in ("ack_route.py", "publish_route.py")
        ),
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
    monkeypatch.setattr(
        grt,
        "COMPONENT_MANDATORINESS_REGISTRY",
        tmp_path / "registry" / "component_mandatoriness.yaml",
    )
    monkeypatch.setattr(
        grt,
        "PRODUCTION_VALIDATOR_SRC",
        tmp_path / "scripts" / "agent" / "production_config_validator.py",
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
            {
                "route": "/events/{event_id}/ack",
                "method": "POST",
                "roles": ["CONSUMER"],
            },
            {"route": "/publish", "method": "POST", "roles": ["PUBLISHER"]},
        ]
        db = grt.build_manifest("db_schema_versions")["entries"]
        assert [(e["kind"], e["name"]) for e in db] == [
            ("db_path", "history.sqlite"),
            ("db_path", "session.sqlite"),
            ("schema", "eventbus"),
            ("schema", "mcp_dedup"),
        ]
        dedup = next(e for e in db if e["name"] == "mcp_dedup")
        assert dedup["source"] == "scripts/shared/mcp_dedup_schema.py"
        # `version` is the store's PRAGMA user_version identity stamp; the
        # content_hash fingerprints the module holding the canonical DDL.
        assert dedup["version"] == 1
        assert (
            dedup["content_hash"]
            == hashlib.sha256(
                (tmp_path / "scripts/shared/mcp_dedup_schema.py").read_bytes()
            ).hexdigest()
        )
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
        assert "disposition" not in health[0]
        coverage = grt.build_manifest("invariant_coverage")["entries"]
        assert [e["adr"] for e in coverage] == ["ADR-001", "ADR-002"]
        assert coverage[1]["exception"] == "exc-002"
        assert coverage[1]["cadence"] == "nightly"
        mand = grt.build_manifest("component_mandatoriness")["entries"]
        assert [e["component_id"] for e in mand] == ["alpha", "beta"]
        assert mand[0]["classification"] == "required"
        assert mand[0]["observability"] == ["ServiceWarning", "metric_drop"]
        assert mand[0]["safely_disableable_functions"] == ["fn_a"]
        assert mand[1]["classification"] == "non_required"
        assert mand[1]["observability"] == []

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
            "CREATE TABLE eventbus_events (id INTEGER, payload TEXT);\n",
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


# ---------------------------------------------------------------------------
# New derivations: gate/check_type mapping, schema rejection, route derivation,
# source declarations, single mandatoriness check, removed disposition, and the
# recursive symbol scan with the size-bounded document split
# ---------------------------------------------------------------------------


_COV_MATRIX_HEADER = (
    "## ADR Invariant Verification Matrix\n\n"
    "| ADR / Invariant | Invariant | Type | Timing | Gate | Verification Status |\n"
    "|---|---|---|---|---|---|\n"
)


def _schema_branch(manifest_name: str) -> dict[str, Any]:
    """Return the schema branch that constrains one manifest's entries."""
    schema: dict[str, Any] = json.loads(
        Path(cm.SCHEMA_PATH).read_text(encoding="utf-8")
    )
    for branch in schema["allOf"]:
        const = (branch.get("if") or {}).get("properties", {}).get("manifest", {})
        if const.get("const") == manifest_name:
            items: dict[str, Any] = branch["then"]["properties"]["entries"]["items"]
            return items
    raise AssertionError(f"no schema branch for manifest {manifest_name!r}")


def _coverage_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    check_type: str,
    gate: str,
) -> list[dict[str, Any]]:
    """Build `invariant_coverage` from one matrix fixture row whose Type and Gate
    cells hold different values, so a swapped column mapping cannot pass."""
    row = (
        f"| ADR-001 INV-01 | gate must run | {check_type} | CI | {gate} | "
        "Confirmed (`tests/tools/test_fake.py::test_gate`, passing) |\n"
    )
    _synthetic_repo(
        tmp_path,
        monkeypatch,
        {"docs/10_adr/adr_01_index.md": f"# ADR Index\n\n{_COV_MATRIX_HEADER}{row}"},
    )
    manifest: dict[str, Any] = grt.build_manifest("invariant_coverage")
    entries: list[dict[str, Any]] = manifest["entries"]
    return entries


class TestInvariantCoverage:
    """T-001/T-002 (REQ-001, REQ-003): each field reads its own matrix column."""

    def test_gate_reads_gate_column(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        entries = _coverage_entries(
            tmp_path, monkeypatch, check_type="Unit Test", gate="Blocking"
        )
        assert entries[0]["gate"] == "Blocking"
        assert entries[0]["gate"] != entries[0]["check_type"]

    def test_check_type_reads_type_column(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        entries = _coverage_entries(
            tmp_path, monkeypatch, check_type="Startup Validation", gate="Non-Blocking"
        )
        assert entries[0]["check_type"] == "Startup Validation"
        assert entries[0]["gate"] == "Non-Blocking"


class TestManifestSchema:
    """T-003/T-004 (REQ-002, REQ-005): the enumerated vocabulary and route pattern."""

    def test_gate_rejects_a_type_column_value(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gate_branch = _schema_branch("invariant_coverage")
        assert gate_branch["properties"]["gate"]["enum"] == [
            "Blocking",
            "Deployment Blocking",
            "Non-Blocking",
        ]
        assert "Unit Test" in gate_branch["properties"]["check_type"]["enum"]
        with pytest.raises(cm.ManifestError, match="rejected by"):
            _coverage_entries(
                tmp_path, monkeypatch, check_type="Unit Test", gate="Unit Test"
            )

    def test_parameterized_route_path_is_accepted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _route_repo(
            tmp_path,
            monkeypatch,
            {
                "dlq_route.py": _route_source(
                    "post", "/dlq/{event_id}/requeue", "OPERATOR", "requeue_event"
                )
            },
        )
        manifest = grt.build_manifest("eventbus_route_roles")
        assert manifest["entries"] == [
            {
                "route": "/dlq/{event_id}/requeue",
                "method": "POST",
                "roles": ["OPERATOR"],
            }
        ]
        route_branch = _schema_branch("eventbus_route_roles")
        assert route_branch["required"] == ["route", "method", "roles"]
        assert route_branch["properties"]["method"]["enum"] == ["GET", "POST"]


def _route_source(method: str, path: str, role: str, name: str) -> str:
    """One synthetic EventBus route module: a router decorator plus a
    `Depends(require_role(Role.X))` parameter default."""
    return (
        "from eventbus.auth import Role, require_role\n"
        "from fastapi import APIRouter, Depends\n\n"
        "router = APIRouter()\n\n\n"
        f'@router.{method}("{path}")\n'
        f"async def {name}(\n"
        f"    _principal=Depends(require_role(Role.{role})),\n"
        ") -> dict:\n"
        '    return {"ok": True}\n'
    )


def _route_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    modules: dict[str, str],
) -> None:
    """Write synthetic route modules and repoint the generator's module list."""
    _synthetic_repo(
        tmp_path,
        monkeypatch,
        {f"scripts/eventbus/{name}": text for name, text in modules.items()},
    )
    monkeypatch.setattr(
        grt,
        "_EVENTBUS_ROUTE_MODULES",
        tuple(tmp_path / "scripts" / "eventbus" / name for name in modules),
    )


class TestRouteRoleEntries:
    """T-005/T-006 (REQ-004, AC-003): entries come from the registered surface."""

    def test_entries_come_from_decorators_and_role_dependency(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _route_repo(
            tmp_path,
            monkeypatch,
            {
                "ack_route.py": _route_source(
                    "post", "/events/{event_id}/ack", "CONSUMER", "ack_event"
                ),
                "health_route.py": _route_source(
                    "get", "/health", "MONITORING", "health_check"
                ),
                "subscribe_route.py": (
                    "from eventbus.auth import Role, require_role\n"
                    "from fastapi import APIRouter, Depends\n\n"
                    "router = APIRouter()\n\n\n"
                    '@router.get("/subscribe", dependencies=[Depends(require_role('
                    "Role.CONSUMER))])\n"
                    "async def subscribe() -> dict:\n"
                    '    return {"ok": True}\n'
                ),
                "helpers.py": "def not_a_route() -> None:\n    return None\n",
            },
        )
        assert grt._route_role_entries() == [
            {
                "route": "/events/{event_id}/ack",
                "method": "POST",
                "roles": ["CONSUMER"],
            },
            {"route": "/health", "method": "GET", "roles": ["MONITORING"]},
            {"route": "/subscribe", "method": "GET", "roles": ["CONSUMER"]},
        ]

    def test_unregistered_route_entry_is_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A registered decorator with no role dependency: fail closed.
        _route_repo(
            tmp_path,
            monkeypatch,
            {
                "publish_route.py": (
                    "from fastapi import APIRouter\n\n"
                    "router = APIRouter()\n\n\n"
                    '@router.post("/publish")\n'
                    "async def publish_event() -> dict:\n"
                    '    return {"ok": True}\n'
                )
            },
        )
        with pytest.raises(cm.ManifestError, match="no Depends\\(require_role"):
            grt.build_manifest("eventbus_route_roles")

        # A non-literal path is not a readable registered route.
        _route_repo(
            tmp_path,
            monkeypatch,
            {
                "publish_route.py": (
                    "from eventbus.auth import Role, require_role\n"
                    "from fastapi import APIRouter, Depends\n\n"
                    "router = APIRouter()\n\n"
                    'PATH = "/publish"\n\n\n'
                    "@router.post(PATH)\n"
                    "async def publish_event(\n"
                    "    _principal=Depends(require_role(Role.PUBLISHER)),\n"
                    ") -> dict:\n"
                    '    return {"ok": True}\n'
                )
            },
        )
        with pytest.raises(cm.ManifestError, match="not a string literal"):
            grt.build_manifest("eventbus_route_roles")

        # A function that requires a role but carries no router decorator is not
        # part of the registered surface, and an empty route manifest is rejected.
        _route_repo(
            tmp_path,
            monkeypatch,
            {
                "admin_route.py": (
                    "from eventbus.auth import Role, require_role\n"
                    "from fastapi import Depends\n\n\n"
                    "def removed_admin_endpoint(\n"
                    "    _principal=Depends(require_role(Role.ADMIN)),\n"
                    ") -> dict:\n"
                    '    return {"ok": True}\n'
                )
            },
        )
        assert grt._route_role_entries() == []
        with pytest.raises(cm.ManifestError, match="rejected by"):
            grt.build_manifest("eventbus_route_roles")


class TestManifestSources:
    """T-009 (REQ-009): each manifest's declared sources are exactly what its
    builder reads."""

    def test_declared_sources_match_builder_reads(self, monkeypatch) -> None:
        reads: list[Path] = []
        real_text = Path.read_text
        real_bytes = Path.read_bytes
        real_open = Path.open

        def spy_text(self: Path, *args: Any, **kwargs: Any) -> Any:
            reads.append(self)
            return real_text(self, *args, **kwargs)

        def spy_bytes(self: Path, *args: Any, **kwargs: Any) -> Any:
            reads.append(self)
            return real_bytes(self, *args, **kwargs)

        def spy_open(self: Path, *args: Any, **kwargs: Any) -> Any:
            reads.append(self)
            return real_open(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", spy_text)
        monkeypatch.setattr(Path, "read_bytes", spy_bytes)
        monkeypatch.setattr(Path, "open", spy_open)

        for name, builder in grt._MANIFEST_BUILDERS.items():
            declared = [PurePosixPath(src) for src in grt._MANIFEST_SOURCES[name]]
            assert declared, name
            reads.clear()
            builder()
            read_paths = []
            for read in reads:
                try:
                    read_paths.append(PurePosixPath(read.relative_to(grt.REPO_ROOT)))
                except ValueError:
                    continue
            uncovered = sorted(
                str(path)
                for path in read_paths
                if not any(path == src or src in path.parents for src in declared)
            )
            unused = [
                str(src)
                for src in declared
                if not any(path == src or src in path.parents for path in read_paths)
            ]
            assert uncovered == [], f"{name}: reads outside its declared sources"
            assert unused == [], f"{name}: declared source never read: {unused}"


class TestMandatorinessClassification:
    """T-010 (REQ-010): one classification source, checked once per --check."""

    def test_mandatoriness_is_drift_checked_once(self, monkeypatch) -> None:
        bound = [
            domain
            for domain, names in grt.MANIFESTS_BY_DOMAIN.items()
            if "component_mandatoriness" in names
        ]
        assert bound == ["mandatoriness"]
        assert "component_mandatoriness" not in grt.UNBOUND_MANIFESTS

        built: list[str] = []
        real_build = grt.build_manifest

        def counting(name: str) -> dict:
            built.append(name)
            return real_build(name)

        monkeypatch.setattr(grt, "build_manifest", counting)
        args = argparse.Namespace(check=True, manifests=False, dry_run=False, type=None)
        assert grt._run_check(args) == 0
        assert built.count("component_mandatoriness") == 1


class TestSymbolEntries:
    """T-011/T-015 (REQ-012, REQ-15): recursive scan and the document split."""

    def test_recursive_scan_covers_agent_subpackages(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _synthetic_repo(
            tmp_path,
            monkeypatch,
            {
                rel: _FIXTURE_MODULE
                for rel in (
                    "scripts/agent/widget.py",
                    "scripts/agent/commands/widget.py",
                    "scripts/agent/services/widget.py",
                    "scripts/agent/shared/widget.py",
                    "scripts/agent/workflow/widget.py",
                    "scripts/agent/workflow/stages/widget.py",
                    "scripts/agent/memory/widget.py",
                )
            },
        )
        agent_files = sorted({e["file"] for e in grt._api_manifest_entries("agent")})
        assert agent_files == [
            "scripts/agent/commands/widget.py",
            "scripts/agent/services/widget.py",
            "scripts/agent/shared/widget.py",
            "scripts/agent/widget.py",
            "scripts/agent/workflow/stages/widget.py",
            "scripts/agent/workflow/widget.py",
        ]
        # `scripts/agent/memory/` is owned by the memory_api manifest instead.
        assert {e["file"] for e in grt._api_manifest_entries("memory")} == {
            "scripts/agent/memory/widget.py"
        }

    def test_generated_agent_index_stays_within_the_document_ceiling(self) -> None:
        entries = grt.build_manifest("agent_api")["entries"]
        top = [e for e in entries if grt._agent_entry_is_top_level(e)]
        subpackages = [e for e in entries if not grt._agent_entry_is_top_level(e)]
        assert top and subpackages
        tables = {
            domain: grt._table_from_entries(domain, entries)
            for domain in ("agent", "agent_subpackages")
        }
        rows = {domain: len(table.splitlines()) - 2 for domain, table in tables.items()}
        assert rows["agent"] == len(top)
        assert rows["agent_subpackages"] == len(subpackages)
        assert sum(rows.values()) == len(entries)
        for domain, doc in (
            ("agent", grt.REFERENCE_DOC_AGENT),
            ("agent_subpackages", grt.REFERENCE_DOC_AGENT_SUBPACKAGES),
        ):
            rendered = grt.render_updated_doc(domain, doc.read_text(encoding="utf-8"))
            assert len(rendered.encode("utf-8")) < MAX_SIZE


class TestHealthContracts:
    """T-014 (REQ-008): no generator-constant `disposition` in health entries."""

    def test_disposition_is_not_a_generator_constant(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _synthetic_repo(tmp_path, monkeypatch, _FULL_SOURCES)
        entries = grt.build_manifest("health_contracts")["entries"]
        assert entries
        assert all(set(entry) == {"server", "checks"} for entry in entries)
        leaked = [
            name
            for name in dir(grt)
            if name.isupper() and getattr(grt, name, None) == "fail-fast"
        ]
        assert leaked == []
        branch = _schema_branch("health_contracts")
        assert "disposition" not in branch["properties"]
        assert "disposition" not in branch["required"]


class TestAgentConfigMigration:
    """T-016/T-017 (REQ-002): the migration table reads the validator mapping as
    source text, and the domain is registered through the contract-manifest path so
    `--check` covers it."""

    def test_mapping_read_from_source_text(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _synthetic_repo(tmp_path, monkeypatch, _FULL_SOURCES)
        mapping = acm.read_mapping(grt.PRODUCTION_VALIDATOR_SRC)
        assert mapping == {
            "tool_safety_tiers": (
                "the per-tool agent_safety_tier field in config/tool_catalog.toml"
            ),
            "approval_risk_rules": "the declared agent_safety_tier (single risk source)",
        }

    def test_entries_are_sorted_and_schema_valid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _synthetic_repo(tmp_path, monkeypatch, _FULL_SOURCES)
        manifest = grt.build_manifest("agent_config_migration")
        assert manifest["sources"] == ["scripts/agent/production_config_validator.py"]
        entries = manifest["entries"]
        assert [e["key"] for e in entries] == [
            "approval_risk_rules",
            "tool_safety_tiers",
        ]
        schema = json.loads(Path(cm.SCHEMA_PATH).read_text(encoding="utf-8"))
        jsonschema.validate(manifest, schema)
        branch = _schema_branch("agent_config_migration")
        assert branch["required"] == ["key", "replacement"]
        assert cm.dump_manifest(manifest) == cm.dump_manifest(
            grt.build_manifest("agent_config_migration")
        )

    def test_table_renders_only_mapping_values(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _synthetic_repo(tmp_path, monkeypatch, _FULL_SOURCES)
        entries = grt._MANIFEST_BUILDERS["agent_config_migration"]()
        table = grt._table_from_entries("agent_config_migration", entries)
        lines = table.splitlines()
        assert lines[0] == (
            "| Removed key (`config/agent.toml`) | Replacement (single source) |"
        )
        assert len(lines) == 2 + len(entries)
        for entry in entries:
            assert f"| `{entry['key']}` | {entry['replacement']} |" in lines
        assert "agent_safety_tier" in table

    def test_unreadable_or_malformed_mapping_is_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _synthetic_repo(tmp_path, monkeypatch, _FULL_SOURCES)
        src = grt.PRODUCTION_VALIDATOR_SRC
        for text in (
            "x = 1\n",
            '_REMOVED_KEY_REPLACEMENTS = ["tool_safety_tiers"]\n',
            '_REMOVED_KEY_REPLACEMENTS = {1: "x"}\n',
            '_REMOVED_KEY_REPLACEMENTS = {"tool_safety_tiers": None}\n',
            '_REMOVED_KEY_REPLACEMENTS = {"a": "x", "a": "y"}\n',
        ):
            src.write_text(text, encoding="utf-8")
            with pytest.raises(cm.ManifestError):
                grt.build_manifest("agent_config_migration")

    def test_domain_is_registered_for_check(self) -> None:
        domain = "agent_config_migration"
        assert domain in grt.DOMAIN_GENERATORS
        assert grt.DOMAIN_DOCS[domain] == grt.REFERENCE_DOC_AGENT_CONFIG_MIGRATION
        assert domain in grt.MANIFESTS_BY_DOMAIN["agent_config_migration"]
        assert grt._RENDER_MANIFEST[domain] == "agent_config_migration"
        assert "agent_config_migration" in grt._MANIFEST_BUILDERS
        assert grt._MANIFEST_SOURCES["agent_config_migration"] == [
            "scripts/agent/production_config_validator.py"
        ]
        assert domain in grt.DOMAIN_GUARDS
        assert grt.DOMAIN_HEADING[domain]
        assert grt.DOMAIN_WELCOME_LINES[domain]

    def test_check_reports_stale_and_missing_block(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _synthetic_repo(tmp_path, monkeypatch, _FULL_SOURCES)
        _write_committed_manifests(["agent_config_migration"])
        doc = tmp_path / "doc.md"
        doc.write_text("# Doc\n", encoding="utf-8")
        monkeypatch.setattr(grt, "DOMAIN_DOCS", {"agent_config_migration": doc})
        doc.write_text(
            grt.render_updated_doc("agent_config_migration", doc.read_text())
        )
        assert grt.check_drift(["agent_config_migration"]) == []

        edited = doc.read_text().replace("(single source)", "(HAND-EDIT)", 1)
        doc.write_text(edited, encoding="utf-8")
        assert grt.check_drift(["agent_config_migration"]) == [
            "doc.md (--type agent_config_migration)"
        ]
        doc.write_text("# no guard\n", encoding="utf-8")
        assert grt.check_drift(["agent_config_migration"]) == [
            "doc.md (guarded block missing)"
        ]
