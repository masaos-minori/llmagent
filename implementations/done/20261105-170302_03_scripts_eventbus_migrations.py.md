## Goal

Move both EventBus registered specs' integrity checks from post-commit `postcondition` callbacks to pre-commit `pre_commit_verification` callbacks (REQ-003 / AC-003), and keep ledger-ordering compatibility with the shared `read_ledger` change (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `scripts/eventbus/migrations.py`. Test row is procedure document 08.

## Assumptions

- Sequencing dependency with the open Plan `plans/20261104-234502_ebschema001_separate-eventbus-schema-create-validate-migrate.md`, which also targets this file. This Plan lands first; ebschema001 must re-verify its rows against the post-change state.
- No archive wiring in this module (adversarial recheck 20261105, Plan Blocker Log step 3): the CLI archive dir is passed at the `scripts/eventbus/migrate.py` call site (procedure 05); the unattended startup caller `scripts/eventbus/schema.py` L109 keeps its archive-less behavior per the owner's runner-optional decision. Do not add `archive_dir` handling here.
- Size gate: file is 8414 B against 24576 B; ample headroom.

## Design decisions

- Rename `_postcondition_ledger_baseline` (L122-L151) → `_precommit_ledger_baseline` and `_postcondition_fingerprint` (L145-L152 area) → `_precommit_fingerprint`; assertion bodies unchanged (Plan Design 4).
- Spec field swap on both `eventbus_ledger_baseline` (L154-L160) and `eventbus_dlq_outbox` (L162-L168): `postcondition=` → `pre_commit_verification=`.
- Ledger ordering: this module does not order rows itself (`read_ledger` in `scripts/shared/db_migrations.py` does, changed in procedure 01); compatibility here means no local `applied_at`-ordered assumptions exist — verified 20261105 by grep of the module.

## Alternatives considered

- Wiring a default archive location in this module for the startup path: rejected by the 20261105 runner-optional owner decision (no location is inferred in code).

## Implementation
### Target file
`scripts/eventbus/migrations.py`
### Procedure

1. Rename the two postcondition functions to `_precommit_*` and update their docstrings to state they run pre-commit inside the step transaction.
2. Replace `postcondition=` with `pre_commit_verification=` on both registered specs; keep `mutation_sql`, versions, and `disable_foreign_keys` unchanged.
3. Leave `runner = MigrationRunner()` (L173) and the `verify_backup` import untouched.

### Method

- Rename + field swap only; no new logic in this row.

### Details

- The fingerprint check reads `scripts/shared/eventbus_schema_fingerprint.py` (reference file, unchanged here).

## Compatibility considerations

- Already-applied databases unaffected (frozen `mutation_sql`).
- `scripts/eventbus/schema.py` startup path behavior unchanged except that a failed integrity check now rolls back instead of committing-then-erroring — strictly safer, same `MigrationRefusalError`-derived `RuntimeError` wrapping at its call site.

## Security considerations

- N/A: no new surface.

## Rollback considerations

- Single-commit revert; no persisted-state change.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_migrations.py` (procedure 08 updates it) — registry pins green; pre-commit failure rolls back schema, `user_version`, ledger.
- `rules/toolchain.md` sequence incl. `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-003 for both eventbus specs; no `postcondition=` argument remains in this registry.

## Out of Scope

- Archive wiring (procedure 05), runner changes (procedure 01), tests (procedure 08), docs (procedure 09), ebschema001's registry additions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename callbacks and swap spec fields (steps 1-3) | Completed | 20261105-211532 | 20261105-211618 |  |
| 2 | Tests carried by procedure 08 (no tests in this document) | Completed | — | 20261105-211618 | test import/name renames applied with the source rename; CHECKPOINT_BUSY assertion and new pre-commit rollback tests land in procedure 08 |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. `check_module_size.py` | Completed | — | 20261105-211618 |  |
| 4 | No docs change in this document (docs are carried by doc 09) | Completed | — | 20261105-211618 |  |

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
- **Requirement ID**: REQ-003, REQ-005 (compatibility only), REQ-001 (explicitly out of this row per 20261105 recheck)
- **Source issue**: issues/20261104-143443_dbmigsafe001_durable-verified-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-233415_dbmigsafe001_durable-verified-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-170302
- **Related target files**: `scripts/eventbus/migrations.py`, `tests/eventbus/test_eventbus_migrations.py`