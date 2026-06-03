# エージェント実行層モジュール (インデックス)

REPL エージェントを構成するランタイムコンポーネント群。

| モジュール | 役割 | 参照ドキュメント |
|---|---|---|
| `agent/session.py` | `AgentSession` — REPL セッション・メッセージの SQLite 永続化マネージャ | [06_ref-agent-session.md](06_ref-agent-session.md) |
| `agent/repl.py` | `AgentREPL` — 全コンポーネントを AgentContext へ DI する薄いコーディネータ | [06_ref-agent-repl.md](06_ref-agent-repl.md) |
| `agent/orchestrator.py` | `Orchestrator` — LLM ループ・ツールディスパッチ・OTel スパン | [06_ref-agent-repl.md](06_ref-agent-repl.md) |
| `agent/config.py` | 共有設定定数 + `AgentConfig` dataclass + `build_agent_config()` | [06_ref-agent-config.md](06_ref-agent-config.md) |
| `agent/context.py` | `AgentContext` — 全コンポーネント参照と per-session mutable state の一元管理 | [06_ref-agent-context.md](06_ref-agent-context.md) |
| `agent/memory/store.py` | `MemoryStore` — memories / memories_fts テーブルの SQLite CRUD + vec0 KNN 検索 | [06_ref-agent-context.md](06_ref-agent-context.md) |
| `agent/memory/layer.py` | `MemoryLayer` — 3 サブサービスへの薄いファサード (SessionStart / UserPrompt / Stop ライフサイクル) | [06_ref-agent-context.md](06_ref-agent-context.md) |
| `agent/memory/injection.py` | `MemoryInjectionService` — セッション開始 / ユーザープロンプト時のメモリ注入 | [06_ref-agent-context.md](06_ref-agent-context.md) |
| `agent/memory/ingestion.py` | `MemoryIngestionService` — セッション終了時の会話履歴からのメモリ抽出・永続化 | [06_ref-agent-context.md](06_ref-agent-context.md) |
| `agent/memory/embedding_client.py` | `EmbeddingClient` — リトライ + サーキットブレーカ付き埋め込みベクトル取得クライアント | [06_ref-agent-context.md](06_ref-agent-context.md) |
| `shared/otel_tracer.py` | `build_tracer()` — プライベート `TracerProvider` 生成・グローバル状態汚染なし | [05_agent-ops.md](05_agent-ops.md) |
| `agent/cli_view.py` | `CLIView` — readline 設定・進捗表示・マルチライン入力 | [06_ref-agent-view.md](06_ref-agent-view.md) |
| `agent/commands/registry.py` | `CommandRegistry` — スラッシュコマンドディスパッチャ (AgentContext 経由で DI) | [06_ref-agent-commands.md](06_ref-agent-commands.md) |
| `shared/llm_client.py` | `LLMClient` — SSE ストリーミング・指数バックオフリトライ・レスポンス整形 | [06_ref-agent-llm.md](06_ref-agent-llm.md) |
| `agent/history.py` | `HistoryManager` — 会話履歴文字数カウント・LLM ベースコンテキスト圧縮 | [06_ref-agent-history.md](06_ref-agent-history.md) |
