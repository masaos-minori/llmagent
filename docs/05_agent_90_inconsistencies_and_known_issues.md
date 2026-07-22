---
title: "Agent Inconsistencies and Known Issues"
category: agent
tags:
  - agent
  - inconsistencies
  - known-issues
  - bugs
related:
  - 05_agent_00_document-guide.md
---

# Agent Inconsistencies and Known Issues

このファイルは、agent 層（`agent/`、`shared/`）における既知の不具合、仕様の矛盾、
文書間の不整合、未実装領域、および未解決の疑問点を記録する。

各エントリの形式:
- **Type:** `Document inconsistency` / `Implementation bug` / `Undocumented` / `Needs confirmation` / `Open Question`
- **Impact scope:** 影響を受けるモジュール／動作
- **Statement A / B:** 矛盾する事実（該当する場合）
- **Current safe interpretation:** 不明な場合に前提とすべき内容
- **Recommended action:** 必要な修正または調査
- **Notes for AI reference:** この問題に関する AI 推論のためのガイダンス

---

## use_memory_layer デフォルト値の文書間不一致

- **Type:** Document inconsistency
- **Impact scope:** Memory layer activation gate documentation
- **Statement A:** `use_memory_layer=False` と記載されているドキュメント（05_agent_08_03, 05_agent_09_02, 05_agent_12_02_part1）
- **Statement B:** `use_memory_layer=True` と記載されているドキュメント（05_agent_08_01, 05_agent_12_05, 05_agent_13_part2）
- **Current safe interpretation:** コード上のデータクラスデフォルトは `use_memory_layer: bool = True`（`config_dataclasses.py:212`）。TOMLでも明示的に `use_memory_layer = true` が設定されている。正しいデフォルトは `True`。
- **Recommended action:** 05_agent_08_03, 05_agent_09_02, 05_agent_12_02_part1 を修正して `True` に統一（完了済み）
- **Notes for AI reference:** `MemoryServices` コンストラクタのデフォルトも `use_memory_layer=True`。`_build_memory_services()` は `ctx.cfg.memory.use_memory_layer` をチェックし `False` の場合は `None` を返す。

---

## /export がトップレベルコマンドとして誤って記載

- **Type:** Document inconsistency
- **Impact scope:** CLI command reference documentation
- **Statement A:** `/export [md|json] [file]` がトップレベルスラッシュコマンドとして記載（05_agent_07_10 line 92）
- **Statement B:** `_COMMANDS` に `/export` エントリが存在せず、`/session export` のサブコマンドとしてのみ定義（command_defs_list.py line 89-90）
- **Current safe interpretation:** `/export` はトップレベルコマンドではない。`/session export markdown [file]` または `/session export json [file]` が正しい構文。
- **Recommended action:** 05_agent_07_10 を修正して `/session export` と明記（完了済み）
- **Notes for AI reference:** タブ補完ヒント（line 90）にも `export markdown|json [file]` が含まれているため、タブ補完時に `/session export` が候補に表示される。

---

## RAG/Export カテゴリ名が誤り（/rag が存在しない）

- **Type:** Document inconsistency
- **Impact scope:** CLI command reference documentation
- **Statement A:** ファイルタイトルと索引で「RAG/Export」カテゴリとして記載（05_agent_07_10 title, 05_agent_07_01 index）
- **Statement B:** `_COMMANDS` に `/rag` エントリが存在しない（command_defs_list.py — RAG検索はLLMが `rag_run_pipeline` ツール経由で自動呼び出し）
- **Current safe interpretation:** 「RAG」カテゴリは存在しない。`/compact` と `/session export` のみ。
- **Recommended action:** 05_agent_07_10 title と 05_agent_07_01 index を「Compact/Export」に統一（完了済み）
- **Notes for AI reference:** このファイルの本文でも RAG検索が「スラッシュコマンドとしては提供されていない」と明記されているため、カテゴリ名との矛盾が明らか。

---

## Related Documents

- `05_agent_00_document-guide.md`

## Keywords

agent
inconsistencies
known-issues
bugs
