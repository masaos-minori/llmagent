"""tests/tools/test_generate_adr_authority.py

Generator reproducibility tests for tools/generate_adr_authority.py, per plan
adrauth001 row 13 (REQ-003, AC-4) and plan adrchk015 row 12 (REQ-014, REQ-027).
Idiom follows tests/tools/test_generate_reference_table.py: tmp sandbox doc +
module-constant monkeypatching + main() return-value assertions for the
--check exit code.

Sandbox-first: tests 1-4 run against a tmp sandbox index, a tmp sandbox
governance_01 (host of the adr-section-header-list block), and a trimmed
fixture model (not the live files). The single live test asserts `--check` is
clean against the committed docs/10_adr/adr_01_index.md,
docs/00_governance/governance_01_documentation-policy.md and
config/adr_authority.toml — the committed-state lock.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.generate_adr_authority as gen
from tools._adr_authority_core import AuthorityModelError, load_model
from tools.check_adr_structure import _CONDITIONAL_HEADINGS, _REQUIRED_HEADINGS
from tools.generate_adr_authority import (
    GUARD_END,
    GUARD_START_AUTHORITY,
    GUARD_START_CYCLES,
    GUARD_START_HEADER_LIST,
    GUARD_START_REFERENCE,
    GUARDS,
    WELCOME,
    main,
    render_updated_doc,
)

# Trimmed copy of the real model semantics: three ADRs, one typed pair with an
# intentional Reference back-edge, one model-only Reference edge.
FIXTURE_MODEL = """\
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
"""

SANDBOX_INDEX = f"""\
# ADR Index

## ADR Dependency Graph

`A → B` semantics sentence (hand-written).

{GUARD_START_REFERENCE}
{GUARD_END}

### Authority Graph

Hand-written authority prose.

{GUARD_START_AUTHORITY}
{GUARD_END}

### Intentional Circular References

Hand-written intro sentence.

{GUARD_START_CYCLES}
{GUARD_END}

Hand-written closing paragraph.
"""

SANDBOX_GOVERNANCE = f"""\
# Governance 01 (sandbox)

## ADR Section Header Standardization

Hand-written intro sentence.

{GUARD_START_HEADER_LIST}
{GUARD_END}

