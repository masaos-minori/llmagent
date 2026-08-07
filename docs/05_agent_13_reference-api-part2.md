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
  - 05_agent_13_reference-api-part2.md
---

# Agent Reference API — Part 2

## Purpose

役割、主要な公開 API、呼び出し元、呼び出し先、関連する設定、失敗時の動作を含む、
モジュールごとの簡潔な API リファレンス。完全なメソッドシグネチャはリンク先の各章を参照。

## Design Intent

API レファレンスは「API は何か」「どのように動作するか」に焦点を当てる。「なぜこの API がこのように設計されたか」は設計文書の範囲である。

## Responsibility Boundary

- このファイルが所有するもの: 関数シグネチャ、パラメータ型、戻り値、エラー条件
- このファイルが所有しないもの: コンポーネントのコンテキスト、データフロー、実行時の動作

## Key Constraints

- API レファレンスの詳細は Canonical Source Rule で定められた正本にのみ存在する
- 他章での API/type/method 詳細の重複は禁止（Canonical Source Rule）
- 不完全な実装変更は `Needs Confirmation` マークで明示する

## Operational Notes

- REPL ループドライバからの呼び出しは常に `await` 形式
- 失敗時はエラー種別ごとに異なるフォールバック動作が存在する
- メモリレイヤーはオプションであり、`ctx.services.memory is None` の場合に安全にガードできる設計になっている

## Known Limitations

- 一部の呼び出し先は間接的な依存関係を含んでいる
- 旧版ドキュメントと現行コードの差分は `Needs Confirmation` マークで明示されている

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_13_reference-api-part1.md`

---

## HistoryManager（`agent/history.py`）

- **役割:** 会話履歴のサイズ管理と LLM ベースの圧縮
- **主要な API:** `await mgr.compress(history)`、`await mgr.force_compress(history)`、`mgr.count_chars(history)`、`mgr.count_tokens(history, last_input_tokens=None)`、`await mgr.count_tokens_async(...)`、`apply_config(...)`
- **呼び出し元:** Orchestrator の履歴圧縮処理、`/compact` コマンド（`force_compress`）
- **呼び出し先:** `httpx.AsyncClient`（コンストラクタで注入される `http`。要約 LLM 呼び出しは `LLMClient` を経由せず `self._http.post()` で直接行う）、`HistorySelectionPolicy`
- **設定:** `cfg.llm.context_char_limit`、`context_compress_turns`、`history_protect_turns`
- **失敗時:** LLM 要約が失敗した場合（`HistoryCompressionError`）→ 文字数制限超過中ならフォールバック切り捨てで低重要度メッセージから切り捨てる。文字数制限内（トークン制限のみ超過）の場合は履歴を変更せずに返す

> **根拠分類: Explicit in code（訂正）。** 旧版は呼び出し先を `LLMClient` としていたが、
> 要約 LLM 呼び出しはコンストラクタで受け取った `httpx.AsyncClient` に対し
> 直接 `self._http.post()` を発行しており、`shared/llm_client.py::LLMClient` のインスタンスは経由しない。
> また「失敗時は圧縮なし」という記述は不完全で、文字数超過時は
> フォールバック切り捨てが行われる（`stat_fallback_truncate_count` が増分される）。トークン制限のみの超過時は
> 変更なしで返る。

完全な詳細: [05_agent_04_01_state-and-persistence-state-model-part1.md §HistoryManager](05_agent_04_01_state-and-persistence-state-model-part1.md)

---

## CommandRegistry（`agent/commands/registry.py`）

- **役割:** すべてのスラッシュコマンドのディスパッチ。15のミックスインベースのコマンドグループ
- **主要な API:** `await cmds.dispatch(line) -> bool`
- **呼び出し元:** REPL ループドライバ
- **呼び出し先:** 15個のミックスインハンドラ＋プラグインレジストリ
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
- **設定:** `config/agent.toml`
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

**有効化:** `use_memory_layer=True`（デフォルト）の場合、`ctx.services.memory` が有効になる。
メモリサービスにアクセスする前に必ず null チェックを行うこと。
