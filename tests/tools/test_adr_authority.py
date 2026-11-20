"""tests/tools/test_adr_authority.py

Unit tests for the ADR authority validator core (tools/_adr_authority_core.py)
and its CLI (tools/check_adr_authority.py), per plan adrauth001 row 12.

Idiom follows tests/tools/test_check_adr_reference.py: direct function calls
against tmp_path fixture files, no subprocess. The CLI surface is locked
through main()'s return value and capsys output. The live repository model is
not re-validated here as a unit test — CI runs the real files (row 11).

Every finding code has a failing fixture: DUP_PRIMARY, DANGLING_ADR,
AUTHORITY_CYCLE, ASSUMPTION_DRIFT, EDGE_UNKNOWN_TYPE, FRONTMATTER_DIVERGENCE,
EDGE_DUPLICATE, ADR_STATUS_INVALID. Mutation spot-checks assert the exact
finding code, not just a nonzero exit.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools._adr_authority_core import (
    AuthorityModelError,
    check_adr_statuses,
    check_assumptions,
    check_authority_cycles,
    check_dangling_adrs,
    check_duplicate_edges,
    check_duplicate_primaries,
    check_edge_types,
    check_frontmatter_consistency,
    load_model,
    validate_model,
)
from tools.check_adr_authority import main

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CLEAN_MODEL = """\
version = "1"

[[authority]]
decision_target = "alpha.decision"
primary_adr = "ADR-001"
supplemental_adrs = [{ adr = "ADR-002", limit = "failure classification only" }]

[[authority]]
decision_target = "beta.decision"
primary_adr = "ADR-002"
supplemental_adrs = []

[[adr_edge]]
from = "ADR-001"
to = "ADR-002"
edge_type = "Requires"

[[adr_edge]]
from = "ADR-002"
to = "ADR-001"
edge_type = "Reference"
intentional = true
note = "ADR-002 classifies failures; ADR-001 owns the decision."

[[adr_edge]]
from = "ADR-001"
to = "ADR-003"
edge_type = "Reference"

[[assumption]]
id = "ARCH-901"
name = "Loopback-only exposure"
current_value = "Servers bind only to 127.0.0.1 loopback addresses"
applicable_adrs = ["ADR-001"]
validation_method = "config-check"
config_keys = ["mcp_servers.*.url"]
owner = "test-owner"
review_triggers = ["network topology change"]

