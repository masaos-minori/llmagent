#!/usr/bin/env python3
"""gen_rag_reference.py — Auto-generate CLI help sections in docs.

Usage:
    python scripts/docs/gen_rag_reference.py          # writes to docs/
    python scripts/docs/gen_rag_reference.py --dry-run # print to stdout only

Writes CLI help blocks for crawler/chunk_splitter/ingester into
docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md.
Config table generation (--dry-run only) is kept for manual inspection.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tomllib
from pathlib import Path

CONFIG_PATHS = [
    Path("config/crawler.toml"),
    Path("config/chunk_splitter.toml"),
    Path("config/ingester.toml"),
]
CLI_HELP_DOC = Path("docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md")
GUARD_START = "<!-- AUTO-GENERATED: gen_rag_reference.py cli-help -->"
GUARD_END = "<!-- END AUTO-GENERATED -->"

CLI_TOOLS = [
    ("scripts/rag/ingestion/crawler.py", "crawler"),
    ("scripts/rag/ingestion/chunk_splitter.py", "chunk_splitter"),
    ("scripts/rag/ingestion/ingester.py", "ingester"),
]


def generate_config_table() -> str:
    lines = ["| Key | Default | Description |", "|---|---|---|"]
    for config_path in CONFIG_PATHS:
        with open(config_path, "rb") as f:
            cfg = tomllib.load(f)
        for section, values in cfg.items():
            if isinstance(values, dict):
                for key, val in values.items():
                    lines.append(f"| `{section}.{key}` | `{val}` | — |")
            else:
                lines.append(f"| `{section}` | `{values}` | — |")
    return "\n".join(lines)


def generate_cli_help(script_path: str, name: str) -> str:
    result = subprocess.run(
        [sys.executable, script_path, "--help"],
        capture_output=True,
        text=True,
    )
    return f"### {name}\n\n```\n{result.stdout.strip()}\n```\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cli_section = "\n".join(generate_cli_help(path, name) for path, name in CLI_TOOLS)
    generated = f"{GUARD_START}\n{cli_section}\n{GUARD_END}"

    if args.dry_run:
        config_section = generate_config_table()
        dry_run_block = f"\n<!-- DRY-RUN ONLY: config table (not written to any file) -->\n{config_section}\n"
        print(dry_run_block)
        print("---")
        print(generated)
        return

    doc = CLI_HELP_DOC.read_text()
    start = doc.find(GUARD_START)
    end = doc.find(GUARD_END)
    if start != -1 and end != -1:
        updated = doc[:start] + generated + doc[end + len(GUARD_END) :]
    else:
        updated = doc + "\n\n" + generated
    CLI_HELP_DOC.write_text(updated)
    print(f"Updated {CLI_HELP_DOC}")


if __name__ == "__main__":
    main()
