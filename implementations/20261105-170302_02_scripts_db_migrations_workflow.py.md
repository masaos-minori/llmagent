## Goal

Move the mutation-integrity assertions of all four registered workflow migration specs from post-commit `postcondition` callbacks to pre-commit `pre_commit_verification` callbacks, so a failed check rolls back schema, `user_version`, and ledger together (REQ-003 / AC-003).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `scripts/db/migrations_workflow.py`. Its test row is procedure document 07.

## Assumptions

- The runner already invokes `pre_commit_verification` inside the step transaction before commit (`scripts/shared/db_migrations.py` L476-L477 call site, verified 20261105); no runner change is needed for this row beyond what procedure 01 adds.
- Changing a registered spec's verification callbacks (not its `mutation_sql` text) does not affect databases that already applied the step (Plan Assumption, `rules/persisted-schema-change.md` item 5).
- Size gate: file is 22158 B against 24576 B (~2.4 KB headroom). This change is a rename + callback-field swap; if it would grow the file past the limit, stop and report before editing.

## Design decisions

- Each `_postcondition_*` function becomes `_precommit_*` with the same assertion bodies; the spec field changes from `postcondition=` to `pre_commit_verification=` (Plan Design 4).
- `postcondition` remains a supported (now unused in this registry) runner field; do not remove it from `MigrationSpec` in this row (procedure 01 records the docstring note instead).

## Alternatives considered

- Keeping `postcondition` as a belt-and-braces second check after commit: rejected — a post-commit failure cannot roll back the step, which is the defect this row fixes.

## Implementation
### Target file
`scripts/db/migrations_workflow.py`
### Procedure

1. Rename `_postcondition_fingerprint` (L204-L218), `_postcondition_tool_state` (L268-L281), `_postcondition_task_nonce` (L331-L347), `_postcondition_attempt_lease` (L392-L409) to `_precommit_fingerprint`, `_precommit_tool_state`, `_precommit_task_nonce`, `_precommit_attempt_lease`; keep the assertion bodies byte-equivalent.
2. In `REGISTRY` (L411-L448), replace `postcondition=_postcondition_*` with `pre_commit_verification=_precommit_*` on all four specs (`workflow_ledger_baseline`, `workflow_tool_call_state`, `workflow_task_nonce`, `workflow_attempt_lease`); keep `name=`, `from_version`/`to_version`, `mutation_sql`, `disable_foreign_keys` unchanged.
3. Update any comment above `REGISTRY` that describes postconditions to describe pre-commit verification.
4. Do not touch `verify_backup` (L450-L472) or the ledger insert path (L498).

### Method

- Rename + field swap only; no new logic. `user_version`, shape, and fingerprint assertions now run while the step transaction is still open, so the runner's rollback restores the pre-step state.

### Details

- `scripts/db/schema_sql.py` marker constant and `create_schema.py` convergence paths are read-only context; unchanged.
- Existing tests import `_postcondition_attempt_lease` (e.g. `tests/db/test_migrations_workflow.py` L29); the import rename is carried by procedure document 07, not here.

## Compatibility considerations

- Databases that already applied these steps are unaffected (frozen `mutation_sql` text).
- `migrate_db.py` and `create_schema.py` call through `runner.apply`; the exception type raised on a failed check is unchanged (`MigrationRefusalError`), so CLI exit mapping (procedure 04) is unaffected.

## Security considerations

- N/A: no new surface; the change strictly narrows the window in which a broken schema can be committed.

## Rollback considerations

- Single-commit revert; no persisted-state change.

## Validation plan

- `uv run pytest tests/db/test_migrations_workflow.py` (updated in procedure 07) — pre-commit failure asserts schema, `user_version`, and ledger unchanged.
- `rules/toolchain.md` sequence incl. `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-003: a failed `pre_commit_verification` changes neither schema, `user_version`, nor ledger, for all four workflow specs.
- No `postcondition=` argument remains in `REGISTRY`.

## Out of Scope

- Runner-side changes (procedure 01), CLI flags (procedure 04), test updates (procedure 07), docs (procedure 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename postcondition functions and swap spec fields (steps 1-4) | Pending | — | — | |
| 2 | Tests carried by procedure 07 (no tests in this document) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. `check_module_size.py` | Pending | — | — | |
| 4 | No docs change in this document (docs are carried by doc 09) | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261104-143443_dbmigsafe001_durable-verified-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-233415_dbmigsafe001_durable-verified-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-170302
- **Related target files**: `scripts/db/migrations_workflow.py`, `tests/db/test_migrations_workflow.py`
