---
title: "Agent CLI and Commands - Slash Commands: Memory, MDQ, Other"
category: agent
tags:
  - agent
  - cli
  - slash-commands
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_07_11_cli-and-commands-slash-commands-memory-other.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

Memory、MDQ、Skillカテゴリのスラッシュコマンドの目的と副作用について文書化する。

## Design Intent

### Memoryカテゴリ

長期記憶に関するコマンド群。`/memory rebuild`はJSONLから全メモリをDELETE + INSERTする（JSONLが正典のソース）。

### MDQカテゴリ

すべての/mdqコマンドは、エージェントのツールエグゼキュータ経由でmdq-mcpのMCPツール（ポート8013）を呼び出す。MDQは`mdq.sqlite`（`rag.sqlite`とは別）を使用する。MDQとRAGの使い分けについては[MDQ vs RAG Boundary](04_mcp_05_04_mdq-rag-boundary.md#mdq-vs-rag-boundary)を参照。

### Skillカテゴリ

`/skill`は`skills/`配下のディレクトリ名一覧を表示する（LLM呼び出しは発生しない）。

`/skill <name> [args]`は`skills/<name>/SKILL.md`の内容が次のLLMターンに渡される。同一セッション内で再実行すると前回分は置き換わる。

**既知の制限:** `_cmd_skill()`が構築するメッセージは`_ephemeral: True`と`_skill_ephemeral: True`を同時に持つが、`TRUSTED_SOURCES["skill_mixin"]`は`_skill_ephemeral`のみを認可するため、`append_message()`の検証に失敗し`_ephemeral`キーはサニタイズ（除去、`warning`ログ）されてから保存される。結果として`_skill_ephemeral: True`のみがhistoryに残る。これは既知かつ許容された挙動変更であり、影響はorchestratorの汎用的な`_ephemeral`ベースの前ターンクリアがスキル注入メッセージを次ターン開始時に自動除去しなくなる点にある。

### Otherカテゴリ

`/help`はこのヘルプ出力を表示する。

## Responsibility Boundary

- **Memory**: 長期記憶のエントリ管理
- **MDQ**: ドキュメントインデックスと検索
- **Skill**: スキル注入
- **Other**: ヘルプ表示

## Key Constraints

- 不明

## Operational Notes

- 不明

## Known Limitations

- `/skill`のephemeralメッセージは`_skill_ephemeral: True`のみがhistoryに残る

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`

## Keywords

memory category
mdq category
skill category
