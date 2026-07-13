---
title: "Agent CLI and Commands - REPL Input/Output Model"
category: agent
tags:
  - agent
  - cli
  - repl-io
related:
  - 05_agent_00_document-guide.md
  - 05_agent_07_01_cli-and-commands-cli-reference.md
  - 05_agent_07_02_cli-and-commands-cliview.md
  - 05_agent_07_03_cli-and-commands-command-registry.md
  - 05_agent_07_04_cli-and-commands-purpose.md
  - 05_agent_07_06_cli-and-commands-hot-reload.md
  - 05_agent_07_07_cli-and-commands-migration-notes.md
  - 05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md
  - 05_agent_07_09_cli-and-commands-slash-commands-context-db.md
  - 05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md
  - 05_agent_07_11_cli-and-commands-slash-commands-memory-other.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## REPL入出力モデル

- **プロンプト:** `> `(固定文字列。`AgentREPL._prompt`プロパティ)
- **通常の入力:** 任意のテキスト → `Orchestrator.handle_turn()`に転送される
- **スラッシュコマンド:** `/`で始まる行 → `CommandRegistry.dispatch(line)`
- **複数行入力:** `\`で終わる行 → `... `プロンプトで継続(`CLIView.read_multiline()`)
- **EOF / Ctrl-D:** 正常なシャットダウン(`_read_input()`が`None`を返し`_repl_loop`を抜ける)
- **Ctrl-C:** `_read_input()`内で`EOFError`と同様に捕捉され、入力待ち中はEOFと同じくREPL終了に至る(現在のツールループ実行中の中断とは別扱い)

### 実装上の補足 (Current behavior)

- `_prompt`はセッションIDを含まない固定値`"> "`。session_idを埋め込む`agent[:#N]>`形式の表記はコード上に見当たらない。[Needs confirmation: 過去の実装からの変更か、doc側の誤記かは未確認]
- 入力待ち中の`KeyboardInterrupt`は`_read_input()`内で捕捉され、`write_turn_end()`を出力した上で`None`を返す。呼び出し元`_repl_loop`は`None`を受けてループを`break`するため、**入力待ち中のCtrl-CはEOFと同様にREPLを終了させる**(現在行のみを中断してプロンプトに戻る挙動ではない)。根拠: `repl.py`の`_read_input`/`_repl_loop`。(Explicit in code)
- SIGTERM受信時は`shutdown_requested`と`_shutdown_event`をセットし、実行中のターンを最大10秒(`_GRACEFUL_TIMEOUT`)待ってから強制終了する(グレースフルシャットダウン)。根拠: `repl.py`の`run()`・`_repl_loop()`。(Explicit in code)
- `/exit`は`_should_exit()`で判定され、`shutdown_requested`が立っている場合も同メソッドでループ終了と判定される。(Explicit in code)

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

REPL input/output model
