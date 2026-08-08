---
title: "Agent CLI and Commands - CommandRegistry"
category: agent
tags:
  - agent
  - cli
  - command-registry
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_07_03_cli-and-commands-command-registry.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

すべてのスラッシュコマンドのディスパッチを担うCommandRegistryの責務と、モジュール間の責任分割について文書化する。

## Design Intent

### CommandRegistryの役割

`CommandRegistry`は`agent/commands/registry.py`にあり、すべてのスラッシュコマンドを`dispatch(line)`によってディスパッチする。

### 責任分割

| コンポーネント | 担当 | 担当しない |
|---|---|---|
| `command_defs.py` | `CommandDef`、`SubcommandSpec`データクラス | コマンドリスト |
| `command_defs_list.py` | 組み込みコマンド定義 | ディスパッチロジック |
| `registry.py` | ディスパッチの挙動、`command_defs_list`からコマンドリストをインポート | コマンドリストの定義 |

### 新規コマンド追加

`command_defs_list.py`に`CommandDef(...)`エントリを追加し、対応するハンドラを適切なmixinファイルに実装する。

## Responsibility Boundary

- `CommandRegistry`は**ディスパッチのみ**を担当する。コマンドの実装は個別のmixinクラスに分散される。
- `CommandRegistry.__init__`はfail-fastでhandler文字列の存在を検証する。

## Key Constraints

- 不明

## Operational Notes

- 不明

## Known Limitations

- `AgentREPL.SLASH_COMMANDS`（タブ補完用）と`command_defs_list._COMMANDS`（ディスパッチ用）は別々に保守されており、現在不一致がある。`SLASH_COMMANDS`には`/memory`, `/audit`, `/plan`, `/skill`, `/mdq`が含まれていないため、これらのコマンドはディスパッチは可能だがタブ補完の対象外になる。

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

CommandRegistry
responsibility boundary
known limitation
