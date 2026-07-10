---
title: "Feature Architecture"
category: overview
tags:
  - feature-architecture
  - implemented-features
  - agent-context
  - memory-layer
  - tool-routing
  - plugin-system
  - sqlite-vec
  - diagnostic-store
related:
  - 01_overview-arch-01-process.md
  - 01_overview-arch-02-pipelines.md
  - 01_overview.md
source:
  - 01_overview-arch.md
---

# 概要・アーキテクチャ

ファイル構成 → [`01_overview-files-01-build.md`](01_overview-files-01-build.md), [`01_overview-files-02-rag.md`](01_overview-files-02-rag.md), [`01_overview-files-03-scripts.md`](01_overview-files-03-scripts.md), [`01_overview-files-04-shared.md`](01_overview-files-04-shared.md), [`01_overview-files-05-config.md`](01_overview-files-05-config.md), [`01_overview-files-06-misc.md`](01_overview-files-06-misc.md)

## 2.4 エージェント機能・コマンド一覧

詳細 → [`05_agent_07_01_cli-and-commands-cli-reference.md`](05_agent_07_01_cli-and-commands-cli-reference.md)

## 2.5 実装済み機能サマリ

| 機能 | 実装場所 |
|---|---|
| RAG 検索 (MQE + KNN + BM25 + RRF + Rerank + Refiner) | `scripts/rag/pipeline.py` |
| MCP ツールコーリング (HTTP, 11 サーバ) | `agent/tool_runner.py`, `shared/tool_executor.py` |
| メモリレイヤー (semantic/episodic) | `agent/memory/` |
| セッション永続化・復元 | `agent/session.py`, `db/` |
| コンテキスト圧縮 (LLM 要約) | `agent/history.py` |
| ツール結果 TTL キャッシュ | `shared/tool_cache.py`, `shared/tool_executor.py` |
| SSE ストリーミング | `shared/llm_client.py` |
| スラッシュコマンド群 | `agent/commands/` |
| ツールループガード (dedup/cycle/retry/error 上限) | `agent/tool_loop_guard.py` |
| ワークフローエンジン (plan/execute/approval/verify) | `agent/workflow/` |
| MDQ/RAG クエリルーティング | `agent/mdq_rag_classifier.py` |
| 依存性注入ハブ (AgentContext) | `agent/context.py` |
| 診断ストア (ターン/セッション統計) | `agent/diagnostic_store.py` |

#### 実装上の補足

**共有状態と依存性注入**

`AgentContext` (`agent/context.py`) が全サービスの依存性注入ハブとして機能する。`ConversationState`・`TurnState`・`RuntimeStats`・`WorkflowState`・`AppServices` を合成し、`AgentREPL`・`Orchestrator`・各コマンドハンドラが同一インスタンスを参照する。(根拠: `agent/context.py`)

**メモリレイヤーの動作モード**

`MemoryServices.get_activation_mode()` が起動時の状態に応じて 4 種のモードを返す: `disabled` (設定で無効)・`fts-only` (embed サーバ不在)・`degraded` (embed サーキットブレーカー開放)・`hybrid` (正常動作)。セマンティック検索が使えない場合は FTS のみにフォールバックし、エラーとして扱わない設計。(根拠: `agent/memory/services.py`)

**ツールルーティング**

`shared/route_resolver.py` がツール名をサーバキーに解決する。ルーティング優先順位は (1) 起動時の `/v1/tools` live discovery マップ、(2) `shared/tool_registry.py` の静的レジストリ。設定 `tool_names` はルーティングには使用せず、ドリフト検証用のメタデータのみ。(根拠: `shared/route_resolver.py`)

**プラグインシステム**

`factory.build_agent_context()` の末尾でプラグインレジストリ初期化が呼ばれ、`plugins/` ディレクトリからツールおよびスラッシュコマンドを動的ロードする。設定による動作制御:

- `plugin_tool_override=False` (デフォルト): 既存 MCP ツール名と衝突するプラグインは拒否
- `plugin_strict=False` (デフォルト): ロード失敗は警告ログに留め、エージェント起動は継続 (fail-open)

(根拠: `agent/factory.py`)

**sqlite-vec 拡張の適用範囲**

`db/helper.py` の `SQLiteHelper` は `target="rag"` 時のみ sqlite-vec 拡張 (`vec0.so`) をロードする。`session`・`workflow`・`eventbus` DB には適用しない。ベクトル演算を RAG DB に限定する意図的な分離。(根拠: `db/helper.py`)

**セッション終了時の診断保存**

REPLループの `finally` ブロックで以下を実行する:

1. セッション診断情報の保存 — ターン数・ツール呼出数・レイテンシ・ワークフロー統計を `DiagnosticStore` に保存
2. セッションメモリの永続化 — セッション履歴からルールベースでメモリを抽出・永続化
3. `session.sqlite` に対して WAL TRUNCATE チェックポイントを実行してからコネクションをクローズ

診断情報は `/db` コマンドで参照できる。(根拠: `agent/repl.py`)

---

## Related Documents

- `01_overview-arch-01-process.md`
- `01_overview-arch-02-pipelines.md`
- `01_overview.md`

## Keywords

feature-architecture
implemented-features
agent-context
memory-layer
tool-routing
plugin-system
sqlite-vec
diagnostic-store
