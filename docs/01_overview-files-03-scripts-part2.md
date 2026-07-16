---
title: "Scripts File Structure: Agent Commands (Part 2/5)"
category: overview
tags:
  - scripts
  - agent
  - mcp-server
  - file-structure
related:
  - 01_overview-files-03-scripts-part1.md
  - 01_overview-files-03-scripts-part3.md
  - 01_overview-files-03-scripts-part4.md
  - 01_overview-files-03-scripts-part5.md
  - 01_overview.md
---


# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:


```
│   │   ├─ commands/
│   │   │   └─ __init__.py                  # commands パッケージ初期化
│   │   │   ├─ registry.py                  # CommandRegistry: スラッシュコマンドディスパッチャ (14 mixins)
│   │   │   ├─ command_defs.py              # CommandDef / SubcommandSpec データクラス (データクラス定義のみ; _COMMANDS は持たない)
│   │   │   ├─ command_defs_list.py         # _COMMANDS: 全組み込みスラッシュコマンドの単一ソース (コマンド追加はここへ)
│   │   │   ├─ mixin_base.py                # MixinBase: 全 mixin の共通基底クラス
│   │   │   ├─ output_port.py               # OutputPort / CliOutputPort: コマンド出力インタフェース
│   │   │   ├─ enums.py                     # コマンド列挙型
│   │   │   ├─ exceptions.py                # コマンド例外定義
│   │   │   ├─ models.py                    # コマンドデータモデル
│   │   │   ├─ utils.py                     # コマンドユーティリティ
│   │   │   ├─ cmd_session.py               # /session コマンド (_SessionMixin)
│   │   │   ├─ cmd_mcp.py                   # /mcp コマンド (_McpMixin)
│   │   │   ├─ cmd_config.py                # /config, /reload コマンド (_ConfigMixin)
│   │   │   ├─ cmd_config_display.py        # /config 表示 (_ConfigMixin)

│   │   │   ├─ cmd_config_stats.py          # /stats コマンド (_ConfigMixin)
│   │   │   ├─ cmd_context.py               # /context, /clear, /undo, /history, /system コマンド (_ContextMixin)

│   │   │   ├─ cmd_tooling.py               # /tool, /plan コマンド (_ToolingMixin)
│   │   │   ├─ cmd_debug.py                 # /debug コマンド (_DebugMixin)
│   │   │   ├─ cmd_audit.py                 # /audit コマンド (_AuditMixin)
│   │   │   ├─ cmd_rag_export.py            # /rag, /export, /compact コマンド (_RagExportMixin)
│   │   │   ├─ cmd_memory.py                # /memory コマンド (_MemoryMixin)
│   │   │   ├─ cmd_mdq.py                   # /mdq コマンド (_MdqMixin): status/index/refresh/search/outline/get/grep
│   │   │   ├─ cmd_plugins.py               # /plugin コマンド (_PluginsMixin): プラグインロード状態表示
│   │   │   ├─ cmd_workflow.py              # /approve, /reject コマンド (_WorkflowMixin)
│   │   │   ├─ cmd_skill.py                 # /skill コマンド (_SkillMixin): SKILL.md を一時的な ephemeral system context として注入
│   │   │   ├─ db_help_display.py           # DB ヘルプ表示
│   │   │   ├─ db_session_ops.py            # セッション DB 操作
│   │   │   ├─ db_stats_display.py          # DB ステータス表示
│   │   │   ├─ db_rag_ops.py                # RAG DB 操作ハンドラ (clean, list_urls, rebuild_fts, vec_rebuild, reconcile_url, recover, consistency)
│   │   │   ├─ memory_data_ops.py           # メモリデータ操作 (list, search, show, pin, delete, prune)
│   │   │   ├─ memory_rebuild_ops.py        # メモリ再構築操作 (rebuild, rebuild-fts, rebuild-vec, check-consistency)
│   │   │   ├─ memory_status.py             # メモリレイヤー状態表示ロジック (MemoryStatus dataclass)
│   │   │   ├─ session_title.py             # セッションタイトル生成ロジック (LLM-based with fallback)
│   │   │   └─ token_display.py             # トークンカウント表示ロジック (TokenDisplay mixin)
```

## Related Documents

- `01_overview-files-03-scripts-part1.md`
- `01_overview-files-03-scripts-part3.md`
- `01_overview-files-03-scripts-part4.md`
- `01_overview-files-03-scripts-part5.md`

## Keywords

scripts
agent
mcp-server
file-structure
