---
title: "Feature Architecture"
category: overview
tags:
  - feature-architecture
  - implemented-features
  - agent-context
  - memory-layer
  - tool-routing
  - sqlite-vec
  - diagnostic-store
related:
  - 01_overview-arch-01-process.md
  - 01_overview-arch-02-pipelines.md
---

# 概要・アーキテクチャ

ファイル構成 → [`01_overview-files-01-build.md`](01_overview-files-01-build.md), [`01_overview-files-02-rag.md`](01_overview-files-02-rag.md), [`01_overview-files-03-scripts.md`](01_overview-files-03-scripts.md), [`01_overview-files-04-shared.md`](01_overview-files-04-shared.md), [`01_overview-files-05-config.md`](01_overview-files-05-config.md), [`01_overview-files-06-misc.md`](01_overview-files-06-misc.md)

## 2.4 エージェント機能・コマンド一覧

詳細 → [`05_agent_07_01_cli-and-commands-cli-reference.md`](05_agent_07_01_cli-and-commands-cli-reference.md)

## 2.5 実装済み機能サマリ

| 機能 | 実装場所 |
|---|---|
| RAG 検索 (MQE + KNN + BM25 + RRF + Rerank + Refiner) | `scripts/rag/` |
| MCP ツールコーリング (HTTP, 11 サーバ) | `scripts/agent/`, `scripts/shared/` |
| メモリレイヤー (semantic/episodic) | `scripts/agent/memory/` |
| セッション永続化・復元 | `scripts/agent/`, `scripts/db/` |
| コンテキスト圧縮 (LLM 要約) | `scripts/agent/` |
| ツール結果 TTL キャッシュ | `scripts/shared/` |
| SSE ストリーミング | `scripts/shared/` |
| スラッシュコマンド群 | `scripts/agent/commands/` |
| ツールループガード (dedup/cycle/retry/error 上限) | `scripts/agent/` |
| ワークフローエンジン (plan/execute/approval/verify) | `scripts/agent/workflow/` |
| MDQ/RAG クエリルーティング | `scripts/agent/` |
| 依存性注入ハブ (AgentContext) | `scripts/agent/` |
| 診断ストア (ターン/セッション統計) | `scripts/agent/` |

詳細なファイル構成については [`01_overview-files-03-scripts-part*.md`](01_overview-files-03-scripts.md) シリーズを参照してください。

### 実装上の補足

**共有状態と依存性注入**

`AgentContext` (`agent/context.py`) が全サービスの依存性注入ハブとして機能する。`ConversationState`・`TurnState`・`RuntimeStats`・`WorkflowState`・`AppServices` を合成し、`AgentREPL`・`Orchestrator`・各コマンドハンドラが同一インスタンスを参照する。(根拠: `agent/context.py`)

**メモリレイヤーの動作モード**

`MemoryServices.get_activation_mode()` が起動時の状態に応じて 4 種のモードを返す: `disabled` (設定で無効)・`fts-only` (embed サーバ不在)・`degraded` (embed サーキットブレーカー開放)・`hybrid` (正常動作)。セマンティック検索が使えない場合は FTS のみにフォールバックし、エラーとして扱わない設計。(根拠: `agent/memory/services.py`)

**ツールルーティング**

`RuntimeToolRegistry` (`shared/route_resolver.py`) が唯一のルーティング権限を持つ。起動時の `/v1/tools` live discovery マップはバリデーション専用であり、ルーティングには使用されない。また、静的レジストリ (`tool_registry.py`) も現在はルーティングには使用されない。設定 `tool_names` はドリフト検証にのみ使用される。(根拠: `shared/route_resolver.py`)

**sqlite-vec 拡張の適用範囲**

`db/helper.py` の `SQLiteHelper` は `target="rag"` 時のみ sqlite-vec 拡張 (`vec0.so`) をロードする。`session`・`workflow`・`eventbus` DB には適用しない。ベクトル演算を RAG DB に限定する意図的な分離。(根拠: `db/helper.py`)

**セッション終了時の診断保存**

REPLループの `finally` ブロックで以下を実行する:

1. セッション診断情報の保存 — ターン数・ツール呼出数・レイテンシ・ワークフロー統計を `DiagnosticStore` に保存
2. セッションメモリの永続化 — セッション履歴からルールベースでメモリを抽出・永続化
3. `session.sqlite` に対して WAL TRUNCATE チェックポイントを実行してからコネクションをクローズ。チェックポイントが失敗した場合は、防御策として `_wal_backup_sync` による WAL ファイルのバックアップが試行されるが、例外は発生せずプロセスは正常に終了する。次回の起動時には SQLite が既存の WAL ファイルを読み込むため、データの損失は発生しない。ただし、繰り返し失敗する場合は WAL ファイルの肥大化に注意が必要である。(根拠: `agent/repl.py`)

診断情報は `/db` コマンドで参照できる。(根拠: `agent/repl.py`)

---

## Related Documents

- `01_overview-arch-01-process.md`
- `01_overview-arch-02-pipelines.md`
- [01_overview.md](01_overview.md)

## Keywords

feature-architecture
implemented-features
agent-context
memory-layer
tool-routing
sqlite-vec
diagnostic-store
