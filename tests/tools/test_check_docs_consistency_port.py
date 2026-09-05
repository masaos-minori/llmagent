"""tests/tools/test_check_docs_consistency_port.py

Regression tests for `check_port_drift()`/`check_port_range_claim()`
confirming both functions still run unchanged under the docs content policy
(Plan `docscope3`, option (c): keep both active pending a documented,
explicit exemption list — see
`docs/00_governance_04_documentation-checks.md`'s Domain Consistency Check
description for the recorded rationale).
"""

from __future__ import annotations

from pathlib import Path

from tools.check_docs_consistency import (
    REPO_ROOT,
    DocFile,
    _extract_authoritative_ports,
    check_port_drift,
    check_port_range_claim,
)


def _mk_file(rel: str, lines: list[str]) -> DocFile:
    return DocFile(path=Path(f"/fake/{rel}"), rel_path=rel, lines=lines)


def test_authoritative_ports_extractable_from_live_config() -> None:
    """Both functions depend on config/agent.toml parsing succeeding; confirm it still does."""
    ports = _extract_authoritative_ports(REPO_ROOT)
    assert ports is not None
    assert len(ports) > 0


def test_check_port_drift_flags_mismatched_port() -> None:
    ports = _extract_authoritative_ports(REPO_ROOT)
    assert ports is not None
    name, expected_port = next(iter(ports.items()))
    wrong_port = str(int(expected_port) + 1)
    doc = _mk_file("fixture.md", [f"## {name} (Port {wrong_port})"])

    issues = check_port_drift(REPO_ROOT / "docs", [doc], REPO_ROOT)

    assert len(issues) == 1
    assert issues[0].severity == "ERROR"
    assert name in issues[0].message


def test_check_port_drift_no_issue_for_matching_port() -> None:
    ports = _extract_authoritative_ports(REPO_ROOT)
    assert ports is not None
    name, expected_port = next(iter(ports.items()))
    doc = _mk_file("fixture.md", [f"## {name} (Port {expected_port})"])

    issues = check_port_drift(REPO_ROOT / "docs", [doc], REPO_ROOT)

    assert issues == []


def test_check_port_range_claim_flags_mismatched_range() -> None:
    ports = _extract_authoritative_ports(REPO_ROOT)
    assert ports is not None
    all_ports = [int(p) for p in ports.values()]
    wrong_min = min(all_ports) - 1
    wrong_max = max(all_ports)
    doc = _mk_file("fixture.md", [f"MCP servers use ports {wrong_min}-{wrong_max}."])

    issues = check_port_range_claim(REPO_ROOT / "docs", [doc], REPO_ROOT)

    assert len(issues) == 1
    assert issues[0].severity == "ERROR"


def test_check_port_range_claim_no_issue_for_matching_range() -> None:
    ports = _extract_authoritative_ports(REPO_ROOT)
    assert ports is not None
    all_ports = [int(p) for p in ports.values()]
    expected_min, expected_max = min(all_ports), max(all_ports)
    doc = _mk_file(
        "fixture.md", [f"MCP servers use ports {expected_min}-{expected_max}."]
    )

    issues = check_port_range_claim(REPO_ROOT / "docs", [doc], REPO_ROOT)

    assert issues == []
