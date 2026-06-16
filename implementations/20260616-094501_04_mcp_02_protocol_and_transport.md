# 04_mcp_02_protocol_and_transport — Implementation Procedure

## Goal
MCPプロトコル仕様とトランスポート層の詳細を一箇所にまとめる。リクエスト/レスポンス構造、認証、制限値、タイムアウトを網羅する。

## Scope
- `docs/06_ref-mcp.md` §1〜2; `docs/04_spec_mcp.md` §6〜8
- CallToolRequest/Response, MCPServer 基底クラス
- HTTP+stdio フォーマット、Bearer 認証、X-Request-Id ヘッダ、監査ログ
- 切り捨て上限 (512KB)、stdio タイムアウト (60s)

## Assumptions
- HTTP トランスポートは SSE を使用; Bearer トークンは設定から注入
- 512KB は単一ツール出力の最大サイズ

## Implementation

### Target file
`docs/04_mcp_02_protocol_and_transport.md`

### Procedure
- CallToolRequest / CallToolResponse のフィールド定義テーブルを作成する
- HTTP / stdio トランスポートのフォーマットをそれぞれ示す
- 認証ヘッダ (Bearer, X-Request-Id) と監査ログフィールドを記載する
- 制限値テーブル（出力 512KB、stdio タイムアウト 60s）を作成する

### Method
06_ref-mcp.md と 04_spec_mcp.md の該当セクションを突合し、重複排除して集約する。

### Details
- CallToolRequest: tool_name, arguments, request_id, session_id
- CallToolResponse: content (list), is_error, truncated フラグ
- MCPServer 基底クラス: execute_tool() / list_tools() 抽象メソッド
- 監査ログ: tool_name, args_hash, duration_ms, result_size, truncated

## Validation plan
- CallToolRequest/Response 全フィールドをコードと照合する
- 制限値定数（512KB, 60s）がソースと一致することを確認する
- Bearer 認証フローが実装と矛盾しないことを確認する
