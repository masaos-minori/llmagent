## Goal

Update `tests/db/test_migrations_workflow.py` for the dbmigsafe001 behavior changes: convert the postcondition tests into pre-commit equivalents (schema/`user_version`/ledger unchanged after a failed check), pin the new gate refusal reasons, extend the CLI tests for the required `--archive-dir` and exit-code mapping, extend the `--status` semantics assertions, and add the REQ-007 restore-from-archive integration test in WAL mode.

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `tests/db/test_migrations_workflow.py`. Covers the test expectations of procedures 02 and 04.

## Assumptions

- Depends on procedures 01 (runner reasons/archive/seq), 02 (renamed `_precommit_*` callbacks), 04 (`--archive-dir`, exit mapping) being implemented first; this document is executed after them.
- Existing anchors (verified 20261105): import of `_postcondition_attempt_lease` at L29; registry field pin `assert spec.postcondition is not None` at L156; postcondition refusal tests L622-L648; gate tests L695-L727; status tests `test_status_reports_marker_and_empty_ledger` L915, `test_apply_then_status_shows_baseline_row` L939; in-process CLI tests L1085-L1112.
- The file is 46457 B; the module size gate measures only `scripts/`, so growth here is not gated.

## Design decisions

- Convert, never delete: each postcondition refusal test becomes a pre-commit refusal test that additionally snapshots `sqlite_master`, `user_version`, and the ledger before the failing step and asserts all three unchanged after the refusal (Plan Tests REQ-003).
- CLI coverage stays in-process (`migrate_db.main(argv)` call style, matching L1085-L1112) so exit codes are asserted without subprocess flakiness.

## Alternatives considered

- Keeping the direct-call postcondition unit tests unchanged: rejected — the callbacks rename and the post-commit window they tested no longer exists.

## Implementation
### Target file
`tests/db/test_migrations_workflow.py`
### Procedure

1. Rename the imported callback (`_postcondition_attempt_lease` → `_precommit_attempt_lease`, L29) and the direct-call refusal tests (L622-L648) to the pre-commit equivalents.
2. Update the registry pin test (L156 area): assert `pre_commit_verification is not None` and `postcondition is None` on all four specs (registry shape pinning, mirrors L113-style eventbus pinning).
3. Gate tests (L695-L727): `test_missing_clean_checkpoint_refuses` asserts `MigrationRefusalReason.CHECKPOINT_BUSY`; the bad-backup gate test keeps asserting `NO_VERIFIED_BACKUP`.
4. CLI tests: update `test_main_apply_in_process_migrates_copy` (L1098) and `test_main_apply_missing_db_refuses_in_process` (L1112) for `--archive-dir`; add `--apply` without `--archive-dir` → exit 2 (`EXIT_REFUSAL`); add a gate-family refusal → exit 1 (`EXIT_GATE_FAILURE`) case; add a CLI apply that asserts the archive file and its JSON audit artifact exist under the given dir with correct SHA-256 and source version (AC-001 CLI half).
5. Status tests (L915-L958): extend to pin both field names and meanings — `user_version=` integer code and `marker=` semantic string present on a fresh and an applied database (AC-007).
6. Add the REQ-007 integration test: WAL-mode database with the production-equivalent workflow schema; apply a multi-step path with a fault injected into the last step (earlier steps committed); assert the durable archive survived; restore the archive over the live database and assert rows, `user_version`, and ledger equal the pre-run snapshot (AC-002).

### Method

- In-process CLI invocation; `sqlite3` snapshots before/after for unchanged-state assertions; audit artifact parsed with `json.loads`.

### Details

- Same-second ledger order is covered in `tests/shared/test_db_migrations.py` (procedure 01 companion); this file only needs the workflow-level ordering spot-check via `LedgerRow.seq` monotonicity in the status output test.

## Compatibility considerations

- N/A: test-only.

## Security considerations

- N/A: test-only.

## Rollback considerations

- Single-commit revert together with the code rows it pins.

## Validation plan

- `uv run pytest tests/db/test_migrations_workflow.py` — all pass.
- Full `uv run pytest` and `rules/toolchain.md` sequence after the code rows land.

## Completion criteria

- AC-002 (restore integration), AC-003 (pre-commit refusal changes nothing, all four specs), AC-005 (exit-code boundary distinguishes gate vs refusal classes), AC-007 (status field semantics pinned).

## Out of Scope

- Shared-runner unit tests (procedure 01 companion `tests/shared/test_db_migrations.py`), eventbus tests (procedure 08), docs (procedure 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement steps 1-6 (test conversions, CLI/status extensions, REQ-007 integration test) | Pending | — | — | |
| 2 | Run targeted pytest: `uv run pytest tests/db/test_migrations_workflow.py` | Pending | — | — | |
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
- **Requirement ID**: REQ-003, REQ-006, REQ-007 (also pins REQ-001/REQ-004 CLI halves)
- **Source issue**: issues/20261104-143443_dbmigsafe001_durable-verified-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-233415_dbmigsafe001_durable-verified-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-170302
- **Related target files**: `tests/db/test_migrations_workflow.py`, `scripts/db/migrations_workflow.py`, `scripts/db/migrate_db.py`
