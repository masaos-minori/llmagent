# Implementation procedure: `scripts/db/schema_sql.py` — retire `execution_snapshots` DDL and `tool_call_state.snapshot_id`

## Goal
Remove the never-written `execution_snapshots` table and the `snapshot_id` column/FK from the `tool_call_state` DDL so fresh databases no longer carry the dead schema surface (`REQ-001`).

## Scope
**Release unit**: wfaudit010-full

- Delete the `CREATE TABLE IF NOT EXISTS execution_snapshots` block (L227-232) and the `snapshot_id TEXT REFERENCES execution_snapshots(snapshot_id)` line (L239) from the workflow schema SQL.
- Companion test file `tests/db/test_create_schema.py` gets the fresh-database exclusion assertions.

## Assumptions
- Retire (not keep) is the plan's recorded decision; `UNK-01` (owner veto) is `Blocking? False` — see Plan Assumptions/Unknowns.
- `UNK-02` (`SELECT` probe on the production `workflow.sqlite` before deploy) is a deploy-time operator action, not a code change in this document.

## Design decisions
- No migration: the workflow layer accepts only fresh-created or current-shape databases; legacy databases keep the leftover column harmlessly because no code names or reads it after this batch (Plan Design "Existing databases").
- Schema-gate boundary confirmed at revalidation: `scripts/agent/services/workflow_schema.py` and `deploy/init_db.sh` do not currently name `execution_snapshots` or `tool_call_state` in their required-shape lists, so this retirement does not change gate behavior; the gate list itself is `wfaudit003`'s scope (which depends on this plan landing first).

## Alternatives considered
- Keep the table dormant and only fix docs: rejected by the Plan Design decision (retire) — keeping it forces `wfaudit003` to gate an empty table and `wfaudit002` to design around a dead FK.

## Implementation
### Target file
`scripts/db/schema_sql.py`

### Procedure
1. Delete the whole `CREATE TABLE IF NOT EXISTS execution_snapshots (...)` statement (L227-232) from the workflow schema SQL builder.
2. Delete the `snapshot_id     TEXT REFERENCES execution_snapshots(snapshot_id),` line from the `tool_call_state` DDL (L239); keep every other column and the `idx_tool_call_state_task_state` index unchanged.

### Method
- Pure deletion from the SQL string; no replacement text. If the surrounding comment block references the snapshot table, adjust the comment to state the retirement in one line.

### Details
- Current state (verified at HEAD `367e583d2`): the two statements sit adjacent in the workflow DDL; `tool_call_state` otherwise unchanged since the compatrm001 migration-framework removal.
- `scripts/shared/execution_snapshot.py` (live shared-domain config-fingerprinting feature) is a different system and MUST stay byte-identical — named in the Plan Validation plan as a post-change confirmation.

### Companion test files
- `tests/db/test_create_schema.py`
  - Procedure: add a test asserting `create_workflow_schema()` on a fresh in-memory database yields no `execution_snapshots` entry in `sqlite_master` and no `snapshot_id` column in `PRAGMA table_info(tool_call_state)`; keep existing `_schema_snapshot` diff tests untouched.
  - Validation: `uv run pytest tests/db/test_create_schema.py -q` — new assertion fails on pre-change HEAD and passes after the change.

## Compatibility considerations
- Legacy databases (column present) keep working because the sibling ops change removes the column from INSERT column lists and row reads (`REQ-003`); a NULL FK-satisfying insert is never attempted.
- No `deploy.sh` impact (file is rsynced); no service restart semantics beyond the standard deploy.

## Security considerations
- N/A: schema deletion of a never-written table; no new input surface.

## Rollback considerations
- Revert the commit restores the DDL for fresh databases only; databases created while retired would lack the table/column (re-adding is a fresh-schema change — Plan Risks row 1).

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/db/schema_sql.py` | schema unit (companion file) | `uv run pytest tests/db/test_create_schema.py -q` | exclusion assertions fail pre-fix, pass post-fix |
| `scripts/shared/execution_snapshot.py` | unchanged check | `git diff HEAD -- scripts/shared/execution_snapshot.py` (after the change commit) | empty |
| gates | static | `rules/toolchain.md` sequence (ruff → mypy → lint-imports → bandit) | clean, no new suppressions |

## Completion criteria
- Fresh workflow databases contain no `execution_snapshots` table and no `snapshot_id` column in `tool_call_state` (`Acceptance Criteria REQ-001`).
- Companion test fails pre-change and passes post-change; `tests/db/` green (`REQ-005`).

## Out of Scope
- Dropping the column from an existing production `workflow.sqlite` (Plan Out-of-Scope: no migration path).
- The required-shape gate list (`wfaudit003`, depends on this plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261108-120435 | 20261108-120435 | Blocks wfaudit003 and wfaudit002: land this plan's batch first |
| 2 | Add or update tests per Validation plan (companion test file) | Completed | 20261108-120435 | 20261108-120435 | Blocks wfaudit003 and wfaudit002: land this plan's batch first |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261108-120435 | 20261108-120435 | ruff/format/mypy/lint-imports/bandit pass; full suite with coverage 11829 passed, 3 failed: 1 environmental (mdq allowed_dir_invalid, unrelated) and 2 fixed afterwards (citation count pinned to 55 after the adrver001 index edit; execution_snapshots inventory entry removed from tools/check_db_separation.py as fallout, plan archived so amend_plan refused); both re-run green; diff-cover N/A (deletions only); new tests fail pre-change |

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
- **Requirement ID**: `REQ-001` (DDL retirement), `REQ-005` (suite green)
- **Source issue**: `issues/20261107-203223_wfaudit010_snapshots-never-written.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: `plans/20261108-084001_wfaudit010_snapshots-never-written.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-092904
- **Related target files**: `scripts/db/schema_sql.py`, `tests/db/test_create_schema.py`
