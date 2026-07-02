# Implementation: docs/05_agent_10_operations-and-observability.md — Add Minimal Agent DB Initialization section

**Plan source:** `plans/20260702-202930_plan.md` (Phase 2)
**Target file:** `docs/05_agent_10_operations-and-observability.md`

---

## Goal

Add a "Minimal Agent DB initialization" section to the operations doc so developers can initialize session.sqlite and workflow.sqlite from scratch (first-time local dev or after wiping databases) without reverse-engineering the codebase.

---

## Scope

**In:**
- New section "Minimal Agent DB Initialization" inserted before the existing "DB verification" subsection (near line 84 of the current file)
- Subsection: When to use (first-time local dev, after wiping session.sqlite or workflow.sqlite)
- Subsection: session.sqlite init command (PYTHONPATH=scripts uv run python inline script calling create_session_schema())
- Subsection: workflow.sqlite init command (same pattern, calling create_workflow_schema())
- Subsection: Table verification commands (sqlite3 .tables checks)
- Re-run safety note: IF NOT EXISTS guarantees idempotence
- workflow.sqlite conditional note: only required when workflow_db_path is configured
- Error context: OperationalError "no such table: sessions" indicates schema not initialized

**Out:**
- rag.sqlite initialization (handled separately by the RAG ingestion pipeline)
- eventbus.sqlite initialization
- sqlite-vec prerequisite documentation (get_embedding_dims() reads from config only — no sqlite-vec dependency at schema init time)
- Any changes to code files

---

## Assumptions

1. `get_embedding_dims()` in `scripts/db/store_protocols.py` calls `build_db_config().embedding_dims` which reads from config, not from the sqlite-vec extension — so sqlite-vec absence does not cause failure during `create_session_schema()` or `create_workflow_schema()` calls.
2. `create_session_schema()` and `create_workflow_schema()` use `IF NOT EXISTS` DDL and are idempotent; running them on an existing DB is safe.
3. `workflow.sqlite` is only required when `workflow_db_path` is set in the agent config; the section must note this conditionality.
4. The new section should sit inside the existing "DB verification" area (around line 75-93) so readers find init steps immediately before the verification commands.

---

## Implementation

### Target file

`docs/05_agent_10_operations-and-observability.md`

### Procedure

1. Open `docs/05_agent_10_operations-and-observability.md`.
2. Locate the line "### DB verification" (currently around line 74).
3. Insert the new "### Minimal Agent DB Initialization" section immediately before "### DB verification".
4. Confirm the inline Python heredoc commands are syntactically correct (copy from create_schema.py function names).
5. Confirm the sqlite3 `.tables` verification commands reference the correct DB paths.

### Method

Edit tool — insert new section text into the existing markdown file.

### Details

Insert the following block immediately before the `### DB verification` heading:

```markdown
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

Creates tables: `sessions`, `messages`, `tool_results`, `memories`, `memories_fts`, `memories_vec`, `session_diagnostics`.

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
# Expected: memories  memories_fts  memories_vec  messages  session_diagnostics  sessions  tool_results

sqlite3 /opt/llm/db/workflow.sqlite ".tables"
# Expected: approvals  artifacts  attempts  processed_events  tasks
```

#### Re-run safety

Both functions use `CREATE TABLE IF NOT EXISTS` — re-running against an existing DB is safe and applies only additive migration patches.

#### Error context

`sqlite3.OperationalError: no such table: sessions` on agent startup means session.sqlite schema has not been initialized. Run the `create_session_schema()` command above.
```

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Lint | ruff check docs/ | 0 errors (markdown, not Python — ruff skips .md) |
| Type check | mypy scripts/db/create_schema.py | no new errors |
| Tests | uv run pytest | all pass |
| Manual check | grep -n "Minimal Agent DB" docs/05_agent_10_operations-and-observability.md | Section found before "### DB verification" |
