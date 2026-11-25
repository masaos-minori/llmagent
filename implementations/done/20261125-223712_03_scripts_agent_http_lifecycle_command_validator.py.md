## Goal

Make trusted-directory confinement the default, add ownership and file-mode checks, capture the validated file identity, and remove the wildcard credential patterns from the inherited environment (REQ-003 validated path, REQ-004 strict confinement, REQ-006 per-server environment).

## Scope
**Release unit**: R1-launch-spec

## Assumptions

- The permissive opt-in variable is `LLMAGENT_COMMAND_MODE=permissive` (Plan Assumptions: a judgment call, falsifiable by the owner at procedure review). No production or development indicator exists in `scripts/`, so an explicit variable is the only available switch.
- `_inside_allowed_binary_dir` (`:204-220`) already requires a regular file directly inside the allowed directory and a directory that is not group- or world-writable; what is missing is the ownership check on both the directory and the executable, and the file-mode check on the executable.
- `CommandValidator.validate` has exactly one production caller (`scripts/agent/http_lifecycle_subprocess_launcher.py:84`), so its return shape can change without touching `scripts/agent/http_lifecycle.py`.

## Design decisions

- Invert the switch: strict is the default, permissive is the opt-in. Delete `_STRICT_ENV_VAR` (`:75`) and `_STRICT_FALSY_VALUES` (`:76`) and read `LLMAGENT_COMMAND_MODE` (new) in `__init__` (`:110-121`) into a `_permissive_mode` (new) flag, so a deployment that sets nothing gets the safe mode (REQ-004).
- `validate` returns the resolved path together with its `(st_dev, st_ino)` identity, so the caller can re-check identity before spawning (REQ-003). The identity is carried into `LaunchSpec` by row 2 and re-checked by row 4.
- Ownership and mode are one helper, `_trusted_ownership_and_mode` (new), applied in the strict branch (`:163-177`): the executable and the realpath of the allowed directory must be owned by `os.geteuid()` or root, and the executable must not be group- or world-writable (REQ-004, AC-2).
- Narrow `_DEFAULT_ALLOWED_ENV_VARS` (`:51-66`) to the REQ-006 fixed runtime set by deleting the `MCP_*_AUTH_TOKEN`, `MCP_*_CONTROL_TOKEN`, and `GITHUB_TOKEN` patterns (`:63-65`); the narrowed constant is the vocabulary `build_child_env` (row 2) imports.
- Delete `filter_env` (`:222-257`): the per-server environment is built in `scripts/agent/http_lifecycle_launch_spec.py` (row 2), which keeps the `_ENV_KEY_DENYLIST` and protected-variable rules by importing `_DEFAULT_PROTECTED_ENV_VARS` (`:29-31`).

## Alternatives considered

Keeping `LLMAGENT_STRICT_COMMAND` and defaulting strict when unset was rejected: the current opt-in is what left production permissive (Plan Issue Verification, "Strict mode is a production control: Corrected"). Keeping `filter_env` with a per-server parameter was rejected: the environment is part of the launch specification, and two builders would split one contract.

## Implementation
### Target file
`scripts/agent/http_lifecycle_command_validator.py`
### Procedure
Flip the confinement default, add the ownership and mode checks and the identity capture, and remove the wildcard environment patterns and `filter_env`.

### Method
- Replace the strict opt-in at `:118-121` with `_permissive_mode` (new) read from `LLMAGENT_COMMAND_MODE` (new); treat only the literal value `permissive` as opting in.
- In `validate` (`:123-198`): keep checks 1-3, run the strict branch (`:163-177`) unless `_permissive_mode` (new), and call `_trusted_ownership_and_mode` (new) inside the strict branch; return the path and the identity pair from the `os.stat` already performed.
- Raise `HttpStartupError(StartupFailure(...))` with a reason naming the server key, the resolved path, and the failed condition, matching the existing messages at `:155-176`.
- Delete the three wildcard patterns at `:63-65` and the comment lines that justify them (`:35-47`), and delete `filter_env` (`:222-257`).
- Update the class docstring (`:79-101`) to state that strict is the default and how permissive mode is selected.

