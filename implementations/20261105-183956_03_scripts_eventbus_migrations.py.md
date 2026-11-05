## Goal

Register the `eventbus_dlq_outbox_fk_dedup` (new) forward migration step (5 -> 6) that rebuilds `dlq_outbox` down to a single inline foreign key, so a `3 -> 4 -> 5 -> 6` migrated database converges on the canonical version-6 fingerprint (REQ-005, REQ-006 / AC-003, AC-005, AC-006).

## Scope
**Release unit**: canonical-version-6

## Assumptions
- The frozen 4 -> 5 `_DLQ_OUTBOX_SQL` (L58-L70) is byte-identical in shape to the double-FK `dlq_outbox` in `schema.sql` prior to this Plan; this Plan edits neither its text nor its version (`_OUTBOX_VERSION = 5`). The 5 -> 6 rebuild produces the post-dedup single-FK v6 shape that `schema.sql` (seq 02) now stamps.
- `assert_matches` compares the structural fingerprint only (not `user_version`), so after the rebuild the rebuilt `dlq_outbox` (single FK, version 6) equals the fresh v6 fingerprint; the version half is enforced separately by `validate_canonical` (new, seq 04) on the create path.
- The runner (`scripts/shared/db_migrations.py`) runs `precondition` before the transaction, `PRAGMA foreign_keys=OFF` outside the transaction, then inside one transaction: the `mutation_sql` statements, the ledger row, `PRAGMA foreign_key_check` (because `disable_foreign_keys=True`), any `pre_commit_verification`, then commit; a failure rolls back schema, `user_version`, and ledger together. `postcondition` re-checks after commit.
- The `disable_foreign_keys` switch is required: dropping and renaming a table that participates in a foreign key while enforcement is ON is unsafe; the runner restores the prior `PRAGMA foreign_keys` value in `finally`.

## Design decisions
- Create-copy-drop-rename with a uniquely named intermediate table (`dlq_outbox_v6` (new)) so the rebuild never collides with the live `dlq_outbox`; recreate `idx_dlq_outbox_status` explicitly after the rename so the index definition is identical to the canonical one (SQLite renames follow the table, but recreating guarantees the exact fingerprinted index).
- Use `disable_foreign_keys=True` plus the runner's automatic `PRAGMA foreign_key_check` for referential-integrity, and `pre_commit_verification=_postcondition_fingerprint` (a full `assert_matches` inside the transaction) to guarantee the rebuilt shape equals canonical before commit.
- Keep the new step's SQL in separate constants next to the frozen `_DLQ_OUTBOX_SQL` so the frozen block stays visually and textually isolated from the new one.

## Alternatives considered
- Editing the frozen 4 -> 5 `_DLQ_OUTBOX_SQL` to the single-FK shape: rejected — rules item 5 forbids editing the released 4 -> 5 SQL, and the v5 intermediate must stay double-FK so the fingerprint comparison against the frozen step's output stays valid.
- Bumping the version in `schema.sql` alone and skipping a registered step: rejected — the FK dedup is a shape change, and rules item 2 requires a version-stamped registered step for any shape change (AC-003).

## Implementation
### Target file
`scripts/eventbus/migrations.py`

### Procedure
1. Add the version-6 constant directly after `_OUTBOX_VERSION = 5` (L39): `_FK_DEDUP_VERSION` (new) = 6.
2. Add the rebuild SQL constants immediately after the frozen `_DLQ_OUTBOX_SQL` / `_OUTBOX_MUTATION_SQL` block (after L72), without touching the frozen block:
   - `_FK_DEDUP_CREATE_SQL` (new): `CREATE TABLE dlq_outbox_v6 (...)` with the **single inline** `PRIMARY KEY REFERENCES events(event_id)` and the same columns and `status` CHECK vocabulary as `_DLQ_OUTBOX_SQL`.
   - `_FK_DEDUP_COPY_SQL` (new): `INSERT INTO dlq_outbox_v6 (event_id, requested_at, status, attempts, last_error, next_attempt_at, completed_at) SELECT ... FROM dlq_outbox;`
   - `_FK_DEDUP_RENAME_SQL` (new): `DROP TABLE dlq_outbox; ALTER TABLE dlq_outbox_v6 RENAME TO dlq_outbox;`
   - `_FK_DEDUP_INDEX_SQL` (new): `CREATE INDEX IF NOT EXISTS idx_dlq_outbox_status ON dlq_outbox(status, next_attempt_at);`
   - `_FK_DEDUP_MUTATION_SQL` (new): the f-string concatenation of the four above ending with ` PRAGMA user_version = {_FK_DEDUP_VERSION};`.
