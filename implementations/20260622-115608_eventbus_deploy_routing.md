# Implementation: Event Bus deploy integration and routing.md update

## Goal

Wire the Event Bus into the production deployment pipeline: startup command in
`setup_services.sh`, DB schema initialization in `init_db.sh`, and an entry in `routing.md`
so future tasks load the correct docs when touching eventbus code.

## Scope

**In-Scope:**
- `deploy/setup_services.sh` — add uvicorn startup for Event Bus on port 8015
- `deploy/init_db.sh` — add eventbus SQLite schema initialization
- `routing.md` — add eventbus task → docs entry

**Out-of-Scope:**
- systemd unit file (out of scope for Phase 1; add when production OS is confirmed)
- Nginx reverse proxy for Event Bus (not needed for single-node internal use)
- Health check integration into agent startup (Phase 2 of agent–eventbus integration)

## Assumptions

1. All eventbus Python files (`config.py`, `db.py`, `app.py`, `offsets.py`, `dlq.py`) are
   deployed under `/opt/llm/scripts/eventbus/` via existing `deploy.sh` rsync.
2. `uvicorn` is available in the `/opt/llm` venv (already in `pyproject.toml`).
3. `PYTHONPATH=/opt/llm/scripts` is set before running uvicorn (consistent with existing
   MCP server launch patterns in the project).
4. `init_db.sh` has access to `sqlite3` CLI.
5. `routing.md` eventbus entry must be added so `02_design.md` and `03_implementation.md`
   workflows load the correct design docs automatically.

## Implementation

### Target files

- `deploy/setup_services.sh`
- `deploy/init_db.sh`
- `routing.md`

### Procedure

#### Step 1: `deploy/setup_services.sh` — Event Bus startup

Add after the LLM service section:

```bash
# ── Event Bus (port 8015) ──────────────────────────────────────────────────────
echo "--- Event Bus 起動 ---"
PYTHONPATH=/opt/llm/scripts \
    uvicorn eventbus.app:app \
    --host 127.0.0.1 \
    --port 8015 \
    --workers 1 \
    --log-level info \
    --access-log \
    >> /opt/llm/logs/eventbus.log 2>&1 &
echo "  Event Bus PID: $!"
echo "  Health: $(sleep 2 && curl -s http://127.0.0.1:8015/health 2>/dev/null || echo 'まだ起動中')"
```

- `--workers 1` — single worker; WAL concurrency is safe for single-writer pattern.
- `>> /opt/llm/logs/eventbus.log` — append-only log for ops inspection.
- `sleep 2` before health check — uvicorn startup takes ~1s on this hardware.

#### Step 2: `deploy/init_db.sh` — eventbus DB initialization

Add a new section (after existing RAG DB init if present):

```bash
echo "--- Event Bus DB 初期化 ---"
EVENTBUS_DB="/opt/llm/db/eventbus.sqlite"
EVENTBUS_SCHEMA="/opt/llm/scripts/eventbus/schema.sql"

if [ ! -f "${EVENTBUS_DB}" ]; then
    echo "  eventbus.sqlite 作成: ${EVENTBUS_DB}"
    sqlite3 "${EVENTBUS_DB}" < "${EVENTBUS_SCHEMA}"
    echo "  完了"
else
    echo "  eventbus.sqlite 既存のためスキップ"
fi
```

- Idempotent: skips if DB already exists (schema has `IF NOT EXISTS`).
- Uses `schema.sql` from the deployed scripts path, not the repo path.

#### Step 3: `routing.md` — eventbus entry

Add to the "Implementation reference" table:

```markdown
| Event Bus (eventbus/app.py, eventbus/dlq.py, eventbus/offsets.py) | `docs/07_eventbus_01_overview.md` |
```

Also add to "Task → skill mapping":

```markdown
| Event Bus implementation / debug | eventbus, event bus, dlq, sse subscribe, replay | `skills/python-implementation/SKILL.md` + `rules/env.md` |
```

Note: `docs/07_eventbus_01_overview.md` does not yet exist. It should be created as part of
the documentation step (separate task). Until then, add a placeholder comment in `routing.md`:

```markdown
| Event Bus (eventbus/*.py) | `docs/07_eventbus_01_overview.md` (TODO: create) |
```

### Method

- `setup_services.sh` uses `&` (background) to match the existing MCP server startup pattern
  in the project; no systemd wrapper needed for single-node dev/staging.
- `init_db.sh` guard (`[ ! -f "${EVENTBUS_DB}" ]`) prevents accidental schema re-application
  on a DB with live data; `IF NOT EXISTS` in SQL provides a second safety layer.
- `routing.md` entry ensures that future `02_design.md` executions auto-load eventbus docs
  rather than falling back to generic search.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| setup_services.sh syntax | Static | `bash -n deploy/setup_services.sh` | no error |
| init_db.sh syntax | Static | `bash -n deploy/init_db.sh` | no error |
| Event Bus startup (staging) | Manual | `bash deploy/setup_services.sh` then `curl http://127.0.0.1:8015/health` | `{"status": "ok"}` |
| DB init (staging) | Manual | `bash deploy/init_db.sh` then `sqlite3 /opt/llm/db/eventbus.sqlite ".tables"` | `events` table present |
| routing.md format | Manual | Verify markdown table renders correctly | No broken table |

## Risks

- **Risk:** `uvicorn` process started with `&` is not monitored — if it crashes, nothing
  restarts it.
  **Mitigation:** Add `systemd` unit file in a follow-up task; for Phase 1, the `/health`
  endpoint allows ops to check status manually.
- **Risk:** `init_db.sh` skip guard (`[ ! -f ... ]`) bypasses schema migration for existing
  DB files — if `schema.sql` adds new columns in future, they won't be applied.
  **Mitigation:** For schema migrations, run `ALTER TABLE` statements separately; `init_db.sh`
  is for initial creation only, not migration.
- **Risk:** `routing.md` references `docs/07_eventbus_01_overview.md` which does not yet
  exist — `02_design.md` workflow will try to load it and fail.
  **Mitigation:** Mark as `(TODO: create)` in the routing entry; create the doc in a
  separate documentation task before running `02_design.md` on eventbus tasks.
