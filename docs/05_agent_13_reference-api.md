---
title: "Agent Reference API"
category: agent
tags:
  - agent
  - reference
  - api
  - types
related:
  - 05_agent_00_document-guide.md
---

# Agent Reference API

- ドキュメントガイド → [05_agent_00_document-guide.md](05_agent_00_document-guide.md)

## 目的

役割、主要な公開 API、呼び出し元、呼び出し先、関連する設定、失敗時の動作を含む、
モジュールごとの簡潔な API リファレンス。完全なメソッドシグネチャはリンク先の各章を参照。

> **本章の範囲:** 関数シグネチャ、パラメータ型、戻り値、エラー条件。
> コンポーネントのコンテキスト、データフロー、実行時の動作については → [05_agent_02 §Runtime Architecture](05_agent_02_runtime-architecture.md) を参照。

---

## AgentREPL（`agent/repl.py`）

- **役割:** REPL コーディネーター。薄い起動／ループドライバ
- **主要な API:** `await AgentREPL().run()`
- **呼び出し元:** `agent/__main__.py`
- **呼び出し先:** `Orchestrator`、`CommandRegistry`、`CLIView`、`factory.build_agent_context()`
- **設定:** `AgentConfig` 全体
- **失敗時:** 未処理の例外はイベントループに伝播する。`finally` は常にリソースをクローズする

完全な詳細: [05_agent_02_runtime-architecture.md §AgentREPL](05_agent_02_runtime-architecture.md)

---

## Orchestrator（`agent/orchestrator.py`）

- **役割:** ターンレベルのファサード。メモリ注入 → 圧縮 → LLM → ツールループを管理する
- **主要な API:** `await Orchestrator.handle_turn(line)`
- **呼び出し元:** REPL ループドライバ
- **呼び出し先:** `LLMTurnRunner`、`HistoryManager`、`AgentSession`、`MemoryInjectionService`
- **設定:** `cfg.llm.*`、`cfg.tool.*`、`cfg.memory.*`
- **失敗時:** `LLMTransportError` は内部で捕捉される。REPL は継続する

完全な詳細: [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)

---

## AgentContext（`agent/context.py`）

- **役割:** セッションごとの DI ハブ。共有される可変状態のコンテナ
- **主要な API:** `ctx.conv`、`ctx.turn`、`ctx.stats`、`ctx.cfg`、`ctx.session`、`ctx.services`
- **呼び出し元:** すべてのコンポーネント
- **呼び出し先:** なし（純粋な状態保持クラス）
- **設定:** `AgentConfig` が `ctx.cfg` として保持される
- **失敗時:** 該当なし

完全な詳細: [05_agent_04_01_state-and-persistence-state-model.md](05_agent_04_01_state-and-persistence-state-model.md)

---

## LLMClient（`shared/llm_client.py`）

- **役割:** LLM との HTTP 通信。SSE ストリーミング＋リトライ
- **主要な API:** `await client.stream(url, history, tool_defs)`、`client.build_payload(...)`
- **呼び出し元:** `LLMTurnRunner`、`HistoryManager`（`call()` 経由）、`SessionTitleService`
- **呼び出し先:** `RobustSSEParser`、`httpx.AsyncClient`
- **設定:** `cfg.llm.*`
- **失敗時:** ストリーム失敗時に `partial_text` を伴う `LLMTransportError` を発生させる

完全な詳細: [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md)

---

## ToolExecutor（`shared/tool_executor.py`）

- **役割:** TTL キャッシュ、副作用の分類、並行数制限を伴う MCP ツールルーティング
- **主要な API:** `await executor.execute(tool_name, args) -> ToolCallResult`
- **呼び出し元:** `LLMTurnRunner`（`execute_all_tool_calls` 経由）
- **呼び出し先:** `ToolRouteResolver`、`HttpTransport`、`McpServerHealthRegistry`
- **設定:** `cfg.tool.*`、`cfg.mcp.*`
- **失敗時:** トランスポート失敗時に `ToolCallResult(is_error=True)` を返す

完全な詳細: [05_agent_06_01_tool-execution-and-approval-execution.md](05_agent_06_01_tool-execution-and-approval-execution.md)

---

## ToolRouteResolver（`shared/route_resolver.py`）— ToolExecutor の内部コンポーネント

- **役割:** 4層構成のツール・サーバー間ルーティングカスケード（live discovery > ToolRegistry > config `tool_names` > 静的定数）
- **主要な API:** `resolve(tool_name) -> server_key`
- **呼び出し元:** ツール実行層
- **呼び出し先:** `McpServerHealthRegistry`、`LifecycleProtocol`（サーバー起動経由）
- **設定:** 直接の設定なし。優先順位に従って ToolRegistry、live discovery マップ、config `tool_names`、`tool_constants.py` の frozenset から読み取る
- **失敗時:** どの層でもツール名を解決できない場合に `KeyError` を発生させる

