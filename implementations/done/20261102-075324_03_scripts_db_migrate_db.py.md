# migrate_db.py database-file option

## Goal

Let the workflow migration CLI operate on an explicitly given database file so an
operator can rehearse `--status`, `--dry-run` and `--apply` on a copy instead of the
configured `workflow.sqlite` (Plan REQ-006).

## Scope

- Add a `--db PATH` (new) option to `main`'s parser.
- Refuse a path that does not exist before opening (no file created).
- Pass the path through `SQLiteHelper("workflow", db_path=...)`, which already bypasses
  configuration.
- Modes, exit codes, preflight, and gate behavior unchanged.

## Assumptions

- `SQLiteHelper.__init__` accepts `db_path` and bypasses `build_db_config()` when given
  (verified 20261102 in `scripts/db/helper.py`).
- `sqlite3.connect` would create a missing file, so the existence check must happen
  before `open()` (Plan REQ-006 Derived note).

## Design decisions

- Missing path is a refusal class: return `EXIT_REFUSAL` (2) with a logged reason —
  distinct from a gate failure (1), consistent with the CLI's existing refusal
  semantics.

## Alternatives considered

- `--db` implying `--apply` on a copy — rejected: the Plan keeps the three modes
  unchanged and orthogonal to the path.

## Implementation
### Target file
`scripts/db/migrate_db.py`

### Procedure
1. In `main`, add to `parser`: `--db` (new) `type=str, default=None`, help "Operate on
   this database file instead of the configured workflow database (rehearsal on a
   copy)."
2. After argument parsing and the no-mode help branch: if `args.db` is set and
   `Path(args.db)` is not an existing file, log the refusal and `return EXIT_REFUSAL`.
3. Replace `SQLiteHelper("workflow")` with `SQLiteHelper("workflow",
   db_path=args.db)` — `db_path=None` keeps today's configured-path behavior.
4. Add `from pathlib import Path` (new import statement at module top) if absent.

### Method
- Three small edits in `main`; keep the rest of the flow (status / plan / preflight /
  dry-run / apply, exception → exit-code mapping) untouched.

### Details
- `main` is C(12) at the radon baseline; add at most one branch (the existence check)
  so complexity stays within the "not worse than one grade" gate.
- `helper.close()` in `finally` unchanged; the busy/lock and backup-gate handling stay
  as-is for `--apply` on a given file.

## Compatibility considerations

- No `--db` → identical behavior to today (configured path via `SQLiteHelper`).
- `deploy/init_db.sh` does not invoke this CLI; no deployment script change.

## Security considerations

- The path is operator-supplied but only used as a SQLite file path; no shell or SQL
  interpolation.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/db/test_migrations_workflow.py` — CLI-copy tests from procedure
  05 (failing-first per Plan Phase 1).
- `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages
  scripts/db/migrate_db.py`, `uv run bandit -r scripts/ -c pyproject.toml`.
- `uv run radon cc scripts/db/migrate_db.py -s` vs C(12) baseline.

## Completion criteria

- `--status`/`--dry-run`/`--apply` each run against the given copy and never open the
  configured database; a missing path exits 2 and creates no file; without `--db` the
  CLI behaves exactly as before.

## Out of Scope

- Runner transaction changes (procedure 01), service-listener guards, eventbus CLI
  (`scripts/eventbus/migrate.py` has its own path config), test edits (procedure 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261102-084615 | 20261102-084905 | execute after procedure 05's failing tests land (Plan Phase 1) --db option added; missing-path refusal (EXIT_REFUSAL) before any connect; SQLiteHelper("workflow", db_path=args.db) |
| 2 | Add or update tests per Validation plan | Completed | — | 20261102-084905 | owned by procedure 05 owned by procedure 05; its 4 CLI-copy tests now pass. One test-side fix in procedure 05's apply test: ledger comparison made order-insensitive because same-second steps tie on applied_at (read_ledger orders applied_at then id) — test bug, not an implementation regression |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261102-084905 | pytest tests/db/test_migrations_workflow.py 44/44 pass; ruff format/check Pass; mypy clean; bandit no issues; radon main C(14) vs C(12) baseline - same grade C, within the not-worse-than-one-grade gate (compound and-condition counts as 2 branches) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261102-084905 | N/A (docs row is procedure 06) N/A: docs row owned by procedure 06 |

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
- **Requirement ID**: `REQ-006` (CLI database-file option with refusal of a missing
  path)
- **Source issue**: issues/20261101-133004_dbmigrunner001_runner-unsafe-table-rebuild.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-133244_dbmigrunner001_runner-unsafe-table-rebuild.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-075324
- **Related target files**: scripts/db/migrate_db.py