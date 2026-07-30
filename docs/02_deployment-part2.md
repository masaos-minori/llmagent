---
title: "Deployment Guide (Part 2)"
category: deployment
tags:
  - deployment
  - environment
  - setup
related:
  - 01_overview.md
source:
  - 02_deployment-part1.md
---

# 導入手順・デプロイ

## 3. DB 初期化

### 3.0 Platform DB overview

The agent uses four SQLite databases. Three have explicit path keys in
`agent.toml`; `workflow_db_path` has no literal entry there and falls back to
`DbConfig`'s Python-level default (`scripts/db/config.py`).

| DB | Default path | Config key | Purpose |
|---|---|---|---|
| `rag.sqlite` | `/opt/llm/db/rag.sqlite` | `rag_db_path` | RAG documents, chunks, embeddings |
| `session.sqlite` | `/opt/llm/db/session.sqlite` | `session_db_path` | Agent sessions, messages |
| `workflow.sqlite` | `/opt/llm/db/workflow.sqlite` | `workflow_db_path` (code default; no `agent.toml` entry) | Task tracking, event processing |
| `eventbus.sqlite` | `/opt/llm/db/eventbus.sqlite` | `eventbus_db_path` | Event Bus records |

Schema details: `90_shared_04_01_db_architecture_and_schema-overview-and-config.md`

### 3.1 スキーマ適用

```bash
bash deploy/init_db.sh
```

**init_db.sh の責務:**
- `workflow.sqlite` と 5つの必須テーブル（tasks, attempts, processed_events, artifacts, approvals）を作成
- インクリメンタルスキーママイグレーションを適用（冪等性あり）
- 全5テーブルが存在することを確認、いずれか欠如時は中止
- スキーマバージョンを記録

### 3.2 デプロイメントチェックリスト

- [ ] `config/workflows/default.json` が存在する
- [ ] `deploy.sh` が正常終了（[FATAL]なし）
- [ ] `init_db.sh` が全5テーブルと正しいスキーマバージョンを報告
- [ ] `setup_services.sh` がプリフライトチェックに合格

### 3.3 失敗モード

| 症状 | 失敗スクリプト | 対処法 |
|---|---|---|
| `[FATAL] Missing required workflow definition` | deploy.sh | config/workflows/default.json を追加 |
| `[FATAL] Invalid workflow definition` | deploy.sh | JSONバリデーションエラーを修正 |
| `[FATAL] Checksum does not match source` | deploy.sh | deploy.sh を再実行、ディスク異常を確認 |
| `[FATAL] Schema is missing or incomplete` | init_db.sh / setup_services.sh | init_db.sh を再実行 |
| `[FATAL] Schema version mismatch` | setup_services.sh | init_db.sh でマイグレーション適用 |

For detailed diagnosis and recovery commands per failure mode, see [Workflow Deployment Runbook](05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md#workflow-deployment-runbook).

このデプロイメント要件がなぜ必須なのか(監査・回復・承認状態の永続化という設計判断)については
[ADR-Workflow-Mandatory](05_agent_03_03_turn-processing-flow-workflow-engine-part1.md#ワークフロー実行必須化-adr-workflow-mandatory)を参照。

## Related Documents

- `01_overview.md`
- `02_deployment-part1.md`
- `05_agent_03_03_turn-processing-flow-workflow-engine-part1.md`

## Keywords

deployment
environment
setup
installation
llama-cpp
sqlite-vec
db-initialization

### DB Path Reference (auto-generated)

<!-- AUTO-GENERATED: gen_deployment_reference.py db-path-reference -->
Generated from `scripts/db/config.py` and `config/agent.toml`. Do not hand-edit between the guard comments; run `python tools/gen_deployment_reference.py` to refresh.

| DB | Default path | Config key | Set in `agent.toml`? |
|---|---|---|---|
| `eventbus.sqlite` | `/opt/llm/db/eventbus.sqlite` | `eventbus_db_path` | Yes |
| `rag.sqlite` | `/opt/llm/db/rag.sqlite` | `rag_db_path` | Yes |
| `session.sqlite` | `/opt/llm/db/session.sqlite` | `session_db_path` | Yes |
| `workflow.sqlite` | `/opt/llm/db/workflow.sqlite` | `workflow_db_path` | No (Python-level default in `scripts/db/config.py`) |
<!-- END AUTO-GENERATED -->
