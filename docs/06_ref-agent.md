# エージェント実行層モジュール (インデックス)

REPL エージェントを構成するランタイムコンポーネント群。

| モジュール | 役割 | 参照ドキュメント |
|---|---|---|
| `agent_session.py` | `AgentSession` — REPL セッション・メッセージの SQLite 永続化マネージャ | [06_ref-agent-session.md](06_ref-agent-session.md) |
| `agent_repl.py` | `AgentREPL` — 全コンポーネントを AgentContext へ DI する薄いコーディネータ | [06_ref-agent-repl.md](06_ref-agent-repl.md) |
| `orchestrator.py` | `Orchestrator` — per-turn RAG 付加・LLM ループ・ツールディスパッチ・OTel スパン | [06_ref-agent-repl.md](06_ref-agent-repl.md) |
| `agent_config.py` | 共有設定定数 + `AgentConfig` dataclass + `build_agent_config()` | [06_ref-agent-config.md](06_ref-agent-config.md) |
| `agent_context.py` | `AgentContext` — 全コンポーネント参照と per-session mutable state の一元管理 | [06_ref-agent-context.md](06_ref-agent-context.md) |
| `memory_store.py` | `MemoryStore` — memory_entries / memory_vec の SQLite CRUD + vec0 KNN 検索 | [06_ref-agent-context.md](06_ref-agent-context.md) |
| `memory_layer.py` | `MemoryLayer` — 4 階層メモリの高レベルファサード (long_term / task) | [06_ref-agent-context.md](06_ref-agent-context.md) |
| `otel_tracer.py` | `build_tracer()` — プライベート `TracerProvider` 生成・グローバル状態汚染なし | [05_agent-ops.md](05_agent-ops.md) |
| `cli_view.py` | `CLIView` — readline 設定・RAG 進捗表示・マルチライン入力 | [06_ref-agent-view.md](06_ref-agent-view.md) |
| `agent_commands.py` | `CommandRegistry` — スラッシュコマンドディスパッチャ (AgentContext 経由で DI) | [06_ref-agent-commands.md](06_ref-agent-commands.md) |
| `llm_client.py` | `LLMClient` — SSE ストリーミング・指数バックオフリトライ・レスポンス整形 | [06_ref-agent-llm.md](06_ref-agent-llm.md) |
| `history_manager.py` | `HistoryManager` — 会話履歴文字数カウント・LLM ベースコンテキスト圧縮 | [06_ref-agent-history.md](06_ref-agent-history.md) |
