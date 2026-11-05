## Goal

Extend the shared migration runner (`scripts/shared/db_migrations.py`) with the four runner-level mechanisms of dbmigsafe001: distinct gate-family refusal reasons, a backup-API WAL-consistent dry-run snapshot, an opt-in durable pre-migration archive with a machine-readable audit artifact, and append-order ledger reads.

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `scripts/shared/db_migrations.py` plus its companion test file `tests/shared/test_db_migrations.py`.

## Assumptions

- Sequencing dependency (not a conflict) with the open Plan `plans/20261104-234502_ebschema001_separate-eventbus-schema-create-validate-migrate.md`: both target `scripts/eventbus/migrations.py`, `tests/eventbus/test_eventbus_migrations.py`, and `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`. This Plan lands first per the Plan's Scope note; ebschema001 must re-verify its rows against the post-change state.
- The Plan's UNK-01 / UNK-02 / UNK-04 `Blocking?` values are conditional on artifacts outside this Plan's scope (retention automation, ADR artifact, deployment enablement); judged non-blocking for this cycle.
- Owner decision 20261105 (Plan Blocker Log step 3): `archive_dir` is optional in the runner API; the unattended EventBus startup caller `scripts/eventbus/schema.py` L109 stays archive-less and unchanged.
- Size gate: the file is 18838 B against the 24576 B limit (~5.7 KB headroom). If the change would exceed the limit, stop and report an additional-target split (module_nodes measure/extract) before editing; do not silently exceed.

## Design decisions

- The transient gate copy and the durable archive stay two separate concepts: the archive runs between the gate and the step loop only when `archive_dir` (new) is supplied (Plan Design 1).
- `MigrationRefusalReason` gains `CHECKPOINT_BUSY` (new), `IN_MEMORY_DATABASE` (new), `NO_ARCHIVE_TARGET` (new), `ARCHIVE_FAILURE` (new); `NO_VERIFIED_BACKUP` is kept exclusively for backup-integrity and verifier failures (Plan Design 2).
- Ledger ordering keys on `rowid`, exposed as `LedgerRow.seq` (new), with no DDL change (Plan Design 5). Append-only assumption verified 20261105 (adversarial recheck): ledger writers in `scripts/` are `record_applied` (shared runner, invoked in `_apply_step` at `scripts/shared/db_migrations.py` L466), the direct baseline insert in `ensure_baseline` at `scripts/db/migrations_workflow.py` L498, and the `INSERT OR IGNORE` baseline insert at `scripts/db/create_schema.py` L99 — all INSERT-only, no UPDATE/DELETE writer exists, so `rowid` order equals application order.

## Alternatives considered

- A registered ledger `seq` column: rejected by the Plan (persisted-schema-change items 2/4/6) — `rowid` already encodes append order for append-only ledgers.

## Implementation
### Target file
`scripts/shared/db_migrations.py`
### Procedure

1. Add the four enum values and their default messages to `MigrationRefusalReason` (enum at L59-L72).
2. Route the checkpoint-busy branch (currently `NO_VERIFIED_BACKUP` at L217-L221) to `CHECKPOINT_BUSY` (new) and the in-memory refusal (L225-L229) to `IN_MEMORY_DATABASE` (new); backup-integrity (L237-L242) and verifier (L243-L253) failures keep `NO_VERIFIED_BACKUP`.
3. Replace `shutil.copyfile(db_path, tmp_path)` (L383) in the dry-run branch with a backup-API snapshot: create the temp file, `live_conn.backup()` a snapshot connection, run `_run_pre_migration_gate` against that snapshot connection, unlink the temp file as today.
4. Add `archive_pre_migration` (new) and wire an optional keyword `archive_dir` (new) through `MigrationRunner.apply` (method at L338): when non-`None`, run the archive step after `_run_pre_migration_gate` (L404) and before the step loop; dry-run never archives.
5. `read_ledger` (L132-L148): select `rowid` as `seq` and order by `rowid` instead of `applied_at, id` (L148); `LedgerRow` (L118) gains `seq: int = 0`.
6. Record in the `MigrationSpec` docstring that `postcondition` is supported for observational checks only; mutation-integrity assertions belong in `pre_commit_verification` (invoked pre-commit at L476-L477 — call site unchanged; docs 02/03 rely on it).

### Method

