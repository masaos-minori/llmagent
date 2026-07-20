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

The agent uses three SQLite databases. All paths are configured in `agent.toml`.

| DB | Default path | Config key | Purpose |

| `rag.sqlite` | `/opt/llm/db/rag.sqlite` | `rag_db_path` | RAG documents, chunks, embeddings |
| `session.sqlite` | `/opt/llm/db/session.sqlite` | `session_db_path` | Agent sessions, messages |
| `workflow.sqlite` | `/opt/llm/db/workflow.sqlite` | `workflow_db_path` | Task tracking, event processing |

Schema details: `90_shared_04_01_db_architecture_and_schema-overview-and-config.md`

### 3.1 Applying schema

```bash
bash deploy/init_db.sh

Verify tables (chunks  chunks_fts  chunks_vec  documents)
```

**Workflow schema responsibilities (init_db.sh):**
- Creates `workflow.sqlite` and its required tables (`tasks`, `attempts`, `processed_events`, `artifacts`, `approvals`) via `create_workflow_schema()`
- Applies incremental schema migrations (idempotent — safe to re-run)
- Verifies all 5 required tables exist after initialization; aborts if any are missing
- Records the current workflow schema version in `workflow_schema_version`

### 3.2 Workflow deployment checklist

- [ ] `config/workflows/default.json` exists in the repository before running `deploy.sh`
- [ ] `bash deploy/deploy.sh` completes with a printed workflow Name/Version/Stages/SHA256 block and no `[FATAL]` errors
- [ ] `bash deploy/init_db.sh` reports all 5 workflow tables present and the expected schema version recorded
- [ ] `bash deploy/setup_services.sh` passes its pre-flight workflow checks before any service starts

### 3.3 Workflow deployment failure modes

| Symptom | Failing script | Remediation |
|---|---|---|
| `[FATAL] Missing required workflow definition` | `deploy.sh` | Add `config/workflows/default.json` to the repository before deploying |
| `[FATAL] Invalid workflow definition ...` | `deploy.sh` | Fix the JSON per the printed validation error (missing field, duplicate stage ID, invalid retry policy, etc.) |
| `[FATAL] Deployed workflow definition checksum does not match source` | `deploy.sh` | Re-run `deploy.sh`; investigate why the copy was not byte-identical (disk/filesystem issue) |
| `[FATAL] Workflow database schema is missing or incomplete` | `init_db.sh` or `setup_services.sh` | Run `bash deploy/init_db.sh` to (re-)create the workflow schema |
| `[FATAL] Workflow schema version mismatch` | `setup_services.sh` (or `RuntimeError` at agent startup) | Run `bash deploy/init_db.sh` to apply pending migrations and record the current version |

For detailed diagnosis and recovery commands per failure mode, see [Workflow Deployment Runbook](05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md#workflow-deployment-runbook).

## Related Documents

- `01_overview.md`
- `02_deployment-part1.md`

## Keywords

deployment
environment
setup
installation
llama-cpp
sqlite-vec
db-initialization
