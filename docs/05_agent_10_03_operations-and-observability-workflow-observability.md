---
title: "Agent Operations and Observability - Workflow Observability"
category: agent
tags:
  - agent
  - operations
  - workflow-observability
  - tracing
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# エージェントの運用と可観測性

- 設定 → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## 目的

ワークフロー実行中の可観測性（スパン、ステータス、状態遷移）を文書化する。

## 設計意図

ワークフローの可観測性は3層に分かれる:

1. **OTelスパン** — 各ワークフローステージの実行時間、エラー、メタデータを記録する。スパン名は `workflow.{stage}` パターンに従う。
2. **監査ログ** — `turn_start`/`turn_end` とワークフロー固有イベント（`workflow_start`, `stage_completed`, `approval_requested`）を JSON-lines で出力する。
3. **セッション診断情報** — `session_diagnostics` テーブルにワークフローの完了ステータス、リトライ回数、最終エラーを記録する。

この3層により、リアルタイムな実行監視、事後の障害調査、長期の運用指標の3つのユースケースに対応する。

## 責務境界

- **対象**: ワークフロー実行中の観測データ生成と出力
- **対象外**: ワークフローエンジン自体の実行ロジック、承認ゲートの決定ロジック
- **所有者**: `agent/workflow.py` (`WorkflowEngine`)、`agent/tool_audit.py`（監査ライター）

## 主要な制約

- ワークフローモード時のみ追加の可観測性イベントが発生する。通常モードでは `turn_start`/`turn_end` のみ。
- ワークフローコンテキスト外で `tool_approval` / `tool_exec` の書き込み関数を呼び出すと assertion error になる。
- セッション診断情報は `session_diagnostics` テーブルに保存され、メッセージテーブルとは分離されている。

## 運用上の注意

### ワークフロースパンの読み方

期待されるスパン名:
- `workflow.run` — ワークフロー全体の実行
- `workflow.stage` — 個別ステージの実行
- `workflow.approval` — 承認ゲート通過
- `workflow.retry` — リトライ待機

### 障害時の確認手順

1. `audit.log` で `workflow_start`/`stage_completed` イベントを確認し、どのステージで失敗したか特定する。
2. `session_diagnostics` でワークフローの完了ステータスと最終エラーを確認する。
3. OTelスパンで詳細な実行時間とメタデータを参照する。

### 正常時の確認

- `workflow_start` が `turn_start` の後に発生していることを確認する。
- `stage_completed` が各ステージ終了時に発生していることを確認する。
- `approval_requested` が承認が必要なステップで発生していることを確認する。

## 既知の制限 / 未解決事項

- ワークフローモード時のみ追加の可観測性イベントが発生するため、通常モードとの区別が必要。
- 監査ログとセッション診断情報の両方にワークフロー情報が重複して記録される可能性がある。

## 関連資料

- [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md) — 起動とヘルスチェック
- [05_agent_10_02_operations-and-observability-audit-and-otel.md](05_agent_10_02_operations-and-observability-audit-and-otel.md) — 監査ログとOTel
- [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md) — session_diagnostics の役割
