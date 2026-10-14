## Goal

Schema tests: Remove the `approvals` DDL copy and assertions (REQ-005: tests).

## Scope

- Remove the `approvals` DDL copy and assertions; make the four `*_schema_timestamps` tests patch `db.helper.build_db_config` to a temporary database (they currently patch only the DDL builder, so `create_workflow_schema()` runs against the real `/opt/llm/db/workflow.sqlite`, which the new UPDATE and DROP migrations would modify) and assert on the database actually created (nullable `attempts.ended_at` has no default); add migration tests on temporary databases built from an old-schema fixture (a `pending_approval` task ends `failed` and the table is dropped, a second run is a no-op, a new database has no `approvals`)

## Assumptions

- Plan `plans/20261014-114443_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Apply only after the repository owner's decision (Plan Step 1) is recorded, together with every other procedure of this plan (Steps 2-11) as one commit unit.
- Line numbers come from the Plan and may shift; locate edits by symbol, test name, or section.

## Design decisions

- Edit by test name; compare `pytest --collect-only -q` counts before and after and confirm only the intended tests changed.
- New test text must not contain registered removed names (the allowlisted test files excepted); use unregistered terms such as require_approval, approvals, or pending_approval where needed.

## Alternatives considered

N/A: test-only change

## Implementation

### Target file

`tests/db/test_create_schema.py`

### Procedure

Remove the `approvals` DDL copy and assertions; make the four `*_schema_timestamps` tests patch `db.helper.build_db_config` to a temporary database (they currently patch only the DDL builder, so `create_workflow_schema()` runs against the real `/opt/llm/db/workflow.sqlite`, which the new UPDATE and DROP migrations would modify) and assert on the database actually created (nullable `attempts.ended_at` has no default); add migration tests on temporary databases built from an old-schema fixture (a `pending_approval` task ends `failed` and the table is dropped, a second run is a no-op, a new database has no `approvals`).

### Method

Evidence recorded in the Plan: `test_create_schema.py` lines 364, 406, 829. Locate the places with a case-sensitive search for the removed names in this file, edit by symbol or section, then format the file.

### Details

- First fix the isolation defect: patch db.helper.build_db_config (as the other tests in this file do) in the four schema timestamp tests so create_workflow_schema, create_rag_schema, create_session_schema, and create_eventbus_schema run against a temporary database; point the final sqlite3 connection at that database. The current tests patch only the DDL builder, so they write to the real databases under /opt/llm. Record the modification times of /opt/llm/db files before and after a run to prove no write happens.
- In the workflow test assert default timestamps only for NOT NULL columns, because the nullable attempts.ended_at has no default; drop approvals from the table loop and from test_creates_all_tables, and drop the approvals DDL copy.
- Add migration tests on temporary databases built from an old-schema fixture (tasks, attempts, approvals, version 1.0.0): a pending_approval task ends failed and approvals is dropped; a second run changes nothing; a new database has no approvals table; the version row 1.1.0 is recorded. Name them test_migration_fails_pending_approval_tasks (new), test_migration_is_idempotent_after_drop (new), and test_new_database_has_no_approvals_table (new).

## Compatibility considerations

N/A: test-only change

## Security considerations

N/A: test-only change

## Rollback considerations

N/A: revert the commit; the whole plan lands as one commit unit.

## Validation plan

- `uv run pytest` on this file passes after the code procedures are applied.
- `uv run ruff format` and `uv run ruff check` on the file are clean.

## Completion criteria

- The file contains no removed gate name outside what the Procedure keeps.
- Remaining tests still pass and the collected-count change matches the Procedure.

## Out of scope

- Tool-level approval (the keep list), the MDQ and eventbus areas, and any file outside this Plan's target table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the edit | Completed | 20261014-142001 | 20261014-142001 |  |
| 2 | Run the affected tests | Completed | 20261014-142001 | 20261014-142001 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261014-142001 | 20261014-142001 |  |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261014-112913_appr001_remove-the-post-execution-approval-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-114443_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-123722
- **Related target files**: tests/db/test_create_schema.py