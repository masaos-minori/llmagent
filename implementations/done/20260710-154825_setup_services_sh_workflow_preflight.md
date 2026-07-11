# Implementation: `setup_services.sh` workflow pre-flight check

## Goal

Add a pre-flight block to `deploy/setup_services.sh` that verifies the deployed workflow definition and DB schema before any service (Event Bus, LLM, MCP) starts.

## Scope

**In:**
- `deploy/setup_services.sh`: new pre-flight block, placed before any service-startup code

**Out:**
- No changes to `deploy/deploy.sh` or `deploy/init_db.sh` — this is an independent, third layer of defense
- No modification of any workflow definition file — read-only checks only

## Assumptions

1. Depends on `implementations/done/20260710-154648_agent_workflow_validate_cli.md` (`scripts/agent/workflow/validate.py`) already being deployed to `/opt/llm/scripts/agent/workflow/validate.py` — guaranteed by `deploy.sh`'s existing wholesale `scripts/` rsync, so no new copy-list entry is needed.
2. Workflow DB path is hardcoded as `/opt/llm/db/workflow.sqlite`, matching `scripts/db/config.py`'s `workflow_db_path` default and `init_db.sh`'s existing `${DEPLOY_DB}/workflow.sqlite` convention — no TOML parsing introduced into this shell script.
3. `setup_services.sh` has no pre-flight section today — this is entirely new code, inserted before the existing "LLM サービスのサブプロセス起動" section.

## Implementation

### Target file

`deploy/setup_services.sh`

### Procedure

1. Locate the `REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"` line.
2. Immediately after it, before the `echo "=== setup_services.sh: サービス設定開始 ==="` banner, insert:
   ```bash
   echo "--- Pre-flight: workflow definition and schema check ---"

   WORKFLOW_JSON="/opt/llm/config/workflows/default.json"
   WORKFLOW_DB="/opt/llm/db/workflow.sqlite"

   if [ ! -f "${WORKFLOW_JSON}" ]; then
     echo "[FATAL] Missing required workflow definition: ${WORKFLOW_JSON}" >&2
     echo "Run deploy/deploy.sh before deploy/setup_services.sh." >&2
     exit 1
   fi

   if ! PYTHONPATH=/opt/llm/scripts uv run python -m agent.workflow.validate "${WORKFLOW_JSON}"; then
     echo "[FATAL] Deployed workflow definition failed validation: ${WORKFLOW_JSON}" >&2
     echo "Run the workflow schema initialization step before starting the agent." >&2
     exit 1
   fi

   if [ ! -f "${WORKFLOW_DB}" ]; then
     echo "[FATAL] Workflow database schema is missing or incomplete." >&2
     echo "Run the workflow schema initialization step before starting the agent." >&2
     exit 1
   fi

   REQUIRED_WORKFLOW_TABLES="tasks attempts processed_events artifacts approvals"
   MISSING_TABLES=""
   for t in ${REQUIRED_WORKFLOW_TABLES}; do
     FOUND=$(sqlite3 "${WORKFLOW_DB}" \
       "SELECT name FROM sqlite_master WHERE type='table' AND name='${t}';")
     if [ -z "${FOUND}" ]; then
       MISSING_TABLES="${MISSING_TABLES} ${t}"
     fi
   done
   if [ -n "${MISSING_TABLES}" ]; then
     echo "[FATAL] Workflow database schema is missing or incomplete." >&2
     echo "Missing table(s):${MISSING_TABLES}" >&2
     echo "Run the workflow schema initialization step before starting the agent." >&2
     exit 1
   fi

   echo "OK: workflow definition and schema pre-flight checks passed"
   echo ""
   ```
3. Confirm `bash -n deploy/setup_services.sh` still parses correctly.

### Method

Direct insertion of a self-contained pre-flight block at the very top of the script's substantive logic — four sequential checks (definition existence → definition validity → DB existence → table completeness), each with its own fail-fast `exit 1`.

### Details

- All four checks run strictly before the existing "LLM サービスのサブプロセス起動" section and the Event Bus subprocess spawn, so any failure here guarantees no service has been started yet.
- This duplicates the same *kind* of check as `deploy.sh` (definition) and `init_db.sh` (tables) deliberately — it is a second/third independent line of defense for the case where `setup_services.sh` runs out of order or after a manual change to `/opt/llm`, not a refactor of those scripts' logic into a shared library (explicitly out of scope per the plan's Risk analysis).

## Validation plan

```bash
bash -n deploy/setup_services.sh

# Positive test
bash deploy/setup_services.sh   # expect "OK: workflow definition and schema pre-flight checks passed", then services start as before

# Negative test: missing definition
mv /opt/llm/config/workflows/default.json /tmp/default.json.bak
bash deploy/setup_services.sh; echo "exit: $?"   # expect non-zero, before any service starts
ps aux | grep eventbus.app | grep -v grep         # expect no new process
mv /tmp/default.json.bak /opt/llm/config/workflows/default.json   # restore

# Negative test: invalid definition
cp /opt/llm/config/workflows/default.json /tmp/default.json.bak2
python3 -c "import json; d=json.load(open('/opt/llm/config/workflows/default.json')); del d['retry_policy']; json.dump(d, open('/opt/llm/config/workflows/default.json','w'))"
bash deploy/setup_services.sh; echo "exit: $?"   # expect non-zero via validation-CLI check
cp /tmp/default.json.bak2 /opt/llm/config/workflows/default.json   # restore

# Negative test: missing DB
mv /opt/llm/db/workflow.sqlite /tmp/workflow.sqlite.bak
bash deploy/setup_services.sh; echo "exit: $?"   # expect non-zero via DB-existence check
mv /tmp/workflow.sqlite.bak /opt/llm/db/workflow.sqlite   # restore
```

Expected outcome: all four checks pass silently (printing only the final "OK: ...") in the normal case; each negative test aborts with the matching `[FATAL]` message and non-zero exit, strictly before any service process is spawned.
