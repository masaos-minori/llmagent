# Implementation Procedure: Add bounded interpreter tests to CommandValidator test suite

## Goal

Add deterministic tests proving the bounded interpreter match: the crafted name
`python3evil` is rejected with `HttpStartupError`, and real interpreters `python3`,
`python3.11`, `python3.12` validate. Rewrite the existing unbounded-prefix test to assert
bounded acceptance. Implements `REQ-002`.

## Scope

Modify `tests/agent/test_http_lifecycle_command_validator.py` only. Add negative/positive
tests in `TestCommandValidatorValidate`; rewrite `test_python3_prefix_allows_python3x`. No
other file is a modification target.

## Assumptions

- `pytest` and `unittest.mock.patch` are available (already imported at the top of the
  test file).
- `shutil.which` can be patched via `patch.object(shutil, "which", ...)` as done in the
  existing `test_symlink_resolved_to_non_file_raises`.
- A regular-file fixture can be created under `/tmp` (tests skip gracefully on symlink
  limitations; use the same guard where relevant).

## Design decisions

- Drive all new cases through a mocked `shutil.which` returning a controlled
  regular-file path, so results are deterministic regardless of the host PATH.
- Assert the exact failure reason substring `"not in the allowed commands list"` for the
  negative case, matching the existing `test_disallowed_command_raises` contract.
- Keep positive assertions identical to the existing pattern
  (`os.path.isabs(result)` and `os.path.isfile(result)`).

## Alternatives considered

- Relying on real `python3.*` binaries present in CI PATH: rejected — non-deterministic
  across hosts; the negative case (`python3evil`) cannot be exercised without a crafted
  fixture.
- Adding a single combined test: rejected — the negative rejection and positive acceptance
  are distinct acceptance criteria (AC1 vs AC2) and should be independently assertable.

## Implementation

### Target file

`tests/agent/test_http_lifecycle_command_validator.py`

### Procedure

1. In `TestCommandValidatorValidate`, add a negative test `test_python3_evil_rejected`:
   - Create a regular-file fixture (e.g. `/tmp/test_validator_python3evil`) guarded by a
     try/finally cleanup.
   - `patch.object(shutil, "which", return_value=str(fixture))`.
   - Build `CommandValidator(allowed_commands=frozenset({"python3"}))`.
   - Assert `pytest.raises(HttpStartupError)` and
     `"not in the allowed commands list" in str(exc_info.value)`.
2. Add a positive test `test_interpreter_variants_accepted` covering
   `["python3", "python3.11", "python3.12"]`, each via a mocked regular-file fixture,
   asserting `os.path.isabs` and `os.path.isfile`.
3. Rewrite `test_python3_prefix_allows_python3x` to assert BOUNDED acceptance: confirm
   `python3`, `python3.11`, `python3.12` pass while a crafted `python3evil` (mocked to a
   regular file) is rejected — replacing the old unbounded `'python3'` prefix claim.

### Method

- Locate the existing test to rewrite with
  `rg -n 'def test_python3_prefix_allows_python3x' tests/agent/test_http_lifecycle_command_validator.py`
  (currently line 155).
- Insert the new tests within `TestCommandValidatorValidate` after
  `test_python3_prefix_allows_python3x` (before `test_validate_returns_absolute_path`,
  line 170).
- Reuse the `patch.object(shutil, "which", ...)` pattern from the existing
  `test_symlink_resolved_to_non_file_raises` (lines 120-145) for deterministic fixtures.

### Details

- Import surface is already sufficient (`os`, `shutil`, `Path`, `patch`, `pytest`,
  `CommandValidator`, `HttpStartupError`, `StartupFailure`) — no new imports required.
- Fixture cleanup mirrors the existing `try/finally` + `unlink(missing_ok=True)` pattern;
  skip on OSError like the symlink test does.
- Do not modify `TestStartupFailure` or the error-class tests.

## Compatibility considerations

- Existing tests unchanged except the rewritten `test_python3_prefix_allows_python3x`
  (now asserts bounded instead of unbounded behavior).
- No changes to test infrastructure, fixtures, or shared helpers.

## Security considerations

- The negative test locks the security property: a crafted basename that merely *starts
  with* `python3` is now rejected, closing the allowlist bypass described in the source
  issue.

## Rollback considerations

- Remove the added tests and revert `test_python3_prefix_allows_python3x` to its prior
  unbounded assertion to restore pre-change test state.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_http_lifecycle_command_validator.py` | Unit | `uv run pytest tests/agent/test_http_lifecycle_command_validator.py -v` | New negative/positive tests pass; rewritten test asserts bounded acceptance; regression suite passes |
| Full suite | Regression | `uv run pytest tests/` | No new failures |

## Completion criteria

- `python3evil` (mocked to a regular file) raises `HttpStartupError` containing
  `"not in the allowed commands list"` (T1 / AC1).
- `python3`, `python3.11`, `python3.12` validate successfully and return an absolute,
  existing file path (T2 / AC2).
- `test_python3_prefix_allows_python3x` now asserts bounded acceptance (rejects
  `python3evil`) rather than unbounded prefix matching (T3 / AC3).
- Full suite passes with no new failures.

## Out of scope

- Changes to `scripts/agent/http_lifecycle_command_validator.py` (covered by the sibling
  implementation procedure for this Plan).
- Changes to other test files or shared test infrastructure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261004-160633 | 20261004-160633 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261004-160633 | 20261004-160633 | 17/17 pass (new: test_python3_evil_rejected, test_interpreter_variants_accepted; rewritten test_python3_prefix_allows_python3x asserts bounded) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261004-160633 | 20261004-160633 | ruff format/check clean; mypy: only pre-existing unused-ignore on unmodified line 83 (repo full-mypy blocked by tool_constants double-discovery); pytest 17/17 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261004-160633 | 20261004-160633 | N/A: no docs/*.md mapping |

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
- **Requirement ID**: `REQ-002` (bounded interpreter acceptance/rejection in tests)
- **Source issue**: issues/20261004-065217_mcp001_commandvalidator-allowlist-python3-prefix-bypass-allows-arbitrary-command-execution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-075440_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-110940
- **Related target files**: tests/agent/test_http_lifecycle_command_validator.py