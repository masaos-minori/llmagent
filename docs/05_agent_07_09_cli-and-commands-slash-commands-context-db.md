---
title: "Agent CLI and Commands - Slash Commands: Context, Plan"
category: agent
tags:
  - agent
  - cli
  - slash-commands
  - context
  - plan
related:
  - 05_agent_00_document-guide.md
  - 05_agent_07_01_cli-and-commands-cli-reference.md
  - 05_agent_07_02_cli-and-commands-cliview.md
  - 05_agent_07_03_cli-and-commands-command-registry.md
  - 05_agent_07_04_cli-and-commands-purpose.md
  - 05_agent_07_05_cli-and-commands-repl-io.md
  - 05_agent_07_06_cli-and-commands-hot-reload.md
  - 05_agent_07_07_cli-and-commands-migration-notes.md
  - 05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md
  - 05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md
  - 05_agent_07_11_cli-and-commands-slash-commands-memory-other.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

### Contextカテゴリ

| Command | 副作用 | 関連する状態 |
|---|---|---|
| `/context` | なし | 履歴サイズ、バジェット、システムプロンプト、ワークフローモード、承認待ち状態を表示 |
| `/compact` | LLM呼び出し(圧縮) | 履歴を即座に圧縮 |
| `/system [name]` | `history[0]`を更新 | `ctx.conv.system_prompt_name` |

### Planカテゴリ

| Command | 副作用 | 関連する状態 |
|---|---|---|
| `/plan` | なし | `ctx.conv.plan_mode`をトグル |

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

context category
plan category
