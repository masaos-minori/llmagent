# Runner transaction tests (failing-first)

## Goal

Add tests that pin the runner's per-step transaction contract — partial-step rollback,
in-transaction ledger row, foreign-key switch/restore, pre-commit verification — and
confirm each fails on the current `executescript` runner before procedure 01 lands
(Plan REQ-009; REQ-001..REQ-004 acceptance).

## Scope

- New test class(es) in `tests/shared/test_db_migrations.py` using the existing toy
  fixtures.
- Toy specs exercising the new `MigrationSpec` fields `disable_foreign_keys` (new) and
  `pre_commit_verification` (new) — they fail today with `TypeError` (unknown field), which
  is the intended failing-first signal.
- No production-code change in this document (procedure 01 owns it).

## Assumptions

- Existing helpers `TestMigrationFramework`, `_init_db`, `_step`, `_toy_registry`,
  `_ok_verifier`, `_failing_verifier`, `_logical_state` are reused (verified 20261102);
  extend `_step` with keyword passthroughs for the two new fields rather than a new
  builder.
- Tests open file-based SQLite fixtures only (tmp_path), default isolation and one
  `isolation_level=None` case.

## Design decisions

- Logical-state snapshot (`_logical_state`) before/after a failed apply is the
  assertion vehicle for AC-1/AC-2/AC-4: one comparable tuple instead of per-object
  asserts.

## Alternatives considered

- N/A: test structure follows the existing file's toy-registry pattern.

## Implementation
### Target file
`tests/shared/test_db_migrations.py`

### Procedure
1. Extend `_step` (new kwargs) to accept `mutation_sql` override, `disable_foreign_keys` (new)
   and `pre_commit_verification` (new) and pass them to `MigrationSpec`.
2. Add `TestStepTransaction` (new):
   - partial-step test: toy spec `1 -> 2` with mutation `CREATE TABLE toy_v2(x); INSERT
     INTO toy_v2 VALUES (1); SELECT no_such_fn(1);` → `apply` raises; `_logical_state`
     equals the pre-apply snapshot and `read_ledger` is empty (fails today: the first
     two statements persist — measured 20261102).
   - ledger-in-transaction test: passing mutation + failing `pre_commit_verification` (new)
     callback → raises; no ledger row, `user_version` unchanged, table absent.
   - in-transaction guard test: caller connection with an open transaction → clear
     `RuntimeError` naming the step.
   - isolation-mode test: the same toy step applies on a default-isolation connection
     and on an `isolation_level=None` connection (eventbus caller shape).
3. Add `TestForeignKeyStep` (new):
   - fixture: parent/child tables with a foreign key and child rows, opened with
     `PRAGMA foreign_keys=ON`.
   - rebuild step (`disable_foreign_keys=True` (new)): create new parent, copy rows,
     drop old, rename → child rows all survive; `PRAGMA foreign_keys` reads back ON
     after the step.
   - dangling variant: rebuild step that drops a parent row still referenced → step
     fails (foreign_key_check) and the whole step rolls back; snapshot unchanged;
     pragma restored.
   - refusal case: failing precondition on a `disable_foreign_keys` (new) step → pragma value
     unchanged after the refusal (AC-3).
4. Keep every new test deterministic: no wall-clock dependence beyond existing
   `_ISO8601_UTC_RE` checks.

### Method
- Pure test additions in the existing file style (module fixtures, no layer imports).

### Details
- `foreign_key_check` expectations: empty result list means pass; rows exist only for
  the dangling variant.
- Expected failure modes today: new-field specs raise `TypeError` (dataclass unknown
  kwarg); the partial-step test raises `sqlite3.OperationalError` yet leaves `toy_v2`
  behind — assert the snapshot to make the failure explicit.

## Compatibility considerations

- Existing `TestMigrationFramework` cases stay untouched and must keep passing once
  procedure 01 lands.

## Security considerations

- N/A: test-only, temporary files under tmp_path.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_db_migrations.py` before procedure 01: the new tests
  fail, old tests pass (Plan AC-8).
- After procedure 01: all pass.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages
  tests/shared/test_db_migrations.py`.

## Completion criteria

- Each new test demonstrably fails against pre-change code (recorded evidence) and
  passes after procedure 01; AC-1..AC-4 are each covered by a named test.

## Out of Scope

- Workflow-registry and CLI tests (procedure 05), runner implementation (procedure 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261102-082519 | 20261102-082831 | tests written first, confirmed failing (Plan Phase 1) |
| 2 | Add or update tests per Validation plan | Completed | — | 20261102-082831 | this document is the test row failing-first recorded: 6 new tests failed (5x TypeError unknown kwarg; partial-step AssertionError shows toy_v2 persisted); 13 passed (12 old + isolation-mode pin, which pins existing behavior) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff format/check Pass; mypy call-arg error is the failing-first type signal, resolved by procedure 01 (verified in its cycle); full-suite/coverage deferred to procedure 01 cycle per Plan failing-first design |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A N/A: test-only change, no docs/00_index.md task-scope row |

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
- **Requirement ID**: `REQ-009` (failing-first tests), `REQ-001`/`REQ-002`/`REQ-003`/
  `REQ-004` acceptance coverage
- **Source issue**: issues/20261101-133004_dbmigrunner001_runner-unsafe-table-rebuild.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-133244_dbmigrunner001_runner-unsafe-table-rebuild.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-075324
- **Related target files**: tests/shared/test_db_migrations.py