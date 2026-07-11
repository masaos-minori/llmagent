---
title: "Agent Reference API (Part 2)"
category: agent
tags:
  - agent
  - reference
  - api
  - types
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_13_reference-api-part1.md
---

# Agent Reference API

- ドキュメントガイド → [05_agent_00_document-guide.md](05_agent_00_document-guide.md)

## HistoryManager（`agent/history.py`）

- **役割:** 会話履歴のサイズ管理と LLM ベースの圧縮
- **主要な API:** `await mgr.compress(history)`、`mgr.count_chars(history)`、`apply_config(...)`
- **呼び出し元:** Orchestrator の履歴圧縮処理
- **呼び出し先:** `LLMClient`、`HistorySelectionPolicy`
- **設定:** `cfg.llm.context_char_limit`、`context_compress_turns`、`history_protect_turns`
- **失敗時:** LLM による要約が失敗した場合 → 履歴を変更せずに返す（圧縮なし）

完全な詳細: [05_agent_04_01_state-and-persistence-state-model-part1.md §HistoryManager](05_agent_04_01_state-and-persistence-state-model-part1.md)

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

完全な詳細: [05_agent_08_01_configuration-loading-agent-config-part1.md](05_agent_08_01_configuration-loading-agent-config-part1.md)

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
- `05_agent_13_reference-api-part1.md`

## Keywords

agent
reference
api
types
