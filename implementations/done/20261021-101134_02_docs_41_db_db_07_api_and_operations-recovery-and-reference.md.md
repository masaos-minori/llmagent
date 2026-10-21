## Goal
Add to `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` the read-only check an operator runs to identify the current schema of `workflow.sqlite`, `eventbus.sqlite`, and `mdq.sqlite`, so the schema inventory can be repeated without changing any database (REQ-002).

## Scope
- In: one new subsection `11a. Identifying a Database's Current Schema` directly after section 11 (DB Recreation Procedure), before the `---` that precedes section 12.
- Out: sections 9 to 12 bodies, the deployment guide, the database design document (row 03 fixes its pointer), any code.

## Assumptions
- Owner decision of 2026-10-21 (Plan Background, Location amendment): the check lives here because the deployment guide has 40 B of headroom under the docs size limit.
- Verified 2026-10-21: `sqlite3` exists on the host; the commands below were run against the deployed databases and left their modification times unchanged.
- The file is 13821 B (limit 24576 B), so the addition fits.
- The supported baseline is defined in the database design document, section 8e.

## Design decisions
- A bullet list instead of a table lists what a baseline-conforming database shows, so database file names do not appear as table keys (the deployment-domain consistency checker treated such a table as a database overview in an earlier attempt).
- Each command is one `SELECT`, so the result is a single line that can be compared by eye.

## Alternatives considered
N/A: the owner chose this location over raising the size ceiling of the deployment guide or compressing it.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
1. Insert the subsection below after the "Important notes" list of section 11 and before the `---` that precedes `## 12. Verification Plan`.
2. Run the documentation checkers.

### Method
Subsection text (English; adjust only to satisfy the checkers):

````markdown
### 11a. Identifying a Database's Current Schema

To see which schema a database has without changing it, open the file read-only (`mode=ro`). Replace each placeholder with the path from the configuration (`mdq.sqlite`: `db_path` in `config/mdq_mcp_server.toml`). The supported baseline is defined in [DB migration and scaling](db_03_architecture_and_schema-migration-and-scaling.md) (section 8e).

```bash
# workflow.sqlite: latest recorded schema version
sqlite3 "file:<workflow_db_path>?mode=ro" \
  "SELECT version FROM workflow_schema_version ORDER BY applied_at DESC LIMIT 1;"

# eventbus.sqlite: column names of its three tables
sqlite3 "file:<eventbus_db_path>?mode=ro" \
  "SELECT group_concat(name) FROM pragma_table_info('events');
   SELECT group_concat(name) FROM pragma_table_info('consumer_delivery');
   SELECT group_concat(name) FROM pragma_table_info('consumer_offsets');"

# mdq.sqlite: first column of the chunk table
sqlite3 "file:<mdq_db_path>?mode=ro" \
  "SELECT name FROM pragma_table_info('chunks') LIMIT 1;"
```

A database at the supported baseline shows:

- `workflow.sqlite`: the version that `setup_services.sh` expects; a mismatch fails startup.
- `eventbus.sqlite`: `events` without `retry_count`; `consumer_delivery` with `acked` and without `acked_at`; `consumer_offsets` with `offset`.
- `mdq.sqlite`: `chunk_id` as the first `chunks` column (`id` is the legacy shape, which the MDQ service rebuilds at start).

A database that does not match is recreated (section 11), not migrated.
````

### Details
- Verified 2026-10-21 on the deployed host: workflow `1.1.0`; eventbus columns as listed; mdq `chunk_id`.
- The anchor of this heading, `#11a-identifying-a-databases-current-schema`, is linked from the database document (row 03); keep the heading text exact.
- Do not write the word "Needs confirmation".

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: the commands open files read-only and print schema names only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`, `check_db_separation.py`.
- Re-run the three commands read-only against the deployed host and confirm the output matches the list (and the files' modification times are unchanged).

## Completion criteria
- The subsection states the read-only check for the three databases and what a baseline-conforming result is (AC-2).
- The listed checkers pass (AC-5).

## Out of Scope
- Defining the baseline (done); changing the deployment guide; adding a script for the check.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add subsection 11a (REQ-002) | Completed | 20261021-103501 | 20261021-103529 | Changed: docs/41_db/db_07_api_and_operations-recovery-and-reference.md (new section 11a) |
| 2 | Run the documentation checkers and re-run the commands read-only (REQ-005) | Completed | 20261021-103501 | 20261021-103529 | check_docs_quality, check_docs_structure, check_docs_content_policy --strict, check_docs_japanese, check_db_separation all exit 0 (file 15342 B); commands re-run read-only on the deployed host, results as listed, mtimes unchanged. Docs-only: no test run. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (read-only schema check in the operations document); `REQ-005` (checkers pass)
- **Source issue**: `issues/20261020-122549_compat001_define-the-supported-from-schema-baseline-and-retire-or-keep-decision-for-each-db-migration.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261020-233138_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-101134
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`