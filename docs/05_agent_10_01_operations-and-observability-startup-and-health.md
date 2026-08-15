---
title: "Agent Operations and Observability - Startup and Health"
category: agent
tags:
  - agent
  - operations
  - startup
  - health-probes
  - operational-verification
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
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

エージェントの起動手順、運用確認、ヘルスチェック、シャットダウン時のリソースクリーンアップを文書化する。

## 設計意図

起動プロセスは3つのフェーズに分かれる: サーバースタート、ヘルスチェック、承認状態の復元。いずれかのフェーズで例外が発生するとロールバックが発火し、起動済みサブプロセスを確実に終了する。

`StartupOrchestrator` は起動シーケンス全体を一元管理する。起動失敗時は `shutdown_all()` を通じて全リソースをクローズし、元の例外を再送出する。ロールバック自体が失敗しても元の例外は保持される（ログのみ記録）。

SIGTERM/SIGINT は起動シーケンス中にも有効に発火する。`asyncio.wait(FIRST_COMPLETED)` で遅延タイマーと競走させ、シャットダウンイベントが先に発火すれば遅延を待たずに中断する。

## 責務境界

- **対象**: エージェントプロセスの起動〜シャットダウンまでのライフサイクル
- **対象外**: MCPサーバーの実装、RAGパイプラインの詳細、LLMエンドポイントの内部動作
- **所有者**: `agent/startup.py` (`StartupOrchestrator`)、`agent/repl.py` (`AgentREPL`)

## 主要な制約

- ワークフロー定義ファイルは起動時に必ずロードされる。欠落または不正がある場合は起動に失敗させる。Direct execution fallback は提供しない。
- 本番モードではヘルスプローブの到達不能は起動失敗（FATAL）として扱う。ローカルモードでは警告のみで継続する。
- 埋め込み次元の不一致は起動失敗として扱う。これはベクトル検索のデータ破損を防ぐため。
- セッション起動時の rolling upgrade では、古いプロセスのシャットダウン前に新しいプロセスの起動を検証し、問題があれば古いプロセスを維持する。

## 運用上の注意

### 起動時検証の重大度マッピング

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

### 起動シーケンス中のSIGINT/SIGTERM中断

起動シーケンス中にSIGINT/SIGTERMを受信した場合、`ShutdownInterrupted` が送出され、ロールバックが発火する。HTTPサブプロセスのヘルスポーリングループもシャットダウンイベントで即時中断する。

## 既知の制限 / 未解決事項

- `startup.py` の一部分岐はテストで確認済みだが、本番環境での実際の動作は限定的にしか検証されていない。
- WALチェックポイントのタイムアウト値（デフォルト30秒）は実環境での負荷に応じて調整が必要になる可能性がある。
- ロールバック失敗時の情報はコンソール画面に表示されず、ログファイルのみで確認できる。

## 関連資料

- [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md) — session_diagnostics の役割
- [05_agent_09_02_data-layer-access-patterns.md](05_agent_09_02_data-layer-access-patterns.md) — DBアクセスパターン
- [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md) — 設定ファイル
