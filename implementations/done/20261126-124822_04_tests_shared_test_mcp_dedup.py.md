## Goal
- Add boundary tests (zero, negative, boolean, minimum, maximum, oversized) for `retention_days` and `pending_timeout_minutes` in the dedup section validator (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: new test cases in `tests/shared/test_mcp_dedup.py`.
- Out of scope: the validator and its ranges, which stay as they are (retention 1..365, pending timeout 1..1440, `scripts/shared/mcp_dedup_config.py:38-44`).

## Assumptions
- No code row of the Plan names this file in its Related Tests, so it keeps its own document.
- Verified in Step 3a: the existing section tests cover `lease_seconds` and `max_attempts` out of range and `retention_days` at 0 only (`test_mcp_dedup.py:805-815`); the validator rejects booleans and non-integers through `_validated_int` (`mcp_dedup_config.py:134-148`); the error message names `dedup.<key>`.
- High-churn file (12 commits in 30 days): add a new class next to `TestDedupSectionValidation`, and rebase before editing.

## Design decisions
- Parametrize over both keys with the shared bound table imported from the module, so the test follows the code's ranges instead of hard-coding copies.

## Alternatives considered
- N/A: test-only row.

## Implementation
### Target file
`tests/shared/test_mcp_dedup.py`

### Procedure
1. Add a test class for the two keys using `load_dedup_section` with `{key: value}` dicts.
2. Rejected values per key: `0`, `-1`, `True`, `False`, the maximum plus one, a large value, a float, and a string; assert `ConfigParseError` with a message matching `dedup.<key>`.
3. Accepted values per key: the minimum and the maximum; assert the returned config carries the value.
4. Assert a table with both keys at their defaults loads and produces the default fingerprint.

### Method
- Take the ranges from `_DEDUP_INT_KEYS` so a future range change updates the test automatically.

### Details
- Keep the existing tests untouched.

## Compatibility considerations
- Test-only.

## Security considerations
- N/A: no secret involved.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/shared/test_mcp_dedup.py -k Section`; `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- Every rejected and accepted value behaves as listed for both keys; existing tests pass; all validation commands pass.

## Out of Scope
- Validator changes, other keys, and the shipped-file test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the tests described in Implementation > Procedure | Completed | 20261126-131011 | 20261126-131011 | Changed: tests/shared/test_mcp_dedup.py |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-131011 | 20261126-131011 | ruff format/check, mypy (CI invocation), lint-imports, bandit, module size, gates passed; full suite (parallel, coverage): 27 failed and 88 errors in tests/agent/* from a pre-existing NameError in scripts/agent/commands/cmd_mcp.py (RuntimeToolRegistry annotation), unrelated to this change; no failing test touches a changed file; targeted tests pass |

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
- **Requirement ID**: `REQ-004` (timing bounds tested at every edge)
- **Source issue**: issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-113156_mcpdd001_dedup-keyless-config-gate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-124822
- **Related target files**: `tests/shared/test_mcp_dedup.py`
