---
title: "MCP Inconsistencies and Known Issues"
category: mcp
tags:
  - mcp
  - inconsistencies
  - known-issues
  - bugs
related:
  - 04_mcp_00_document-guide.md
---

# MCPにおける不整合と既知の問題

このファイルは、ドキュメント再構成の過程で発見されたMCPレイヤーにおけるバグ、未実装の機能、
仕様間の矛盾、未定義動作をカタログ化するものである。

各エントリの形式:
- **Type:** `Implementation bug` / `Unimplemented` / `Document inconsistency` / `Undefined` / `Needs confirmation`
- **Impact scope:** 影響を受けるモジュール/動作
- **Statement A / B:** 矛盾する事実(該当する場合)
- **Current safe interpretation:** 不明な場合に前提とすべき内容
- **Recommended action:** 必要な修正または調査
- **Notes for AI reference:** この問題についてAIが推論する際の指針

---

## MDQ ハイブリッド検索はstub（未実装）

- **Type:** `Unimplemented`
- **Impact scope:** `scripts/mcp_servers/mdq/search.py`, `scripts/mcp_servers/mdq/tools.py`
- **Current behavior:** `use_embedding = true` でハイブリッド検索が有効になるが、`_search_vector()` は常に空リストを返す。セマンティック検索の結果は得られない。
- **Affected config:** `config/mdq_mcp_server.toml` の `use_embedding = true`
- **Recommended action:** ハイブリッド検索を本番投入するには、`_search_vector()` の実装が必要
- **Notes for AI reference:** MDQ のハイブリッド検索（`use_embedding = true`）は未実装（stub）。セマンティック検索が必要な場合は RAG パイプラインを使用すること。

---

## Related Documents

- `04_mcp_00_document-guide.md`

## Keywords

mcp
inconsistencies
known-issues
bugs
