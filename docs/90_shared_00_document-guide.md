---
title: "Shared/DB Documentation Guide"
category: shared
tags:
  - shared
  - db
  - documentation
  - guide
  - routing
  - ai reference
related:
  - 90_shared_90_inconsistencies_and_known_issues.md
source:
  - 90_shared_00_document-guide.md
---

# Shared/DB Documentation Guide

再構成された `shared/` および `db/` レイヤードキュメントのエントリポイント。
どの章を開くべきか判断するため、まずこのファイルを読むこと。

---

## Purpose of This Document Set

`shared/`レイヤー(共通型、設定、ロギング、OTel、ツールルーティング)と`db/`レイヤー(SQLite接続管理、スキーマ、ストアプロトコル、メンテナンス)をドキュメント化。

---

## Recommended Reading Order (Human)

``` text
01 Overview → 02 Types and Protocols → 03 Runtime and Execution
  → 04 DB Architecture/Schema → 05 DB API and Operations → 90 Inconsistencies
```

---

## AI Query Routing

| 質問 | 参照先 |
|---|---|
| `shared/`の用途・インポートルール | `01_overview` / `01_constraints` |
| 型定義、ツール定数 | `02_core-types` / `02_reference` |
| ConfigLoader, ロギング | `03_config-and-logging` |
| ToolExecutor, LLMClient | `03_tool-executor` / `03_llm-and-mcp-clients` |
| スキーマ、マイグレーション | `04_overview` / `04_schema` / `04_migration` |
| モジュール境界、プロトコル | `05_module-boundaries` / `05_protocol` |
| メンテナンス、復旧 | `05_maintenance` / `05_recovery` |
| 既知の問題 | `90_inconsistencies` |
---

## Navigation to Major Known Issues

既知の不整合の全カタログは [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) を参照(現時点でオープンな項目はない)。`ArtifactEvent`にイベントバスがない点は対象外(データ定義のみ)。

---

## Canonical Source Rules

- `06_spec_shared.md` / `07_ref-sqlite.md` / `07_spec_db.md` / `90_shared.md` は削除済みのレガシーソースであり、その内容は上記の `90_shared_02_*` から `90_shared_05_*` の各ファイルに存在する
- ソースファイル間で内容が矛盾する場合は、新しい再構成後のファイルを信頼すること（すべての不一致については `90_shared_90` を参照）

---

## File Index

shared/ ドキュメント群は `01_overview` → `02_types` → `03_runtime` の順に読み進める。db/ ドキュメント群は `04_schema` → `05_operations` の順に読む。(Explicit in code)

---

## Governance

Cross-cutting documentation rules and policies:

- [Documentation Governance](00_governance_01_documentation-governance.md)
- [Canonical Source Rule](00_governance_02_canonical-source-rule.md)
- [Evidence Labels](00_governance_03_evidence-labels.md)
- [Known Issues Template](00_governance_04_known-issues-template.md)
- [Deprecated Items](00_governance_05_deprecated-items.md)
- [AI Reading Metadata](00_governance_06_ai-reading-metadata.md)
- [Terminology Glossary](00_governance_09_terminology-glossary.md)

## Guidance for Safe AI Use

1. `load_all()`は`agent.toml`のみを含む(`_BASE_CONFIG_FILES = ("agent.toml",)`、詳細`90_shared_03_01`§2a)。`rag_pipeline.toml`という設定ファイルは存在しない — 各MCPサーバー(rag-pipeline-mcp含む)はプロセス分離方針により自身の`config/<key>_mcp_server.toml`のみを個別にロードし、エージェント側で明示ロードする必要はない(Explicit in code)。
2. `orjson.dumps()`は`bytes`を返す(要`.decode()`)。
3. `ArtifactEvent` はデータのみでイベントバスは存在しない。
4. `LLMMessage` は7フィールド(`importance`/`pinned`含む。旧`90_shared.md`の5ではない)。
5. DBトリガーが `chunks_fts` を自動同期するため手動INSERT禁止。
6. `SQLiteHelper("workflow")`は有効(`90_shared_04_01`参照)。
7. `LLMClient`詳細は`05_agent_05_llm-and-streaming.md`参照(本書対象外)。


