#!/usr/bin/env python3
"""check_adr_authority.py — Validate the ADR authority model (ADR-016, plan adrauth001 REQ-004).

Loads `config/adr_authority.toml` and runs every model validator from
tools/_adr_authority_core.py: duplicate primaries (DUP_PRIMARY), dangling ADR
IDs (DANGLING_ADR), authority-graph cycles and intentional-pair violations
(AUTHORITY_CYCLE), unknown edge types (EDGE_UNKNOWN_TYPE), and config-check
assumption drift (ASSUMPTION_DRIFT). Any finding exits 1 — a broken model
file (unreadable TOML, missing fields) is also a fail-closed error.

The front matter/model cross-check (FRONTMATTER_DIVERGENCE) is NOT run here;
tools/check_adr_reference.py owns it (ADR-016 Verification section).

CLI contract mirrors tools/check_adr_reference.py: no required arguments,
`--format json`, nonzero exit on any finding. Path overrides exist only for
test fixtures.

Usage:
    python tools/check_adr_authority.py
    python tools/check_adr_authority.py --format json
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
    AuthorityModelError,
    Finding,
    load_model,
    validate_model,
)


def collect_findings(
    model_path: Path = MODEL_PATH,
    adr_dir: Path = ADR_DIR,
    config_path: Path = AGENT_CONFIG_PATH,
) -> list[Finding]:
    model = load_model(model_path)
    return validate_model(model, adr_dir=adr_dir, config_path=config_path)


def render_json(findings: list[Finding]) -> str:
    payload = [
        {"code": f.code, "location": f.location, "message": f.message}
        for f in sorted(findings, key=lambda f: (f.code, f.location, f.message))
    ]
    return orjson.dumps(payload, option=orjson.OPT_INDENT_2).decode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate config/adr_authority.toml against the ADR-016 authority "
            "model rules (single primary per target, acyclic authority graph, "
            "resolvable ADR ids, config-check assumption drift)."
        )
    )
    parser.add_argument(
        "--format",
        choices=["json"],
        default=None,
        help="Machine-readable output format (default: human-readable text)",
    )
    parser.add_argument(
        "--model", type=Path, default=MODEL_PATH, help=argparse.SUPPRESS
    )
    parser.add_argument("--adr-dir", type=Path, default=ADR_DIR, help=argparse.SUPPRESS)
    parser.add_argument(
        "--config", type=Path, default=AGENT_CONFIG_PATH, help=argparse.SUPPRESS
    )
    args = parser.parse_args(argv)

    try:
        findings = collect_findings(args.model, args.adr_dir, args.config)
    except AuthorityModelError as exc:
        message = f"authority model is invalid: {exc}"
        if args.format == "json":
            print(
                render_json(
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

    if args.format == "json":
        print(render_json(findings))
        return 1 if findings else 0

    if findings:
        for finding in sorted(findings, key=lambda f: (f.code, f.location, f.message)):
            print(f"[{finding.code}] {finding.location}: {finding.message}")
        print(f"\nFound {len(findings)} finding(s).", file=sys.stderr)
        return 1
    print("Authority model OK: no findings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