3. Add `_precondition_fk_dedup_step` (new) next to `_precondition_outbox_step`: refuse unless `user_version == _OUTBOX_VERSION` (5), `schema_migrations` is present (forged-stamp guard), the core `_REQUIRED_TABLES` are present, and `dlq_outbox` is present (there is nothing to rebuild otherwise).
4. Register `eventbus_dlq_outbox_fk_dedup` (new) in `REGISTRY` after the `eventbus_dlq_outbox` entry: `from_version=_OUTBOX_VERSION`, `to_version=_FK_DEDUP_VERSION`, `preconditions=(_precondition_fk_dedup_step,)`, `mutation_sql=_FK_DEDUP_MUTATION_SQL`, `disable_foreign_keys=True`, `pre_commit_verification=_postcondition_fingerprint`, `postcondition=_postcondition_fingerprint`.
5. Update the module docstring (L4-L7) to record the three-step chain `3 -> 4 -> 5 -> 6` and name the new `eventbus_dlq_outbox_fk_dedup` (new) rebuild step.

### Method
- The rebuild is a single-transaction shape surgery: disable FK enforcement, materialize the single-FK copy, transfer rows, drop the old table, rename into place, recreate the index, stamp version 6, record the ledger row, then the runner's `PRAGMA foreign_key_check` and `pre_commit_verification` (`assert_matches`) confirm integrity and shape before commit.
- `pre_commit_verification` runs inside the transaction so a shape mismatch rolls back the whole step (schema, `user_version`, ledger unchanged); `postcondition` re-verifies after commit for defense in depth.

### Details
- Pre-change anchors: L36-L39 (`_OUTBOX_VERSION = 5`), L55-L72 (frozen `_DLQ_OUTBOX_SQL` + `_OUTBOX_MUTATION_SQL` — do NOT edit), L162-L169 (existing `eventbus_dlq_outbox` registry entry), L153-L170 (REGISTRY dict).
- `_FK_DEDUP_CREATE_SQL` (new) must keep the exact `CHECK (status IN ('pending', 'done', 'failed'))` clause and column order so the rebuilt table's fingerprint matches canonical; the intermediate table name `dlq_outbox_v6` (new) is dropped by the rename and never appears in the fingerprint.
- The differing-version refusal message may carry the numeric version (schema, not data); it must not name row content.
- Layering unchanged: this module still imports only `shared.db_migrations` and `shared.eventbus_schema_fingerprint`; no `db.*` import is introduced.

