# Implementation Procedure: scripts/docs/gen_rag_reference.py

## Goal

config キーリストと CLI 引数リストをソースから自動生成するスクリプトを作成する。

## Scope

**In:**
- 新規 `scripts/docs/gen_rag_reference.py` — config テーブル + CLI ヘルプ生成
- `docs/03_rag_05_configuration_and_operations.md` — `<!-- AUTO-GENERATED -->` ガード追加
- `docs/03_rag_00_document-guide.md` — 生成メンテナンスモデルのドキュメント追加

**Out:** 全ドキュメントをドキュメントフレームワークに移行

## Implementation

### scripts/docs/gen_rag_reference.py

```python
#!/usr/bin/env python3
"""gen_rag_reference.py — Auto-generate RAG reference sections in docs.

Usage:
    python scripts/docs/gen_rag_reference.py          # writes to docs/
    python scripts/docs/gen_rag_reference.py --dry-run # print to stdout only
"""
from __future__ import annotations
import argparse
import subprocess
import sys
import tomllib
from pathlib import Path


CONFIG_PATH = Path("config/rag_pipeline.toml")
OPS_DOC = Path("docs/03_rag_05_configuration_and_operations.md")
GUARD_START = "<!-- AUTO-GENERATED: gen_rag_reference.py config -->"
GUARD_END = "<!-- END AUTO-GENERATED -->"

CLI_TOOLS = [
    ("scripts/rag/ingestion/crawler.py", "crawler"),
    ("scripts/rag/ingestion/chunk_splitter.py", "chunk_splitter"),
    ("scripts/rag/ingestion/ingester.py", "ingester"),
]


def generate_config_table() -> str:
    with open(CONFIG_PATH, "rb") as f:
        cfg = tomllib.load(f)
    lines = ["| Key | Default | Description |", "|---|---|---|"]
    for section, values in cfg.items():
        if isinstance(values, dict):
            for key, val in values.items():
                lines.append(f"| `{section}.{key}` | `{val}` | — |")
    return "\n".join(lines)


def generate_cli_help(script_path: str, name: str) -> str:
    result = subprocess.run(
        [sys.executable, script_path, "--help"],
        capture_output=True, text=True,
    )
    return f"### {name}\n\n```\n{result.stdout.strip()}\n```\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config_section = generate_config_table()
    cli_section = "\n".join(
        generate_cli_help(path, name) for path, name in CLI_TOOLS
    )
    generated = f"{GUARD_START}\n{config_section}\n\n{cli_section}\n{GUARD_END}"

    if args.dry_run:
        print(generated)
        return

    doc = OPS_DOC.read_text()
    start = doc.find(GUARD_START)
    end = doc.find(GUARD_END)
    if start != -1 and end != -1:
        updated = doc[:start] + generated + doc[end + len(GUARD_END):]
    else:
        updated = doc + "\n\n" + generated
    OPS_DOC.write_text(updated)
    print(f"Updated {OPS_DOC}")


if __name__ == "__main__":
    main()
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| スクリプト存在 | `ls scripts/docs/gen_rag_reference.py` | found |
| ドライラン | `python scripts/docs/gen_rag_reference.py --dry-run` | 0 errors, Markdown 出力 |
| doc ガード更新 | `grep -n "AUTO-GENERATED" docs/03_rag_00_document-guide.md` | found |
