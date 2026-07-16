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
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## CommandRegistry (`agent/commands/registry.py`)

すべてのスラッシュコマンドは`CommandRegistry.dispatch(line)`によってディスパッチされる。

検索順序:
1. 組み込みコマンドリストにおける完全一致またはプレフィックス一致
2. `@register_command`デコレータで登録されたプラグインコマンド(優先度は低い)

境界条件: `line == name`(完全一致)または`line.startswith(name + " ")`(プレフィックス一致)。

`dispatch(line)`は`line`が`str`でなければ`TypeError`を送出し、空文字列は`False`を返す(未マッチ扱い)。組み込みコマンド(`_COMMANDS`)で一致しない場合、`_dispatch_plugin(line)`に処理を委譲し、`shared.plugin_registry.iter_commands()`に登録済みのプラグインコマンド(完全一致・プレフィックス一致の両方に対応)を順に試す。根拠: `agent/commands/registry.py`。(Explicit in code)

`CommandRegistry.__init__`は、`_COMMANDS`内の全`CommandDef.handler`文字列が実際に`self`上に存在するかをfail-fastで検証し、存在しなければ`AttributeError`を送出する。(Explicit in code)

### モジュールの責務

| Module | Owns | Does NOT Own |
|--------|------|--------------|
| `command_defs.py` | `CommandDef`、`SubcommandSpec`データクラス | コマンドリスト |
| `command_defs_list.py` | 組み込みコマンド定義 | ディスパッチロジック |
| `registry.py` | ディスパッチの挙動、`command_defs_list`からコマンドリストをインポート | コマンドリストの定義 |

`CommandRegistry`は15個のmixinクラス(`_SessionMixin`, `_McpMixin`, `_ConfigMixin`, `_ContextMixin`, `_ToolingMixin`, `_DebugMixin`, `_AuditMixin`, `_RagExportMixin`, `_MemoryMixin`, `_WorkflowMixin`, `_PluginsMixin`, `_MdqMixin`, `_SkillMixin`, `_ConfigDisplayMixin`, `_ConfigStatsMixin`)を多重継承する。各mixinは対応する`agent/commands/cmd_*.py`ファイルに実装される。(Explicit in code)

> **今後のコマンド追加:** `command_defs_list.py`にのみ新しい`CommandDef(...)`エントリを追加する。
> 対応するハンドラは適切なmixinファイルに実装すること。

### 境界条件 (Boundary and ownership)

- `AgentREPL.SLASH_COMMANDS`(`agent/repl.py`、タブ補完用の一覧)と`command_defs_list._COMMANDS`(ディスパッチ用の正本)は別々に保守されているリストであり、現状一致していない。`SLASH_COMMANDS`には`/memory`, `/audit`, `/plan`, `/plugin`, `/skill`, `/mdq`が含まれていない。そのためこれらのコマンドはディスパッチは可能だがタブ補完の対象外になる。(Explicit in code。矛盾点として明記)

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
