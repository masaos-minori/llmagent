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

## SPEC-01: `04_mcp_06_11` からの `04_mcp_90 §SPEC-01` 参照が本ファイル内に存在しない（解決済み）

- **Type:** `Document inconsistency` — **Resolved**(本エントリの追加によりリンク切れは解消済み)
- **Impact scope:** `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md` から本ファイルへのリンク（ドキュメント内リンクの整合性のみ。実装動作には影響しない）
- **Statement A:** `04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md` の冒頭注記は「ルーティングのドリフト検出（`route_resolver.py` の `validate_routing_against_live`）と tool definitions チェック（`repl_health.py`）は異なる機能である — `04_mcp_90 §SPEC-01` も参照」と記載している。
- **Statement B:** 本ファイル（`04_mcp_90_inconsistencies_and_known_issues.md`）には `SPEC-01` という見出し・エントリは（本エントリを追記する前の時点で）存在しなかった。参照先が実体を欠いた壊れた内部リンクになっていた。
- **Current safe interpretation:** 2つの検証機構は実装上明確に分離されている（根拠: `scripts/shared/tool_routing_validation.py` に `validate_routing_against_config` / `validate_routing_against_live` / `validate_all_routing` が定義され、`scripts/agent/repl_health.py` に `check_tool_definitions_startup` / `check_tool_definitions_runtime` が別途定義されている）。したがって `04_mcp_06_11` の技術的記述自体は実装と矛盾しない。矛盾していたのはリンク先の欠落のみであり、本エントリの追加によって解消したとみなしてよい。
- **Recommended action:** 対応不要（本エントリの追加により参照先が実体を持った）。今後 `04_mcp_06_11` 側を編集する場合は、参照テキストを本エントリ名（`SPEC-01`）に合わせて更新すること。
- **Notes for AI reference:** ルーティングのドリフト検出（config/live 突合）と tool definitions strict チェック（起動時の `/v1/tools` 比較）を混同しないこと。前者は `ToolRegistry` を正とした運用時ドリフト検知、後者は `config/agent.toml` の `tool_definitions` と実サーバー応答の起動時整合性チェックであり、責務が異なる。(根拠分類: Explicit in code)

---

## Related Documents

- `04_mcp_00_document-guide.md`

## Keywords

mcp
inconsistencies
known-issues
bugs