- `archive_pre_migration` (new) `(live_conn, archive_dir)`: write `live_conn.backup()` to `<db-stem>-v<user_version>-<utc-stamp>.sqlite` under `archive_dir`; run `PRAGMA integrity_check` on the archive; hash SHA-256 over the archive file; write a sidecar JSON audit artifact named `<archive-stem>.audit.json` (new) carrying the keys `archive_path`, `sha256`, `source_db`, `source_version` (new), `created_at`, `retention_status` (new) with `retention_status` the literal `"unset"` (UNK-01 open); a missing or unwritable directory raises `NO_ARCHIVE_TARGET` (new), any other failure raises `ARCHIVE_FAILURE` (new) — both refuse the run (fail closed). Nothing ever prunes archives. The function is public (tests call it directly) and returns a frozen `MigrationArchive` (new) dataclass `{archive_path, audit_path, sha256, source_version, created_at}`. The archive runs after `_run_pre_migration_gate` and before `ensure_ledger`, so it captures the exact pre-run database state.

### Details

- No behavior change for callers that do not pass `archive_dir` (default `None`), including `scripts/eventbus/schema.py` L109 and both dry-run call sites.
- `shutil` import may become unused after step 3 — remove it if ruff flags it.

### Companion test files
- `tests/shared/test_db_migrations.py`
  - Procedure: convert `test_missing_clean_checkpoint_refuses` (L275) and `test_backup_gate_refuses_on_bad_backup` (L260) to assert their own distinct reason values; add an in-memory-branch test; add a WAL-mode dry-run test (committed-but-uncheckpointed rows visible to the gate, live file and sidecars byte-identical); add archive tests (artifact fields, SHA-256 and source version correct, `NO_ARCHIVE_TARGET` (new) on unwritable dir); add a same-second ordering test pinning identical `applied_at` values and asserting insertion order via `seq`.
  - Validation: `uv run pytest tests/shared/test_db_migrations.py` passes with the distinct reasons observable on exception objects.

## Compatibility considerations

- Enum change is additive; the only re-routed behaviors are the checkpoint-busy and in-memory branches. Consumer CLIs map the new reasons in docs 04/05.
- `apply` gains a keyword-only default — every existing call site keeps working unchanged.
- Read order changes from `(applied_at, id)` to `rowid`: same row set, corrected order; tests that compare sets remain valid.
- Size gate headroom ~5.7 KB — see Assumptions.

## Security considerations

- The archive is a full copy of a production database: its location comes only from the operator-supplied argument and is never inferred; integrity (SHA-256 + `PRAGMA integrity_check`) and provenance are recorded in the audit artifact.

## Rollback considerations

- Single-commit revert. No DDL or persisted-state change; the only durable output is the archive file, and only when `archive_dir` is passed.

## Validation plan

- `uv run pytest tests/shared/test_db_migrations.py` — all pass; distinct reasons on exception objects.
- `rules/toolchain.md` sequence: `uv run ruff check .`, `uv run mypy scripts/`, lint-imports, bandit, `uv run pytest`, `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-003 boundary holds via the pre-commit call site (docs 02/03 consume it); AC-004: dry-run sees WAL-committed rows and leaves the live database byte-identical; AC-005: checkpoint-busy and backup-failure refusals carry different `MigrationRefusalReason` values; AC-006: ledger output preserves application order for same-second steps; AC-001 (runner half): a supplied archive target yields archive + audit artifact, and archive failure refuses the run.

## Out of Scope

- CLI flags and exit mapping (docs 04/05), registry callback conversion (docs 02/03), archive retention/pruning (UNK-01), EventBus startup-path archive wiring (`scripts/eventbus/schema.py` untouched per the 20261105 decision).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement steps 1-6 of Procedure in `scripts/shared/db_migrations.py` | Completed | 20261105-205550 | 20261105-211013 |  |
| 2 | Add companion tests in `tests/shared/test_db_migrations.py` | Completed | — | 20261105-211013 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. `check_module_size.py` | Completed | — | 20261105-211024 | targeted validation green (ruff/mypy/bandit/lint-imports/module-size/pytest tests-shared); full pytest runs after procedures 07-08 update the 3 downstream checkpoint-busy assertions |
| 4 | No docs change in this document (docs are carried by doc 09) | Completed | — | 20261105-211024 |  |

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
- **Requirement ID**: REQ-001 (durable archive), REQ-002 (WAL-consistent dry-run), REQ-004 (distinct refusal reasons), REQ-005 (append-order ledger)
- **Source issue**: issues/20261104-143443_dbmigsafe001_durable-verified-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-233415_dbmigsafe001_durable-verified-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-170302
- **Related target files**: `scripts/shared/db_migrations.py`, `tests/shared/test_db_migrations.py`