### Companion test files
- `tests/eventbus/test_eventbus_migrations.py`
  - Procedure: (a) `test_registry_holds_both_registered_steps` (L113-L122) — extend the registry pin to `["eventbus_ledger_baseline", "eventbus_dlq_outbox", "eventbus_dlq_outbox_fk_dedup"]` and assert the new step's `from_version == 5`, `to_version == 6`, non-empty `mutation_sql`, `disable_foreign_keys`, and `pre_commit_verification`; (b) `test_runner_resolves_the_unique_forward_path` (L124-L134) — `target_version=5` -> `6` and add `"eventbus_dlq_outbox_fk_dedup"` to the planned list; (c) `test_apply_migrates_and_preserves_rows_and_fingerprint` (L136-L181) — `target_version=5` -> `6`, final `user_version == 6`, and add the third ledger row `{("eventbus_dlq_outbox_fk_dedup", 5, 6)}`; (d) `test_fresh_baseline_and_migrated_database_are_fingerprint_equal` (L234-L250) — `runner.plan(3, ..., 5)` -> `6` so both sides carry the single FK (otherwise the fingerprint comparison fails on the FK difference); (e) add a `TestEventbusFkDedupStep` (new) class covering: rebuild preserves all `dlq_outbox` rows and the status CHECK vocabulary and recreates `idx_dlq_outbox_status`; `PRAGMA foreign_key_list(dlq_outbox)` returns exactly one entry after the step; a pre-commit verification failure (seed a dangling reference before the step) rolls back schema, `user_version`, and ledger together; the precondition refuses a forged version-5 stamp missing `schema_migrations` and a version-5 database missing `dlq_outbox`. A `_baseline_v5_db` (new) helper (build via `apply_schema_in_memory`/`schema.sql`, then set `user_version = 5`) supports these.
  - Validation: `uv run pytest tests/eventbus/test_eventbus_migrations.py -q`.

## Compatibility considerations
- The 4 -> 5 step's frozen `_DLQ_OUTBOX_SQL` keeps its two-FK shape; the comment at L55-L57 ("byte-identical in shape to the same block appended to scripts/eventbus/schema.sql") is now imprecise because canonical `schema.sql` is single-FK (v6) while the v5 intermediate is double-FK; seq 02 updates that comment.
- Startup wiring (`scripts/eventbus/schema.py`) and the CLI (`scripts/eventbus/migrate.py`) consume `REGISTRY` by iteration, so the added step extends the forward path automatically; re-verify the startup auto-migration reaches version 6 (companion `test_eventbus_schema_version.py`, seq 02).

## Security considerations
- `disable_foreign_keys` during the rebuild is scoped to the single runner-owned transaction and restored afterward; the post-mutation `PRAGMA foreign_key_check` rejects any dangling reference before commit, so the rebuild cannot leave a partially-linked `dlq_outbox`.

## Rollback considerations
- Remove the `_FK_DEDUP_VERSION` (new) / `_FK_DEDUP_*_SQL` constants, `_precondition_fk_dedup_step` (new), the registry entry, and revert the docstring; the frozen 4 -> 5 block is untouched.

## Validation plan
- Unit: the new `TestEventbusFkDedupStep` (new) rebuild/preserve/single-FK/rollback/precondition tests.
- Convergence: `test_fresh_baseline_and_migrated_database_are_fingerprint_equal` at `target_version=6` (fresh v6 vs migrated v6 fingerprint-equal, one FK entry).
- Static + layer: `lint-imports`, `tools/check_db_separation.py`, full suite.

## Completion criteria
- `REGISTRY` holds the three ordered steps `eventbus_ledger_baseline` (3->4), `eventbus_dlq_outbox` (4->5), `eventbus_dlq_outbox_fk_dedup` (new) (5->6); the frozen 4 -> 5 SQL is byte-identical.
- The 5 -> 6 step rebuilds `dlq_outbox` to one FK, preserves rows and `idx_dlq_outbox_status`, and rolls back atomically on any integrity/shape failure.
- The companion migration tests pass.

## Out of Scope
- The `schema.sql` version bump and FK removal (seq 02), the fingerprint contract extension (seq 04), the `create_eventbus_schema` three-path rewrite (seq 01), the equivalence test (seq 06), and the doc corrections (seq 09, seq 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Register the 5 -> 6 `eventbus_dlq_outbox_fk_dedup` (new) rebuild step in `scripts/eventbus/migrations.py` | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-005`, `REQ-006`
- **Source issue**: issues/20261104-143443_ebschema001_separate-eventbus-schema-create-validate-migrate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-234502_ebschema001_separate-eventbus-schema-create-validate-migrate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-183956
- **Related target files**: `scripts/eventbus/migrations.py`, `tests/eventbus/test_eventbus_migrations.py`
