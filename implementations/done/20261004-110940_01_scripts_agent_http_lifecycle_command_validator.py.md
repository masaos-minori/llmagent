# Implementation Procedure: Bound CommandValidator python3 allowlist prefix to a bounded interpreter match

## Goal

Narrow the `CommandValidator.validate()` interpreter exception so only genuine Python
interpreter basenames (`python3`, `python3.<version>`) pass, rejecting crafted names such
as `python3evil` or `python3-config`. Implements `REQ-001` (bounded interpreter-basename
match) and `REQ-004` (preserve public signature).

## Scope

Modify `scripts/agent/http_lifecycle_command_validator.py` only. Add `import re`, a
module-level compiled constant, and replace the open `startswith("python3")` comparison
inside `validate()`. No other file is a modification target.

## Assumptions

- Admin deployment configs reference only standard interpreter basenames (`python3`,
  `python3.<NN>`), accepted by the bounded pattern.
- `re.fullmatch()` behaves as in the stdlib (Python 3.13); `from __future__ import
  annotations` is already present.
- The primary allowlist membership test and the `validate()` signature are unchanged.

## Design decisions

- Use a single compiled module-level constant
  `_INTERPRETER_BASENAME_RE = re.compile(r"python3(?:\.\d+)?")` so the regex is built
  once, not per call.
- Apply `re.fullmatch()` against the resolved basename so the ENTIRE basename must match:
  bare `python3` and `python3.<digits>` match; `python3evil`, `python3-config`,
  `python3distutils` do not.
- Keep the primary allowlist membership test (`base_name not in self._allowed_commands`)
  and combine with the interpreter match via logical OR, preserving existing
  allowlisted-command behavior.
- Introduce no runtime dependencies; `re` is stdlib.

## Alternatives considered

- `str.startswith("python3")`: rejected — unbounded, admits `python3evil`.
- `re.match(r"python3(?:\.\d+)?", base_name)` / `re.search`: rejected — these anchor only
  at the start, so `python3evil` would still match; `fullmatch` is required to reject
  suffixes.
- Extending the primary allowlist to include `python3`: rejected — broadens the
  security-critical allowlist and changes behavior for every caller; the exception was
  intentionally scoped to interpreters.
- Version-gated pattern requiring a digit (`python3(?:\.\d+)`): rejected — rejects bare
  `python3`, which existing tests require to validate successfully and which is not in the
  primary allowlist.

## Implementation

### Target file

`scripts/agent/http_lifecycle_command_validator.py`

### Procedure

1. Add `import re` to the top-of-module imports (stdlib group alongside `logging`, `os`,
   `shutil`).
2. Add a module-level compiled constant next to `_DEFAULT_ALLOWED_COMMANDS` /
   `_DEFAULT_PROTECTED_ENV_VARS`:
   ```python
   _INTERPRETER_BASENAME_RE = re.compile(r"python3(?:\.\d+)?")
   ```
3. In `CommandValidator.validate()`, replace the open interpreter branch:
   ```python
   if base_name not in self._allowed_commands and not base_name.startswith(
       "python3"
   ):
   ```
   with the bounded fullmatch:
   ```python
   if base_name not in self._allowed_commands and not _INTERPRETER_BASENAME_RE.fullmatch(
       base_name
   ):
   ```
   Keep the surrounding `raise HttpStartupError(...)` block and the
   `"not in the allowed commands list"` reason string unchanged.

### Method

- Locate the current check with
  `rg -n 'startswith\("python3"\)' scripts/agent/http_lifecycle_command_validator.py`
  (currently lines 82-84).
- Edit the import block (lines 10-16) to add `import re`; add the constant after line 25;
  edit the allowlist condition at lines 82-84.
- Verify the returned path (`return cmd_path`, line 96) is unchanged.

### Details

- Import ordering: `re` sorts alphabetically among stdlib imports (`logging`, `os`, `re`,
  `shutil`) — place it before `shutil` to satisfy ruff `I` rules.
