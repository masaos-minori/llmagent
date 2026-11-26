#!/usr/bin/env python3
"""tools/replace_hand_maintained_schemas.py

Replace hand-maintained `inputSchema` dict literals in an MCP tools module with
`build_input_schema(model)` calls, one per tool entry, in file order.

Used by the plan batch for `scripts/mcp_servers/file/write_tools.py` and
`delete_tools.py` (procedures seq 04, 06): the tool entries are processed in the
order they appear, and each replacement uses the model name supplied on the
command line, so the mapping from tool name to request model is explicit.

Usage:
    uv run python tools/replace_hand_maintained_schemas.py <file> <model> [<model> ...]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCHEMA_BLOCK = re.compile(r'"inputSchema": \{.*?\n        \},', re.S)


def main() -> int:
    path = Path(sys.argv[1])
    models = sys.argv[2:]
    text = path.read_text(encoding="utf-8")
    blocks = SCHEMA_BLOCK.findall(text)
    if len(blocks) != len(models):
        print(f"{path}: found {len(blocks)} schema blocks, expected {len(models)}")
        return 1
    for model in models:
        match = SCHEMA_BLOCK.search(text)
        if match is None:
            return 1
        text = (
            text[: match.start()]
            + f'"inputSchema": build_input_schema({model}),'
            + text[match.end() :]
        )
    path.write_text(text, encoding="utf-8")
    print(f"{path}: {len(models)} blocks replaced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
