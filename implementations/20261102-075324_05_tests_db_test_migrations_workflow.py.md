# Workflow step-literal and CLI-copy tests (failing-first)

## Goal

Add tests pinning each workflow migration step's written marker literal and the CLI's
database-file option, update the existing per-step marker assertions to the pinned
values, and confirm the new expectations fail on current code before procedures 02–03
land (Plan REQ-009; REQ-005/REQ-006 acceptance).

## Scope

- New `TestStepVersionLiterals` (new) and CLI-copy cases in `tests/db/test_migrations_workflow.py`.
- Update two existing marker assertions (tool_call_state and task_nonce step tests).
- No production-code change in this document (procedures 02–03 own them).

## Assumptions

- Existing fixtures reused: `_legacy_workflow_db`, `TestWorkflowToolCallStateStep.
  _bootstrapped`, `TestWorkflowCli._run_cli` (sandboxed config dir + subprocess),
  `_write_cli_config` (verified 20261102).
- Today the step tests assert the marker `1.4.0` after each individual step (lines 290,
  434, 533); only the first two change value.

## Design decisions

- Patch-constant test asserts the invariant the literal pins: bumping
  `db.schema_sql.WORKFLOW_SCHEMA_VERSION` must not move any step's written marker.

## Alternatives considered

- N/A: follows the file's existing fixture/subprocess patterns.

## Implementation
### Target file
`tests/db/test_migrations_workflow.py`

### Procedure
1. Add `TestStepVersionLiterals` (new):
   - legacy fixture → apply `workflow_tool_call_state` → latest marker `== "1.2.0"`;
   - continue with `workflow_task_nonce` → latest marker `== "1.3.0"`;
   - continue with `workflow_attempt_lease` → latest marker `== "1.4.0"`;
   - head-constant case: `monkeypatch.setattr` a bumped value (e.g. `"9.9.9"`) on
     `db.schema_sql.WORKFLOW_SCHEMA_VERSION`, re-run the same chain (module reload is
     unnecessary once procedure 02 drops the import; keep the patch anyway as the
     regression pin) and assert the same pinned literals.
   - Failing-first evidence today: the first case writes `1.4.0` and fails.
2. Update existing assertions to the pinned values:
   - line 290 (`test_step_migrates_preserves_rows_and_stamps_marker`): `"1.4.0"` →
     `"1.2.0"`;
   - line 434 (task_nonce step test): `"1.4.0"` → `"1.3.0"`;
   - line 533 (attempt_lease step test) and line 391 (fresh-vs-migrated parity, full
     chain) stay `"1.4.0"`.
3. Add `TestWorkflowCliDbOption` (new) cases via `_run_cli`:
   - `--status --db <copy>` reports the copy's marker/ledger and the sandboxed
     configured database file is byte-identical (never opened);
   - `--dry-run --db <copy>` leaves the copy byte-identical (`_hash_file`-style
     compare);
   - `--apply --db <copy>` migrates the copy (ledger rows + `user_version` advance,
     marker chain `1.2.0`→`1.3.0`→`1.4.0` observable) while the configured file is
     untouched;
   - `--apply --db <missing path>` exits non-zero (refusal class) and creates no file.
   - Failing-first evidence today: `--db` is an unrecognized argument (argparse exit
     2, no behavior under test).

### Method
- Test additions plus two literal edits in existing assertions; fixture helpers
  unchanged.

### Details
- `_run_cli(workflow_db, config_dir, *args)` already passes the configured path via
  `_write_cli_config`; the copy path rides in `args` as `--db`.
- Byte-identity comparisons must checkpoint WAL first (existing tests close the
  connection before the subprocess for the same reason).

## Compatibility considerations

- All other existing cases in the file stay untouched and must keep passing after
  procedures 02–03 (REQ-008).

## Security considerations

- N/A: test-only, temporary files under tmp_path; subprocess argv is fixed.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/db/test_migrations_workflow.py` before procedures 02–03: new and
  updated assertions fail on current code, unrelated cases pass (Plan AC-8).
- After procedures 01–03 land: all pass.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages
  tests/db/test_migrations_workflow.py`.

## Completion criteria

- Each step's written marker is asserted at its own pinned literal regardless of the
  head constant; the CLI runs all three modes against a copy without touching the
  configured database and refuses a missing path; failures on pre-change code are
  recorded.

## Out of Scope

- Shared-runner transaction tests (procedure 04), production code (procedures 01–03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | tests written first, confirmed failing (Plan Phase 1) |
| 2 | Add or update tests per Validation plan | Pending | — | — | this document is the test row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-009` (failing-first tests), `REQ-005` (pinned markers),
  `REQ-006` (CLI database-file option)
- **Source issue**: issues/20261101-133004_dbmigrunner001_runner-unsafe-table-rebuild.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-133244_dbmigrunner001_runner-unsafe-table-rebuild.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-075324
- **Related target files**: tests/db/test_migrations_workflow.py
