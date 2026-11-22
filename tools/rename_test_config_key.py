#!/usr/bin/env python3
"""rename_test_config_key.py — Rename a configuration key inside test fixture mappings.

Plan agentcfg004 REQ-001 moves `embed_url` from the infrastructure block to the Memory
section as `memory_embed_url`. The test fixtures that supply the key through a mapping must
follow the rename, including the comment that explains why the value is non-empty.

For each file given:
  - replace the string literal `"<from>"` with `"<to>"`
  - rewrite the mention of `<from>` in a comment on the same or the preceding line

Only the files named on the command line are touched, because `embed_url` is still the
correct key in the config files that own it (`config/ingester.toml`,
`config/rag_pipeline_mcp_server.toml`) and in the tests for those consumers. `--module-from`/
`--module-to` apply the same rename to the attribute form `cfg.<module>.<key>`, which is how a
mocked context exposes the value to the code under test. `--dry-run` prints a diff and changes
nothing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def rename(
    text: str, old: str, new: str, module_from: str = "", module_to: str = ""
) -> tuple[str, int]:
    """Rewrite the key in literals and in the comment that names it, once per line."""
    changed = 0
    out_lines = []
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("#"):
            new_line = line.replace(old, new)
        elif module_from and module_to:
            new_line = line.replace(f"{module_from}.{old}", f"{module_to}.{new}")
        else:
            new_line = line.replace(f'"{old}"', f'"{new}"')
        if new_line != line:
            changed += 1
        out_lines.append(new_line)
    return "".join(out_lines), changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--from", dest="old", required=True)
    parser.add_argument("--to", dest="new", required=True)
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument(
        "--module-from",
        default="",
        help="rename `cfg.<module_from>.<key>` attribute reads instead of mapping keys",
    )
    parser.add_argument("--module-to", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    total = 0
    for name in args.files:
        path = Path(name) if Path(name).is_absolute() else ROOT / name
        text = path.read_text(encoding="utf-8")
        result, changed = rename(
            text, args.old, args.new, args.module_from, args.module_to
        )
        total += changed
        if not changed:
            print(f"{path.relative_to(ROOT)}: no occurrence")
            continue
        if args.dry_run:
            for before, after in zip(
                text.splitlines(), result.splitlines(), strict=False
            ):
                if before != after:
                    print(f"{path.relative_to(ROOT)}: - {before.strip()}")
                    print(f"{path.relative_to(ROOT)}: + {after.strip()}")
        else:
            path.write_text(result, encoding="utf-8")
        print(f"{path.relative_to(ROOT)}: {changed} line(s)", file=sys.stderr)
    if not total:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
