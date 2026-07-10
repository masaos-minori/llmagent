---
title: "Agent Operations and Observability"
category: agent
tags:
  - agent
  - agent
  - operations
  - observability
  - monitoring
related:
  - 05_agent_00_document-guide.md
---

# Agent Operations and Observability

ploy files (if changed)
cp -r scripts/agent   /opt/llm/scripts/agent
cp -r scripts/shared  /opt/llm/scripts/shared

# 2. Activate venv
source /opt/llm/venv/bin/activate

# 3. Start agent
cd /opt/llm/scripts && python -m agent
```

Expected startup banner:
```
DB: 12,345 chunks | Tools: 14
Memory: disabled
Type /help for commands, Ctrl-C or Ctrl-D to exit.

agent[:#1]>
```

**Memory line:** Present only when `write_startup_banner()` receives `memory_enabled != None`. Since `repl.py` always passes `ctx.cfg.memory.use_memory_layer`, this line is always shown — `disabled` by default, `enabled` when `use_memory_layer=True`.

---

### Workflow Pending Approval Recovery

When the agent starts and a previous session had an approval gate that was not resolved (i.e., `/approve` or `/reject` was never issued), `startup.py` recovers the pending approval state:

- **When:** During startup, if `ctx.workflow is not None`
- **What is recovered:** The latest global pending approval from `workflow.sqlite` via `StateStore.find_latest_pending_approval()`
- **Multi-session behavior:** Only one pending approval is tracked at a time; the latest record across all sessions is restored (not session-specific)
- **Startup warning format:** `[workflow] Pending approval from previous session — task=<task_id> approval=<approval_id> reason=<reason>. Use /approve [reason] or /reject [reason].`
- **How to inspect:** `sqlite3 /opt/llm/db/workflow.sqlite "SELECT * FROM approvals WHERE status='pending' ORDER BY created_at DESC LIMIT 1;"`

---

## Operational Verification

### LLM 

service check

```bash
curl -s http://127.0.0.1:8001/v1/chat/completions -d '{"messages":[{"role":"user","content":"hi"}],"max_tokens":5}' -H 'Content-Type: application/json'
```

### Embedding service check

```bash
curl -s http://127.0.0.1:8003/health
```

### MCP server status

```
agent[:#1]> /mcp
```

Expected: all servers listed with `OK` status.

### Minimal Agent DB Initialization

#### When to use

- First-time local development: session.sqlite and workflow.sqlite do not exist yet.
- After wiping either database file: the agent raises `OperationalError: no such table: sessions` on startup if the schema is absent.

#### Initialize session.sqlite

```bash
PYTHONPATH=scripts uv run python - <<PY
from db.create_schema import create_session_schema
create_session_schema()
print("session schema OK")
PY
```

Creates tables: `sessions`, `messages`, `memories`, `memories_fts`, `memories_vec`, `session_diagnostics`.

#### Initialize workflow.sqlite

Only required when `workflow_db_path` is configured in the agent config.

```bash
PYTHONPATH=scripts uv run python - <<PY
from db.create_schema import create_workflow_schema
create_workflow_schema()
print("workflow schema OK")
PY
```

Creates tables: `tasks`, `attempts`, `processed_events`, `artifacts`, `approvals`.

#### Verify tables

```bash
sqlite3 /opt/llm/db/session.sqlite  ".tables"
# Expected: memories  memories_fts  memories_vec  messages  session_diagnostics  sessions

sqlite3 /opt/llm/db/workflow.sqlite ".tables"
# Expected: approvals  artifacts  attempts  processed_events  tasks
```

#### Re-run safety

Both functions use `CREATE TABLE IF NOT EXISTS` — re-running against an existing DB is safe and applies only additive migration patches.

#### Error context

`sqlite3.OperationalError: no such table: sessions` on agent startup means session.sqlite schema has not been initialized. Run the `create_session_schema()` command above.

---

### DB verification

Three platform databases to verify:

```bash
# rag.sqlite — RAG documents, chunks, embeddings
sqlite3 /opt/llm/db/rag.sqlite "SELECT lang, COUNT(*) AS docs FROM documents GROUP BY lang;"
sqlite3 /opt/llm/db/rag.sqlite "SELECT COUNT(*) AS chunks FROM chunks;"
sqlite3 /opt/llm/db/rag.sqlite "SELECT chunk_id, LENGTH(embedding) AS bytes FROM chunks_vec LIMIT 3;"
# Expected bytes: 1536 (384 dimensions × 4 bytes)

# session.sqlite — agent sessions and messages
sqlite3 /opt/llm/db/session.sqlite "SELECT session_id, created_at, title FROM sessions ORDER BY session_id DESC LIMIT 5;"
sqlite3 /opt/llm/db/session.sqlite "SELECT COUNT(*) AS messages FROM messages;"

# workflow.sqlite — task tracking and event processing
sqlite3 /opt/llm/db/workflow.sqlite "SELECT COUNT(*) AS tasks FROM tasks;"
sqlite3 /opt/llm/db/workflow.sqlite "SELECT status, COUNT(*) FROM tasks GROUP BY status;"
```

Schema details for all three: `90_shared_04_db_overview_and_config.md`.

---

## Health Probes

`check_readiness()`

## Related Documents

- `agent`
- `operations`
- `observability`

## Keywords

agent
operations
observability
monitoring
