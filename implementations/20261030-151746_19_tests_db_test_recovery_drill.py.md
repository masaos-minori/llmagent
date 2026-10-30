## Goal

Create the drill harness tests in `tests/db/test_recovery_drill.py` (`REQ-007`, four domains, artifact emission, measurement fields).

## Scope

- Create only `tests/db/test_recovery_drill.py`.

## Assumptions

- Depends on rows 10, 11, 12. The tests also carry the coverage the rotation row needs (a corrupt archive is rejected and removed) and the wrapper coverage of row 10, because neither row has its own new test file in the Plan.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Build tiny databases for all four domains under `tmp_path` and point the drill at them by patching `build_db_config` at the module that uses it.

## Alternatives considered

- N/A: lightweight test row.

## Implementation

### Target file

`tests/db/test_recovery_drill.py` (new)

### Procedure

1. Add tests for: the drill returns an entry for each of rag, session, workflow, and eventbus with `restore_seconds`, `data_loss_window_seconds`, `integrity`, `domain_identity`, `archive_path`, and `ok`; the JSON artifact is written, parses, and is retained in the archive directory; the live database files are unchanged (hash compare); a database failing the workflow or eventbus required-table check is reported `ok: false` and the run continues; rotation rejects and removes a corrupt archive; `check_db_integrity` and `verify_backup` agree with the private helpers.

### Method

- The rag and session databases need the extension-free parts only: create minimal tables (`documents`, `sessions`) rather than the full DDL if `sqlite-vec` is unavailable in the test environment.

### Details

- Use `tmp_path`; never `/opt/llm`.

## Compatibility considerations

- New test module.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/db/test_recovery_drill.py tests/db/test_db_maintenance.py tests/db/test_db_recovery.py -v`
- `uv run ruff check tests/db/test_recovery_drill.py`

## Completion criteria

- The listed cases pass; existing maintenance and recovery tests still pass unmodified.

## Out of Scope

- Numeric RPO/RTO assertions (UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the tests per Procedure | Pending | — | — | Plan Phase 4; with rows 10-12 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: tests/db/test_recovery_drill.py
