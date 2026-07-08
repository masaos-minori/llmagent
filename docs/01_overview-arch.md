# 概要・アーキテクチャ

ファイル構成 → [`01_overview-files.md`](01_overview-files.md)

## 1. 概要・目的

エージェント + MCP サーバによるマルチエージェントオーケストレーションシステムの構築
- llama.cpp を用いた LLM サーバ群
- 単一責務ツール実行 MCP サーバ群
- 日本語・英語双方に対応した LLM エージェント
- SQLite ベースのベクトル DB による RAG 環境
- 対象 OS は Gentoo Linux or Ubuntu Linux
- 用途はプログラム開発

## 2. アーキテクチャ

### 2.1 プロセス構成

```
ユーザー
    │ 対話入力 (agent[chat]> / agent[code]> プロンプト)
    ▼
┌──────────────────────────────────────────────────────┐
│  agent.py (CLI REPL ツール)                           │
│  入力 → RAG 検索 → LLM 呼出 → MCP ツール実行 → 回答  │
└───────┬─────────────┬──────────────────┬─────────────┘
        │             │                  │
        ▼             ▼                  ▼
:8003 embed-LLM  :8001 agent-LLM   MCP サーバ群 (http)
(RAG 検索時)                       11 サーバ (:8004〜:8014)
```

#### 実装上の補足

- エントリポイントは `scripts/agent/__main__.py` であり、`python -m agent` で起動する。図中の `agent.py` はこのモジュールエントリを指す。(根拠: `__main__.py` の docstring)
- MCP サーバのトランスポートは設定上 `http` / `stdio` の両方が定義可能だが、現在の実装では `ToolExecutor` が HTTP POST `/v1/call_tool` を使用する。(根拠: `shared/tool_executor.py` の `HttpTransport`, stdio トランスポートは削除済み)
- 起動シーケンス (MCP サーバ起動・ヘルスチェック・セキュリティ監査・プロンプトセットアップ) は `agent/startup.py` の `StartupOrchestrator` に分離されており、`AgentREPL.run()` から委譲される。(根拠: `agent/startup.py`)

#### 設定ファイル分離方針

各プロセス (エージェント・各 MCP サーバー・crawler・ingester・chunk_splitter) は独立して動作し、**自身に対応する設定ファイル 1 つのみを読み込む**。他プロセスの設定ファイル (`agent.toml` を含む) は読み込まない。DB パス・外部サービス URL などが複数プロセスで必要な場合は共通ファイルを作らず、各プロセスの設定ファイルに個別に記述する。

| プロセス | 設定ファイル |
|---|---|
| agent | `config/agent.toml` |
| 各 MCP サーバー | `config/<key>_mcp_server.toml` |
| crawler | `config/crawler.toml` |
| ingester | `config/ingester.toml` |
| chunk_splitter | `config/chunk_splitter.toml` |

詳細 → [90_shared_03 §2a](90_shared_03_runtime_and_execution.md#2a-プロセス分離方針-config-isolation-policy)

| サービス | ポート | モデル | 役割 |
|---|---|---|---|
| `agent-llm` | 8001 | Qwen3.6-Instruct-Q4_K_M | チャット/コード生成 LLM (MQE・再ランク兼用) |
| `embed-llm` | 8003 | multilingual-E5-small | テキスト → 384 次元ベクトル変換 |
| `web-search-mcp` | 8004 | — | Web 検索 MCP サーバ (DuckDuckGo) |
| `file-read-mcp` | 8005 | — | ファイル読み取り MCP サーバ |
| `github-mcp` | 8006 | — | GitHub 操作 MCP サーバ |
| `file-write-mcp` | 8007 | — | ファイル書き込み MCP サーバ |
| `file-delete-mcp` | 8008 | — | ファイル削除 MCP サーバ |
| `shell-mcp` | 8009 | — | シェルコマンド実行 MCP サーバ |
| `rag-pipeline-mcp` | 8010 | — | RAG パイプライン MCP サーバ |
| `cicd-mcp` | 8012 | — | GitHub Actions CI/CD MCP サーバ |
| `mdq-mcp` | 8013 | — | Markdown Context Compression Engine MCP サーバ |
| `git-mcp` | 8014 | — | ローカル git 操作 MCP サーバ |

### 2.2 取込パイプライン

詳細 → [`03_rag_02_ingestion_pipeline.md`](03_rag_02_ingestion_pipeline.md)

```
target_urls → crawler.py (BFS クロール) → rag-src/*.json
           → chunk_splitter.py (JA/EN/code 分割) → rag-src/chunk/*.json
           → ingester.py (embed → SQLite INSERT) → rag-src/registered/
```

### 2.3 クエリパイプライン

詳細 → [`03_rag_03_query_pipeline.md`](03_rag_03_query_pipeline.md)

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

**workflow_mode の3種**

| workflow_mode | 動作 | 失敗時挙動 |
|---|---|---|
| `auto` (デフォルト) | ワークフロー定義が存在すれば有効化 | ロード失敗は警告ログで継続 |
| `required` | ワークフロー定義が必須 | ロード失敗は `RuntimeError` で起動中断 |
| `disabled` | 常にダイレクト実行 | ワークフローを完全バイパス |

`workflow_require_approval=True` で execute → verify 間に人間承認ゲートを挿入できる。承認待ち状態は `workflow.sqlite` に永続化されるため、再起動後も pending approvals が復元される。(根拠: `agent/config_dataclasses.py`, `agent/orchestrator.py`, `agent/startup.py`)

**MCP サーバの startup_mode**

`McpServerConfig.startup_mode` で2種類:

- `persistent` (デフォルト): 外部で常時起動済みのサーバに接続する
- `subprocess`: エージェント起動時にサブプロセスとして起動し、`/health` ポーリングで準備完了を確認する。起動失敗は `RuntimeError` ではなく警告ログに留め、REPL 起動を継続する (fail-open)。

(根拠: `shared/mcp_config.py`, `agent/startup.py`)

### 2.4 エージェント機能・コマンド一覧

詳細 → [`05_agent_07_cli-and-commands.md`](05_agent_07_cli-and-commands.md)

### 2.5 実装済み機能サマリ

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
