# Implementation: Fix deploy/init_db.sh PYTHONPATH and table validation

## Goal

Fix `deploy/init_db.sh` so that it correctly initializes all three SQLite schemas (rag, session, workflow) by correcting the PYTHONPATH variable reference and adding explicit table-level validation for all expected tables.

## Scope

- **In-Scope**:
  - `deploy/init_db.sh`: fix PYTHONPATH variable reference, add session.sqlite table checks, include `approvals` in workflow table checks
- **Out-of-Scope**:
  - `scripts/db/create_schema.py` (canonical logic is correct, no changes needed)
  - `scripts/db/schema_sql.py` (DDL is correct)
  - Any Python source files
  - DB migration logic

## Assumptions

- `deploy/deploy.sh` has already been run before `init_db.sh`, so `/opt/llm/scripts/` directory exists with all packages
- The production venv is at `/opt/llm/venv/` and `uv` is available at runtime
- `sqlite3` CLI is available on the deployment host
- `create_schema.py` is invoked as `python -m db.create_schema` or via direct path with correct PYTHONPATH
- The `uv run` command in `/opt/llm/` context resolves dependencies from the deployed `pyproject.toml` and `uv.lock`

## Unknowns & Gaps

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? |
|---|---|---|---|---|
| UNK-01 | Whether `uv run python /path/to/create_schema.py` vs `uv run python -m db.create_schema` is the correct invocation pattern at `/opt/llm` | No live environment to test; deploy.sh shows scripts are rsynced to `/opt/llm/scripts/` keeping package structure | Inspect existing working deploy and check how other scripts are invoked; the module form is safer given package imports in create_schema.py | No — module invocation form is determinable from the import structure |

## Verification Results

### 1. PYTHONPATH bug confirmed
- **File**: `deploy/init_db.sh:11`
- **Code**: `DEPLOY_SCRIPTS="/opt/llm/scripts/db"`
- **Problem**: PYTHONPATH points to `/opt/llm/scripts/db` but `create_schema.py` uses `from db.helper import ...` which requires `/opt/llm/scripts` (the parent of `db/`) on PYTHONPATH

### 2. deploy.sh comparison
- **File**: `deploy/deploy.sh:13`
- **Code**: `DEPLOY_SCRIPTS="/opt/llm/scripts"` — correct, points to package root

### 3. Session schema tables verification
- **File**: `scripts/db/schema_sql.py:67-138`
- `_SESSION_SCHEMA_TEMPLATE` contains: `sessions`, `messages`, `tool_results`, `memories`, `memories_fts`, `memory_links`, `session_diagnostics`, `memories_vec`
- No `notes` table exists — current comment in init_db.sh incorrectly lists `notes`

### 4. Workflow schema tables verification
- **File**: `scripts/db/schema_sql.py:151-200`
- `_WORKFLOW_SCHEMA` contains: `tasks`, `attempts`, `processed_events`, `artifacts`, `approvals`
- Current comment in init_db.sh is correct — no change needed

### 5. Path resolution after fix
- After changing DEPLOY_SCRIPTS to `/opt/llm/scripts`:
  - PYTHONPATH = `/opt/llm/scripts` ✓ (correct for `from db.helper import ...`)
  - File check: `${DEPLOY_SCRIPTS}/db/create_schema.py` = `/opt/llm/scripts/db/create_schema.py` ✓
  - Python invocation: `"${DEPLOY_SCRIPTS}/db/create_schema.py"` = `/opt/llm/scripts/db/create_schema.py` ✓

## Implementation

### Target file: `deploy/init_db.sh`

#### Procedure

Apply all changes from Phase 2 of the plan to deploy/init_db.sh.

#### Method

Direct file edit — multiple targeted replacements.

#### Details

**Change 1: Fix DEPLOY_SCRIPTS variable (line 11)**
```bash
# Before:
DEPLOY_SCRIPTS="/opt/llm/scripts/db"
# After:
DEPLOY_SCRIPTS="/opt/llm/scripts"
```

