## Goal
Remove the tests of the legacy offset import, keep the retained file-helper collision tests under their own class, and add a test that a non-empty `offsets_dir` is neither read nor modified by startup (REQ-002).

## Scope
- Delete `TestLegacyOffsetMigrationHttp` and the migration tests inside `TestLegacyOffsetMigrationDirect`; keep every other test class unchanged.

## Assumptions
- After the last migration test of `TestLegacyOffsetMigrationDirect`, the file has a stray docstring ("Tests for REQ-001: identity validation before offset comparison.") followed by three tests that call only `write_offset` (`test_collision_rejected_for_equal_seq`, `..._lower_seq`, `..._higher_seq`); they belong to the retained helpers and must survive (verified).
- The `client` fixture builds the app config with `offsets_dir=tmp_path/"offsets"` and starts the app inside `with TestClient(...)`, so files seeded in that directory before the fixture runs exist at startup.

## Design decisions
- Delete by method/class; re-home the three collision tests by giving them a class header that describes identity validation (for example `TestFileOffsetIdentityValidation` (new)), fixing the stray docstring.
- New test: a fixture `legacy_offset_files` (new) (listed before `client` in the test signature so pytest runs it first) creates `tmp_path/"offsets"` with an offset file and a `.map` file; after startup the test asserts `consumer_offsets` has no row for that consumer and the file bytes and mtime are unchanged.

## Alternatives considered
- Parametrizing the `client` fixture to seed files: rejected, a separate seeding fixture keeps the existing fixture unchanged.

## Implementation
### Target file
`tests/eventbus/test_eventbus_offsets.py`

### Procedure
1. Delete `TestLegacyOffsetMigrationHttp` entirely.
2. In `TestLegacyOffsetMigrationDirect`, delete `test_migration_is_idempotent`, `test_migration_multi_consumer`, `test_migration_missing_map_companion_falls_back`, `test_migration_collision_detected_for_sanitized_name_overlap`; then add a class header for the three remaining collision tests and fix their docstring.
3. Add the `legacy_offset_files` (new) fixture and the "offsets_dir ignored and unmodified" test.
4. Remove imports left unused after the deletions.

### Method
- Use `Path.read_bytes()` and `stat().st_mtime_ns` to assert the files are unchanged; query `consumer_offsets` through `client.app.state.db`.
- Run `rg "migrate_legacy_offsets" tests` afterwards (no match expected).

### Details
- Keep `TestConsumerIdSanitization`, `TestFileOffsetMonotonicity`, `TestSqliteOffsetMonotonicity`, `TestConsumerOffsetsTable`, `TestCrashResistance`, and `TestMalformedContent` untouched.

## Compatibility considerations
N/A: test-only; ACK-advanced and resume tests are unchanged.

## Security considerations
N/A: temporary files only.

## Rollback considerations
N/A: revert the commit with the source change.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_offsets.py tests/eventbus/test_eventbus_restart_resume.py tests/eventbus/test_eventbus_startup.py -q`, then the full suite once.
- `uv run ruff format`/`check` on the file.

## Completion criteria
- No test references `migrate_legacy_offsets`; the three collision tests still pass; the new test passes and fails if startup reads or modifies the files.

## Out of Scope
- File-helper tests other than the re-homed ones.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the import tests; re-home the collision tests | Completed | 20261022-114126 | 20261022-114126 | Changed: tests/eventbus/test_eventbus_offsets.py |
| 2 | Add the untouched-`offsets_dir` fixture and test | Completed | 20261022-114126 | 20261022-114126 | validated; full suite 9686 passed, 14 skipped; ruff, mypy, lint-imports, check_module_size pass; offset, resume, startup tests pass; new untouched-offsets_dir test added |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261022-114126 | 20261022-114126 | validated; full suite 9686 passed, 14 skipped; ruff, mypy, lint-imports, check_module_size pass; offset, resume, startup tests pass; new untouched-offsets_dir test added |

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
- **Requirement ID**: `REQ-002` (remove import tests, keep helper tests, add the untouched-files test)
- **Source issue**: `issues/20261021-102244_rmoffimp_remove-the-legacy-offset-import.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094316_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101417
- **Related target files**: tests/eventbus/test_eventbus_offsets.py