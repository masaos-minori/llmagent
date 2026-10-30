#!/usr/bin/env python3
"""generate_adr_authority.py — Generate the ADR index graph sections from the authority model (ADR-016, plan adrauth001 REQ-003).

Rewrites three guarded blocks in `docs/10_adr/adr_01_index.md` from
`config/adr_authority.toml` via tools/_adr_authority_core.py, so the graphs
are never hand-maintained:

  adr-reference-graph       the `ADR-A → B` text fence under
                            `## ADR Dependency Graph` (all edges)
  adr-authority-graph       typed-edge lines plus the primary-authority table
                            under `### Authority Graph` (non-Reference edges)
  adr-intentional-cycles    the `ADR-A ↔ ADR-B: note` bullets under
                            `### Intentional Circular References`

All prose outside the guard comments (Purpose, ADR List, edge-meaning
sentences, the cycle-closing paragraph, the invariant matrix) is hand-written
and untouched. The generator refuses to emit when the model fails the shared
validator core, so a broken model never lands generated content.

`--check` writes nothing and exits 1 when a guarded block is missing or
differs from the generator output (ADR-016 INV-01... see INV-03), mirroring
tools/generate_reference_table.py's drift gate.

Usage:
    python tools/generate_adr_authority.py            # refresh the three blocks
    python tools/generate_adr_authority.py --check    # CI drift gate
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import orjson

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._adr_authority_core import (
    ADR_DIR,
    AGENT_CONFIG_PATH,
    MODEL_PATH,
    AuthorityModel,
    AuthorityModelError,
    Finding,
    load_model,
    validate_model,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_DOC = REPO_ROOT / "docs" / "10_adr" / "adr_01_index.md"

GUARD_END = "<!-- END AUTO-GENERATED -->"
GUARD_START_REFERENCE = (
    "<!-- AUTO-GENERATED: generate_adr_authority.py adr-reference-graph -->"
)
GUARD_START_AUTHORITY = (
    "<!-- AUTO-GENERATED: generate_adr_authority.py adr-authority-graph -->"
)
GUARD_START_CYCLES = (
    "<!-- AUTO-GENERATED: generate_adr_authority.py adr-intentional-cycles -->"
)

GUARDS: tuple[tuple[str, str], ...] = (
    ("adr-reference-graph", GUARD_START_REFERENCE),
    ("adr-authority-graph", GUARD_START_AUTHORITY),
    ("adr-intentional-cycles", GUARD_START_CYCLES),
)

WELCOME = (
    "Generated from `config/adr_authority.toml` by `tools/generate_adr_authority.py`. "
    "Do not hand-edit between the guard comments; run "
    "`python tools/generate_adr_authority.py` to refresh."
)


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------


def render_reference_graph(model: AuthorityModel) -> str:
    """The `ADR-A → B` fence: one line per source with outgoing edges, sources
    ascending, targets comma-separated ascending."""
    targets: dict[str, set[str]] = {}
    for edge in model.edges:
        targets.setdefault(edge.from_adr, set()).add(edge.to_adr)
    lines = ["```text"]
    for source in sorted(targets):
        lines.append(f"{source} → {', '.join(sorted(targets[source]))}")
    lines.append("```")
    return "\n".join(lines)


def render_authority_graph(model: AuthorityModel) -> str:
    """Typed-edge lines (non-Reference edges) plus the primary-authority table."""
    typed = sorted(
        (e for e in model.edges if e.edge_type != "Reference"),
        key=lambda e: (e.from_adr, e.to_adr, e.edge_type),
    )
    lines = ["```text"]
    for edge in typed:
        lines.append(f"{edge.from_adr} --{edge.edge_type}--> {edge.to_adr}")
    lines.append("```")
    lines.append("")
    lines.append(
        "| Decision target | Primary ADR | Supplemental ADRs (authority limit) |"
    )
    lines.append("|---|---|---|")
    for entry in sorted(model.authorities, key=lambda a: a.decision_target):
        if entry.supplemental_adrs:
            supplemental = "; ".join(
                f"{sup.adr} — {sup.limit}" for sup in entry.supplemental_adrs
            )
        else:
            supplemental = "—"
        lines.append(
            f"| `{entry.decision_target}` | {entry.primary_adr} | {supplemental} |"
        )
    return "\n".join(lines)


def render_intentional_cycles(model: AuthorityModel) -> str:
    """One `ADR-A ↔ ADR-B: note` bullet per intentional bidirectional pair,
    pairs ascending, note taken verbatim from the model's intentional edge."""
    by_pair = {(e.from_adr, e.to_adr): e for e in model.edges}
    bullets: list[str] = []
    for a, b in sorted(by_pair):
        if a >= b:
            continue
        forward, reverse = by_pair[(a, b)], by_pair.get((b, a))
        if reverse is None:
            continue
        sides = (forward, reverse)
        if all(s.edge_type == "Reference" for s in sides) or all(
            s.edge_type != "Reference" for s in sides
        ):
            continue  # validator core reports these; emit the split pairs only
        reference = next(s for s in sides if s.edge_type == "Reference")
        bullets.append(f"- {a} ↔ {b}: {reference.note}")
    return "\n".join(bullets)