[[assumption]]
id = "ARCH-902"
name = "Single-agent runtime"
current_value = "One agent process serves all sessions"
applicable_adrs = ["ADR-002"]
validation_method = "manual-review"
owner = "test-owner"
review_triggers = ["concurrency change"]
"""

ADR_FILE_NAMES = (
    "adr_02_01_001_alpha.md",
    "adr_02_01_002_beta.md",
    "adr_02_01_003_gamma.md",
)

LOOPBACK_CONFIG = """\
[mcp_servers.alpha]
url = "http://127.0.0.1:9001"
"""


def _write_model(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "adr_authority.toml"
    path.write_text(text, encoding="utf-8")
    return path


def _adr_dir(tmp_path: Path, related: dict[str, list[str]] | None = None) -> Path:
    """Sandbox docs/10_adr/ shape: adr_02_* body files with optional related lists."""
    directory = tmp_path / "adr"
    directory.mkdir(exist_ok=True)
    for name in ADR_FILE_NAMES:
        entries = (related or {}).get(name, [])
        related_block = "\n".join(f"  - {entry}" for entry in entries) or "  []"
        (directory / name).write_text(
            f"---\ntitle: {name}\nrelated:\n{related_block}\n---\n# body\n\n"
            "## Status\nAccepted\n",
            encoding="utf-8",
        )
    return directory


def _config(tmp_path: Path, text: str = LOOPBACK_CONFIG) -> Path:
    path = tmp_path / "agent.toml"
    path.write_text(text, encoding="utf-8")
    return path


def _validate(tmp_path: Path, model_text: str) -> list[str]:
    model = load_model(_write_model(tmp_path, model_text))
    findings = validate_model(
        model, adr_dir=_adr_dir(tmp_path), config_path=_config(tmp_path)
    )
    return [f.code for f in findings]


def _mutate(text: str, old: str, new: str) -> str:
    assert old in text
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Conforming fixture
# ---------------------------------------------------------------------------


def test_conforming_model_is_clean(tmp_path: Path) -> None:
    assert _validate(tmp_path, CLEAN_MODEL) == []


def test_multiple_findings_aggregate(tmp_path: Path) -> None:
    broken = _mutate(
        CLEAN_MODEL,
        'decision_target = "beta.decision"',
        'decision_target = "alpha.decision"',
    )
    broken = _mutate(broken, 'edge_type = "Requires"', 'edge_type = "Controls"')
    assert sorted(_validate(tmp_path, broken)) == sorted(
        ["EDGE_UNKNOWN_TYPE", "DUP_PRIMARY"]
    )


def test_model_file_structural_error_raises(tmp_path: Path) -> None:
    broken = _write_model(tmp_path, 'version = "1"\n[[authority]]\nprimary_adr = 7\n')
    with pytest.raises(AuthorityModelError, match="not a string"):
        load_model(broken)


# ---------------------------------------------------------------------------
# DUP_PRIMARY
# ---------------------------------------------------------------------------


def test_dup_primary_fails(tmp_path: Path) -> None:
    mutated = _mutate(
        CLEAN_MODEL,
        'decision_target = "beta.decision"',
        'decision_target = "alpha.decision"',
    )
    model = load_model(_write_model(tmp_path, mutated))
    findings = check_duplicate_primaries(model)
    assert [f.code for f in findings] == ["DUP_PRIMARY"]
    assert "ADR-001" in findings[0].message and "ADR-002" in findings[0].message


def test_primary_repeated_as_supplemental_fails(tmp_path: Path) -> None:
    mutated = _mutate(
        CLEAN_MODEL,
        'supplemental_adrs = [{ adr = "ADR-002", limit = "failure classification only" }]',
        'supplemental_adrs = [{ adr = "ADR-001", limit = "self" }]',
    )
    model = load_model(_write_model(tmp_path, mutated))
    assert [f.code for f in check_duplicate_primaries(model)] == ["DUP_PRIMARY"]


# ---------------------------------------------------------------------------
# DANGLING_ADR
# ---------------------------------------------------------------------------


def test_dangling_adr_fails(tmp_path: Path) -> None:
    mutated = _mutate(CLEAN_MODEL, 'to = "ADR-003"', 'to = "ADR-099"')
    model = load_model(_write_model(tmp_path, mutated))
    findings = check_dangling_adrs(model, _adr_dir(tmp_path))
    assert [f.code for f in findings] == ["DANGLING_ADR"]
    assert "ADR-099" in findings[0].message


# ---------------------------------------------------------------------------
# EDGE_DUPLICATE (plan adrchk015 REQ-001: pair-keyed consumers must not
# silently overwrite a duplicate [[adr_edge]] row)
# ---------------------------------------------------------------------------

DUPLICATE_EDGE_MODEL = (
    CLEAN_MODEL
    + """
[[adr_edge]]
from = "ADR-001"
to = "ADR-003"
edge_type = "Reference"
"""
)


def test_duplicate_edge_pair_fails(tmp_path: Path) -> None:
    model = load_model(_write_model(tmp_path, DUPLICATE_EDGE_MODEL))
    findings = check_duplicate_edges(model)
    assert [f.code for f in findings] == ["EDGE_DUPLICATE"]
    assert "ADR-001 -> ADR-003 appears 2 times" in findings[0].message
    assert "(from, to) pairs must be unique" in findings[0].message


def test_duplicate_edge_surfaces_in_validate_model(tmp_path: Path) -> None:
    assert _validate(tmp_path, DUPLICATE_EDGE_MODEL) == ["EDGE_DUPLICATE"]


# ---------------------------------------------------------------------------
# ADR_STATUS_INVALID (plan adrchk015 REQ-004/REQ-005: model-referenced ADRs
# must carry a governance_01 status; Withdrawn owns nothing, Proposed is not
# primary)
# ---------------------------------------------------------------------------

GOVERNANCE_STATUS_TEXT = """\
## ADR Status Definitions

