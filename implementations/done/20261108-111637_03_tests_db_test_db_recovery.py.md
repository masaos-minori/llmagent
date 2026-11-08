## Goal
Add a Dry Run test that uses a real corrupt SQLite file and proves its bytes are unchanged and no artifact is created (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit
Adds one test to `tests/db/test_db_recovery.py`. No production change.

## Assumptions
- Existing Dry Run tests patch `_run_integrity_check` and use fixed `/tmp/*.db` paths from `mock_db_cfg`, so none touches a real file (verified).
- `recover_corruption()` resolves the path from `build_db_config()` by target name, so the test patches `build_db_config` to return a config whose `rag_db_path` points into `tmp_path`.
- Independent of the ADR-editing procedures.

## Design decisions
- Write a file that SQLite reports as corrupt (random bytes with a valid-looking header is not required; a non-database file is enough if the integrity check classifies it as corrupt) and compare bytes before and after.
- Assert the directory listing under `tmp_path` is unchanged.

## Alternatives considered
N/A: using the real integrity check is the Plan decision.

## Implementation
### Target file
`tests/db/test_db_recovery.py`

### Procedure
1. Add `test_recover_dry_run_corrupt_file_unchanged`(new): create the corrupt file in `tmp_path`, patch `db.recovery.build_db_config` to point `rag_db_path` at it, run `recover_corruption(target="rag", dry_run=True)`.
2. Assert the returned result reports dry run and a corrupt condition without success of a restore, the file bytes equal the original, and the directory listing is identical (no archive, sidecar or restore artifact).

### Method
Use `tmp_path`, `MagicMock(spec=DbConfig)` like `mock_db_cfg`, and `Path.read_bytes()` comparison.

### Details
- If the real integrity check does not classify the chosen bytes as corrupt, adjust the bytes; do not patch `_run_integrity_check`.
- Check the actual `RecoveryResult` fields before writing assertions.

## Compatibility considerations
Test-only addition.

## Security considerations
N/A: test-only change; no production code, secret, or permission behavior changes

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/db/test_db_recovery.py -q`: pass
- Mutation check: make the dry-run branch write a file and confirm the test fails, then restore.
- `uv run ruff check` and `uv run mypy` on the file

## Completion criteria
- The new test passes against a real corrupt file and fails if Dry Run mutates or creates anything.

## Out of Scope
- Production recovery code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or change the test as described in Implementation > Procedure | Completed | 20261108-113844 | 20261108-113844 | — |
| 2 | Run the test file, the mutation check, and lint and type checks | Completed | 20261108-113844 | 20261108-113844 | ruff/format/mypy/lint-imports pass; mutation check failed as expected then restored; full suite 7716 passed, 1 unrelated failure (tests/mcp_servers/mdq/test_mdq_health_posture.py, allowed_dir_invalid in this environment, no source touched); diff-cover N/A (no source change) |

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
- **Requirement ID**: `REQ-004` (Dry Run byte-identity test)
- **Source issue**: issues/20261107-050705_adrver001_align-invariant-verification-claims.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-092352_adrver001_align-invariant-verification-claims.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-111637
- **Related target files**: `tests/db/test_db_recovery.py`
