---
title: "Agent CLI and Commands - CommandRegistry"
category: agent
tags:
  - agent
  - cli
  - command-registry
  - module-ownership
related:
  - 05_agent_00_document-guide.md
  - 05_agent_07_01_cli-and-commands-cli-reference.md
  - 05_agent_07_02_cli-and-commands-cliview.md
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

## CommandRegistry (`agent/commands/registry.py`)

すべてのスラッシュコマンドは`CommandRegistry.dispatch(line)`によってディスパッチされる。

検索順序:
1. 組み込みコマンドリストにおける完全一致またはプレフィックス一致
2. `@register_command`デコレータで登録されたプラグインコマンド(優先度は低い)

境界条件: `line == name`(完全一致)または`line.startswith(name + " ")`(プレフィックス一致)。

### モジュールの責務

| Module | Owns | Does NOT Own |
|--------|------|--------------|
| `command_defs.py` | `CommandDef`、`SubcommandSpec`データクラス | コマンドリスト |
| `command_defs_list.py` | 組み込みコマンド定義 | ディスパッチロジック |
| `registry.py` | ディスパッチの挙動、`command_defs_list`からコマンドリストをインポート | コマンドリストの定義 |

> **今後のコマンド追加:** `command_defs_list.py`にのみ新しい`CommandDef(...)`エントリを追加する。
> 対応するハンドラは適切なmixinファイルに実装すること。

---

## Related Documents

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
module ownership
