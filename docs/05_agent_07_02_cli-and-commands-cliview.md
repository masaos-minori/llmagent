---
title: "Agent CLI and Commands - CLIView"
category: agent
tags:
  - agent
  - cli
  - cliview
  - callbacks
related:
  - 05_agent_00_document-guide.md
  - 05_agent_07_01_cli-and-commands-cli-reference.md
  - 05_agent_07_03_cli-and-commands-command-registry.md
  - 05_agent_07_04_cli-and-commands-purpose.md
  - 05_agent_07_05_cli-and-commands-repl-io.md
  - 05_agent_07_06_cli-and-commands-hot-reload.md
  - 05_agent_07_07_cli-and-commands-migration-notes.md
  - 05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md
  - 05_agent_07_09_cli-and-commands-slash-commands-context-db.md
  - 05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md
  - 05_agent_07_11_cli-and-commands-slash-commands-memory-other.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## CLIView (`agent/cli_view.py`)

プレゼンテーション層のみを担当する。各コンポーネントにコールバックとして注入される。

### コールバック

| Callback | Injected into | Called when |
|---|---|---|
| `write_token(token)` | `LLMClient(on_token=...)` | SSEトークンが届くたびに |
| `write_compress_notice(n)` | `HistoryManager(on_compress=...)` | 履歴が圧縮されたとき |
| `write_turn_start()` | `Orchestrator(on_turn_start=...)` | 各ツールループのターン開始前 |
| `write_turn_end()` | `Orchestrator(on_turn_end=...)` | 最終的なLLM回答の後 |
| `write_llm_error(e)` | `Orchestrator(on_error=...)` | LLMリクエストが失敗したとき |

### 主要メソッド

| Method | Output |
|---|---|
| `setup_readline()` | タブ補完(スラッシュコマンド)、emacs編集モード、履歴ファイルの読み込み |
| `write_progress(msg)` | `  [rag] {msg:<24}` をその場で上書き表示(`\r`) |
| `clear_progress()` | 進捗行をスペースで消去 |
| `write_warning(msg)` | `[warn] {msg}` |
| `write_fatal(msg)` | `[fatal] {msg}` |
| `write_startup_banner(chunk_count, n_tools, workflow_status="", memory_mode=None)` | `DB: {n} chunks \| Tools: {n}`。`memory_mode`指定時は`Memory: {mode}`行、`workflow_status`指定時は`Workflow: {status}`行を追加出力し、最後に`Type /help for commands, /exit to quit.`を表示 |
| `write_history()` | readlineの履歴を`~/.agent_history`に保存(最大1000件) |
| `async read_multiline(loop, first_line)` | `\`で終わる行を収集し、`\n`で連結 |
| `async start_spinner(msg="Thinking")` / `stop_spinner()` | 非同期スピナー(`⠋⠙⠹...`)をその場でアニメーション表示・停止 |
| `write_debug_rag(data)` | RAGパイプラインのデバッグ情報(RRF設定・MQEクエリ・マージ結果・リランク結果)を構造化表示。`/rag ... --debug`から利用 |

### 実装上の補足 (Current behavior)

- `write_token()`はトークン出力の直前に`stop_spinner()`を呼び、スピナー表示中でもストリーミングトークンが割り込めるようにしている。(Explicit in code)
- `write_startup_banner()`のシグネチャは`workflow_status`・`memory_mode`引数を持つ。ドキュメント記載の`write_startup_banner(chunk_count, n_tools)`は簡略化された旧形。(Explicit in code)
- `CLIView.__init__(slash_commands)`はスラッシュコマンド一覧(タブ補完候補)を必須引数として受け取る。

### プロトコル(テスト用)

`Writer`プロトコル(出力操作)と`Reader`プロトコル(複数行入力)。
`Writer`には`write_fatal`・`write_startup_banner`(拡張シグネチャ)を含む。
テストでは実際のCLIViewの代わりに別実装を注入できる。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

CLIView
callbacks
key methods
protocols for testing