SECTION_RENDERERS = {
    "adr-reference-graph": render_reference_graph,
    "adr-authority-graph": render_authority_graph,
    "adr-intentional-cycles": render_intentional_cycles,
}


# ---------------------------------------------------------------------------
# Guarded-block replacement
# ---------------------------------------------------------------------------


def render_updated_doc(model: AuthorityModel, doc_content: str) -> str:
    """Return doc_content with all three guarded blocks regenerated.

    Raises AuthorityModelError when a guard comment pair is missing — the
    sections live at fixed positions in the index, so appending a missing
    block at EOF (the generate_reference_table.py fallback) would be wrong."""
    for name, guard_start in GUARDS:
        start = doc_content.find(guard_start)
        end = doc_content.find(GUARD_END, start + 1) if start != -1 else -1
        if start == -1 or end == -1:
            raise AuthorityModelError(
                f"guard comments for section {name!r} missing from "
                f"{INDEX_DOC.relative_to(REPO_ROOT)}; add the guard pair at the "
                "section's position before running the generator"
            )
        body = SECTION_RENDERERS[name](model)
        generated = f"{guard_start}\n{WELCOME}\n\n{body}\n{GUARD_END}"
        doc_content = (
            doc_content[:start] + generated + doc_content[end + len(GUARD_END) :]
        )
    return doc_content


def check_drift(model: AuthorityModel, index_path: Path) -> list[str]:
    """Return one drift entry per guarded section that is missing or differs."""
    drifted: list[str] = []
    content = index_path.read_text(encoding="utf-8")
    for name, guard_start in GUARDS:
        if guard_start not in content or GUARD_END not in content:
            drifted.append(
                f"{index_path.relative_to(REPO_ROOT)} (section {name}: guarded block missing)"
            )
    try:
        if render_updated_doc(model, content) != content:
            for name, guard_start in GUARDS:
                start = content.find(guard_start)
                end = content.find(GUARD_END, start + 1)
                body = SECTION_RENDERERS[name](model)
                current = content[start + len(guard_start) : end].strip("\n")
                if current != f"{WELCOME}\n\n{body}":
                    drifted.append(
                        f"{index_path.relative_to(REPO_ROOT)} (section {name})"
                    )
    except AuthorityModelError:
        pass  # already reported as "guarded block missing"
    return drifted


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _render_findings_json(findings: list[Finding]) -> str:
    payload = [
        {"code": f.code, "location": f.location, "message": f.message}
        for f in sorted(findings, key=lambda f: (f.code, f.location, f.message))
    ]
    return orjson.dumps(payload, option=orjson.OPT_INDENT_2).decode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the ADR index graph sections (reference graph, authority "
            "graph, intentional cycles) from config/adr_authority.toml."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Write nothing; exit 1 when a guarded section is missing or drifted.",
    )
    parser.add_argument(
        "--format",
        choices=["json"],
        default=None,
        help="Machine-readable findings/drift output (default: human-readable text)",
    )
    parser.add_argument(
        "--model", type=Path, default=MODEL_PATH, help=argparse.SUPPRESS
    )
    parser.add_argument("--index", type=Path, default=INDEX_DOC, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    try:
        model = load_model(args.model)
    except AuthorityModelError as exc:
        message = f"authority model is invalid: {exc}"
        if args.format == "json":
            print(
                _render_findings_json(
                    [
                        Finding(
                            code="MODEL_INVALID",
                            location=str(args.model),
                            message=message,
                        )
                    ]
                )
            )
        else:
            print(f"[ERROR] {message}", file=sys.stderr)
        return 1

    findings = validate_model(model, adr_dir=ADR_DIR, config_path=AGENT_CONFIG_PATH)
    if findings:
        if args.format == "json":
            print(_render_findings_json(findings))
        else:
            for finding in findings:
                print(f"[{finding.code}] {finding.location}: {finding.message}")
            print(
                f"\nRefusing to generate: {len(findings)} finding(s) in the model. "
                "Fix config/adr_authority.toml (see tools/check_adr_authority.py).",
                file=sys.stderr,
            )
        return 1

    if args.check:
        drifted = check_drift(model, args.index)
        if args.format == "json":
            print(orjson.dumps(drifted, option=orjson.OPT_INDENT_2).decode())
        else:
            for entry in drifted:
                print(f"DRIFT: {entry}")
            if not drifted:
                print("No drift found")
        return 1 if drifted else 0

    try:
        content = args.index.read_text(encoding="utf-8")
        updated = render_updated_doc(model, content)
    except AuthorityModelError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    if updated == content:
        print("No changes: guarded sections already current.")
        return 0
    args.index.write_text(updated, encoding="utf-8")
    print(
        f"Refreshed {len(GUARDS)} guarded sections in {args.index.relative_to(REPO_ROOT)}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
