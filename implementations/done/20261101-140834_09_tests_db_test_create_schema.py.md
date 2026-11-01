## Goal

Update the workflow DDL copy and uniqueness test in `tests/db/test_create_schema.py` and add the rename-migration test (Plan REQ-003 DDL rename, REQ-004 registered migration preserving rows).

## Scope

- DDL copy of the `tasks` table at `:386`: rename `idempotency_key` to `task_nonce` (new).
- `test_tasks_idempotency_key_unique` (`:522`): rename to `test_tasks_task_nonce_unique` (new) and adapt column names.
- Add a migration test proving AC-4 against the registry step from row 12.

## Assumptions

- Re-verified 2026-11-01: cites shifted from the Plan's original `:359`/`:495` to `:386`/`:522` (toolexec001 landed between); the Plan row was corrected in the 2026-11-01 re-verification.
- Plan overlap judgment (re-recorded): `test_create_schema.py` with dbmig001 — compatible (additive tests); the migration test mirrors the registry harness pattern from `tests/db/test_migrations_workflow.py`. That file IS modified by row 12 (legacy fixture and version/registry assertions must track the new step), so this row borrows its fixtures but does not depend on them staying byte-identical.

## Design decisions

- The migration test lives in this file (Plan's frozen row), not in `tests/db/test_migrations_workflow.py`, so no additional target file is needed.

## Alternatives considered

- Only testing fresh-creation shape: rejected — AC-4 requires proof that existing rows survive the registered `RENAME COLUMN`.

## Implementation
### Target file
`tests/db/test_create_schema.py`

### Procedure
1. Rename the column in the embedded DDL copy (`:386`).
2. Rename and adapt `test_tasks_idempotency_key_unique` (`:522`): two inserts with the same `task_nonce` (new) must hit the UNIQUE constraint; distinct UUID4s succeed.
3. Add `test_workflow_task_nonce_migration_preserves_rows` (new): build a `workflow.sqlite` at the previous version (pre-rename shape) with task rows, run the workflow registry migration (row 12's step via its `MigrationRunner` entry point), then assert every original row is present with its old key value now stored in `task_nonce` (new), the recorded version string advanced, and a downgrade or unregistered path is still refused.

### Method
Extend the existing create-schema test fixtures; mirror the ledger/backup-gate setup used by the dbmig001 tests.

### Details
- Assert both paths converge: a fresh-created database and a migrated one have identical `tasks` column lists (the registry's postcondition fingerprint depends on this).
- The refused-downgrade assertion reuses the existing version-guard tests' pattern (`create_schema.py:54-77`).

## Compatibility considerations

- High-churn file (Plan Risks: 15 commits/30d); keep additions isolated to the workflow-domain test section.

## Security considerations

- N/A: test-only change; the migration itself is exercised, not implemented, here.

## Rollback considerations

- Test additions are revertable independently of the rename unit; the uniqueness-test rename must revert with rows 03/04.

## Validation plan

- `uv run pytest tests/db/ -v` (AC-4).
- `uv run python tools/check_db_separation.py` (Plan Validation plan).

## Completion criteria

- The DDL copy matches row 04; the uniqueness test passes under the new name; the migration test proves rows preserved and `task_nonce` (new) populated from old values, with refusal of unregistered/downgrade paths (AC-3, AC-4).

## Out of Scope

- Registry implementation (row 12); production database runs (deployment phase, user decision).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-01 | 2026-11-01 | DDL copy + uniqueness test renamed; fresh-stamp assertion 2->3 |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-01 | 2026-11-01 | recovery_drill fixture DDL renamed (row 09 addition) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-01 | 2026-11-01 | cycle 2 landed: full pytest suite 10869 passed, ruff/mypy/lint-imports/bandit/check_db_separation pass |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Verification Notes (2026-11-01)
- Passed. DDL copy `idempotency_key` line confirmed at `:386`;
  `test_tasks_idempotency_key_unique` confirmed at `:522`
  (`TestCreateWorkflowSchema` spans `:423-~666`).
- Correction to Assumptions: `tests/db/test_migrations_workflow.py` is not a
  read-only reference — row 12 must update its legacy fixture, registry set
  assertion, forward-path list, version assertions, and CLI ledger
  assertions (see row 12's Verification Notes). No `tests/db/test_migrations.py`
  exists.
- Consistency addition (agreed during verification): `tests/db/test_recovery_drill.py:52`
  fixture DDL uses `idempotency_key` in a hand-rolled legacy tasks table. It
  stays valid after the rename (the drill checks table presence only), but
  row 09 renames it to `task_nonce` (new) in the same commit for repo-wide
  consistency (AC-3 wording "no remaining references" would otherwise leave
  a confusing literal).

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` (DDL copy rename), `REQ-004` (migration test)
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-140834
- **Related target files**: tests/db/test_create_schema.py, tests/db/test_recovery_drill.py (verification addition, `:52` fixture DDL consistency)