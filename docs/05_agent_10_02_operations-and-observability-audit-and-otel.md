---
title: "Agent Operations and Observability - Audit Log and OTel"
category: agent
tags:
  - agent
  - operations
  - audit-log
  - otel
  - observability
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
  - 05_agent_10_03_operations-and-observability-workflow-observability.md
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# エージェントの運用と可観測性

- 設定 → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## 目的

監査ログとOTelトレーシングの設計意図と運用方法を文書化する。

## 設計意図

### 監査ログ

各ターンごとに `turn_start` / `turn_end` の2つのイベントが生成される。ワークフロー固有のイベント（`workflow_start`, `stage_completed`, `approval_requested`）はワークフローモード時のみ追加で発行される。

監査ログは永続的な証跡であり、再起動後も分析可能である。`RuntimeStats` のようなセッション内観測用カウンタとは異なり、障害対応や変更判断に使用できる。

### OTelトレーシング

OTel SDKは任意依存として扱われ、未インストール環境でもエージェントが起動できるようNoOp実装へ常にフォールバックする。グローバルな `TracerProvider` を意図的に設定しない — プロセス内での複数トレーサーインスタンス共存とテスト間の汚染防止のため。

## 責務境界

- **対象**: エージェントプロセスの観測データ出力（監査ログ、OTelスパン）
- **対象外**: 外部システムへのデータ送信、メトリクス収集基盤の詳細
- **所有者**: `agent/tool_audit.py`（監査ライター）、`shared/otel_tracer.py`（トレーサー初期化）

## 主要な制約

- 監査ログの形式はJSON-linesであり、後から解析可能な構造を持つ。
- OTelの設定キー（`otel_enabled`, `otel_endpoint`, `otel_service_name`）は `config/agent.toml` で設定する。
- `otel_endpoint = ""` の場合、スパンは標準出力 / `agent.log` に書き込まれる。
- ワークフローコンテキスト外で `tool_approval` / `tool_exec` の書き込み関数を呼び出すとassertion errorになる。

## 運用上の注意

### 監査ログの読み方

- `turn_start` / `turn_end` は全ターンで発生する基本イベント。
- `workflow_start` / `stage_completed` / `approval_requested` はワークフローモード時のみ発生する追加イベント。
- `turn_end` イベントにはワークフローコンテキスト（`workflow_id`）が含まれる。
- 監査ロガーが未設定の場合、これらのイベントは一切発行されない。

### OTelスパンの読み方

期待されるスパン名:
- `llm` — LLM呼び出し
- `compress` — 履歴圧縮
- `workflow.run` — ワークフロー実行
- `workflow.stage` — ステージ実行
- `workflow.approval` — 事後実行承認通過
- `workflow.retry` — リトライ待機

### 障害時の確認箇所

- トレーニングエラーやトークン統計の確認には `audit.log` または `session_diagnostics` を使用する。
- スパンの抽出には `grep '"name":' /opt/llm/logs/agent.log` を使用する。

## 既知の制限 / 未解決事項

- OTelは任意依存であり、本番環境以外では通常無効。
- グローバル `TracerProvider` を設定しないため、他のプロセスとのトレーシング統合はできない。

## 関連資料

- [05_agent_10_03_operations-and-observability-workflow-observability.md](05_agent_10_03_operations-and-observability-workflow-observability.md) — ワークフローの可観測性
- [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md) — session_diagnostics の役割
- `00_security_01_architecture-and-trust-boundaries.md` — システムセキュリティアーキテクチャ / 信頼境界 / 脅威モデル / 認証認可 / 監査 / ローカルvs本番 / Fail-open/Fail-closed / プロンプトインジェクション責任境界
