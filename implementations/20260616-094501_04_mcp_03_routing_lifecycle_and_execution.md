# 04_mcp_03_routing_lifecycle_and_execution — Implementation Procedure

## Goal
ToolExecutor と ToolRouteResolver の動作、サーバーライフサイクル管理、新規サーバー追加手順を1ファイルで説明する。

## Scope
- `docs/06_ref-mcp.md` §3; `docs/04_mcp-protocol.md` §2
- ToolExecutor, ToolRouteResolver, startup_mode ライフサイクル
- watchdog / idle_timeout 仕様; /mcp install ウィザード

## Assumptions
- ToolRouteResolver は静的ルーティングテーブルを持つ
- watchdog は異常終了時に自動再起動; idle_timeout は on-demand サーバーの自動停止に使用

## Implementation

### Target file
`docs/04_mcp_03_routing_lifecycle_and_execution.md`

### Procedure
- ツール呼び出しシーケンス（エージェント→ToolExecutor→ToolRouteResolver→MCPサーバー）を示す
- ToolRouteResolver のルーティングロジック（静的マップ＋フォールバック）を説明する
- startup_mode 別ライフサイクル状態遷移と watchdog/idle_timeout 設定を記載する
- /mcp install ウィザードの手順を箇条書きで示す

### Method
06_ref-mcp.md §3 と 04_mcp-protocol.md §2 を統合し、実装クラスと対応させながら記述する。

### Details
- ToolExecutor: _raw_execute() が実際のMCP呼び出しを行う; HealthRegistry への記録が現在未実装（90参照）
- ToolRouteResolver: tool_name → server_name の辞書; query_sqlite は静的ルーティング未登録（既知課題）
- watchdog: SIGTERM後 5s でSIGKILL; 再起動は最大3回
- idle_timeout: デフォルト 300s; on-demand サーバーのみ適用
- /mcp install: config 追加→ポート決定→OpenRC unit 生成→起動確認→tool_names 登録

## Validation plan
- ルーティングフローが実装コードと一致することを確認する
- watchdog/idle_timeout の設定値がコード定数と一致することを確認する
- 新規サーバー追加手順を実際に1台追加してトレースする
