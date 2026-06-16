# 11 Extension Points — Agent Documentation Restructuring

## Goal
プラグインアーキテクチャ・カスタムツール追加・MCPサーバー統合の拡張手順を1章にまとめる。

## Scope
- プラグインシステムの仕組みと登録API
- カスタムツールの実装インタフェース
- MCPサーバーの設定と接続方法

## Assumptions
- 05_ref-agent-repl.md §7 (plugin architecture) が本章の主ソース
- 05_ref-agent-config.md の McpServerConfig を補足として使用
## Implementation

### Target file
`docs/05_agent/11_extension-points.md`

### Procedure
- 05_ref-agent-repl.md §7 からプラグイン登録API・フック定義・ライフサイクルを全件抽出
- 05_ref-agent-repl.md §7 のカスタムツール実装インタフェース(抽象クラス/プロトコル)を抽出
- 05_ref-agent-config.md の McpServerConfig を参照してMCP設定方法を記述
- プラグイン追加の最小実装例(擬似コード)を1件含める

### Method
- H2: プラグインシステム概要 / カスタムツール追加 / MCPサーバー統合 / フック一覧
- フック一覧は「フック名 — 呼び出しタイミング — 引数」の箇条書き
- MCP統合は設定ファイル記述例 + 接続確認コマンドの手順で記述

### Details
- プラグイン登録: PluginRegistry.register(plugin) / エントリーポイント経由の自動検出
- カスタムツールインタフェース: name, description, input_schema, execute(args) の4要素
- フック例: on_startup, on_turn_start, on_turn_end, on_tool_call, on_shutdown
- McpServerConfig: name, command, args, env で外部MCPサーバーを定義
- MCP接続確認: ToolExecutor.list_tools() でMCPツールが列挙されることを確認

## Validation plan
- プラグイン登録APIが05_ref-agent-repl.md §7と一致していること
- カスタムツールインタフェースの4要素が記述されていること
- McpServerConfigの設定例が05_ref-agent-config.mdの仕様と一致していること
