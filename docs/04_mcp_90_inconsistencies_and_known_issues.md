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

## 移行ノート

- 移行日: 2026-07-23
- 移行元フォーマット: 既存のバレット形式（Type, Impact scope, Statement A/B, Current safe interpretation, Recommended action, Notes for AI reference）
- 移行先フォーマット: 共通テンプレート（17フィールド）
- 注: 既存のエントリ内容は維持。不足フィールドは「未確認」で埋める。

# MCPにおける不整合と既知の問題

このファイルは、ドキュメント再構成の過程で発見されたMCPレイヤーにおけるバグ、未実装の機能、
仕様間の矛盾、未定義動作をカタログ化するものである。

---

### MCP-001: include_disabled フィルタと disabled_code 構造化コードは評価済みだが未実装

- **ID**: MCP-001
- **Title**: include_disabled フィルタと disabled_code 構造化コードは評価済みだが未実装
- **Status**: open
- **Severity**: Medium
- **Area**: MCP
- **Type**: implementation-bug
- **Source**: scripts/mcp_servers/*/server.py の10実装すべて
- **Owner**: Unassigned
- **First Found**: 未確認
- **Target**: /v1/tools エンドポイント
- **Related**: plans/20260717-181151_plan.md
- **Summary**: /v1/tools がクエリパラメータを受け付けないため include_disabled フィルタが機能しない
- **Current Description**: /v1/tools は現在クエリパラメータを一切受け付けず、常に全ツールを無条件に返す
- **Observed Implementation**: include_disabled クエリパラメータおよび disabled_code 列挙型は要求20で評価済みだが実装なし
- **Impact**: 無効化されたツールのフィルタリングができない
- **Recommended Action**: plans/20260717-181151_plan.md の "Future / deferred design options" を参照して実装
- **Resolution Notes**: 意図的に延期

---

### MCP-002: ツール実行時可用性メタデータは一部実装済み

- **ID**: MCP-002
- **Title**: ツール実行時可用性メタデータ（config_dependent/enabled/disabled_reason/RuntimeToolRegistry）は一部実装済み
- **Status**: open
- **Severity**: Low
- **Area**: MCP
- **Type**: implementation-bug
- **Source**: scripts/mcp_servers/web_search/, scripts/agent/**
- **Owner**: Unassigned
- **First Found**: 未確認
- **Target**: scripts/mcp_servers/web_search/, scripts/agent/**
- **Related**: docs/04_mcp_03_06_tool-runtime-availability-metadata.md
- **Summary**: config_dependent は一部採用済みだが enabled/disabled_reason は未実装
- **Current Description**: web_search-mcp の browser_fetch が config_dependent: True を採用したが enabled/disabled_reason は /v1/tools レスポンスに存在しない
- **Observed Implementation**: RuntimeToolRegistry は McpToolDiscoveryService によりライブ検出され ToolExecutor.set_runtime_registry() で接続済み
- **Impact**: 他の MCP サーバーの config_dependent 移行と enabled/disabled_reason の実装が必要
- **Recommended Action**: 他の MCP サーバーの config_dependent 移行と enabled/disabled_reason の実装完了後、本エントリを削除
- **Resolution Notes**: 部分的に実装済み

---

## Related Documents

- `04_mcp_00_document-guide.md`

## Keywords

mcp
inconsistencies
known-issues
bugs
