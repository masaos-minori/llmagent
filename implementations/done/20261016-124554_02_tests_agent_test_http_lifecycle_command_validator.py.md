## Goal
- `REQ-007`: cover strict rejection and acceptance, permissive preservation, symlink-escape rejection, the `LLMAGENT_BINARY_DIR` override and `/opt/llm/bin` fallback, and the LLMAGENT_STRICT_COMMAND value handling.

## Scope
- Additions to `tests/agent/test_http_lifecycle_command_validator.py` only. The code change is the other row's document (`scripts/agent/http_lifecycle_command_validator.py`).

## Assumptions
- Strict mode is read from the environment inside `CommandValidator.__init__`, so each test sets the variable with `monkeypatch` before constructing the validator.
- The existing class for the directory branch (its `tmp_path` directory helper and `shutil.which` patching) shows the pattern to follow; its tests stay unchanged.

## Design decisions
- One new test class holds the strict-mode tests so permissive-mode tests in the existing classes stay untouched.
- Failures are asserted through `HttpStartupError`; strict rejections are matched on the text `outside the trusted binary directory` so they are distinct from the permissive `not in the allowed commands list`.

## Alternatives considered
N/A: testing the private strict attribute directly was rejected; behavior through `validate` is the contract.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_command_validator.py`

### Procedure
- Add class `TestCommandValidatorStrictConfinement` (new) after the existing directory-branch class, with a helper that creates a non-writable (`0o755`) trusted directory under `tmp_path` and a helper that patches `shutil.which` to a given path.
- `test_strict_rejects_allowlisted_name_outside_trusted_dir` (new): put a file named `node` outside the trusted directory, set strict and `LLMAGENT_BINARY_DIR` to the trusted directory, and assert `HttpStartupError` containing `outside the trusted binary directory`.
- `test_strict_accepts_non_allowlisted_name_inside_trusted_dir` (new): a regular file `mcp_shell` directly inside the trusted directory is accepted and the returned path is its realpath.
- `test_strict_rejects_symlink_escape` (new): a symlink in the trusted directory named `node` pointing to a file outside it is rejected in strict mode (skip if symlinks cannot be created).
- `test_strict_trusted_dir_falls_back_to_default_when_unset` (new): with strict set and `LLMAGENT_BINARY_DIR` unset, a file outside `/opt/llm/bin` is rejected and the failure reason names `/opt/llm/bin`.
- `test_permissive_default_allows_allowlisted_name_outside_trusted_dir` (new): with no flag, an allowlisted-named file outside the trusted directory is accepted.
- `test_flag_value_controls_strict_mode` (new), parametrized: the values unset, empty, `0`, `false`, `FALSE`, `off`, `no`, and ` No ` leave the allowlisted-named outside file accepted; `1`, `yes`, `true`, and `enabled` reject it.

### Method
- Use `monkeypatch.setenv` and `monkeypatch.delenv` for LLMAGENT_STRICT_COMMAND and `LLMAGENT_BINARY_DIR`; build files with `tmp_path` and `write_text`.
- Name new tests only inside this Procedure section; other sections refer to them by description.

### Details
- Run the new tests against the unmodified validator first: the strict-mode tests are expected to fail (strict is not implemented) and the permissive-default test is expected to pass. Record the observed result in Notes.
- Tests use temporary directories only and never touch `/opt/llm`.

## Compatibility considerations
N/A: additive tests; no existing test is edited.

## Security considerations
N/A: test-only change; files are created in `tmp_path` and never executed.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_command_validator.py -v` (new strict tests fail before and pass after the code change; existing tests pass throughout)
- `uv run ruff format tests/agent/test_http_lifecycle_command_validator.py`, `uv run ruff check tests/agent/test_http_lifecycle_command_validator.py`, `uv run mypy --no-namespace-packages tests/agent/test_http_lifecycle_command_validator.py` (compare against the baseline error count)
- `uv run python tools/check_mock_patch_targets.py`
- `uv run coverage run -m pytest tests/agent/test_http_lifecycle_command_validator.py`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`

## Completion criteria
- The new tests exist and pass after the code change; the strict-mode ones fail beforehand.
- Existing tests in the file pass unchanged and no new mypy error appears.
- Diff coverage of the validator's changed lines is at least 90% or the gap is recorded in Notes.

## Out of scope
- Other test modules, the validator source, `http_lifecycle.py`, and `docs/*.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the strict-confinement test class and its tests | Completed | 20261016-124805 | 20261016-125158 | changed: tests/agent/test_http_lifecycle_command_validator.py; 6 test functions (flag-value parametrized into 12 cases) |
| 2 | Run the new tests against the unmodified validator and record the result | Completed | 20261016-125158 | 20261016-125158 | red check on HEAD validator: 7 failed (strict rejections, default-dir fallback, 4 strict flag values), 36 passed (incl. strict acceptance and permissive cases, which hold in both modes) |
| 3 | Run the validation sequence (`rules/toolchain.md`) after the code change | Completed | 20261016-125158 | 20261016-125158 | ruff clean; mypy 1 error identical to baseline; check_mock_patch_targets clean; diff-cover 100%; full suite 8449 passed |

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
- **Requirement ID**: REQ-007 (strict, permissive, symlink-escape, override, and flag-value tests)
- **Source issue**: issues/20261016-093001_mcp003_allowlist_basename_only_path_injection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-104809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-124554
- **Related target files**: tests/agent/test_http_lifecycle_command_validator.py