完全な詳細: [04_mcp_03 §Routing Source of Truth](04_mcp_03_routing_lifecycle_and_execution.md#routing-source-of-truth)

---

## HistoryManager（`agent/history.py`）

- **役割:** 会話履歴のサイズ管理と LLM ベースの圧縮
- **主要な API:** `await mgr.compress(history)`、`mgr.count_chars(history)`、`apply_config(...)`
- **呼び出し元:** Orchestrator の履歴圧縮処理
- **呼び出し先:** `LLMClient`、`HistorySelectionPolicy`
- **設定:** `cfg.llm.context_char_limit`、`context_compress_turns`、`history_protect_turns`
- **失敗時:** LLM による要約が失敗した場合 → 履歴を変更せずに返す（圧縮なし）

完全な詳細: [05_agent_04_01_state-and-persistence-state-model.md §HistoryManager](05_agent_04_01_state-and-persistence-state-model.md)

---

## CommandRegistry（`agent/commands/registry.py`）

- **役割:** すべてのスラッシュコマンドのディスパッチ。13のミックスインベースのコマンドグループ
- **主要な API:** `await cmds.dispatch(line) -> bool`
- **呼び出し元:** REPL ループドライバ
- **呼び出し先:** 10個のミックスインハンドラ＋プラグインレジストリ
- **設定:** コマンドごとに異なる `cfg.*` フィールド
- **失敗時:** コマンドエラーはユーザーに表示される。REPL は継続する

完全な詳細: [05_agent_07_01_cli-and-commands-cli-reference.md](05_agent_07_01_cli-and-commands-cli-reference.md)

---

## CLIView（`agent/cli_view.py`）

- **役割:** CLI 表示層。readline、進捗表示、複数行入力
- **主要な API:** `setup_readline()`、`write_token()`、`write_progress()`、`async read_multiline()`
- **呼び出し元:** `AgentREPL`、`Orchestrator`（Writer プロトコルのコールバック経由）
- **呼び出し先:** `readline`、`sys.stdout`
- **設定:** 直接の設定なし。構築時にコールバックが配線される
- **失敗時:** I/O エラーは呼び出し元に伝播する

完全な詳細: [05_agent_07_01_cli-and-commands-cli-reference.md §CLIView](05_agent_07_01_cli-and-commands-cli-reference.md)

---

## AgentSession（`agent/session.py`）

- **役割:** セッションとメッセージの SQLite への永続化（RAG ドキュメント操作は rag-pipeline-mcp に移管済み）
- **主要な API:** `start()`、`save(role, content)`、`save_diagnostic(content)`、`fetch_messages(session_id)`
- **スキップカウンタ:** `skipped_no_session_count`、`skipped_invalid_role_count`（セッションごとの読み取り専用プロパティ）
- **strict モード:** `AgentSession(strict_mode=True)` は、警告の代わりに最初のスキップされた保存時に `RuntimeError` を発生させる
- **呼び出し元:** `Orchestrator`、`CommandRegistry`（`/session` コマンド。`/db` コマンドは rag-pipeline-mcp に委譲する）
- **呼び出し先:** `SQLiteHelper`
- **設定:** DB パスは `config/agent.toml` から取得
- **失敗時:** 致命的な失敗時に `sqlite3.Error`。`session_id=None` の場合は警告をログ出力し、カウンタを増加させる

完全な詳細: [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)

---

## AgentConfig（`agent/config_dataclasses.py`）

- **役割:** 設定コンテナ。7個のサブ設定。`/reload` によるホットリロードが可能
- **主要な API:** `build_agent_config(cfg_override=None) -> AgentConfig`
- **呼び出し元:** セッション初期化、設定の再読み込み
- **呼び出し先:** `ConfigLoader.load_all()`
- **設定:** `config/` 内のすべての TOML ファイル
- **失敗時:** ファイルの読み込み／パース失敗時に `ConfigLoadError`

完全な詳細: [05_agent_08_01_configuration-loading-agent-config.md](05_agent_08_01_configuration-loading-agent-config.md)

---

## MemoryServices（`agent/memory/`）

- **役割:** オプションの永続的セマンティックメモリサブシステム
- **主要な API:** `memory.on_session_start()`、`memory.on_user_prompt(query, session_id)`、`memory.on_session_stop()`
- **呼び出し元:** `Orchestrator`、`AgentREPL`（起動／シャットダウン時）
- **呼び出し先:** `MemoryStore`、`MemoryRetriever`、`EmbeddingClient`
- **設定:** `cfg.memory.*`
- **失敗時:** エラーはログ出力される。REPL はメモリなしで継続する（グレースフルデグラデーション）

**有効化:** `use_memory_layer=False`（デフォルト）の場合、`ctx.services.memory` は `None` になる。
メモリサービスにアクセスする前に必ず null チェックを行うこと。

## Related Documents

- `05_agent_00_document-guide.md`

## Keywords

agent
reference
api
types
