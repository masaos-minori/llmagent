## Goal

Update `tests/eventbus/test_eventbus_migrations.py` for dbmigsafe001: pin the registry's new `pre_commit_verification` callbacks, convert the ledger-baseline postcondition refusal tests to pre-commit equivalents, pin the distinct gate refusal reasons, and replace the same-second ledger caveat with a `seq`-based order assertion (REQ-003, REQ-004, REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `tests/eventbus/test_eventbus_migrations.py`. Covers the test expectations of procedures 03 and 05.

## Assumptions

- Depends on procedures 01 (reasons + `LedgerRow.seq`), 03 (renamed `_precommit_*` callbacks), 05 (CLI `--archive-dir`/exit mapping) being implemented first.
- Existing anchors (verified 20261105): `test_registry_holds_both_registered_steps` L113; `test_ledger_baseline_postcondition_refuses_unstamped_result` L333, `..._missing_ledger` L343, `..._missing_core_tables` L352; `test_missing_clean_checkpoint_refuses` L399; `test_dry_run_leaves_file_byte_identical` L424; `test_backup_gate_refuses_on_bad_backup` L439.
- Sequencing dependency with the open ebschema001 Plan (also edits this file later); this Plan lands first.

## Design decisions

- Registry pin becomes: both specs have `pre_commit_verification` set and `postcondition` unset — mirrors the workflow pin (procedure 07 step 2) so a regression that re-adds a postcondition fails here.
- The three `test_ledger_baseline_postcondition_refuses_*` tests (L333-L352) call the renamed `_precommit_ledger_baseline` directly and additionally assert nothing changed when run against a failing database copy (schema, `user_version`, ledger snapshots before/after).

## Alternatives considered

- Deleting the direct-call refusal tests and relying only on runner-level rollback tests: rejected — the plan mandates conversion, not deletion (Plan Tests REQ-003).

## Implementation
### Target file
`tests/eventbus/test_eventbus_migrations.py`
### Procedure

1. Update the registry pin test (L113): assert `pre_commit_verification` is not `None` and `postcondition` is `None` on both registered specs; import names follow procedure 03's renames.
2. Convert the three ledger-baseline refusal tests (L333-L352) to the `_precommit_ledger_baseline` equivalents with unchanged-state snapshots.
3. `test_missing_clean_checkpoint_refuses` (L399): assert `MigrationRefusalReason.CHECKPOINT_BUSY`; `test_backup_gate_refuses_on_bad_backup` (L439) keeps `NO_VERIFIED_BACKUP`.
4. Ledger ordering: locate the same-second caveat comment in the ledger assertions and replace it with an explicit test — record three ledger rows with identical `applied_at` values via `record_applied` and assert `read_ledger` returns them in insertion order via `LedgerRow.seq` (AC-006 through the eventbus ledger).
5. Add `--apply` without `--archive-dir` CLI coverage for the EventBus CLI (procedure 05): in-process `migrate.main(argv)` returns `EXIT_REFUSAL` (2).

### Method

- In-process invocation and direct callback calls with `sqlite3` before/after snapshots; no subprocesses (matches the file's existing style).

### Details

- The fingerprint equality tests (L234) and row-preservation tests (L136) must stay green through the callback move without edits — they are the behavior-lock for REQ-003.

## Compatibility considerations

- N/A: test-only.

## Security considerations

- N/A: test-only.

## Rollback considerations

- Single-commit revert together with the code rows it pins.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_migrations.py` — all pass.
- Full `uv run pytest` and `rules/toolchain.md` sequence after the code rows land.

## Completion criteria

- AC-003 for both eventbus specs; AC-005 through the shared gate reasons; AC-006 via `seq` ordering on the eventbus ledger.

## Out of Scope

- Shared-runner unit tests (procedure 01 companion), workflow tests (procedure 07), docs (procedure 09), ebschema001's future registry additions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement steps 1-5 (registry pin, refusal conversions, reason pins, seq ordering, CLI coverage) | Pending | — | — | |
| 2 | Run targeted pytest: `uv run pytest tests/eventbus/test_eventbus_migrations.py` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
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
- **Requirement ID**: REQ-003, REQ-004, REQ-005 (also pins REQ-001 CLI half)
- **Source issue**: issues/20261104-143443_dbmigsafe001_durable-verified-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-233415_dbmigsafe001_durable-verified-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-170302
- **Related target files**: `tests/eventbus/test_eventbus_migrations.py`, `scripts/eventbus/migrations.py`, `scripts/eventbus/migrate.py`
