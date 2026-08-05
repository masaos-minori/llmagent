#!/usr/bin/env python3
"""gen_rag_reference.py — Generate configuration tables for documentation.

Usage:
    python tools/gen_rag_reference.py          # print to stdout
    python tools/gen_rag_reference.py --dry-run # print to stdout only
"""

from __future__ import annotations

import argparse
import tomllib
from pathlib import Path

CONFIG_PATHS = [
    Path("config/crawler.toml"),
    Path("config/chunk_splitter.toml"),
    Path("config/ingester.toml"),
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config_section = generate_config_table()
    if args.dry_run:
        print(f"<!-- DRY-RUN ONLY: config table -->\n{config_section}\n")
    else:
        print(config_section)


if __name__ == "__main__":
    main()