- Line length: the replacement condition exceeds 88 chars; wrap the argument across lines
  as shown, matching the existing multi-line style.
- Do not alter `filter_env`, checks 2-3 (symlink resolution / regular-file verification),
  or the `PROTECTED_ENV_VARS` class attribute.
- Reference dependency (read-only):
  `scripts/agent/http_lifecycle.py:_create_and_validate_proc` (lines 257-285) calls
  `validate()`; the internal comparison change does not affect the caller.

## Compatibility considerations

- Public signature `validate(server_key: str, cmd_name: str) -> str` is unchanged
  (`REQ-004`).
- Existing allowlisted commands (`python`, `node`, `uvx`, etc.) continue to validate
  unchanged (`REQ-003`).
- Real interpreters `python3`, `python3.11`, `python3.12` still validate; any
  non-standard interpreter basename now fails closed with a clear `HttpStartupError` at
  startup rather than executing silently.

## Security considerations

- This is the final allowlist boundary before `subprocess.Popen()` launch in
  `_create_and_validate_proc`; the previous `startswith("python3")` admitted crafted
  basenames (`python3foo`) placed in a PATH directory via `shutil.which()`.
- `re.fullmatch()` enforces an exact bounded match, restoring the allowlist as an
  effective control without widening the primary allowlist.
- Fail-closed by design: unknown interpreter variants raise `HttpStartupError` at
  startup, making a mismatch observable rather than a silent execution gap.

## Rollback considerations

- Revert the three edits (remove `import re`, remove the constant, restore
  `base_name.startswith("python3")`) to return to prior behavior.
- No schema, config, or deploy.sh impact (stdlib-only change; no new `config/*.toml`).

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/http_lifecycle_command_validator.py` | Static: format, lint, type, security | `uv run ruff format scripts/agent/http_lifecycle_command_validator.py` then `uv run ruff check scripts/agent/http_lifecycle_command_validator.py`; `uv run mypy scripts/agent/http_lifecycle_command_validator.py`; `uv run bandit scripts/agent/http_lifecycle_command_validator.py` | Clean; no new errors/findings |
| Full module | Regression | `uv run pytest tests/agent/test_http_lifecycle_command_validator.py -v` | All existing + new tests pass |

## Completion criteria

- `python3`, `python3.11`, `python3.12` validate successfully and return an absolute,
  existing file path (AC2).
- A crafted basename (`python3evil`, mocked to a regular file) raises `HttpStartupError`
  containing `"not in the allowed commands list"` (AC1).
- Existing allowlisted commands still validate; no pre-existing test regresses (AC3).
- `ruff format`, `ruff check`, `mypy`, `bandit` clean on the touched file.

## Out of scope

- Changing the primary allowlist contents (`node`, `uvx`, `python`, etc.).
- Reworking symlink-resolution, regular-file, or PATH-lookup checks.
- Any change to `filter_env` or subprocess launch logic.
- Documentation updates (`docs/*.md`): the allowlist policy is not documented there.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261004-154856 | 20261004-154856 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261004-154856 | 20261004-154856 | Regression run passed (15/15); new-interpreter tests are proc 02 scope |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261004-154856 | 20261004-154856 | ruff format/check clean; mypy clean (isolated; repo-wide tool_constants double-discovery blocks full run - pre-existing); bandit 0 issues; pytest 15/15 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261004-154856 | 20261004-154856 | N/A: allowlist policy not documented in `docs/*.md` N/A: allowlist policy not documented in docs/*.md |

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
- **Requirement ID**: `REQ-001` (bounded interpreter-basename match), `REQ-004` (preserve public signature)
- **Source issue**: issues/20261004-065217_mcp001_commandvalidator-allowlist-python3-prefix-bypass-allows-arbitrary-command-execution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-075440_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-110940
- **Related target files**: scripts/agent/http_lifecycle_command_validator.py