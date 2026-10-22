## Goal
Remove `offsets_dir` from every config construction and TOML fixture, and add a test that a configuration still carrying the key is rejected as unknown (REQ-003 and REQ-004).

## Scope
- In: remove the key from the 37 occurrences (constructor calls and TOML fixture strings) and add `test_load_config_rejects_offsets_dir` (new).
- Out: tests unrelated to the key; a test that asserts the key is required (delete it if present, since the requirement is gone).

## Assumptions
- `test_load_config_rejects_unknown_key` (about line 216) already shows the pattern: write a TOML string, call `load_config()`, expect `ValueError` with `match="unknown key"`; the new test follows it.
- Some tests assert the required-key list or error messages that may name `offsets_dir`; those assertions must be updated or removed.

## Design decisions
- Reuse the existing unknown-key test's helper/fixture for the new test instead of inventing a second TOML builder.
- Do not parametrize away existing explicit tests.

## Alternatives considered
Folding the new case into the existing unknown-key test was rejected: a dedicated test names the removed key and survives refactors of the generic one.

## Implementation
### Target file
`tests/eventbus/test_eventbus_config.py`

### Procedure
1. List occurrences: `rg -n offsets_dir tests/eventbus/test_eventbus_config.py`.
2. Remove each keyword argument and each `offsets_dir = ...` TOML line; delete any test that only checks the key is required or typed.
3. Add `test_load_config_rejects_offsets_dir` (new) that writes a valid configuration plus `offsets_dir = "/x"` and asserts `ValueError` matching `unknown key`.
4. Run the file's tests.

### Method
Mechanical removal plus one new test following `test_load_config_rejects_unknown_key`.

### Details
- The new test's TOML must otherwise be valid (all required keys, auth token handling as the neighboring test does), so the failure is attributable to `offsets_dir` alone.
- Assert the message names the key.

## Compatibility considerations
Test-only change; locks the new contract (Plan AC-3).

## Security considerations
N/A: test code only.

## Rollback considerations
Revert the commit.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_config.py -q`; `rg offsets_dir tests/eventbus/test_eventbus_config.py` shows only the new rejection test.

## Completion criteria
- The only remaining `offsets_dir` occurrences are in the new rejection test, and the file passes (REQ-003, REQ-004; Plan AC-3, AC-4).

## Out of Scope
Every other file of the Plan (each has its own procedure document); ADR text (Plan UNK-01); deleting `/opt/llm/offsets` (Plan UNK-03); offset storage, monotonic advancement, ACK-advanced offsets, and resume computation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the key from every construction and TOML fixture | Completed | 20261022-134019 | 20261022-134019 | Changed: see commit |
| 2 | Add the unknown-key rejection test | Completed | 20261022-134019 | 20261022-134019 | Verified: tests/eventbus 324 passed, full suite 9649 passed; ruff, mypy, lint-imports, docs checkers pass |
| 3 | Run the file's tests and the validation sequence (`rules/toolchain.md`) | Completed | 20261022-134019 | 20261022-134019 | Verified: tests/eventbus 324 passed, full suite 9649 passed; ruff, mypy, lint-imports, docs checkers pass |

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
- **Requirement ID**: `REQ-003` (key rejected by the loader), `REQ-004` (drop the key from fixtures, add the rejection test)
- **Source issue**: `issues/20261022-124119_offhelper_remove-unused-file-offset-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-125806_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-132500
- **Related target files**: `tests/eventbus/test_eventbus_config.py`