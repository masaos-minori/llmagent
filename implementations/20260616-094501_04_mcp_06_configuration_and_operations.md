# 04_mcp_06_configuration_and_operations — Implementation Procedure

## Goal
MCPサーバーの設定ファイル構造、OpenRCによる起動管理、ヘルスチェック、監査ログ、新規サーバー追加チェックリストを運用者向けにまとめる。

## Scope
- 各サーバーのコンフィグファイルパスと形式; OpenRC サービス unit
- 起動確認手順; ヘルスプローブ (/v1/tools); 監査ログ; 新規サーバー追加チェックリスト

## Assumptions
- init system は OpenRC (systemd ではない)
- ヘルスプローブは HTTP GET /v1/tools の 200 レスポンスで確認; 監査ログは JSON Lines

## Implementation

### Target file
`docs/04_mcp_06_configuration_and_operations.md`

### Procedure
- コンフィグファイル一覧テーブル（サーバー名・ファイルパス・形式）を作成する
- OpenRC コマンド、startup verification、ヘルスプローブ (curl 例)、監査ログ確認方法を記載する
- 新規サーバー追加チェックリストを作成する（10項目）

### Method
既存の運用ドキュメントと OpenRC 設定ファイルを参照し、実際の運用手順として記述する。

### Details
- コンフィグ: 各サーバーは /etc/mcp/{server_name}/config.toml または config.yaml
- OpenRC: rc-service mcp-{server_name} start/stop/status; rc-update add で自動起動登録
- startup verification: curl -s http://localhost:{port}/v1/tools | jq length でツール数確認
- 監査ログ: /var/log/mcp/{server_name}/audit.jsonl; フィールド: timestamp, tool_name, duration_ms, result_size, error
- 新規サーバー追加チェックリスト: ポート決定→コンフィグ作成→MCPServer 実装→OpenRC unit 作成→起動確認→tool_names 登録→セキュリティ設定→ドキュメント更新→ヘルスチェック確認→カタログ追記

## Validation plan
- チェックリスト全項目を新規サーバー1台の追加で実際にトレースする
- 記載コマンドが実環境で動作することを確認する
- 監査ログのフィールドが実装と一致することを確認する
