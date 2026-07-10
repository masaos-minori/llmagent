# Implementation: `init_db.sh` active workflow-table verification

## Goal

Replace `init_db.sh`'s informational `.tables` echo for `workflow.sqlite` with an active per-table existence check that fails fast with a remediation message if any of the 5 required tables are missing.

## Scope

**In:**
- `deploy/init_db.sh`: replace the `workflow.sqlite` `.tables` block only

**Out:**
- No changes to `scripts/db/create_schema.py`/`schema_sql.py` (schema creation, including `create_workflow_schema()`, is already correctly wired and idempotent)
- No equivalent active check added for `rag.sqlite`/`session.sqlite`/`eventbus.sqlite` (out of scope per the plan)

## Assumptions

1. The existing `sqlite3 "${DEPLOY_DB}/workflow.sqlite" ".tables"` line is purely informational today (output never captured/compared) — this is the exact gap being closed.
2. Table existence is checked via `SELECT name FROM sqlite_master WHERE type='table' AND name='<table>'` per table, not by parsing `.tables`'s column-formatted output, to avoid any substring/word-boundary ambiguity.

## Implementation

### Target file

`deploy/init_db.sh`

### Procedure

1. Locate:
   ```bash
   sqlite3 "${DEPLOY_DB}/workflow.sqlite" ".tables"
   # expected: artifacts  attempts  approvals  processed_events  tasks
   ```
2. Replace it with:
   ```bash
   echo "--- workflow.sqlite テーブル確認 ---"
   REQUIRED_WORKFLOW_TABLES="tasks attempts processed_events artifacts approvals"
   MISSING_TABLES=""
   for t in ${REQUIRED_WORKFLOW_TABLES}; do
     FOUND=$(sqlite3 "${DEPLOY_DB}/workflow.sqlite" \
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
   echo "OK: all required workflow.sqlite tables present (${REQUIRED_WORKFLOW_TABLES})"
   ```
3. Leave the other three `.tables` informational checks (`rag.sqlite`, `session.sqlite`, `eventbus.sqlite`) unchanged.
4. Confirm `bash -n deploy/init_db.sh` still parses correctly.

### Method

Direct block replacement — a `for` loop over a fixed table-name list, each checked via an exact `sqlite_master` query, accumulating any misses into `MISSING_TABLES` before a single fail-fast check.

### Details

- `MISSING_TABLES` accumulates all missing tables (not just the first) so the operator sees the complete picture in one run, rather than fixing one table and re-running to discover the next.
- The remediation message text matches the requirement's "Suggested Remediation Message" verbatim: `Workflow database schema is missing or incomplete.` / `Run the workflow schema initialization step before starting the agent.`

## Validation plan

```bash
bash -n deploy/init_db.sh
shellcheck deploy/init_db.sh   # if available

# Positive + idempotency test
bash deploy/init_db.sh   # expect "OK: all required workflow.sqlite tables present ..."
bash deploy/init_db.sh   # run again; expect same success, no duplicate-table errors

# Negative test (scratch DB only — do not touch the real /opt/llm/db/workflow.sqlite)
cp /opt/llm/db/workflow.sqlite /tmp/workflow_test.sqlite
sqlite3 /tmp/workflow_test.sqlite "DROP TABLE approvals;"
# Temporarily point DEPLOY_DB at /tmp for this test invocation, or adapt the check inline for a manual run:
sqlite3 /tmp/workflow_test.sqlite "SELECT name FROM sqlite_master WHERE type='table' AND name='approvals';"
# expect empty result, confirming the loop would detect and report this as missing
```

Expected outcome: normal runs print "OK: ..." and exit 0, including on repeated (idempotent) runs; a DB missing any required table causes exit 1 with the exact `[FATAL]` remediation message naming the missing table(s).
