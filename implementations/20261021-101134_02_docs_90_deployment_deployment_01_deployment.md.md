## Goal
Add to `docs/90_deployment/deployment_01_deployment.md` the read-only check that identifies the current schema of `workflow.sqlite`, `eventbus.sqlite`, and `mdq.sqlite`, so an operator can repeat the schema inventory without changing any database (REQ-002).

## Scope
- In: one new subsection at the end of section 3.1 "Applying Schema" (before `### 3.2 Deployment Checklist`).
- Out: the `session.sqlite` recreation table, section 3.3, the auto-generated DB Path Reference block, any other document, any code or test.

## Assumptions
- The `sqlite3` command-line tool is available on the host (verified 2026-10-21: `/usr/bin/sqlite3`).
- The check opens each file with `mode=ro`, so it writes nothing, even when the service is stopped.
- Database paths are not repeated here; the DB Path Reference lists the config keys, and `mdq.sqlite` uses `db_path` of `config/mdq_mcp_server.toml`.

## Design decisions
- Use `pragma_table_info()` in a `SELECT` so each result is one line that an operator can compare by eye.
- State what a conforming result looks like in the same subsection, so the check is self-contained; the baseline itself is defined in the database document.

## Alternatives considered
N/A: the Plan fixes the location and purpose (read-only check in the operator document).

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md`

### Procedure
1. Insert the subsection below after the "Recreating `session.sqlite`" content of section 3.1 (after the sentence "Sessions, messages, and diagnostics are not recovered; past sessions can no longer be loaded.") and before `### 3.2 Deployment Checklist`.
2. Run the documentation checkers.

### Method
Subsection text (English; adjust only to satisfy the checkers):

````markdown
**Identifying a database's current schema.** The checks below only read: each file is opened with `mode=ro`. Replace each placeholder with the path from the DB Path Reference (`mdq.sqlite`: `db_path` in `config/mdq_mcp_server.toml`). The supported baseline is defined in [DB migration and scaling](../41_db/db_03_architecture_and_schema-migration-and-scaling.md) (section 8e).

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

| Database | A database at the supported baseline shows |
|---|---|
| `workflow.sqlite` | The version `setup_services.sh` expects (a mismatch is the failure mode in section 3.3) |
| `eventbus.sqlite` | `events` without `retry_count`; `consumer_delivery` with `acked` and without `acked_at`; `consumer_offsets` with `offset` |
| `mdq.sqlite` | `chunk_id` as the first `chunks` column (`id` means the legacy shape, which the MDQ service rebuilds at start) |
````

### Details
- Verified 2026-10-21 against the deployed host: workflow `1.1.0`; eventbus columns as listed; mdq `chunk_id`. The commands leave each file's modification time unchanged.
- Keep the subsection to the operator check; the baseline wording lives in the database document, which the subsection links to.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: the commands open files read-only and print schema names only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py` (internal link to section 8e must resolve), `check_docs_content_policy.py --strict`, `check_docs_japanese.py`.
- Re-run the three commands against the deployed host once more and confirm the results match the table (read-only).

## Completion criteria
- The subsection states the read-only check for the three databases and what a baseline-conforming result is (AC-2).
- The listed checkers pass (AC-5).

## Out of Scope
- Defining the baseline (row 01); changing deploy scripts; adding a script for the check.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the read-only schema check subsection to section 3.1 (REQ-002) | Blocked | 20261021-101337 | — | Blocked: deployment_01_deployment.md is 24536 B at HEAD, 40 B under the 24576 B limit of tools/check_docs_structure.py; the planned subsection (~1.5 KB) fails check_docs_structure.py (26012 B). Edit reverted. A table of *.sqlite names also trips check_docs_consistency.py --domain deployment (use a list). |
| 2 | Run the documentation checkers and re-run the commands read-only (REQ-005) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `deployment_01_deployment.md` has 40 B of headroom under the 24576 B limit of `tools/check_docs_structure.py`; the planned subsection does not fit. Needs an owner decision: raise the file's size ceiling, move the check to another operations document (Plan amendment), or free space in this file. | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (read-only schema check in the operator document); `REQ-005` (checkers pass)
- **Source issue**: `issues/20261020-122549_compat001_define-the-supported-from-schema-baseline-and-retire-or-keep-decision-for-each-db-migration.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261020-233138_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-101134
- **Related target files**: `docs/90_deployment/deployment_01_deployment.md`