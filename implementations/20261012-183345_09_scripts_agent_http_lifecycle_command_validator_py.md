## Goal

Extend `CommandValidator.validate` so an MCP server whose fully resolved real path is a regular file directly inside an allowed, non group/world-writable binary directory (default `/opt/llm/bin`) passes validation, while leaving the existing basename allowlist behavior for all other commands unchanged. Implements `REQ-004` / AC-06.

## Scope

Modifies `scripts/agent/http_lifecycle_command_validator.py`: add an allowed-binary-directory rule to `validate` and a supporting helper. Does NOT modify `scripts/agent/http_lifecycle.py` (which constructs `CommandValidator`) — the default binary dir lives in the validator itself.

## Assumptions

- `validate(server_key, cmd_name)` currently performs four checks in order: (1) `shutil.which` PATH lookup, (2) `os.path.realpath` symlink resolution, (3) `os.path.isfile` regular-file check, (4) basename allowlist against `self._allowed_commands` plus the `_INTERPRETER_BASENAME_RE` (`python3.N`) match; it raises `HttpStartupError(StartupFailure(...))` on failure and returns the resolved path on success (verified at lines 49-102).
- The default production layout writes `/opt/llm/bin` as a directory not writable by group/others (Plan Assumptions).

## Design decisions

- Add a fifth, additive acceptance path: a command passes if it satisfies the existing allowlist (checks 1-4) OR its resolved real path is a regular file directly inside the allowed binary directory that is not group/world-writable. The existing allowlist branch is not altered, so `uv`, `python`, and every currently-allowed basename behave exactly as before.
- Make the allowed directory a class attribute `_DEFAULT_ALLOWED_BINARY_DIR = "/opt/llm/bin"` overridable by the `LLMAGENT_BINARY_DIR` environment variable, so the gate host can point it elsewhere without code change.
- Resolve symlinks once (check 2 already calls `os.path.realpath`); the directory rule evaluates that same resolved path, so a symlink planted in `/opt/llm/bin` pointing elsewhere is rejected by the regular-file/parent-match checks.

## Alternatives considered

- Adding the binary basename (`mcp_shell`, …) to `_ALLOWED_COMMANDS`: rejected — the whole point is that the binary name is arbitrary and fixed per deploy; the directory+regular-file+writability rule is the control, not a name allowlist.
- Requiring the binary to live next to the interpreter: rejected — the fixed install root `/opt/llm/bin` is the deployed convention and is independent of where `python` runs.

## Implementation

### Target file

`scripts/agent/http_lifecycle_command_validator.py`

### Procedure

Add the allowed-binary-directory rule to `validate` and expose it through a private helper.

### Method

1. Add a class attribute near `PROTECTED_ENV_VARS`: `_DEFAULT_ALLOWED_BINARY_DIR: str = "/opt/llm/bin"`.
2. Add (new) a helper method `_allowed_binary_dir(self) -> str` returning `os.environ.get("LLMAGENT_BINARY_DIR") or self._DEFAULT_ALLOWED_BINARY_DIR`, and (new) `_inside_allowed_binary_dir(self, cmd_path: str) -> bool` that:
   - resolves `allowed = os.path.realpath(self._allowed_binary_dir())`;
   - returns `False` unless `os.path.isfile(cmd_path)` and `os.path.realpath(cmd_path).parent == allowed` (a regular file directly inside the directory, not a subdirectory);
   - reads `os.stat(cmd_path).st_mode` and returns `False` unless neither the group-write nor world-write bit is set (`mode & (stat.S_IWGRP | stat.S_IWOTH) == 0`).
   Import `stat` at the top.
3. In `validate`, rewrite check 4 so the rejection fires only when the command is outside BOTH controls:
   ```python
   base_name = os.path.basename(cmd_path)
   in_allowlist = base_name in self._allowed_commands or bool(_INTERPRETER_BASENAME_RE.fullmatch(base_name))
   if not in_allowlist and not self._inside_allowed_binary_dir(cmd_path):
       raise HttpStartupError(...)
   ```
4. Update the `validate` docstring from "four security checks" to "five" and describe the added directory rule.

### Details

- Keep the existing `StartupFailure` reason strings for the allowlist branch; add a distinct reason for the directory branch when needed by tests (AC-06 reject cases).
- The parent-match uses `==` on the resolved paths so a nested file (`/opt/llm/bin/sub/mcp_x`) is rejected.

## Compatibility considerations

- Every currently-allowed command still passes via the unchanged allowlist branch; the new branch only ADDS acceptance for binaries in the allowed directory. Existing allowlist test cases pass unchanged (AC-06).

## Security considerations

- This weakens nothing: the new rule requires a regular file, an exact real-path directory match, and a directory that is not group/world-writable, and it resolves symlinks before checking (so an install-directory symlink pointing elsewhere is rejected). Keep the basename allowlist intact. Cover the accept/reject matrix from AC-06 in tests.

## Rollback considerations

- N/A: revert the commit; the allowlist branch is byte-for-byte preserved.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_command_validator.py` — accept a regular file whose real path is directly inside an allowed, non-writable binary directory; reject a symlink in that directory pointing elsewhere, a file in a writable directory, a non-regular file, and any basename outside the allowlist and outside the directory; confirm existing allowlist cases still pass. Use temporary directories for the matrix.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports` clean.

## Completion criteria

- `validate` accepts a regular file directly inside the allowed binary directory and rejects the four AC-06 reject cases; the existing allowlist test cases are unmodified and passing.

## Out of scope

- `scripts/agent/http_lifecycle.py` (no change needed), the `config/agent.toml` `cmd` rewrite, and the deploy/start rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the allowed-binary-directory rule to `validate` | Pending | — | — | security-critical |
| 2 | Add accept/reject cases to `tests/agent/test_http_lifecycle_command_validator.py` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/done/20260717-171259_nuitka_onefile_packaging_proposal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-104451_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183345
- **Related target files**: scripts/agent/http_lifecycle_command_validator.py