Hand-written closing sentence.
"""


@pytest.fixture
def sandbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """(fixture model path, sandbox index path) with the core constants redirected.

    The fixture model references ADR-001..ADR-003 with a config-check
    assumption; the sandbox ADR dir and config make validation deterministic
    instead of coupling the fixture to live repository state. The sandbox
    governance_01 hosts the adr-section-header-list guard pair so write and
    --check runs never touch the live document.
    """
    model_path = tmp_path / "adr_authority.toml"
    model_path.write_text(FIXTURE_MODEL, encoding="utf-8")
    index = tmp_path / "adr_01_index.md"
    index.write_text(SANDBOX_INDEX, encoding="utf-8")
    governance = tmp_path / "governance_01.md"
    governance.write_text(SANDBOX_GOVERNANCE, encoding="utf-8")

    adr_dir = tmp_path / "adr"
    adr_dir.mkdir()
    for name in ("adr_02_01_001_a.md", "adr_02_01_002_b.md", "adr_02_01_003_c.md"):
        (adr_dir / name).write_text(
            "---\ntitle: t\nrelated: []\n---\n# body\n\n## Status\nAccepted\n",
            encoding="utf-8",
        )
    config = tmp_path / "agent.toml"
    config.write_text(
        '[mcp_servers.alpha]\nurl = "http://127.0.0.1:9001"\n', encoding="utf-8"
    )

    monkeypatch.setattr(gen, "ADR_DIR", adr_dir)
    monkeypatch.setattr(gen, "AGENT_CONFIG_PATH", config)
    monkeypatch.setattr(gen, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(gen, "INDEX_DOC", index)
    monkeypatch.setattr(gen, "GOVERNANCE_01_DOC", governance)
    return model_path, index


def _generate(model_path: Path, index: Path) -> int:
    return main(["--model", str(model_path), "--index", str(index)])


def _extract_guarded(index: Path, guard_start: str) -> str:
    content = index.read_text(encoding="utf-8")
    start = content.find(guard_start)
    end = content.find(GUARD_END, start + 1)
    return content[start:end]


# ---------------------------------------------------------------------------
# 1. Reproducibility: regeneration is byte-stable
# ---------------------------------------------------------------------------


def test_double_generation_is_identical(sandbox: tuple[Path, Path]) -> None:
    model_path, index = sandbox
    assert _generate(model_path, index) == 0
    first = index.read_text(encoding="utf-8")

    assert _generate(model_path, index) == 0  # "No changes" path
    assert index.read_text(encoding="utf-8") == first

    model = load_model(model_path)
    again = render_updated_doc(model, first)
    assert again == first  # rendering is deterministic, not state-dependent


def test_sections_render_from_the_model(sandbox: tuple[Path, Path]) -> None:
    model_path, index = sandbox
    assert _generate(model_path, index) == 0

    reference = _extract_guarded(index, GUARD_START_REFERENCE)
    assert "ADR-001 → ADR-002, ADR-003" in reference
    assert "ADR-002 → ADR-001" in reference

    authority = _extract_guarded(index, GUARD_START_AUTHORITY)
    assert "ADR-001 --Requires--> ADR-002" in authority
    assert "ADR-002 --Reference--> ADR-001" not in authority  # only typed edges
    assert "| `alpha.decision` | ADR-001 |" in authority

    cycles = _extract_guarded(index, GUARD_START_CYCLES)
    assert (
        "- ADR-001 ↔ ADR-002: ADR-002 classifies failures; ADR-001 owns the decision."
        in cycles
    )


# ---------------------------------------------------------------------------
# 2-3. Drift detection: tamper and missing guards
# ---------------------------------------------------------------------------


def test_hand_edit_inside_guard_is_reported(sandbox: tuple[Path, Path]) -> None:
    model_path, index = sandbox
    assert _generate(model_path, index) == 0

    tampered = index.read_text(encoding="utf-8").replace("ADR-003", "ADR-999", 1)
    index.write_text(tampered, encoding="utf-8")

    rc = main(["--model", str(model_path), "--index", str(index), "--check"])
    assert rc == 1
    assert gen.check_drift(load_model(model_path), index) == [
        "adr_01_index.md (section adr-reference-graph)"
    ]
    assert index.read_text(encoding="utf-8") == tampered  # --check never writes


def test_missing_guard_is_reported(sandbox: tuple[Path, Path]) -> None:
    model_path, index = sandbox
    stripped = index.read_text(encoding="utf-8").replace(
        GUARD_START_CYCLES + "\n" + GUARD_END, "hand-written bullets"
    )
    index.write_text(stripped, encoding="utf-8")

    drifted = gen.check_drift(load_model(model_path), index)
    assert drifted == [
        "adr_01_index.md (section adr-intentional-cycles: guarded block missing)"
    ]
    assert main(["--model", str(model_path), "--index", str(index), "--check"]) == 1
    with pytest.raises(AuthorityModelError, match="guard comments"):
        render_updated_doc(load_model(model_path), stripped)


# ---------------------------------------------------------------------------
# 4. Hand-written regions outside the guards are byte-unchanged by a write run
# ---------------------------------------------------------------------------


def test_write_mode_preserves_hand_written_regions(sandbox: tuple[Path, Path]) -> None:
    model_path, index = sandbox
    before = index.read_text(encoding="utf-8")
    assert _generate(model_path, index) == 0
    after = index.read_text(encoding="utf-8")

    outside_before, outside_after = before, after
    for _name, guard_start in GUARDS:
        for text in (outside_before, outside_after):
            start = text.find(guard_start)
            end = text.find(GUARD_END, start + 1)
            assert start != -1 and end != -1
        outside_before = (
            outside_before[: outside_before.find(guard_start)]
            + outside_before[outside_before.find(GUARD_END) + len(GUARD_END) :]
        )
    assert outside_after.count("Hand-written") == before.count("Hand-written")
    assert "semantics sentence (hand-written)" in outside_after
    # The only differences are the guard bodies themselves.
    for _name, guard_start in GUARDS:
        assert _extract_guarded(index, guard_start).startswith(guard_start)


# ---------------------------------------------------------------------------
# 4b. governance_01 header-list block (plan adrchk015 row 12, REQ-014/REQ-027)
# ---------------------------------------------------------------------------


def test_generated_header_list_mirrors_the_checker_constant(
    sandbox: tuple[Path, Path],
) -> None:
    model_path, _index = sandbox
    assert _generate(model_path, _index) == 0
    block = _extract_guarded(gen.GOVERNANCE_01_DOC, GUARD_START_HEADER_LIST)
    body = block[len(GUARD_START_HEADER_LIST) :].strip("\n")
    assert body == f"{WELCOME}\n\n{gen.render_header_list(load_model(model_path))}"
    for heading in _REQUIRED_HEADINGS:
        assert f"`{heading}`" in block
    for heading in _CONDITIONAL_HEADINGS:
        assert f"`{heading}`" in block


def test_hand_edited_header_list_block_is_drift(sandbox: tuple[Path, Path]) -> None:
    model_path, index = sandbox
    assert _generate(model_path, index) == 0
    tampered = gen.GOVERNANCE_01_DOC.read_text(encoding="utf-8").replace(
        "1. `Keywords`", "1. `Headingz`", 1
    )
    gen.GOVERNANCE_01_DOC.write_text(tampered, encoding="utf-8")

    assert main(["--model", str(model_path), "--index", str(index), "--check"]) == 1
    assert gen.check_drift(
        load_model(model_path), gen.GOVERNANCE_01_DOC, gen.HEADER_LIST_GUARDS
    ) == ["governance_01.md (section adr-section-header-list)"]


def test_missing_governance_guard_blocks_the_whole_write_atomically(
    sandbox: tuple[Path, Path],
) -> None:
    model_path, index = sandbox
    gen.GOVERNANCE_01_DOC.write_text("# no guards here\n", encoding="utf-8")
    before = index.read_text(encoding="utf-8")
    assert _generate(model_path, index) == 1
    assert index.read_text(encoding="utf-8") == before  # nothing written on refusal


# ---------------------------------------------------------------------------
# 4c. Refusal gate on the new finding codes (plan adrchk015 REQ-003)
# ---------------------------------------------------------------------------


def test_generation_refuses_on_duplicate_edge(
    sandbox: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    model_path, index = sandbox
    before = index.read_text(encoding="utf-8")
    model_path.write_text(
        FIXTURE_MODEL
        + '\n[[adr_edge]]\nfrom = "ADR-001"\nto = "ADR-002"\nedge_type = "Requires"\n',
        encoding="utf-8",
    )
    assert _generate(model_path, index) == 1
    assert "[EDGE_DUPLICATE]" in capsys.readouterr().out
    assert index.read_text(encoding="utf-8") == before


def test_generation_refuses_on_invalid_status(
    sandbox: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    model_path, index = sandbox
    before = index.read_text(encoding="utf-8")
    (index.parent / "adr" / "adr_02_01_001_a.md").write_text(
        "---\ntitle: t\nrelated: []\n---\n# body\n\n## Status\nDeprecated\n",
        encoding="utf-8",
    )
    assert _generate(model_path, index) == 1
    assert "[ADR_STATUS_INVALID]" in capsys.readouterr().out
    assert index.read_text(encoding="utf-8") == before


# ---------------------------------------------------------------------------
# 5. Live committed-state lock (passes only with rows 02/03/06 landed)
# ---------------------------------------------------------------------------


def test_live_docs_and_model_have_no_drift() -> None:
    assert main(["--check"]) == 0


def test_live_index_guarded_sections_are_byte_reproducible(tmp_path: Path) -> None:
    model = load_model(gen.MODEL_PATH)
    committed = gen.INDEX_DOC.read_text(encoding="utf-8")
    assert render_updated_doc(model, committed) == committed
