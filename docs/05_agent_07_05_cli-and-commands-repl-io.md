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

- **プロンプト:** `> `(固定文字列。REPLプロンプトプロパティ)
- **通常の入力:** 任意のテキスト → `Orchestrator.handle_turn()`に転送される
- **スラッシュコマンド:** `/`で始まる行 → `CommandRegistry.dispatch(line)`
- **複数行入力:** `\`で終わる行 → `... `プロンプトで継続(`CLIView.read_multiline()`)
- **EOF / Ctrl-D:** 正常なシャットダウン(REPL入力が`None`を返しループを抜ける)
- **Ctrl-C:** 入力内で`EOFError`と同様に捕捉され、入力待ち中はEOFと同じくREPL終了に至る(現在のツールループ実行中の中断とは別扱い)

### 実装上の補足 (Current behavior)

- プロンプトプロパティ(`repl.py:96-98`)はセッションIDを含まない固定値`"> "`を返すプロパティであり、動的な文字列生成は行わない。session_idを埋め込む`agent[:#N]>`形式の表記は現行コードに存在しない(Explicit in code — 2026-07-17時点で直接確認済み)。
- `CLIView.read_multiline()`の複数行継続入力は`... `プロンプトを表示するが、これは`read_multiline`内部の継続専用プロンプト文字列であり、REPLプロンプト自体を書き換えるものではない — 通常入力に戻れば再び固定値`"> "`が使われる。
- 入力待ち中の`KeyboardInterrupt`は入力内で捕捉され、`write_turn_end()`を出力した上で`None`を返す。呼び出し元ループは`None`を受けてループを`break`するため、**入力待ち中のCtrl-CはEOFと同様にREPLを終了させる**(現在行のみを中断してプロンプトに戻る挙動ではない)。根拠: `repl.py`の`_read_input`/`_repl_loop`。(Explicit in code)
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
