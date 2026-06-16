# 04_mcp_90_inconsistencies_and_known_issues — Implementation Procedure

## Goal
MCPシステムの実装上の不整合・既知バグ・未実装機能を一箇所に集約し、トラブルシュートと将来の修正作業を支援する。

## Scope
- HealthRegistry record_success/failure 未呼び出し (_raw_execute); mdq プレースホルダー実装
- shell_run_bg 未実装; query_sqlite 静的ルーティング未登録
- startup_mode="subprocess"+transport="stdio" バリデーション未文書化
- McpServerConfig.transport 型 (Literal 未使用)

## Assumptions
- BUG: 動作に影響する実装上の誤り; MISSING: 設計上あるべき機能が未実装; UNDOC: 未文書化の挙動

## Implementation

### Target file
`docs/04_mcp_90_inconsistencies_and_known_issues.md`

### Procedure
- 各課題を番号付きで列挙する（ID, タグ, タイトル, 影響度, 場所, 暫定回避策, 修正難易度）

### Method
既知の課題リストをテーブル形式で整理し、再現手順または影響範囲の説明を付ける。

### Details
- BUG-01: HealthRegistry.record_success/failure が _raw_execute() で呼ばれていない→ヘルスダッシュボードが常に初期値; 影響: 監視; 場所: mcp/tool_executor.py
- BUG-02: McpServerConfig.transport が str 型（Literal["http","stdio"] ではない）→不正値が実行時まで検出されない; 場所: mcp/models.py
- MISSING-01: shell_run_bg ツールが未実装（ルーティングには登録済み）→呼び出すと NotImplementedError; 場所: mcp/servers/shell.py
- MISSING-02: mdq サーバーが全ツールでプレースホルダーを返す→実用不可; 場所: mcp/servers/mdq.py
- MISSING-03: query_sqlite が ToolRouteResolver の静的マップに未登録→tool_names 設定が必要だが手順未文書化; 場所: mcp/routing.py
- UNDOC-01: startup_mode="subprocess" + transport="stdio" の組み合わせのバリデーションロジックが未文書化

## Validation plan
- 各 BUG が再現するテストケースを記述する（またはリンクする）
- MISSING 項目に GitHub Issue 番号を付与する（作成後）
- 次回リリース前に本ファイルを参照し、解消済み課題をアーカイブする