### Details
- The permissive branch (`:180-196`) keeps the basename allowlist plus the allowed-directory rule unchanged, so development and tests that rely on `node` or `python3.13` keep working only under the explicit opt-in.
- `_allowed_binary_dir` (`:200-202`) and `LLMAGENT_BINARY_DIR` stay as the trusted-directory source; tests point it at a tmp directory.
- `PROTECTED_ENV_VARS` (`:105-107`) and the `protected_env_vars` constructor parameter stay, because the denylist and protected-variable rules are still enforced, now by the launch-spec builder.
- `LLMAGENT_BINARY_DIR` and the mode variable remain parent-only: they are deliberately absent from the narrowed allowlist (`:47`).

## Compatibility considerations

`filter_env` is a public method of `CommandValidator`; removing it changes the generated API artifacts (rows 15-16) and the two test files that call it (rows 9 and 11). `validate`'s return type changes for its single production caller (row 4). Servers whose binaries are outside the trusted directory, or owned by another user, now abort startup with a named `StartupFailure` (Plan Risks, UNK-02).

## Security considerations

Strict-by-default closes the PATH-injection path the permissive mode left open (REQ-004). Ownership and mode checks close the "writable directory, trusted basename" case. Removing the wildcard patterns stops one server's token, or `GITHUB_TOKEN`, from reaching every other server (REQ-006, AC-3).

## Rollback considerations

Revert the commit. The change is only valid together with rows 2 and 4 (R1-launch-spec): the launcher must already build the environment through the spec when `filter_env` disappears.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_command_validator.py`
- `uv run mypy scripts/agent/http_lifecycle_command_validator.py`
- `uv run ruff format` and `uv run ruff check`
- `uv run bandit -r scripts/agent/http_lifecycle_command_validator.py -c pyproject.toml`

## Completion criteria

- With no environment variable set, a binary outside the trusted directory, a group- or world-writable executable, a group- or world-writable directory, or a binary owned by another user is rejected with `HttpStartupError`.
- `LLMAGENT_COMMAND_MODE=permissive` restores the basename allowlist behavior.
- `validate` returns the resolved path and its `(st_dev, st_ino)` pair, and `_DEFAULT_ALLOWED_ENV_VARS` contains no `MCP_*_AUTH_TOKEN`, `MCP_*_CONTROL_TOKEN`, or `GITHUB_TOKEN` pattern.
- `filter_env` no longer exists in the module.

## Out of Scope

- Building the child environment and the audit line (row 2).
- Calling `Popen` and the identity re-check call site (row 4).
- Documenting the policy (row 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261126 | Execute after the row 9 Phase 1 tests are in place (REQ-009) Implemented as specified, with the Step 3a verification findings applied. |
| 2 | Confirm the Phase 1 test additions from row 9 fail before this change and pass after it | Completed | — | 20261126 | Tests-first order per Plan Phase 1 Targeted tests plus ruff/mypy/module-size/mock-patch/suppression gates pass. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261126 | Batch-end validation (release unit R1-launch-spec): ruff format+check, mypy 473 files, bandit 0 issues, lint-imports 6 contracts kept, check_module_size, check_mock_patch_targets, check_suppression_justification, check_docstrings. Full suite: 15116 passed, 16 failed (identical to the HEAD baseline: tests/integration/test_call_state_* pre-existing ToolCallState.args_hash failures). diff-cover 100% on changed source lines. |

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
- **Requirement ID**: REQ-003 (validate and execute the same executable), REQ-004 (strict confinement by default), REQ-006 (per-server child environment)
- **Source issue**: issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-111909_cliplc006_mcp-launch-spec-credentials.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-223712
- **Related target files**: `scripts/agent/http_lifecycle_command_validator.py`