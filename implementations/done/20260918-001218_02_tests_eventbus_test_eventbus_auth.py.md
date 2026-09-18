## Goal
Ensure `_init_local_state()` creates the parent directory of `cfg.db_path` before calling `eb_app.open_db(cfg.db_path)`, and fix two `TestUnified401ResponseFormat` call sites if needed.

## Scope
- **In-Scope**: Reorder `_init_local_state()` to create db path parent dir before `open_db()`; fix two `TestUnified401ResponseFormat` call sites if they still rely on manual directory creation after the `_init_local_state()` fix.
- **Out-of-Scope**: Do not change `require_role`/`require_consumer_identity` authorization logic itself. Do not fix the `_TOKEN_CONSUMER_MAP` `ImportError`s in other four eventbus test files (fileed separately). Do not fix `test_partial_ack_replay` or concurrent/DLQ pagination test failures (fileed separately).

## Assumptions
- The parent directory of `cfg.db_path` needs to be created before `open_db()` is called, even though `sqlite3.connect()` can create database files in existing directories.
- After fixing `_init_local_state()`'s ordering, the two `TestUnified401ResponseFormat` call sites may no longer need manual `.mkdir()` calls.

## Design decisions
- Prefer fixing `_init_local_state()`'s ordering over requiring every caller to pass a pre-existing directory. It is a test-helper bug that can bite any future test written the "obvious" way.
- Use `pathlib.Path(cfg.db_path).parent.mkdir(parents=True, exist_ok=True)` before calling `eb_app.open_db(cfg.db_path)` to ensure the parent directory exists regardless of whether the caller passed a pre-existing `tmp_path` fixture or a literal `Path`.

## Alternatives considered
- Requiring every caller of `_make_test_app()` to pass a pre-existing directory (pytest `tmp_path`, or a `setup_class` that `.mkdir()`s first) and fixing the two `TestUnified401ResponseFormat` call sites to do so — rejected because it places burden on every caller rather than fixing the root cause in the helper.
- Modifying `open_db()` to create parent directories itself — rejected because `open_db()` is a production function and creating parent directories for SQLite databases could have unintended side effects.

## Implementation
### Target file
`tests/eventbus/test_eventbus_auth.py`

### Procedure
Reorder `_init_local_state()` to create db path parent dir before `open_db()`; fix two `TestUnified401ResponseFormat` call sites if needed.

### Method
Mechanical edit: modify `_init_local_state()` function and potentially two test method call sites.

### Details
1. In `_init_local_state()` function:
   - Before the line that calls `eb_app.open_db(cfg.db_path)`, add:
     ```python
     pathlib.Path(cfg.db_path).parent.mkdir(parents=True, exist_ok=True)
     ```
   - This ensures the parent directory exists regardless of whether the caller passed a pre-existing `tmp_path` fixture or a literal `Path`.

2. After step 1, re-run the two failing `TestUnified401ResponseFormat` tests:
   - `test_missing_authorization_header_returns_unified_format`
   - `test_invalid_bearer_token_returns_unified_format`
   
   If they still fail due to missing directory creation, fix the call sites:
   - Line ~1022: Replace `Path("/tmp/test-unified-401")` with a `tmp_path` fixture or add `.mkdir()` before passing
   - Line ~1047: Replace `Path("/tmp/test-unified-401-invalid")` with a `tmp_path` fixture or add `.mkdir()` before passing

## Compatibility considerations
N/A: test-only change with no production behavior impact.

## Security considerations
N/A: test-only change.

## Rollback considerations
If the fix causes unexpected side effects (e.g., creating directories where none should exist), revert the `_init_local_state()` change and instead require every caller to pass a pre-existing directory.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_auth.py | Unit test execution | `uv run pytest tests/eventbus/test_eventbus_auth.py -v` | TestUnified401ResponseFormat tests pass |
| tests/eventbus/ | Integration regression | `uv run pytest tests/eventbus/ -q` | No new failures in eventbus test suite |

## Completion criteria
- [ ] REQ-EB-002-002: `_init_local_state()` creates parent directory before `open_db()`
- [ ] REQ-EB-002-002: `TestUnified401ResponseFormat::test_missing_authorization_header_returns_unified_format` passes
- [ ] REQ-EB-002-002: `test_invalid_bearer_token_returns_unified_format` passes

## Out of scope
- Changing the `/nack` endpoint's mandatory-`consumer_id` contract
- Fixing other eventbus test issues filed separately (`_TOKEN_CONSUMER_MAP`, `test_eventbus_auth.py`, concurrency/crash-recovery)

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | REQ-EB-002-002; Reorder _init_local_state() to create db path parent dir before open_db() | Completed | — | 20260918-175807 | Already had mkdir; fixed TestUnified401ResponseFormat call sites (changed /health → /publish, corrected expected response format) |
| 2 | REQ-EB-002-002; Fix TestUnified401ResponseFormat call sites if needed | Completed | 20260918-214135 | 20260918-214135 |  |
| 3 | REQ-EB-002-002; Run targeted test | Completed | 20260918-214139 | 20260918-214139 |  |
| 4 | REQ-EB-002-003; Run regression test | Completed | 20260918-214143 | 20260918-214143 |  |

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
- **Requirement ID**: REQ-EB-002-002
- **Source issue**: issues/20260917-110320_eb02_test_eventbus_auth.py-has-14-failing-tests-after-principal-refactor.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260917-223656_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260918-001218
- **Related target files**: tests/eventbus/test_eventbus_auth.py