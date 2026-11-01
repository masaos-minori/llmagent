# Runner per-step transaction contract

## Goal

Make `MigrationRunner` run each step — its statements, the ledger row, and any
pre-commit verification — inside one runner-owned write transaction with an optional
foreign-key switch, so a failing step leaves no partial change (Plan REQ-001, REQ-002,
REQ-003, REQ-004; REQ-007 docstring correction; REQ-008 unchanged behavior for
registered steps).

## Scope

- `MigrationSpec`: add `disable_foreign_keys` (new) and `pre_commit_verification` (new) fields.
- `_apply_step`: replace `executescript` with explicit `BEGIN IMMEDIATE`, individual
  statement execution, in-transaction ledger write, optional `PRAGMA foreign_key_check`
  and pre-commit callback, single `commit`, `finally` restore of the foreign-key
  setting.
- `apply`: drop the separate `record_applied` + `commit` after each step (the write
  moves into `_apply_step`).
- Docstrings of `_apply_step` and `apply` corrected to the real contract.
- No registry, schema, or domain changes (rows 02–03 own those).

## Assumptions

- Measured 20261102 on this repo's Python: `executescript` is non-atomic — after a
  3-statement script whose third statement fails, the first two persist. The Plan's
  defect claim is confirmed.
- `PRAGMA foreign_keys` is a no-op inside a transaction: switch OFF only before
  `BEGIN` and restore only after commit/rollback, in `finally`.
- The runner's own `ensure_ledger` + `conn.commit()` before the loop leaves no open
  transaction at step start; guard `conn.in_transaction` with a clear error per the
  Plan's risk mitigation.
- `sqlite3.complete_statement` accumulation splits trigger bodies correctly (Plan
  Assumption; registered steps contain plain DDL/DML only).
- Tests for this row are procedures 04 (`tests/shared/test_db_migrations.py`) and part
  of 05; per the Plan's Phase 1 (failing-first), those documents execute before this
  one.

## Design decisions

- Runner owns the transaction: explicit `BEGIN IMMEDIATE`, one `commit`, rollback on
  any failure; `isolation_level` of caller connections untouched otherwise (eventbus
  callers use plain `sqlite3.connect`).
- Foreign-key control is opt-in per step (`disable_foreign_keys` (new), default off meaning
  enforcement untouched); previous pragma value is read and restored, not forced ON.

## Alternatives considered

- Keep `executescript` and embed `BEGIN`/`COMMIT` in step SQL — rejected (Plan Design
  1: `executescript` commits pending transactions first; that is the defect).
- Per-step savepoints — rejected: cannot switch foreign keys and adds nothing over a
  top-level transaction.

## Implementation
### Target file
`scripts/shared/db_migrations.py`

### Procedure
1. Add to `MigrationSpec` (frozen dataclass): `disable_foreign_keys` (new) `bool = False`
   and `pre_commit_verification` (new) `Callable[[sqlite3.Connection], None] | None =
   None`.
2. Add module-level `_split_statements` (new) `(sql: str) -> list[str]`: accumulate
   fragments and cut where `sqlite3.complete_statement` returns true on the
   accumulated text; skip empty/whitespace-only fragments.
3. Rewrite `_apply_step` to the order fixed in the Plan (line 40): run
   `preconditions`; if `spec.disable_foreign_keys`: read `PRAGMA foreign_keys` into a
   saved value and set it OFF (still outside any transaction); guard
   `conn.in_transaction` (raise `RuntimeError` naming the step id if already open);
   `conn.execute("BEGIN IMMEDIATE")`; for each statement of
   `_split_statements(spec.mutation_sql)`: `conn.execute(...)`; `record_applied(conn,
   spec)` inside the same transaction; if enforcement was switched off: any row from
   `PRAGMA foreign_key_check` → rollback and raise; run `pre_commit_verification` (new) if
   set; `conn.commit()`; on any `Exception`: `conn.rollback()` and re-raise; `finally`:
   if switched, restore the saved `PRAGMA foreign_keys` value. A spec with empty
   `mutation_sql` still runs preconditions, the ledger write, and the commit in one
   transaction.
4. In `apply`'s step loop: call `self._apply_step(conn, spec)` only (remove the
   separate `record_applied(conn, spec)` and `conn.commit()`); keep the post-commit
   `spec.postcondition(conn)` call and the `LedgerRow` built from
   `read_ledger(conn)[-1].applied_at` (the row now lands during `_apply_step`; read
   after commit).
