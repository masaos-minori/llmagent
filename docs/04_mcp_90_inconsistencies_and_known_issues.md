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

## `include_disabled` フィルタと `disabled_code` 構造化コードは評価済みだが未実装（意図的に延期）

- **Type:** `Unimplemented`
- **Impact scope:** `/v1/tools` エンドポイント全般（`scripts/mcp_servers/*/server.py` の10実装すべて）、将来の `disabled_reason` フィールド（requirement 15、未実装）
- **Current behavior:** `/v1/tools` は現在クエリパラメータを一切受け付けず、常に全ツールを無条件に返す（無効化されたツールも除外しない）。`include_disabled` クエリパラメータおよび `disabled_code` 列挙型はどちらも要求20で評価されたが、実装は行われていない。
- **Recommended action:** 実装が必要になった場合は `plans/20260717-181151_plan.md` の "Future / deferred design options" 提案（`docs/04_mcp_03_06_tool-runtime-availability-metadata.md` 作成後に追記予定）を参照すること。初期の RuntimeToolRegistry 移行（requirements 14-19）はこれらのオプションに依存しない。
- **Notes for AI reference:** `include_disabled=false` や `disabled_code` への言及がコード上に見つからない場合、それは正常（未実装が既定の状態）。`config_dependent`/`disabled_reason` 自体も別途未実装（requirements 14-18 未着手）であり、本エントリはそれらの実装状況を変更するものではない。

---

## ツール実行時可用性メタデータ（config_dependent/enabled/disabled_reason/RuntimeToolRegistry）は一部実装済み

- **Type:** `Partially implemented`
- **Impact scope:** `scripts/mcp_servers/web_search/`（`browser_fetch` の `config_dependent` 採用済み、web_search-mcp に統合）、`scripts/agent/**`（RuntimeToolRegistry配線済み）
- **Current behavior:** web_search-mcp の `browser_fetch` が `config_dependent: True` を採用した。RuntimeToolRegistry は McpToolDiscoveryService によりライブ検出され、`ToolExecutor.set_runtime_registry()` で接続された。ただし `enabled`/`disabled_reason` は `/v1/tools` レスポンスに存在せず、他の MCP サーバーは `config_dependent` をまだ採用していない。
- **Affected config:** N/A（コード側フィールド名の問題であり、config側の値ではない）
- **Recommended action:** 他の MCP サーバーの `config_dependent` 移行と `enabled`/`disabled_reason` の実装完了後、本エントリを削除すること。
- **Notes for AI reference:** `config_dependent`/`enabled`/`disabled_reason`/`RuntimeToolRegistry`という語がコード中またはテスト中に見つかる場合、これは部分的に実装済みである。`enabled`/`disabled_reason` はまだ未実装であり、`04_mcp_03_06`の「Implementation status」コールアウトも参照すること。

---

## Related Documents

- `04_mcp_00_document-guide.md`

## Keywords

mcp
inconsistencies
known-issues
bugs
