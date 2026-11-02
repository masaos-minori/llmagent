# rules/persisted-schema-change.md — Checklist for persisted SQLite schema changes

Planning-time checklist for any change to a persisted SQLite schema: DDL, a schema version, or a
migration step. It is guidance, not a gate: a Plan records the outcome of each item (applies,
does not apply and why, or open question) in its Design or Risks. Each item states the rule, why
it matters in this repository, and a verification (a command, a test, or the scratch-database
recipe below). Framework files are cited by path only; read them for current facts.

Framework files: `scripts/shared/db_migrations.py` (runner, ledger, refusal semantics),
`scripts/db/migrations_workflow.py` (workflow registry), `scripts/eventbus/migrations.py` and
`scripts/eventbus/migrate.py` (event bus registry and CLI), `scripts/db/schema_sql.py` and
`scripts/eventbus/schema.sql` (canonical DDL), `scripts/shared/eventbus_schema_fingerprint.py`
(shape fingerprint).

## Scratch-database recipe

Used by items 3, 4, 5 and 7. Never run it against a database under `/opt/llm/`.

1. Create a scratch database in a temporary directory with the previous canonical shape (apply the
   DDL as it was before the change), and seed rows that exercise the change: parent and child rows,
   rows with every status value, rows with NULL in nullable columns.
2. Open the connection the way production code does (foreign keys enforced for write
   connections; see `scripts/db/helper.py`), apply the candidate change through the registered
   migration step, not by hand.
3. Compare row counts per table before and after, run `PRAGMA foreign_key_check` and
   `PRAGMA integrity_check`, and compare the resulting shape with a freshly created canonical
   database (fingerprint or schema dump).
4. Record the outcome in the Plan. Existing migration tests are the template: the workflow
   registry tests in `tests/db/test_migrations_workflow.py` and the event bus ones in
   `tests/eventbus/test_eventbus_migrations.py`.

## 1. Version storage is per database, and the stores move together

- Rule: identify every place a database records its version before choosing a version number. The
  workflow database has a string marker (the `workflow_schema_version` table, written by
  `scripts/db/create_schema.py`, constant in `scripts/db/schema_sql.py`) and an integer ledger
  code (`PRAGMA user_version` stamped by each registered step; the string-to-code map and head code
  live in `scripts/db/migrations_workflow.py`). The event bus database uses `PRAGMA user_version`
  stamped by `scripts/eventbus/schema.sql` and by its registry.
- Why: updating one store and not the other makes a fresh database and a migrated one disagree,
  and the runner refuses a database whose marker is not in its map.
- Verification: `rg -n "user_version|workflow_schema_version" scripts/` lists every writer and
  reader; the Plan names each one it changes. Then the fresh-versus-migrated convergence tests
  named in the recipe pass.

## 2. A shape change moves the fingerprint, so it needs a version stamp and a baseline step

- Rule: any table, column, index, constraint, foreign key, or trigger change alters the schema
  fingerprint (`scripts/shared/eventbus_schema_fingerprint.py` for the event bus). Register a
  migration step that stamps the new version and, for a new ledger-like table, the baseline row;
  do not edit canonical DDL alone.
- Why: the startup shape gate compares a database with canonical DDL even when the version number
  matches, so an unregistered change makes existing databases fail the gate.
- Verification: recipe step 3 (fingerprint comparison); `uv run python tools/check_db_separation.py`
  for table ownership and cross-database references.

## 3. Table rebuild and foreign-key cascade

- Rule: SQLite cannot alter a column's constraints in place, so a rebuild is create, copy, drop,
  rename. `DROP TABLE` on a parent with foreign keys enforced runs an implicit delete and cascades
  to child rows. `PRAGMA foreign_keys=OFF` is a no-op inside a transaction, so a step that runs in
  the runner's transaction cannot switch it off.
- Why: a rebuild of a parent table can silently delete child rows while every check on the parent
  passes.
- Verification: recipe step 3 with child rows seeded for each rebuilt parent; row counts of child
  tables must be unchanged and `PRAGMA foreign_key_check` empty. The runner's opt-in foreign-key
  switch is planned in `plans/done/20261101-133244_dbmigrunner001_runner-unsafe-table-rebuild.md`
  and is not implemented yet; until it lands the recipe is the verification, and this item is
  updated to cite the runner contract once it exists.

