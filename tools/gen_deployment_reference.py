#!/usr/bin/env python3
"""gen_deployment_reference.py — Auto-generate the platform DB path/config-key reference table.

Companion to gen_mcp_reference.py / gen_rag_reference.py, applying the same
"generate the objective facts from live code instead of hand-maintaining a
copy" approach to docs/02_deployment-part2.md's DB overview table. This is
exactly the table whose hand-maintained copy went stale (see
check_deployment_docs_consistency.py's docstring and NC findings in
docs_review_deployment.md: "three databases" claimed for four, eventbus.sqlite
missing from the table, workflow_db_path claimed to be in agent.toml when it
is not). Regenerating it from scripts/db/config.py + config/agent.toml makes
that drift structurally impossible going forward.

Only the mechanically derivable columns (DB name, default path, config key,
whether agent.toml sets it explicitly) are generated -- the "Purpose" column
requires human judgment and stays hand-maintained in the surrounding prose.

Usage:
    python tools/gen_deployment_reference.py          # writes to docs/
    python tools/gen_deployment_reference.py --dry-run # print to stdout only
"""

from __future__ import annotations

import argparse
import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_TOML = REPO_ROOT / "config" / "agent.toml"
DB_CONFIG_SRC = REPO_ROOT / "scripts" / "db" / "config.py"
REFERENCE_DOC = REPO_ROOT / "docs" / "02_deployment-part2.md"
GUARD_START = "<!-- AUTO-GENERATED: gen_deployment_reference.py db-path-reference -->"
GUARD_END = "<!-- END AUTO-GENERATED -->"

_DB_PATH_FIELD_RE = re.compile(
    r'^\s+(\w+_db_path):\s*str(?:\s*=\s*"([^"]*)")?', re.MULTILINE
)


def _default_db_paths() -> dict[str, str | None]:
    """Return {config_key: python_level_default_or_None} from DbConfig's fields."""
    content = DB_CONFIG_SRC.read_text(encoding="utf-8")
    return {key: default for key, default in _DB_PATH_FIELD_RE.findall(content)}


def _agent_toml_db_paths() -> dict[str, str]:
    """Return {config_key: path} for every `*_db_path = "..."` set in agent.toml."""
    with AGENT_TOML.open("rb") as f:
        cfg = tomllib.load(f)
    return {
        k: v for k, v in cfg.items() if k.endswith("_db_path") and isinstance(v, str)
    }


def generate_reference_table() -> str:
    defaults = _default_db_paths()
    configured = _agent_toml_db_paths()

    lines = [
        "| DB | Default path | Config key | Set in `agent.toml`? |",
        "|---|---|---|---|",
    ]
    for key in sorted(defaults):
        db_name = f"{key.removesuffix('_db_path')}.sqlite"
        if key in configured:
            path = configured[key]
            in_toml = "Yes"
        else:
            path = defaults[key] or "(no default)"
            in_toml = "No (Python-level default in `scripts/db/config.py`)"
        lines.append(f"| `{db_name}` | `{path}` | `{key}` | {in_toml} |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    table = generate_reference_table()
    generated = (
        f"{GUARD_START}\n"
        f"Generated from `scripts/db/config.py` and `config/agent.toml`. "
        f"Do not hand-edit between the guard comments; run "
        f"`python tools/gen_deployment_reference.py` to refresh.\n\n"
        f"{table}\n"
        f"{GUARD_END}"
    )

    if args.dry_run:
        print(generated)
        return

    doc = REFERENCE_DOC.read_text(encoding="utf-8")
    start = doc.find(GUARD_START)
    end = doc.find(GUARD_END)
    if start != -1 and end != -1:
        updated = doc[:start] + generated + doc[end + len(GUARD_END) :]
    else:
        updated = (
            doc.rstrip("\n")
            + "\n\n### DB Path Reference (auto-generated)\n\n"
            + generated
            + "\n"
        )
    REFERENCE_DOC.write_text(updated, encoding="utf-8")
    print(f"Updated {REFERENCE_DOC.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