- `Accepted`: the decision is in force.
- `Proposed`: the decision is not yet accepted.
- `Withdrawn`: the ADR no longer makes any decision.

## Invariants Governing These Documents

Invariant fixture text.
"""

ALL_ACCEPTED = {
    "adr_02_01_001_alpha.md": "Accepted",
    "adr_02_01_002_beta.md": "Accepted",
    "adr_02_01_003_gamma.md": "Accepted",
}


def _governance(tmp_path: Path, text: str = GOVERNANCE_STATUS_TEXT) -> Path:
    path = tmp_path / "governance_01_fixture.md"
    path.write_text(text, encoding="utf-8")
    return path


def _status_adr_dir(tmp_path: Path, statuses: dict[str, str]) -> Path:
    directory = tmp_path / "adr-status"
    directory.mkdir(exist_ok=True)
    for name, status in statuses.items():
        (directory / name).write_text(
            f"---\ntitle: {name}\nrelated: []\n---\n# body\n\n## Status\n{status}\n",
            encoding="utf-8",
        )
    return directory


def test_accepted_statuses_pass(tmp_path: Path) -> None:
    model = load_model(_write_model(tmp_path, CLEAN_MODEL))
    findings = check_adr_statuses(
        model, _status_adr_dir(tmp_path, ALL_ACCEPTED), _governance(tmp_path)
    )
    assert findings == []


def test_status_outside_allowed_set_fails(tmp_path: Path) -> None:
    statuses = ALL_ACCEPTED | {"adr_02_01_002_beta.md": "Deprecated"}
    model = load_model(_write_model(tmp_path, CLEAN_MODEL))
    findings = check_adr_statuses(
        model, _status_adr_dir(tmp_path, statuses), _governance(tmp_path)
    )
    assert [f.code for f in findings] == ["ADR_STATUS_INVALID"]
    assert "Deprecated" in findings[0].message


def test_status_without_value_fails(tmp_path: Path) -> None:
    statuses = ALL_ACCEPTED | {"adr_02_01_001_alpha.md": ""}
    model = load_model(_write_model(tmp_path, CLEAN_MODEL))
    findings = check_adr_statuses(
        model, _status_adr_dir(tmp_path, statuses), _governance(tmp_path)
    )
    assert [f.code for f in findings] == ["ADR_STATUS_INVALID"]
    assert "carries no value" in findings[0].message


def test_withdrawn_adr_owns_nothing_fails(tmp_path: Path) -> None:
    statuses = ALL_ACCEPTED | {"adr_02_01_002_beta.md": "Withdrawn"}
    model = load_model(_write_model(tmp_path, CLEAN_MODEL))
    findings = check_adr_statuses(
        model, _status_adr_dir(tmp_path, statuses), _governance(tmp_path)
    )
    assert all(f.code == "ADR_STATUS_INVALID" for f in findings)
    text = "\n".join(f.message for f in findings)
    assert "listed as primary_adr of decision_target 'beta.decision'" in text
    assert "listed as supplemental of decision_target 'alpha.decision'" in text
    assert "holds the Requires edge ADR-001 -> ADR-002" in text


def test_withdrawn_adr_with_only_reference_edges_passes(tmp_path: Path) -> None:
    statuses = ALL_ACCEPTED | {"adr_02_01_003_gamma.md": "Withdrawn"}
    model = load_model(_write_model(tmp_path, CLEAN_MODEL))
    findings = check_adr_statuses(
        model, _status_adr_dir(tmp_path, statuses), _governance(tmp_path)
    )
    assert findings == []


def test_proposed_adr_claiming_primary_fails(tmp_path: Path) -> None:
    statuses = ALL_ACCEPTED | {"adr_02_01_001_alpha.md": "Proposed"}
    model = load_model(_write_model(tmp_path, CLEAN_MODEL))
    findings = check_adr_statuses(
        model, _status_adr_dir(tmp_path, statuses), _governance(tmp_path)
    )
    assert [f.code for f in findings] == ["ADR_STATUS_INVALID"]
    assert "claims primary_adr" in findings[0].message


def test_unparseable_governance_fails_closed(tmp_path: Path) -> None:
    model = load_model(_write_model(tmp_path, CLEAN_MODEL))
    findings = check_adr_statuses(
        model,
        _status_adr_dir(tmp_path, ALL_ACCEPTED),
        _governance(tmp_path, "# nope\n"),
    )
    assert [f.code for f in findings] == ["ADR_STATUS_INVALID"]
    assert "could not parse" in findings[0].message


def test_live_status_validation_passes() -> None:
    # All live model-referenced ADRs are Accepted; ADR-010 (Withdrawn) is not
    # referenced by the model and stays outside the scan.
    assert check_adr_statuses(load_model()) == []


# ---------------------------------------------------------------------------
# AUTHORITY_CYCLE (graph split: typed cycles fail, intentional pairs pass)
# ---------------------------------------------------------------------------


def test_typed_cycle_fails(tmp_path: Path) -> None:
    mutated = _mutate(
        CLEAN_MODEL,
        'from = "ADR-002"\nto = "ADR-001"\nedge_type = "Reference"',
        'from = "ADR-002"\nto = "ADR-001"\nedge_type = "Governs"',
    )
    model = load_model(_write_model(tmp_path, mutated))
    findings = check_authority_cycles(model)
    assert [f.code for f in findings] == ["AUTHORITY_CYCLE"]
    assert "cycle" in findings[0].message


def test_typed_cycle_across_three_adrs_fails(tmp_path: Path) -> None:
    # Move the model-only Reference edge off ADR-003 so the only pair-shaped
    # edges stay legal and the DFS cycle finding is the single report.
    mutated = _mutate(
        CLEAN_MODEL,
        'from = "ADR-001"\nto = "ADR-003"\nedge_type = "Reference"',
        'from = "ADR-001"\nto = "ADR-004"\nedge_type = "Reference"',
    )
    mutated += """
