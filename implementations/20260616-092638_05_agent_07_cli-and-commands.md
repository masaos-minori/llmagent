# 07 CLI and Commands — Agent Documentation Restructuring

## Goal
CLIViewの表示API・スラッシュコマンド体系・CommandRegistryの仕組みを1章にまとめる。

## Scope
- CLIView の Writer/Reader プロトコルと主要メソッド
- CommandRegistry によるコマンド登録・ディスパッチ
- 全13スラッシュコマンドの概要

## Assumptions
- 05_ref-agent-view.md が CLIView と Writer/Reader の正典
- 05_ref-agent-commands.md が CommandRegistry と13コマンドミックスインの正典
- 05_agent.md §3 のスラッシュコマンド一覧を補足として使用
## Implementation

### Target file
`docs/05_agent/07_cli-and-commands.md`

### Procedure
- 05_ref-agent-view.md 全体から CLIView クラス、Writer/Reader プロトコル定義を抽出
- 05_ref-agent-view.md のコールバック定義を抽出
- 05_ref-agent-commands.md の CommandRegistry クラスと登録APIを抽出
- 05_ref-agent-commands.md の13コマンドミックスイン名と用途を全件抽出
- 05_agent.md §3 でコマンド名と動作の対応を確認
### Method
- H2: CLIView概要 / Writer・Readerプロトコル / CommandRegistry / コマンド一覧
- Writer/Readerのメソッドは「名前(シグネチャ) — 説明」形式
- コマンド一覧は「/コマンド名 — 用途(1行)」の箇条書き
### Details
- CLIView: print_message(), stream_delta(), show_tool_call(), prompt_approval() の主要メソッド
- Writer: write(), write_stream() / Reader: readline(), read_char() のプロトコル
- コールバック: on_turn_start, on_turn_end, on_tool_approval_request
- CommandRegistry: register(), dispatch(), list_commands()
- 13コマンド: /help, /exit, /clear, /history, /config, /session, /tools, /model, /system, /compact, /export, /import, /debug

## Validation plan
- 05_ref-agent-view.mdに記載のWriter/Readerプロトコルメソッドが完全に記述されていること
- 13コマンドが05_ref-agent-commands.mdの全ミックスインと一致していること
- CommandRegistryのAPIが05_ref-agent-commands.mdと一致していること
