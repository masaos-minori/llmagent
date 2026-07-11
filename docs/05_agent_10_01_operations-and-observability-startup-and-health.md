---
title: "Agent Operations and Observability - Startup and Health"
category: agent
tags:
  - agent
  - operations
  - startup
  - health-probes
  - operational-verification
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 05_agent_10_03_operations-and-observability-workflow-observability.md
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# エージェントの運用と可観測性

- 設定 → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## Purpose(目的)

起動手順、運用確認、ヘルスチェック、監査ログ、
OTelトレーシング、`/context` と `/stats` の解釈、トラブルシューティングを文書化する。

---

## Startup Procedure(起動手順)

```bash
# 1. Deploy files (if changed)
cp -r scripts/agent   /opt/llm/scripts/agent
cp -r scripts/shared  /opt/llm/scripts/shared

# 2. Activate venv
source /opt/llm/venv/bin/activate

# 3. Start agent
cd /opt/llm/scripts && python -m agent
```

期待される起動バナー:
```
DB: 12,345 chunks | Tools: 14
Memory: disabled
Type /help for commands, Ctrl-C or Ctrl-D to exit.

agent[:#1]>
```

**Memoryの行:** `write_startup_banner()` が `memory_enabled != None` を受け取った場合のみ表示される。`repl.py` は常に `ctx.cfg.memory.use_memory_layer` を渡すため、この行は常に表示される — デフォルトは `disabled`、`use_memory_layer=True` の場合は `enabled`。

---

### Workflow Pending Approval Recovery

エージェント起動時に、前回のセッションで解決されなかった承認ゲート(つまり `/approve` も `/reject` も発行されなかったもの)が存在する場合、`startup.py` は保留中の承認状態を復元する:

- **タイミング:** 起動時、`ctx.workflow is not None` の場合
- **復元される内容:** `StateStore.find_latest_pending_approval()` を通じて `workflow.sqlite` から取得される最新のグローバルな保留中承認
- **複数セッション時の動作:** 保留中の承認は同時に1件のみ追跡される。全セッションを通じた最新のレコードが復元される(セッション固有ではない)
- **起動時警告の形式:** `[workflow] Pending approval from previous session — task=<task_id> approval=<approval_id> reason=<reason>. Use /approve [reason] or /reject [reason].`
- **確認方法:** `sqlite3 /opt/llm/db/workflow.sqlite "SELECT * FROM approvals WHERE status='pending' ORDER BY created_at DESC LIMIT 1;"`

---

## Operational Verification(運用確認)

### LLMサービスの確認

```bash
curl -s http://127.0.0.1:8001/v1/chat/completions -d '{"messages":[{"role":"user","content":"hi"}],"max_tokens":5}' -H 'Content-Type: application/json'
```

### 埋め込みサービスの確認

```bash
curl -s http://127.0.0.1:8003/health
```

### MCPサーバの状態

```
agent[:#1]> /mcp
```

期待される結果: すべてのサーバが `OK` ステータスで表示される。

### Minimal Agent DB Initialization(エージェントDBの最小初期化)

#### 使用場面

- 初めてのローカル開発時: session.sqlite と workflow.sqlite がまだ存在しない。
- いずれかのデータベースファイルを削除した後: スキーマが存在しない場合、起動時にエージェントが `OperationalError: no such table: sessions` を発生させる。

#### session.sqlite の初期化

```bash
PYTHONPATH=scripts uv run python - <<PY
from db.create_schema import create_session_schema
create_session_schema()
print("session schema OK")
PY
```

作成されるテーブル: `sessions`、`messages`、`memories`、`memories_fts`、`memories_vec`、`session_diagnostics`。

#### workflow.sqlite の初期化

エージェント設定で `workflow_db_path` が設定されている場合のみ必要。

```bash
PYTHONPATH=scripts uv run python - <<PY
from db.create_schema import create_workflow_schema
create_workflow_schema()
print("workflow schema OK")
PY
```

作成されるテーブル: `tasks`、`attempts`、`processed_events`、`artifacts`、`approvals`。

#### テーブルの検証

```bash
sqlite3 /opt/llm/db/session.sqlite  ".tables"
# Expected: memories  memories_fts  memories_vec  messages  session_diagnostics  sessions

sqlite3 /opt/llm/db/workflow.sqlite ".tables"
# Expected: approvals  artifacts  attempts  processed_events  tasks
```

#### 再実行の安全性

両関数とも `CREATE TABLE IF NOT EXISTS` を使用する — 既存のDBに対して再実行しても安全であり、追加的なマイグレーションパッチのみが適用される。

#### エラーの文脈

エージェント起動時の `sqlite3.OperationalError: no such table: sessions` は、session.sqliteのスキーマが初期化されていないことを意味する。上記の `create_session_schema()` コマンドを実行すること。

---

### DB verification(DBの検証)

検証すべき3つのプラットフォームデータベース:

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

3つすべてのスキーマ詳細: `90_shared_04_01_db_architecture_and_schema-overview-and-config.md`。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_10_02_operations-and-observability-audit-and-otel.md`
- `05_agent_10_03_operations-and-observability-workflow-observability.md`
- `05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md`
- `05_agent_10_05_operations-and-observability-monitoring.md`
- `05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`

## Keywords

startup procedure
operational verification
health probes
minimal agent db initialization