**Change 2: Update existence check path (line 17)**
```bash
# Before:
if [ ! -f "${DEPLOY_SCRIPTS}/create_schema.py" ]; then
# After:
if [ ! -f "${DEPLOY_SCRIPTS}/db/create_schema.py" ]; then
```

**Change 3: Update error message path (line 18)**
```bash
# Before:
echo "エラー: create_schema.py が見つかりません: ${DEPLOY_SCRIPTS}/create_schema.py"
# After:
echo "エラー: create_schema.py が見つかりません: ${DEPLOY_SCRIPTS}/db/create_schema.py"
```

**Change 4: Update python invocation (line 28)**
```bash
# Before:
(cd /opt/llm && PYTHONPATH="${DEPLOY_SCRIPTS}" uv run python "${DEPLOY_SCRIPTS}/create_schema.py")
# After:
(cd /opt/llm && PYTHONPATH="${DEPLOY_SCRIPTS}" uv run python "${DEPLOY_SCRIPTS}/db/create_schema.py")
```

**Change 5: Update session.sqlite table comment (line 36)**
```bash
# Before:
# 期待値: memories  memory_links  messages  notes  sessions  session_diagnostics  tool_results
# After:
# 期待値: memories  memories_fts  memories_vec  memory_links  messages  session_diagnostics  sessions  tool_results
```

**Change 6: Verify workflow comment is correct (line 39)**
- Current: `# expected: artifacts  attempts  approvals  processed_events  tasks`
- Schema tables: `tasks, attempts, processed_events, artifacts, approvals`
- **No change needed** — already correct

### Target file: `deploy/init_db.sh`

#### Procedure (optional)

Consider changing the python invocation to use module form for consistency with package structure.

#### Method

Replace direct path with `-m db.create_schema`.

#### Details

```bash
# Before:
(cd /opt/llm && PYTHONPATH="${DEPLOY_SCRIPTS}" uv run python "${DEPLOY_SCRIPTS}/db/create_schema.py")
# After (optional):
(cd /opt/llm && PYTHONPATH="${DEPLOY_SCRIPTS}" uv run python -m db.create_schema)
```

**Decision**: Leave as direct path for now — the plan specifies using `${DEPLOY_SCRIPTS}/db/create_schema.py` and no requirement to change to module form.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `deploy/init_db.sh` | Shell syntax check | `bash -n deploy/init_db.sh` | No syntax errors |
| `deploy/init_db.sh` | Clean-run integration test | `bash deploy/init_db.sh` on host with `/opt/llm/` deployed | Exit 0; all table lists printed |
| `rag.sqlite` | Table existence | `sqlite3 /opt/llm/db/rag.sqlite ".tables"` | `chunks  chunks_fts  chunks_vec  documents` |
| `session.sqlite` | Table existence | `sqlite3 /opt/llm/db/session.sqlite ".tables"` | `memories  memories_fts  memories_vec  memory_links  messages  session_diagnostics  sessions  tool_results` |
| `workflow.sqlite` | Table existence | `sqlite3 /opt/llm/db/workflow.sqlite ".tables"` | `approvals  artifacts  attempts  processed_events  tasks` |
| `deploy/init_db.sh` | Idempotency | Run script twice in a row | Second run exits 0; no "table already exists" errors |

## Risks & Mitigations

- **Risk**: Correcting `DEPLOY_SCRIPTS` from `/opt/llm/scripts/db` to `/opt/llm/scripts` changes the path used by `uv run python` invocation → if any other part of the script relied on the old path, it breaks → **Mitigation**: The script only uses `DEPLOY_SCRIPTS` in two places (existence check and python invocation); both are updated consistently
- **Risk**: `uv run` in `/opt/llm/` may not resolve the venv correctly if `uv.lock` is stale → **Mitigation**: `deploy.sh` copies both `pyproject.toml` and `uv.lock`; document that `uv sync` must be run after deploy if dependencies changed
- **Risk**: `notes` table not in `schema_sql.py` for session — comment in current script mentions it → **Mitigation**: Verify against `_SESSION_SCHEMA_TEMPLATE` before adding to validation; `notes` is NOT in the DDL, so omit from the table check list
