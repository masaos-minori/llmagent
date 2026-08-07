---
title: "Agent Operations and Observability - Validation and Troubleshooting (Part 1)"
category: agent
tags:
  - agent
  - operations
  - validation
  - troubleshooting
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 05_agent_10_03_operations-and-observability-workflow-observability.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md
---

# エージェントの運用と可観測性

- 設定 → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## ワークフロー起動時検証

エージェントはオーケストレータを初期化する前に、ワークフロー定義ファイルが存在することを無条件に検証する。このチェックを無効化・縮退させる設定は存在しない。

**期待されるパス:** `config/workflows/default.json`

### 重大度マッピング

| 重大度 | 意味 | 挙動 |
|---|---|---|
| FATAL | 起動できない条件 | 全チェック完了後に `RuntimeError` を送出し、起動を中断する |
| WARNING | チェックを実行したが問題を検出した | 起動を継続するが、オペレーターが確認すべき状態 |
| SKIPPED | チェック自体を実行できなかった | 起動を継続する。環境依存のチェックが利用不可の場合に発生する |
| OK | チェックを正常に実行した | 正常状態を示す（ただし security_audit の OK は「問題なし」ではなく「チェック完了」を意味する） |

**重要な注意点:**
- `routing_drift_live` と `routing_safety_tiers` は正常時に何のoutcomeも記録されない（silence means healthy）。
- `tool_definitions` は strict モードでも FATAL にはならない — 常に WARNING にダウングレードされる。
- `mcp_tool_discovery` の失敗は本番/ローカル問わず FATAL として扱う。ツールディスカバリに失敗するとセッション全体のツール呼び出しが不可能になるため。

### 起動シーケンス中のSIGINT/SIGTERM中断

起動シーケンス中にSIGINT/SIGTERMを受信した場合、`ShutdownInterrupted` が送出され、ロールバックが発火する。HTTPサブプロセスのヘルスポーリングループもシャットダウンイベントで即時中断する。

### 保留中の承認状態の復元

エージェント起動時に前回のセッションで解決されなかった承認ゲートが存在する場合、`StateStore.find_latest_pending_approval()` を通じて `workflow.sqlite` から復元する。この復元は同時に1件のみ追跡され、全セッションを通じた最新のレコードが適用される。

既存の `pending_approval_task_id` が設定されている状態で復元値を設定する場合、WARNING レベルでログを出力するが、値は上書きされる（処理は中断しない）。

### シャットダウン時のリソースクリーンアップ

`finally` ブロックで以下の順序でリソースをクローズする:

1. WALチェックポイント（PASSIVE→TRUNCATEフォールバック）
2. WALバックアップ（パス検証付き）
3. `lifecycle.shutdown_all()`
4. `http.aclose()`

各ステップは独立してガードされており、一方が失敗しても他のステップは実行される。WALバックアップは `allowed_root` 範囲内のパスのみ許可し、シンボリックリンクを解決してから検証する。

## ワークフローデプロイメントランブック

ワークフローは **必須** のデプロイメントアーティファクトであり、これを無効またはバイパスするための設定項目、環境変数、デプロイフラグは存在しない。

### クイック検証コマンド

```bash
# ワークフロー定義ファイルを直接検証（サービスを開始しない）
PYTHONPATH=scripts uv run python -m agent.workflow.validate config/workflows/default.json

# ワークフローDBスキーマのテーブルとバージョンを確認
sqlite3 /opt/llm/db/workflow.sqlite ".tables"
sqlite3 /opt/llm/db/workflow.sqlite "SELECT * FROM workflow_schema_version ORDER BY applied_at DESC;"
```

### よくある障害と対応

#### `config/workflows/default.json` の欠落

**症状:** `deploy.sh` が `[FATAL] Missing required workflow definition: config/workflows/default.json` を出力して終了する。

**対応:** バージョン管理から復元して再デプロイする。

#### ワークフローJSONのパースエラー

**症状:** `deploy.sh` またはバリデータCLIが `[FATAL] Invalid workflow definition ...: <JSON parse error>` を出力する。

**対応:** 報告されたJSON構文エラーを修正し、再デプロイ前に再検証する。

#### 必須ステージの欠落

**症状:** バリデータが `required stages missing: <names>` を報告する。

**対応:** ワークフロー定義の `stages` 配列に `plan`, `execute`, `verify` の `id` を持つオブジェクトを含める。

#### 不正なリトライポリシー

**症状:** バリデータが `retry_policy.max_attempts must be >= 1` または `retry_policy.backoff_sec must be >= 0` を報告する。

**対応:** 報告されたフィールドを修正し、再検証する。

#### `workflow.sqlite` の欠落または不完全

**症状:** `init_db.sh` または `setup_services.sh` が `[FATAL] Workflow database schema is missing or incomplete.` を出力する。

**対応:** デプロイスクリプトを再実行する。

#### スキーマバージョンの不整合

**症状:** エージェント起動またはデプロイスクリプトが `Workflow schema version mismatch: expected <X>, found <Y>` を報告する。

**対応:** デプロイスクリプトを再実行してマイグレーションを適用する。

#### ワークフロー定義の更新には再起動が必要

**説明:** ワークフロー定義はエージェント起動時に一度だけ検証・読み込みされる。ホットリロード可能な設定ではない — `/reload` では適用されない。

**対応:** 新しい定義をデプロイ後、エージェントプロセスを完全に再起動する。

## 関連資料

- [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md) — 起動とヘルスチェック
- [05_agent_10_02_operations-and-observability-audit-and-otel.md](05_agent_10_02_operations-and-observability-audit-and-otel.md) — 監査ログとOTel
- [05_agent_10_03_operations-and-observability-workflow-observability.md](05_agent_10_03_operations-and-observability-workflow-observability.md) — ワークフローの可観測性
- [05_agent_10_05_operations-and-observability-monitoring.md](05_agent_10_05_operations-and-observability-monitoring.md) — モニタリング
- [05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md](05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md) — RAG診断とメモリ
- [05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md](05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md) — 追加検証とトラブルシューティング
