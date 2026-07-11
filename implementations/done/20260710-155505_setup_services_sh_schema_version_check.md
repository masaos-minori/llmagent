# Implementation: schema version check in `setup_services.sh` pre-flight

## Goal

Extend the `deploy/setup_services.sh` pre-flight block (from `implementations/done/20260710-154825_setup_services_sh_workflow_preflight.md`) to print and compare the workflow schema version, aborting before any service starts on mismatch.

## Scope

**In:**
- `deploy/setup_services.sh`: append a version-check block to the existing pre-flight section, after its table-existence loop

**Out:**
- No change to the existing pre-flight checks (definition existence, definition validity, DB existence, table completeness) added by `implementations/done/20260710-154825_setup_services_sh_workflow_preflight.md`

## Assumptions

1. Depends on `implementations/20260710-155420_workflow_schema_version_table_and_recording.md` (the `workflow_schema_version` table + `WORKFLOW_SCHEMA_VERSION` constant) and `implementations/done/20260710-154825_setup_services_sh_workflow_preflight.md` (the pre-flight block this extends) both being implemented first.
2. The expected version is read from Python (`from db.schema_sql import WORKFLOW_SCHEMA_VERSION`) rather than hardcoded a second time in shell, so the two locations cannot drift out of sync — consistent with `implementations/done/20260710-154825_setup_services_sh_workflow_preflight.md`'s existing use of `PYTHONPATH=/opt/llm/scripts uv run python`.

## Implementation

### Target file

`deploy/setup_services.sh`

### Procedure

1. Locate the end of the pre-flight block's existing table-existence loop (the `MISSING_TABLES` check from `implementations/done/20260710-154825_setup_services_sh_workflow_preflight.md`), specifically right before the final `echo "OK: workflow definition and schema pre-flight checks passed"` line.
2. Insert immediately before that final success echo:
   ```bash
   EXPECTED_SCHEMA_VERSION=$(PYTHONPATH=/opt/llm/scripts uv run python -c \
     "from db.schema_sql import WORKFLOW_SCHEMA_VERSION; print(WORKFLOW_SCHEMA_VERSION)")
   ACTUAL_SCHEMA_VERSION=$(sqlite3 "${WORKFLOW_DB}" \
     "SELECT version FROM workflow_schema_version ORDER BY applied_at DESC LIMIT 1;")
   echo "Workflow schema version: ${ACTUAL_SCHEMA_VERSION:-<none>} (expected: ${EXPECTED_SCHEMA_VERSION})"
   if [ "${ACTUAL_SCHEMA_VERSION}" != "${EXPECTED_SCHEMA_VERSION}" ]; then
     echo "[FATAL] Workflow schema version mismatch: expected ${EXPECTED_SCHEMA_VERSION}, found ${ACTUAL_SCHEMA_VERSION:-<none>}." >&2
     echo "Run deploy/init_db.sh to migrate the workflow schema before starting services." >&2
     exit 1
   fi
   ```
3. Confirm `bash -n deploy/setup_services.sh` still parses correctly.

### Method

Direct insertion at the end of the existing pre-flight block, before its final success message — no restructuring of the earlier checks.

### Details

- `${WORKFLOW_DB}` is already defined earlier in the same pre-flight block (from `implementations/done/20260710-154825_setup_services_sh_workflow_preflight.md`); this block reuses it rather than redefining it.
- `${ACTUAL_SCHEMA_VERSION:-<none>}` renders as the literal string `<none>` when the query returns empty (no row / table just created), matching the same "no prior version recorded" case documented in `implementations/20260710-155420_workflow_schema_version_table_and_recording.md`.

## Validation plan

```bash
bash -n deploy/setup_services.sh

# Positive test
bash deploy/setup_services.sh
# expect: "Workflow schema version: 1.0.0 (expected: 1.0.0)" then "OK: ..." then services start

# Negative test: stale version in a scratch copy of the DB
cp /opt/llm/db/workflow.sqlite /tmp/workflow_test.sqlite
sqlite3 /tmp/workflow_test.sqlite "UPDATE workflow_schema_version SET version='0.9.0' WHERE rowid = (SELECT rowid FROM workflow_schema_version ORDER BY applied_at DESC LIMIT 1);"
sqlite3 /tmp/workflow_test.sqlite "SELECT version FROM workflow_schema_version ORDER BY applied_at DESC LIMIT 1;"
# expect: 0.9.0 — confirms the query used by the script would detect this mismatch
```

Expected outcome: normal deploy prints the matching version pair and proceeds; a DB with a stale or missing `workflow_schema_version` row causes the pre-flight block to abort with the `[FATAL]` version-mismatch message, strictly before any service starts.
