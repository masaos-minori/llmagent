---
title: "Pipeline Architecture"
category: overview
tags:
  - pipeline-architecture
  - ingestion-pipeline
  - query-pipeline
  - rag
  - architecture
  - embedding
  - search
related:
  - 01_overview-arch-01-process.md
  - 01_overview-arch-03-features.md
  - 01_overview.md
source:
  - 01_overview-arch.md
---

# 概要・アーキテクチャ

ファイル構成 → [`01_overview-files-01-build.md`](01_overview-files-01-build.md), [`01_overview-files-02-rag.md`](01_overview-files-02-rag.md), [`01_overview-files-03-scripts.md`](01_overview-files-03-scripts.md), [`01_overview-files-04-shared.md`](01_overview-files-04-shared.md), [`01_overview-files-05-config.md`](01_overview-files-05-config.md), [`01_overview-files-06-misc.md`](01_overview-files-06-misc.md)

## 2. アーキテクチャ

### 2.2 取込パイプライン

詳細 → [`03_rag_02_01_ingestion_pipeline-overview.md`](03_rag_02_01_ingestion_pipeline-overview.md)

```
target_urls → crawler.py (BFS クロール) → rag-src/*.json
           → chunk_splitter.py (JA/EN/code 分割) → rag-src/chunk/*.json
           → ingester.py (embed → SQLite INSERT) → rag-src/registered/
```

### 2.3 クエリパイプライン

詳細 → [`03_rag_03_01_query_pipeline-overview.md`](03_rag_03_01_query_pipeline-overview.md)

```
ユーザー入力
  → MQE + embed → KNN+BM25 → RRF → Rerank → Refiner → コンテキスト付加
  → LLM (:8001) → tool_calls → MCP サーバ群 (:8004〜:8014)
  → 最終回答 (SSE ストリーミング)
```

#### 実装上の補足

- ターン処理は 4 層に分離されている: `AgentREPL`(REPL ループ) → `Orchestrator`(ターン制御・ワークフロー管理) → `LLMTurnRunner`(LLM ストリーミング + 内部ツールループ) → `agent/tool_runner.py`(ツール実行)。各層の責務は `agent/repl.py` の docstring で宣言されている。
- MDQ/RAG ツール選択: `agent/mdq_rag_classifier.py` がクエリ文字列を解析し、Markdown 構造系キーワードを含む場合は MDQ ツール、それ以外は RAG ツールを優先するよう `system` ロールのエフェメラルメッセージとして hint をhistory に注入する。設定で固定も可能。(根拠: `agent/orchestrator.py`)
- ツールループガード: 同一ターン内で重複ツール呼び出し (`dedup`)・失敗済み呼び出しの再試行 (`retry`)・ラウンド指紋の繰り返し (`cycle`)・連続エラー上限 (`consecutive_errors`) の 4 種の異常を検出して LLM に停止ヒントを返す。(根拠: `agent/tool_loop_guard.py`)
- ワークフローエンジン: `agent/workflow/workflow_engine.py` が plan → execute → [approval gate] → verify のステージ遷移を管理する。`/approve` / `/reject` スラッシュコマンドで人間承認ゲートを通過させる。ターン開始時に承認待ち状態であれば LLM 処理はブロックされる。(根拠: `agent/orchestrator.py`)

**ターン内の処理順序**

ターン内の実行順序はコードで確定している (`orchestrator.py`):

1. メモリ注入 — セマンティックメモリをフラグ付きのシステムメッセージとして追加
2. MDQ/RAG ヒント注入 — フラグ付きシステムメッセージとして追加
3. ユーザメッセージ追加 — システムプロンプト同期後に `history` へ追加し `session.sqlite` へ保存
4. 履歴圧縮 — 文字数/トークン超過時のみ LLM 要約を実行
5. LLM 呼び出し — LLMTurnRunner によるストリーミング + ツールループ

フラグを持つメッセージは、各ターン開始時のシステムプロンプト同期処理で除去される。永続セッション履歴には保存されない。

**ワークフローは常時必須(モード設定なし)**

`workflow_mode` は設定キーとして存在しない(`build_agent_config()` の `_FORBIDDEN_KEYS` に含まれ、設定すると `ConfigLoadError` で起動不可)。ワークフロー定義 (`config/workflows/default.json` としてデプロイされる **required workflow deployment artifact**) は常に必須であり、存在しない・不正な場合は起動前に `RuntimeError` で中断する。ダイレクト実行へのフォールバックや、ワークフローを無効化する経路は一切存在しない。

詳細: [02_deployment.md §Workflow deployment checklist](02_deployment.md) / [Workflow Deployment Runbook](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook)

`workflow_require_approval=True` で execute → verify 間に人間承認ゲートを挿入できる。承認待ち状態は `workflow.sqlite` に永続化されるため、再起動後も pending approvals が復元される。(根拠: `agent/config_dataclasses.py`, `agent/orchestrator.py`, `agent/startup.py`)

**MCP サーバの startup_mode**

`McpServerConfig.startup_mode` で2種類:

- `persistent` (デフォルト): 外部で常時起動済みのサーバに接続する
- `subprocess`: エージェント起動時にサブプロセスとして起動し、`/health` ポーリングで準備完了を確認する。起動失敗は `RuntimeError` ではなく警告ログに留め、REPL 起動を継続する (fail-open)。

(根拠: `shared/mcp_config.py`, `agent/startup.py`)

## Related Documents

- `01_overview-arch-01-process.md`
- `01_overview-arch-03-features.md`
- `01_overview.md`

## Keywords

pipeline-architecture
ingestion-pipeline
query-pipeline
rag
turn-processing
workflow-mode
startup-mode
