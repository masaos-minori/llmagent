# Implementation: document `workflow_schema_version` and schema-version-mismatch recovery

## Goal

Document the new `workflow_schema_version` table and the recovery procedure for a schema-version mismatch, in the existing db-schema reference doc.

## Scope

**In:**
- `docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md`: add the `workflow_schema_version` table to section 7 (`workflow.sqlite` Schema), plus a "Schema version mismatch" recovery subsection

**Out:**
- No change to `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`'s existing "Workflow Startup Validation" section content — only a one-line cross-link is added there (see Details), since that section covers workflow-definition-file validation, not DB schema version

## Assumptions

1. `docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md` section 7 (`## 7. \`workflow.sqlite\` Schema`, starting line 176) is the single authoritative location documenting all `workflow.sqlite` tables (`tasks`, `approvals`, `attempts`/`processed_events`/`artifacts`) — confirmed by direct read; this is the correct place to add the new `workflow_schema_version` table.
2. Depends on `implementations/20260710-155420_workflow_schema_version_table_and_recording.md`, `implementations/20260710-155445_repl_health_schema_version_check.md`, and `implementations/20260710-155505_setup_services_sh_schema_version_check.md` all being implemented, so the documented behavior matches the actual code.

## Implementation

### Target file

`docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md`

### Procedure

1. Immediately after the existing line 208 (`See \`scripts/db/schema_sql.py\` for full DDL. All use \`CREATE TABLE IF NOT EXISTS\`.`) and before the `---` at line 210, insert:
   ```markdown
   ### `workflow_schema_version` table

   | Column | Type | Note |
   |---|---|---|
   | `version` | TEXT NOT NULL | e.g. `1.0.0` |
   | `applied_at` | TEXT NOT NULL | ISO-8601 UTC, `DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))` |

   Append-only log — one row per version ever applied. The "current version" is the row with the maximum `applied_at`. `create_workflow_schema()` inserts a new row only when the latest recorded version differs from `WORKFLOW_SCHEMA_VERSION` (in `scripts/db/schema_sql.py`), keeping repeated runs idempotent.

   ### Schema version mismatch

   Both `agent/repl_health.py::check_workflow_schema()` (agent startup) and `deploy/setup_services.sh`'s pre-flight block (deploy-time) compare the latest `workflow_schema_version.version` row against the `WORKFLOW_SCHEMA_VERSION` constant, and fail with a `[FATAL]`/`RuntimeError` message naming both the expected and found versions if they differ (including when no row exists yet — e.g. a `workflow.sqlite` created before this table existed).

   **Recovery**: re-run `deploy/init_db.sh` (or call `create_workflow_schema()` directly) to bring the schema up to the expected version. `_WORKFLOW_MIGRATIONS` and the version-recording insert are both idempotent, so re-running is always safe.
   ```
2. In `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`, under its existing `## Workflow Startup Validation` heading, add one cross-link line: `See also: [workflow_schema_version and schema version mismatch recovery](90_shared_04_02_db_architecture_and_schema-schema-reference.md#7-workflowsqlite-schema).`

### Method

Direct documentation insertion at a confirmed, already-read location — no restructuring of either file's existing sections.

### Details

- The recovery text mirrors the exact remediation wording used in the code (`implementations/20260710-155445_repl_health_schema_version_check.md`'s `RuntimeError` message and `implementations/20260710-155505_setup_services_sh_schema_version_check.md`'s `[FATAL]` message: "Run create_workflow_schema() to migrate" / "Run deploy/init_db.sh to migrate the workflow schema"), so the doc and the actual error messages stay consistent.

## Validation plan

```bash
uv run python -c "import check_docs_consistency" 2>/dev/null || true
grep -n "workflow_schema_version" docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md
grep -n "Workflow Startup Validation" -A5 docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md
```

Expected outcome: `docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md` now documents the `workflow_schema_version` table and its recovery procedure inside section 7, immediately alongside the other `workflow.sqlite` tables; the operations/troubleshooting doc cross-links to it without duplicating content.
