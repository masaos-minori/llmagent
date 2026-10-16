## Goal
- `REQ-001`, `REQ-003`, `REQ-005`: add a strict mode in which a command is allowed only when its resolved real path passes the existing trusted-directory check; the basename allowlist branch does not apply.
- `REQ-002`, `REQ-004`: keep the current permissive behavior unchanged, and gate strict mode behind LLMAGENT_STRICT_COMMAND, read in `CommandValidator.__init__`, off by default.
- `REQ-006`: document the modes, the trusted-directory model, and the flag in the validator docstring.

## Scope
- `scripts/agent/http_lifecycle_command_validator.py` only. Tests are the other row's document. No docs file is changed (decided with the Plan).

## Assumptions
- The only production construction site is `HttpServerLifecycleManager.__init__` in `http_lifecycle.py` (`CommandValidator(allowed_commands=...)`), which stays unchanged; the flag is read from the process environment inside `__init__`.
- `_inside_allowed_binary_dir` already enforces a regular file directly inside the trusted directory, a directory that is neither group- nor world-writable, and resolves symlinks with `os.path.realpath`; strict mode reuses it unchanged.
- Deployed server commands are real files under `/opt/llm/bin` (for example `/opt/llm/bin/mcp_shell`), whose basenames are not on the allowlist; they must keep working in strict mode.

## Design decisions
- Add module-level constants `_STRICT_ENV_VAR` (new) set to the string LLMAGENT_STRICT_COMMAND and `_STRICT_FALSY_VALUES` (new) set to the frozenset `{"", "0", "false", "off", "no"}`. Strict is on when the lower-cased, stripped value of the variable is not in that set, so an unexpected value enables strict (fail closed).
- Store the resolved boolean on the instance as `self._strict_confinement` (new) in `__init__`.
- In `validate`, branch at check 4: when strict is on, require `self._inside_allowed_binary_dir(cmd_path)` and otherwise raise `HttpStartupError(StartupFailure(...))` whose reason names the command, the resolved path, and the trusted directory and says it is outside it; when strict is on and the check passes, return the path without consulting the allowlist. When strict is off, keep the existing code path byte for byte.

## Alternatives considered
- A per-server config field (Design B in the Plan): rejected, it needs changes to the launch site and `mcp_config.py`, outside the Plan's scope.
- Keeping "allowlist AND directory" for strict mode: rejected, it would reject every deployed `mcp_*` server.
- Looking the command up inside the trusted directory instead of through `PATH` in strict mode: deferred (Plan UNK-04); strict mode fails closed if `PATH` yields a binary outside the directory.

## Implementation
### Target file
`scripts/agent/http_lifecycle_command_validator.py`

### Procedure
- Below the existing module constants, add `_STRICT_ENV_VAR` (new) and `_STRICT_FALSY_VALUES` (new).
- In `CommandValidator.__init__`, after the existing assignments, set `self._strict_confinement` (new) from the environment per the rule above.
- In `validate`, after the realpath and regular-file checks (checks 2 and 3), add the strict branch described above before the existing allowlist computation; leave checks 1 to 3 and the permissive branch untouched.
- Rewrite the `CommandValidator` class docstring and the `validate` docstring section: describe permissive mode (allowlist, `python3[.N]` pattern, or trusted directory), strict mode (trusted directory only), the trusted directory (`LLMAGENT_BINARY_DIR`, else `/opt/llm/bin`, real regular files directly inside, not group/world-writable, symlinks resolved before the check so a symlink into the directory that points elsewhere is rejected), and the LLMAGENT_STRICT_COMMAND flag with its falsy values.

### Method
- Reuse `_allowed_binary_dir()` for the directory shown in the failure reason; do not add a second directory source.
- Use the existing `HttpStartupError` and `StartupFailure` types; no new exception.
- Keep lines at 88 characters or fewer.

### Details
- The existing tests assert the message `not in the allowed commands list` for permissive rejections; the strict failure uses different wording so the modes are distinguishable.
- No other file reads or changes the flag; `filter_env` and the launch path are untouched.

## Compatibility considerations
- With the flag unset (the default) behavior is identical to today. Enabling the flag is an explicit operator action; deployed `/opt/llm/bin/mcp_*` commands pass, while commands resolved elsewhere (for example `/usr/bin/node`) are rejected.

## Security considerations
- Strict mode removes the PATH-injection path for names on the allowlist: a binary resolved outside the trusted directory is rejected regardless of its basename. The value check fails closed on unexpected flag values. Symlinks are resolved before the check, so a symlink planted in the trusted directory does not bypass it. A misspelled variable name leaves strict off; the docstring names the variable exactly.

## Rollback considerations
N/A: revert the commit; with the flag unset the change is inert.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_command_validator.py tests/agent/test_http_lifecycle.py tests/agent/test_lifecycle.py tests/agent/test_http_lifecycle_integration.py tests/agent/test_http_lifecycle_warning.py -q`
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit scripts/agent/http_lifecycle_command_validator.py -c pyproject.toml`, `uv run vulture scripts/agent/http_lifecycle_command_validator.py --min-confidence 80`, `uv run radon cc scripts/agent/http_lifecycle_command_validator.py -s`
- `uv run python tools/check_suppression_justification.py`, `uv run python tools/generate_reference_table.py --check`

## Completion criteria
- Strict mode allows only commands that pass the trusted-directory check and rejects the others with a descriptive failure; permissive mode is unchanged.
- The flag is read in `__init__`, off by default, and fails closed on unexpected values.
- The docstrings describe the modes, the trusted-directory model, and the flag.
- Lint, type, architecture, and security checks report no new findings; the full suite shows no new failure.
- No `docs/*.md` change is made; deployment is a Plan note (environment variable only, no `deploy.sh` change).

## Out of scope
- `http_lifecycle.py`, `filter_env`, `mcp_config.py`, the allowlist contents, the lookup of commands inside the trusted directory (UNK-04), and `docs/*.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the flag constants, read the flag in `__init__`, and add the strict branch in `validate` | Completed | 20261016-124747 | 20261016-124805 | changed: scripts/agent/http_lifecycle_command_validator.py (constants, __init__ flag, strict branch) |
| 2 | Update the class and `validate` docstrings | Completed | 20261016-124805 | 20261016-124805 | class and validate docstrings updated in the same edit |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-124805 | 20261016-125158 | ruff/mypy/lint-imports/bandit/vulture/suppression/reference-table clean; validator+lifecycle modules 152 passed; full suite 8449 passed 0 failed; diff-cover 100% on the validator; radon validate B(6)->B(8); docs N/A (decided with the Plan) |

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
- **Requirement ID**: REQ-001, REQ-003, REQ-005 (strict mode via the trusted-directory check), REQ-002, REQ-004 (permissive default, opt-in flag), REQ-006 (docstring)
- **Source issue**: issues/20261016-093001_mcp003_allowlist_basename_only_path_injection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-104809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-124554
- **Related target files**: scripts/agent/http_lifecycle_command_validator.py