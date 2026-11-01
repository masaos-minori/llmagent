"""Tests for tools/check_component_mandatoriness.py."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import pytest
from shared.component_mandatoriness import (
    ComponentClassification,
    ComponentMandatorinessError,
)

from tools import check_component_mandatoriness as mod

GUARD_START = (
    "<!-- AUTO-GENERATED: generate_reference_table.py "
    "component-mandatoriness-reference -->"
)
GUARD_END = "<!-- END AUTO-GENERATED -->"


def _entry(
    component_id: str, classification: str, rationale: str = "r"
) -> ComponentClassification:
    return ComponentClassification(
        component_id=component_id,
        classification=classification,
        failure_category="safety-integrity",
        safety_role="test",
        safely_disableable_functions=frozenset(),
        startup_consequence="abort_startup",
        observability=frozenset({"ServiceWarning"}),
        owner="agent-architecture-owner",
        authority_adr="ADR-004",
        rationale=rationale,
    )


def _registry(**pairs: str) -> dict[str, ComponentClassification]:
    """Build a synthetic registry mapping component_id -> classification."""
    return {cid: _entry(cid, cls) for cid, cls in pairs.items()}


def _doc(rows: list[tuple[str, str, str]], *, markers: bool = True) -> str:
    """Build a doc with a mandatoriness table; ``markers`` toggles the guard block."""
    lines = ["# heading", "", "intro line"]
    if markers:
        lines.append(GUARD_START)
    lines.append("Generated from `registry/component_mandatoriness.yaml`.")
    lines.append("")
    lines.append("| Server (`config/agent.toml` key) | Classification | Rationale |")
    lines.append("|---|---|---|")
    if markers:
        for cid, cls, rat in rows:
            lines.append(f"| `{cid}` | {cls} | {rat} |")
    if markers:
        lines.append(GUARD_END)
    return "\n".join(lines) + "\n"


def test_live_repository_has_no_violations() -> None:
    registry = mod._load_registry()
    assert registry is not None
    doc_text = mod.DOC_PATH.read_text(encoding="utf-8")
    config = mod._load_config_requireds()
    assert mod.run_checks(registry, doc_text, config) == []


def test_check1_classification_mismatch() -> None:
    registry = _registry(shell="required")
    doc = _doc([("shell", "non_required", "r")])
    violations = mod.check_registry_vs_table(registry, doc)
    assert any("classification" in v.detail for v in violations)


def test_check1_rationale_mismatch() -> None:
    registry = _registry(shell="required", rationale="actual rationale")
    doc = _doc([("shell", "required", "different rationale")])
    violations = mod.check_registry_vs_table(registry, doc)
    assert any("rationale" in v.detail for v in violations)


def test_check1_table_row_missing_from_registry() -> None:
    registry = _registry(shell="required")
    doc = _doc([("shell", "required", "r"), ("ghost", "required", "r")])
    violations = mod.check_registry_vs_table(registry, doc)
    assert any(v.component_id == "ghost" for v in violations)


def test_check2_config_conflict() -> None:
    registry = _registry(shell="required")
    violations = mod.check_registry_vs_config(registry, {"shell": False})
    assert any("conflicts with registry" in v.detail for v in violations)


def test_check2_unknown_server() -> None:
    registry = _registry(shell="required")
    violations = mod.check_registry_vs_config(registry, {"orphan_srv": True})
    assert any("absent from registry" in v.detail for v in violations)


def test_check2_orphan_entry() -> None:
    registry = _registry(shell="required", ghost="required")
    violations = mod.check_registry_vs_config(registry, {"shell": True})
    assert any(v.component_id == "ghost" for v in violations)


def test_check3_missing_start_marker() -> None:
    doc = _doc([("shell", "required", "r")], markers=False)
    violations = mod.check_table_freshness(doc)
    assert any("start marker" in v.detail for v in violations)


def test_check3_missing_end_marker() -> None:
    doc = _doc([("shell", "required", "r")])
    # Remove the end marker to simulate a torn guard block.
    doc = doc.replace(GUARD_END, "")
    violations = mod.check_table_freshness(doc)
    assert any("END AUTO-GENERATED marker" in v.detail for v in violations)


def test_check3_no_table_inside_markers() -> None:
    doc = (
        "# heading\n\n"
        f"{GUARD_START}\nGenerated from `registry/component_mandatoriness.yaml`.\n{GUARD_END}\n"
    )
    violations = mod.check_table_freshness(doc)
    assert any("no classification table" in v.detail for v in violations)


def test_check3_duplicate_start_marker() -> None:
    doc = f"{GUARD_START}\n{GUARD_START}\n| `shell` | required | r |\n{GUARD_END}\n"
    violations = mod.check_table_freshness(doc)
    assert any("duplicate" in v.detail for v in violations)


def test_load_failure_returns_none() -> None:
    def boom() -> None:
        raise ComponentMandatorinessError("missing file")

    old = mod.load_component_mandatoriness
    mod.load_component_mandatoriness = boom
    try:
        assert mod._load_registry() is None
    finally:
        mod.load_component_mandatoriness = old


def test_main_exit_0_clean(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    registry = _registry(shell="required")
    doc = _doc([("shell", "required", "r")])
    monkeypatch.setattr(mod, "_load_registry", lambda: registry)
    target = tmp_path / "doc.md"
    target.write_text(doc, encoding="utf-8")
    monkeypatch.setattr(mod, "DOC_PATH", target)
    monkeypatch.setattr(mod, "_load_config_requireds", lambda: {"shell": True})
    assert mod.main([]) == 0


def test_main_exit_1_on_violation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = _registry(shell="required")
    doc = _doc([("shell", "required", "r")])
    monkeypatch.setattr(mod, "_load_registry", lambda: registry)
    target = tmp_path / "doc.md"
    target.write_text(doc, encoding="utf-8")
    monkeypatch.setattr(mod, "DOC_PATH", target)
    monkeypatch.setattr(mod, "_load_config_requireds", lambda: {"shell": False})
    assert mod.main([]) == 1


def test_main_missing_registry_exit_1(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom() -> None:
        raise ComponentMandatorinessError("missing")

    monkeypatch.setattr(mod, "load_component_mandatoriness", boom)
    assert mod.main([]) == 1


def test_main_json_format(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    registry = _registry(shell="required")
    doc = _doc([("shell", "required", "r")])
    monkeypatch.setattr(mod, "_load_registry", lambda: registry)
    target = tmp_path / "doc.md"
    target.write_text(doc, encoding="utf-8")
    monkeypatch.setattr(mod, "DOC_PATH", target)
    monkeypatch.setattr(mod, "_load_config_requireds", lambda: {"shell": True})
    buf = io.StringIO()
    with redirect_stdout(buf):
        assert mod.main(["--format", "json"]) == 0
    payload = json.loads(buf.getvalue())
    assert payload["violations"] == []