[[adr_edge]]
from = "ADR-002"
to = "ADR-003"
edge_type = "Specializes"

[[adr_edge]]
from = "ADR-003"
to = "ADR-001"
edge_type = "Extends"
"""
    model = load_model(_write_model(tmp_path, mutated))
    findings = check_authority_cycles(model)
    assert [f.code for f in findings] == ["AUTHORITY_CYCLE"]
    assert "ADR-001" in findings[0].message


def test_intentional_bidirectional_reference_pair_passes(tmp_path: Path) -> None:
    """Same pair as the failing cycle test, kept as typed + intentional Reference."""
    model = load_model(_write_model(tmp_path, CLEAN_MODEL))
    assert check_authority_cycles(model) == []


def test_unflagged_bidirectional_reference_fails(tmp_path: Path) -> None:
    mutated = _mutate(CLEAN_MODEL, "intentional = true", "intentional = false")
    model = load_model(_write_model(tmp_path, mutated))
    findings = check_authority_cycles(model)
    assert [f.code for f in findings] == ["AUTHORITY_CYCLE"]
    assert "intentional = true" in findings[0].message


def test_reference_only_pair_with_notes_passes(tmp_path: Path) -> None:
    """INV-02 reference-only pair form: both directions intentional with notes."""
    mutated = _mutate(
        CLEAN_MODEL,
        'from = "ADR-001"\nto = "ADR-002"\nedge_type = "Requires"',
        'from = "ADR-001"\nto = "ADR-002"\nedge_type = "Reference"\n'
        'intentional = true\nnote = "ADR-001 owns the decision; ADR-002 owns classification."',
    )
    model = load_model(_write_model(tmp_path, mutated))
    assert check_authority_cycles(model) == []


def test_reference_only_pair_missing_flag_fails(tmp_path: Path) -> None:
    mutated = _mutate(
        CLEAN_MODEL,
        'from = "ADR-001"\nto = "ADR-002"\nedge_type = "Requires"',
        'from = "ADR-001"\nto = "ADR-002"\nedge_type = "Reference"',
    )
    model = load_model(_write_model(tmp_path, mutated))
    findings = check_authority_cycles(model)
    assert [f.code for f in findings] == ["AUTHORITY_CYCLE", "AUTHORITY_CYCLE"]
    assert "intentional = true" in findings[0].message
    assert "reference-only" in findings[1].message


def test_reverse_only_reference_pair_is_clean(tmp_path: Path) -> None:
    mutated = _mutate(
        CLEAN_MODEL,
        'from = "ADR-001"\nto = "ADR-002"\nedge_type = "Requires"',
        'from = "ADR-009"\nto = "ADR-008"\nedge_type = "Requires"',
    )
    model = load_model(_write_model(tmp_path, mutated))
    # Cycle logic only: dangling IDs are reported by check_dangling_adrs instead.
    assert check_authority_cycles(model) == []


# ---------------------------------------------------------------------------
# EDGE_UNKNOWN_TYPE
# ---------------------------------------------------------------------------


def test_unknown_edge_type_fails(tmp_path: Path) -> None:
    mutated = _mutate(CLEAN_MODEL, 'edge_type = "Requires"', 'edge_type = "Controls"')
    model = load_model(_write_model(tmp_path, mutated))
    findings = check_edge_types(model)
    assert [f.code for f in findings] == ["EDGE_UNKNOWN_TYPE"]
    assert "Controls" in findings[0].message


# ---------------------------------------------------------------------------
# ASSUMPTION_DRIFT
# ---------------------------------------------------------------------------


def test_assumption_drift_against_live_config_shape(tmp_path: Path) -> None:
    model = load_model(_write_model(tmp_path, CLEAN_MODEL))
    config = _config(tmp_path, '[mcp_servers.alpha]\nurl = "http://10.0.0.5:9001"\n')
    findings = check_assumptions(model, config)
    assert [f.code for f in findings] == ["ASSUMPTION_DRIFT"]
    assert "10.0.0.5" in findings[0].message


def test_assumption_drift_when_current_value_changes(tmp_path: Path) -> None:
    mutated = _mutate(
        CLEAN_MODEL, "bind only to 127.0.0.1 loopback addresses", "bind to any address"
    )
    model = load_model(_write_model(tmp_path, mutated))
    findings = check_assumptions(model, _config(tmp_path))
    assert [f.code for f in findings] == ["ASSUMPTION_DRIFT"]
    assert "current_value" in findings[0].message


def test_config_check_without_config_keys_fails(tmp_path: Path) -> None:
    mutated = _mutate(
        CLEAN_MODEL, 'config_keys = ["mcp_servers.*.url"]', "config_keys = []"
    )
    model = load_model(_write_model(tmp_path, mutated))
    findings = check_assumptions(model, _config(tmp_path))
    assert [f.code for f in findings] == ["ASSUMPTION_DRIFT"]


def test_unimplementable_config_key_fails_closed(tmp_path: Path) -> None:
    mutated = _mutate(
        CLEAN_MODEL,
        'config_keys = ["mcp_servers.*.url"]',
        'config_keys = ["agent.some.other.key"]',
    )
    model = load_model(_write_model(tmp_path, mutated))
    findings = check_assumptions(model, _config(tmp_path))
    assert [f.code for f in findings] == ["ASSUMPTION_DRIFT"]
    assert "fail-closed" in findings[0].message


def test_unknown_validation_method_fails(tmp_path: Path) -> None:
    mutated = _mutate(
        CLEAN_MODEL,
        'validation_method = "manual-review"',
        'validation_method = "vibe-check"',
    )
    model = load_model(_write_model(tmp_path, mutated))
    findings = check_assumptions(model, _config(tmp_path))
    assert [f.code for f in findings] == ["ASSUMPTION_DRIFT"]


def test_manual_review_assumption_is_not_policed(tmp_path: Path) -> None:
    """A manual-review assumption may contradict the config file without a finding."""
    model = load_model(_write_model(tmp_path, CLEAN_MODEL))
    config = _config(tmp_path, '[mcp_servers.alpha]\nurl = "http://10.0.0.5:9001"\n')
    mutated = _mutate(
        CLEAN_MODEL,
        'validation_method = "config-check"',
        'validation_method = "manual-review"',
    )
    model = load_model(_write_model(tmp_path, mutated))
    assert check_assumptions(model, config) == []


# ---------------------------------------------------------------------------
# ASSUMPTION_DRIFT for eventbus.host (plan adrchk015 REQ-006, ARCH-002)
# ---------------------------------------------------------------------------

EVENTBUS_ASSUMPTION = """
[[assumption]]
id = "ARCH-903"
name = "Loopback EventBus host"
current_value = "The EventBus binds to 127.0.0.1 by default"
applicable_adrs = ["ADR-001"]
validation_method = "config-check"
config_keys = ["eventbus.host"]
owner = "test-owner"
review_triggers = ["network topology change"]
"""


def _eventbus_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "eventbus.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_eventbus_host_not_loopback_fails(tmp_path: Path) -> None:
    model = load_model(_write_model(tmp_path, CLEAN_MODEL + EVENTBUS_ASSUMPTION))
    findings = check_assumptions(
        model, _config(tmp_path), _eventbus_config(tmp_path, 'host = "0.0.0.0"\n')
    )
    assert [f.code for f in findings] == ["ASSUMPTION_DRIFT"]
    assert "eventbus.host" in findings[0].message


def test_eventbus_localhost_host_passes(tmp_path: Path) -> None:
    model = load_model(_write_model(tmp_path, CLEAN_MODEL + EVENTBUS_ASSUMPTION))
    assert (
        check_assumptions(
            model, _config(tmp_path), _eventbus_config(tmp_path, 'host = "localhost"\n')
        )
        == []
    )


def test_eventbus_absent_host_asserts_documented_default(tmp_path: Path) -> None:
    # config/eventbus.toml ships no host key: scripts/eventbus/config.py binds
    # 127.0.0.1 by default, which is the asserted state.
    model = load_model(_write_model(tmp_path, CLEAN_MODEL + EVENTBUS_ASSUMPTION))
    assert (
        check_assumptions(
            model, _config(tmp_path), _eventbus_config(tmp_path, "[bus]\nport = 9100\n")
        )
        == []
    )


def test_eventbus_config_missing_fails_closed(tmp_path: Path) -> None:
    model = load_model(_write_model(tmp_path, CLEAN_MODEL + EVENTBUS_ASSUMPTION))
    findings = check_assumptions(model, _config(tmp_path), tmp_path / "missing.toml")
    assert [f.code for f in findings] == ["ASSUMPTION_DRIFT"]
    assert "fail-closed" in findings[0].message


def test_eventbus_current_value_must_state_loopback(tmp_path: Path) -> None:
    mutated = _mutate(
        CLEAN_MODEL + EVENTBUS_ASSUMPTION,
        'current_value = "The EventBus binds to 127.0.0.1 by default"',
        'current_value = "The EventBus binds to the container bridge network"',
    )
    model = load_model(_write_model(tmp_path, mutated))
    findings = check_assumptions(
        model, _config(tmp_path), _eventbus_config(tmp_path, 'host = "127.0.0.1"\n')
    )
    assert [f.code for f in findings] == ["ASSUMPTION_DRIFT"]
    assert "current_value" in findings[0].message


def test_live_eventbus_assertion_passes() -> None:
    # ARCH-002 now asserts eventbus.host against config/eventbus.toml; the
    # absent key asserts the documented 127.0.0.1 default, so the live model
    # stays clean.
    assert check_assumptions(load_model()) == []


# ---------------------------------------------------------------------------
# FRONTMATTER_DIVERGENCE (row 05's rules, exercised on sandbox ADR files)
# ---------------------------------------------------------------------------


def test_frontmatter_edge_missing_from_model_fails(tmp_path: Path) -> None:
    model = load_model(_write_model(tmp_path, CLEAN_MODEL))
    adr = _adr_dir(
        tmp_path,
        {
            "adr_02_01_001_alpha.md": ["adr_02_01_002_beta.md"],
            "adr_02_01_002_beta.md": [
                "adr_02_01_003_gamma.md",
                "adr_02_01_001_alpha.md",
            ],
        },
    )
    # (ADR-002 -> ADR-003) exists in front matter only; the model has no such edge.
    findings = check_frontmatter_consistency(model, adr)
    assert [f.code for f in findings] == ["FRONTMATTER_DIVERGENCE"]
    assert "ADR-002 -> ADR-003" in findings[0].message


def test_non_reference_model_edge_missing_from_frontmatter_fails(
    tmp_path: Path,
) -> None:
    model = load_model(_write_model(tmp_path, CLEAN_MODEL))
    adr = _adr_dir(tmp_path)  # empty related lists everywhere
    findings = check_frontmatter_consistency(model, adr)
    codes = [f.code for f in findings]
    assert codes == ["FRONTMATTER_DIVERGENCE"]
    assert "ADR-001 -> ADR-002" in findings[0].message


def test_model_only_reference_edge_is_clean(tmp_path: Path) -> None:
    model = load_model(_write_model(tmp_path, CLEAN_MODEL))
    adr = _adr_dir(
        tmp_path,
        {
            "adr_02_01_001_alpha.md": ["adr_02_01_002_beta.md"],
            "adr_02_01_002_beta.md": ["adr_02_01_001_alpha.md"],
        },
    )
    # 001 -> 003 is a model-only Reference edge: clean by ADR-016 Decision 7.
    assert check_frontmatter_consistency(model, adr) == []


def test_index_and_guide_frontmatter_are_excluded(tmp_path: Path) -> None:
    model = load_model(_write_model(tmp_path, CLEAN_MODEL))
    adr = _adr_dir(tmp_path)
    (adr / "adr_01_index.md").write_text(
        "---\ntitle: index\nrelated:\n  - adr_02_01_001_alpha.md\n---\n# index\n",
        encoding="utf-8",
    )
    findings = check_frontmatter_consistency(model, adr)
    assert all("adr_01_index.md" not in f.location for f in findings)


# ---------------------------------------------------------------------------
# CLI surface (main() return values, per test_check_adr_reference.py idiom)
# ---------------------------------------------------------------------------


def test_cli_clean_exits_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "--model",
            str(_write_model(tmp_path, CLEAN_MODEL)),
            "--adr-dir",
            str(_adr_dir(tmp_path)),
            "--config",
            str(_config(tmp_path)),
        ]
    )
    assert rc == 0
    assert "no findings" in capsys.readouterr().out.lower()


def test_cli_finding_exits_one_with_exact_code(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    mutated = _mutate(
        CLEAN_MODEL,
        'decision_target = "beta.decision"',
        'decision_target = "alpha.decision"',
    )
    rc = main(
        [
            "--model",
            str(_write_model(tmp_path, mutated)),
            "--adr-dir",
            str(_adr_dir(tmp_path)),
            "--config",
            str(_config(tmp_path)),
        ]
    )
    assert rc == 1
    assert "DUP_PRIMARY" in capsys.readouterr().out


def test_cli_json_format_reports_findings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    mutated = _mutate(CLEAN_MODEL, 'edge_type = "Requires"', 'edge_type = "Controls"')
    rc = main(
        [
            "--model",
            str(_write_model(tmp_path, mutated)),
            "--adr-dir",
            str(_adr_dir(tmp_path)),
            "--config",
            str(_config(tmp_path)),
            "--format",
            "json",
        ]
    )
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert [entry["code"] for entry in payload] == ["EDGE_UNKNOWN_TYPE"]
    assert set(payload[0]) == {"code", "location", "message"}


def test_cli_invalid_model_file_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(["--model", str(tmp_path / "missing.toml")])
    assert rc == 1
    assert "[ERROR]" in capsys.readouterr().err