5. Update the `_apply_step` docstring (current text wrongly claims `executescript`
   runs all statements in one implicit transaction) and the `apply` docstring step
   order (preconditions → optional FK switch → BEGIN → statements → ledger row →
   foreign_key_check → pre-commit verification → commit → postcondition re-check → FK
   restore in `finally`) per REQ-007.

### Method
- Edit in place; keep the module stdlib-only (`shared` leaf contract).
- `import sqlite3` already present; `sqlite3.complete_statement` needs no new import.

### Details
- Current code references: `MigrationSpec` fields (`id`, `from_version`,
  `to_version`, `preconditions`, `mutation_sql`, `postcondition`); `_apply_step` ends
  `conn.executescript(spec.mutation_sql); conn.commit()` with `except
  sqlite3.Error: conn.rollback(); raise`; `apply` loop lines call `self._apply_step`,
  then `record_applied` + `conn.commit()`, then `postcondition`.
- `record_applied` already inserts via bound parameters; calling it while a
  transaction is open just enlists in it — no signature change.
- Failure of a mid-list statement, a `foreign_key_check` row, or a failing
  `pre_commit_verification` (new) must all leave schema, `user_version`, and the ledger
  unchanged (AC-1, AC-2, AC-4).
- Module size: 15651 B today against the 20480 B gate; the added helper and
  transaction code are expected to fit (`tools/check_module_size.py` validates).

## Compatibility considerations

- Registered workflow/eventbus steps contain only plain statements; splitting is
  behavior-identical (REQ-008 regression rows 05 and eventbus test runs).
- Callers (`db.migrate_db`, `db.migrations_workflow`, `eventbus.migrate`,
  `eventbus.schema.open_db`) keep their connection styles; the runner must not assume
  `foreign_keys=ON` (eventbus connections have it off) and restores whatever it read.
- `postcondition` semantics unchanged (still post-commit); `dry_run` path untouched.

## Security considerations

- No new dynamic SQL: statement text comes from registry constants; ledger insert
  stays parameter-bound. Keep existing `# nosec B608` justifications where lines move.

## Rollback considerations

- Single revert commit restores `executescript` behavior; no schema or data change to
  undo (the runner change mutates no database by itself).

## Validation plan

- `uv run pytest tests/shared/test_db_migrations.py` (tests added by procedure 04 must
  pass; old tests unchanged) and `uv run pytest tests/db/test_migrations_workflow.py
  tests/eventbus/test_eventbus_migrations.py tests/eventbus/test_eventbus_db_migration.py
  tests/deploy/test_init_db_ledger_gate.py` (REQ-008 regression).
- `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages
  scripts/shared/db_migrations.py`, `uv run bandit -r scripts/ -c pyproject.toml`.
- `PYTHONPATH=scripts uv run lint-imports` (6 contracts kept) and `uv run python
  tools/check_module_size.py`.
- `uv run radon cc scripts/shared/db_migrations.py -s`: baseline `plan` C(14),
  `apply` B(8), `_apply_step` A(4); no function worse than one grade up.

## Completion criteria

- A mid-step failure leaves schema, `user_version` and ledger untouched; the ledger row
  commits in the same transaction as its step; the foreign-key pragma holds its prior
  value after success, failure and refusal; the new fields exist and default values
  leave every existing registered step's observable result identical.

## Out of Scope

- Registry steps and version literals (procedure 02), CLI option (procedure 03), test
  files (procedures 04–05), docs text (procedure 06), `postcondition` repositioning
  (Plan UNK-01 keeps it post-commit).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Confirm tests from procedures 04–05 pass after this change | Pending | — | — | failing-first: they are added before this step |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | docs row is procedure 06 |

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
- **Requirement ID**: `REQ-001` (runner-owned step transaction), `REQ-002` (ledger in
  the step transaction), `REQ-003` (opt-in foreign-key switch and restore), `REQ-004`
  (pre-commit verification), `REQ-007` (docstring accuracy), `REQ-008` (compatibility)
- **Source issue**: issues/20261101-133004_dbmigrunner001_runner-unsafe-table-rebuild.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-133244_dbmigrunner001_runner-unsafe-table-rebuild.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-075324
- **Related target files**: scripts/shared/db_migrations.py
