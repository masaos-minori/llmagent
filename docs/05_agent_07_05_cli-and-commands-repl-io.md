---
title: "Agent CLI and Commands - REPL Input/Output Model"
category: agent
tags:
  - agent
  - cli
  - repl-io
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_07_05_cli-and-commands-repl-io.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

REPL入出力モデルの設計意図と運用判断を文書化する。

## Design Intent

### REPL入出力モデル

- **プロンプト:** `> `(固定文字列)
- **通常の入力:** 任意のテキスト → `Orchestrator.handle_turn()`に転送される
- **スラッシュコマンド:** `/`で始まる行 → `CommandRegistry.dispatch(line)`
- **複数行入力:** `\`で終わる行 → `... `プロンプトで継続
- **EOF / Ctrl-D:** 正常なシャットダウン(REPL入力がNoneを返しループを抜ける)
- **Ctrl-C:** 入力内で捕捉され、入力待ち中はEOFと同じくREPL終了に至る(現在の実装ではツールループ実行中の中断とは別扱い)

### 実装上の補足

- プロンプトはセッションIDを含まない固定値`"> "`を返すプロパティであり、動的な文字列生成は行わない。session_idを埋め込む`agent[:#N]>`形式の表記は現行コードに存在しない。
- `CLIView.read_multiline()`の複数行継続入力は`... `プロンプトを表示するが、これはread_multiline内部の継続専用プロンプト文字列であり、REPLプロンプト自体を書き換えるものではない。通常入力に戻れば再び固定値`"> "`が使われる。
- 入力待ち中のKeyboardInterruptは入力内で捕捉され、write_turn_end()を出力した上でNoneを返す。呼び出し元ループはNoneを受けてループをbreakするため、**入力待ち中のCtrl-CはEOFと同様にREPLを終了させる**(現在行のみを中断してプロンプトに戻る挙動ではない)。
- SIGTERM受信時はshutdown_requestedと_shutdown_eventをセットし、実行中のターンを最大10秒(_GRACEFUL_TIMEOUT)待ってから強制終了する(グレースフルシャットダウン)。
- `/exit`は_should_exit()で判定され、shutdown_requestedが立っている場合も同メソッドでループ終了と判定される。

## Responsibility Boundary

- `AgentREPL`は薄いコーディネータであり、ターン処理はorchestratorに、スラッシュコマンドのディスパッチはCommandRegistryに、端末I/OはCLIViewに委譲される。

## Key Constraints

- プロンプトは固定文字列`"> "`であり、セッションIDやステータスを動的に表示しない。
- 入力待ち中のCtrl-Cは現在行を中断するのではなくREPL全体を終了させる。

## Operational Notes

- 複数行入力の継続プロンプトは`... `であり、REPLプロンプトとは異なる。
- グレースフルシャットダウンのタイムアウトは10秒。

## Known Limitations

- 不明

## Related Docs

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