## 4. NOT NULL without a default, and schema versus write path

- Rule: a new `NOT NULL` column needs a default or a backfill, and the write path must populate
  it. Schema and the code that writes the column ship in one release unit, in an order where no
  intermediate state exists in which an existing `INSERT` fails.
- Why: a `NOT NULL` column without a default makes every existing `INSERT` that omits it raise,
  including inserts in tests and in other modules.
- Verification: `rg -n "INSERT (OR \w+ )?INTO <table>" scripts/ tests/` lists every writer; each
  is updated or shown to be unaffected. Recipe step 1 seeds rows whose columns predate the change.
  Tightened constraints (`CHECK`, `NOT NULL`) need a seed with every value currently stored.

## 5. Frozen migration text versus canonical DDL

- Rule: a registered migration's SQL is frozen once released; later schema changes add new steps.
  The result of applying all steps must equal the canonical DDL.
- Why: editing an old step rewrites history for databases that already applied it, while editing
  only canonical DDL leaves migrated databases in a different shape from fresh ones.
- Verification: the fresh-versus-migrated convergence tests (`test_fresh_and_migrated_databases_converge`
  in `tests/db/test_migrations_workflow.py`, `test_fresh_baseline_and_migrated_database_are_fingerprint_equal`
  in `tests/eventbus/test_eventbus_migrations.py`) pass, and `git diff` shows no change to the text
  of an already-registered step.

## 6. Tests that pin the registry

- Rule: before registering a step, find tests that assert the registry's contents, target version,
  or version map (for example "registry is empty" or "head code equals N"), and update them in the
  same change.
- Why: such a test fails at the first registration, which is found late and looks unrelated.
- Verification: `rg -n "REGISTRY|WORKFLOW_TARGET_VERSION|WORKFLOW_VERSION_CODES|_TARGET_VERSION" tests/`
  lists the pinning tests; the Plan names the ones it updates.

## 7. Rows with an old meaning

- Rule: when a change gives existing values a new meaning, or rejects values that retained rows
  may hold (new statuses, new constraints), decide explicitly what happens to those rows: fail
  closed with the offending rows listed, map automatically, or delete. The owner confirms the
  decision before the Plan is frozen.
- Why: production data was not inspected at planning time, so the migration may meet rows the
  design never considered.
- Verification: recipe step 1 includes such rows; the step's precondition refuses and lists them,
  or the mapping is tested. The Plan names the owner decision or records it as an unknown.

## Decision: documented recipe, no probe tool

A scratch-database probe tool is not built now. Reasons: the framework already runs a fingerprint
postcondition and per-step tests; a probe needs a seed shaped per change, so reuse across Plans is
unproven; `AGENTS.md` Global Rule 7 asks for a tool after three repetitions of the same operation.
Revisit when three Plans have used the recipe, or when a Plan author reports the recipe is too
costly to repeat.

## Origin

Findings in `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md`
(read-only retroactive review) mapped to the items above.

| Historical finding in that Plan | Item |
|---|---|
| Rebuild of `tasks`, `attempts`, `processed_events` to add `CHECK` and `NOT NULL` (Design, Migration) | 3, 4 |
| `attempt_number NOT NULL` backfilled with `ROW_NUMBER()` and a unique index | 4 |
| Existing tests seeding raw status rows must use the new status vocabulary (UNK-06) | 4, 7 |
| Retained rows violating the new constraints; precondition fails closed (UNK-07, Risks) | 7 |
| Migration step registered in the workflow registry with a backup-gate rollback | 5 |
| Version numbers assigned in landing order across Plans; two Plans must not target one version | 1 (partly) |
| Schema row must land before the code rows that use it (Assumptions, execution order) | 4 |
| Registry facts such as `WORKFLOW_TARGET_VERSION` changed between drafting and implementation | 6 (partly) |
| Concurrent writers, `BEGIN IMMEDIATE`, unique-index backstop | Not covered: write concurrency, not a schema-change pitfall |
| Stale `path:line` citations re-verified | Not covered: general Plan verification, not schema-specific |
| Foreign-key cascade on rebuild, version-store split, fingerprint stamp | Not raised in that Plan; items 1, 2, 3 would have raised them at planning time |
