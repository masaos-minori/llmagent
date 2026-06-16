# 10 Operations and Observability — Agent Documentation Restructuring

## Goal
起動手順・動作確認・トラブルシューティング・オブザーバビリティの運用ガイドを1章にまとめる。

## Scope
- 起動・停止手順
- 動作確認チェックリスト
- ログ・メトリクス・トレースの収集方法
- 代表的な障害パターンと対処法

## Assumptions
- 05_agent-ops.md 全体が本章の唯一のソース
- 05_ref-agent-context.md §5 の RuntimeStats を補足として使用
## Implementation

### Target file
`docs/05_agent/10_operations-and-observability.md`

### Procedure
- 05_agent-ops.md の起動セクションから起動コマンドと前提条件を抽出
- 05_agent-ops.md の動作確認セクションからチェックリストを抽出
- 05_agent-ops.md のトラブルシューティングセクションから障害パターンと対処法を抽出
- 05_agent-ops.md のオブザーバビリティセクションからログ・メトリクス設定を抽出
- 05_ref-agent-context.md §5 の RuntimeStats フィールドを参照してメトリクス項目を補足
### Method
- H2: 起動・停止 / 動作確認 / ログ設定 / メトリクス / トラブルシューティング
- 障害パターンは「症状 → 原因 → 対処」の箇条書き
- 起動手順は番号付きステップで記述
### Details
- 起動: `uv run python -m agent` + 環境変数 ANTHROPIC_API_KEY 必須
- HealthRegistry によるliveness確認エンドポイント
- RuntimeStats: total_turns, total_tokens, error_count, avg_latency_ms
- ログ: log_level=DEBUG でSSEパースデバッグ情報が出力される
- 代表障害: API認証エラー / コンテキスト長超過 / SQLite書き込み権限エラー / MCPサーバー接続失敗

## Validation plan
- 起動コマンドが05_agent-ops.mdの記述と一致していること
- 障害パターンが3件以上記述されていること
- RuntimeStatsのフィールドが05_ref-agent-context.md §5と一致していること
