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
source:
  - 05_agent_07_cli-and-commands.md
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
| `write_startup_banner(chunk_count, n_tools)` | `DB: {n} chunks \| Tools: {n}` |
| `write_history()` | readlineの履歴を`~/.agent_history`に保存(最大1000件) |
| `async read_multiline(loop, first_line)` | `\`で終わる行を収集し、`\n`で連結 |

### プロトコル(テスト用)

`Writer`プロトコル(出力操作)と`Reader`プロトコル(複数行入力)。
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
