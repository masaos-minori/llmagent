# エージェント実行層モジュール (インデックス)

REPL エージェントを構成するランタイムコンポーネント群。

| モジュール | 役割 | 参照ドキュメント |
|---|---|---|
| `agent/session.py` | `AgentSession` — REPL セッション・メッセージの SQLite 永続化マネージャ | [05_ref-agent-session.md](05_ref-agent-session.md) |
| `agent/repl.py` | `AgentREPL` — 全コンポーネントを AgentContext へ DI する薄いコーディネータ | [05_ref-agent-repl.md](05_ref-agent-repl.md) |
| `agent/orchestrator.py` | `Orchestrator` — LLM ループ・ツールディスパッチ・OTel スパン | [05_ref-agent-repl.md](05_ref-agent-repl.md) |
| `agent/config.py` | 共有設定定数 + `AgentConfig` dataclass + `build_agent_config()` | [05_ref-agent-config.md](05_ref-agent-config.md) |
| `agent/context.py` | `AgentContext` — 全コンポーネント参照と per-session mutable state の一元管理 | [05_ref-agent-context.md](05_ref-agent-context.md) |
| `agent/memory/store.py` | `MemoryStore` — memories / memories_fts / memories_vec テーブルの SQLite CRUD | [05_ref-agent-context.md](05_ref-agent-context.md) |
| `agent/memory/services.py` | `MemoryServices` — memory サブサービスのコンテナ (AppServices.memory の型) | [05_ref-agent-context.md](05_ref-agent-context.md) |
| `agent/memory/injection.py` | `MemoryInjectionService` — セッション開始 / ユーザープロンプト時のメモリ注入 | [05_ref-agent-context.md](05_ref-agent-context.md) |
| `agent/memory/ingestion.py` | `MemoryIngestionService` — セッション終了時の会話履歴からのメモリ抽出・永続化 | [05_ref-agent-context.md](05_ref-agent-context.md) |
| `agent/memory/embedding_client.py` | `EmbeddingClient` / `EmbeddingClientConfig` / `EmbeddingResult` — リトライ + サーキットブレーカ付き埋め込みベクトル取得クライアント | [05_ref-agent-context.md](05_ref-agent-context.md) |
| `agent/memory/retriever.py` | `HybridRetriever` / `FtsRetriever` / `VectorRetriever` — FTS5 BM25 + KNN 検索、RRF マージ、スコアリング | [05_ref-agent-context.md](05_ref-agent-context.md) |
| `agent/memory/jsonl_store.py` | `JsonlMemoryStore` — 追記専用 JSONL ソース（正源ファイル） | [05_ref-agent-context.md](05_ref-agent-context.md) |
| `agent/memory/extract.py` | `extract_memories()` / `ExtractionPolicy` — 会話履歴からのルールベースメモリ抽出 | [05_ref-agent-context.md](05_ref-agent-context.md) |
| `agent/memory/mapper.py` | `row_to_entry()` — SQLite row → MemoryEntry 変換ヘルパー | [05_ref-agent-context.md](05_ref-agent-context.md) |
| `agent/memory/enums.py` | `MemoryType` / `RetrievalMode` / `ExtractionDecision` — ドメイン列挙型 | [05_ref-agent-context.md](05_ref-agent-context.md) |
| `agent/memory/exceptions.py` | `MemorySchemaError` / `JsonlFormatError` / `MemoryConsistencyError` 等 — ドメイン例外 | [05_ref-agent-context.md](05_ref-agent-context.md) |
| `agent/memory/types.py` | `MemoryEntry` / `MemoryQuery` / `MemoryHit` / `EmbeddingResult` / `SourceType` — データ型 | [05_ref-agent-context.md](05_ref-agent-context.md) |
| `agent/memory/models.py` | `HistoryMessage` / `JsonlRecord` / `ConsistencyReport` / `MemorySnippet` — DTO | [05_ref-agent-context.md](05_ref-agent-context.md) |
| `shared/otel_tracer.py` | `build_tracer()` — プライベート `TracerProvider` 生成・グローバル状態汚染なし | [05_agent-ops.md](05_agent-ops.md) |
| `agent/cli_view.py` | `CLIView` — readline 設定・進捗表示・マルチライン入力 | [05_ref-agent-view.md](05_ref-agent-view.md) |
| `agent/commands/registry.py` | `CommandRegistry` — スラッシュコマンドディスパッチャ (AgentContext 経由で DI) | [05_ref-agent-commands.md](05_ref-agent-commands.md) |
| `shared/llm_client.py` | `LLMClient` — SSE ストリーミング・指数バックオフリトライ・レスポンス整形 | [05_ref-agent-llm.md](05_ref-agent-llm.md) |
| `agent/history.py` | `HistoryManager` — 会話履歴文字数カウント・LLM ベースコンテキスト圧縮 | [05_ref-agent-history.md](05_ref-agent-history.md) |
