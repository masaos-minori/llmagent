## Goal

Expose File Write server self-validation results and the posture they produce, so file-write-mcp
validates its own configuration instead of being audited by the Agent (`REQ-009`, `AC-005`).

## Scope

- One new module `scripts/mcp_servers/file/write_security_validation.py`: a file-write self-validation
  function that combines the shared base (row `12`) with the write-specific checks.
- Existing write behavior in `scripts/mcp_servers/file/write_service.py`, including atomic write and
  its exception mapping, is unchanged and the module is not edited.
- `/health` publication is row `12` (`_health()` in `scripts/mcp_servers/file/common.py`); the
  one-line call-site change is row `48` (`scripts/mcp_servers/file/write_server.py:151`).

## Assumptions

- Current module verified: `WriteFileService(FileSecurityMixin)` at
  `scripts/mcp_servers/file/write_service.py:43`, `__init__(allowed_dirs, max_write_bytes)` at
  `:46-53`, `_apply_text_edits()` at `:57-67`, `_cleanup_tmp()` at `:95-98`, `write_file()` at
  `:121-135` (byte-limit rejection at `:127-130`), `_atomic_write()` at `:137-159` (tmp file
  `target.parent / f".tmp_{target.name}"` at `:144`, `mkdir(parents=True, exist_ok=True)` at `:146`,
  `PermissionError` -> `FileAuthorizationError` at `:150-152`, other `OSError` ->
  `FileValidationError` at `:153-155`).
- `FileWriteConfig` fields are `max_write_bytes`, `allowed_dirs`, `supported_extensions`,
  `auth_token` (`scripts/mcp_servers/file/write_models.py:28-32`).
- Verified fact: `supported_extensions` is parsed (`write_models.py:42-44`) but is not referenced by
  any guard in `write_service.py` (the only occurrences in `scripts/mcp_servers/file/` are in
  `write_models.py`). It is currently unenforced configuration.
- **Needs confirmation**: the file-write check ids below are finalized here from `REQ-009`;
  `memo2.md`'s original list is unrecoverable (Plan `UNK-01`).

## Design decisions

- Add `validate_file_write_security(cfg: FileWriteConfig) -> list[SecurityCheckResult]` (new
  module-level function) that starts from `validate_file_security_base(cfg.allowed_dirs)` (row `12`)
  and appends the write-specific checks.
- Check ids (finalized here, Needs confirmation):
  - the two shared base checks from row `12` (`server.allowed_dirs_configured`,
    `server.allowed_dirs_exist`);
  - `server.max_write_bytes` — `max_write_bytes <= 0` is `FAILED` with reason `config_invalid`,
    because a non-positive limit makes `write_file()` reject every write (`:127-130`);
  - `server.write_dirs_writable` — a configured allowed directory that exists but is not writable is
    `FAILED` with reason `dependency_unreachable`, because today that failure only appears as
    `FileAuthorizationError` on the first write (`:150-152`);
  - `server.supported_extensions` — always `NOT_APPLICABLE` with reason `not_applicable`, because
    the setting is parsed but not enforced anywhere in this module. Reporting it as enforced would be
    a false claim in the posture.
- `server.supported_extensions` is reported rather than omitted so the gap stays visible in every
  posture and in row `05`'s check-set comparison. **Open item (user decision pending)**: whether to
  open a follow-up issue that enforces or removes the setting; this row does not change enforcement
  behavior, and no issue was opened while executing this row.
- Writability is tested with `os.access(dir, os.W_OK)` on the configured directory, not by creating
  a probe file, so validation performs no filesystem mutation.

## Alternatives considered

- Report `supported_extensions` as `OK` when it is non-empty — rejected: nothing reads the value, so
  an `OK` would assert an enforcement that does not exist.
- Validate inside `WriteFileService.__init__` — rejected: raising in a constructor cannot produce the
  posture, and `REQ-002` requires the failure to be visible on `/health`.
- Skip the writability check because `_atomic_write()` already creates parent directories
  (`:146`) — rejected: `mkdir` succeeding does not mean the directory is writable; the failure mode
  that matters (`PermissionError`) is only discovered at request time today.

## Implementation
### Target file

`scripts/mcp_servers/file/write_security_validation.py` (new)

### Procedure

1. Import `SecurityCheckResult`, `SecurityCheckStatus`, and the reason-code constants from
   `shared.security.result_dto` (row `02`), and `validate_file_security_base` from
   `mcp_servers.file.common` (row `12`).
2. Add `validate_file_write_security()` (new) as the module's only function; `write_service.py` is
   not edited, so its class body and helpers stay byte-identical.
3. Keep `write_file()`, `_atomic_write()`, `_cleanup_tmp()`, `_apply_text_edits()`,
   `_write_if_changed()`, and the dry-run paths unchanged.

### Method

- Fixed check order: the two base checks, then `server.max_write_bytes`, then
  `server.write_dirs_writable`, then `server.supported_extensions`. Rows `11`, `13`, `14` share the
  same base prefix so their check sets are comparable (row `05`).
- The byte-limit rule is expressed once: the validator tests the same configured value
  `write_file()` compares against at `:127`, so the startup check and the runtime rejection cannot
  diverge.
- Messages report counts and setting names only. Directory paths are sensitive paths under `REQ-002`;
  extension patterns are allowlist values and are reported as counts only.

### Details

- Resolved (user decision): the validator lives in the new sibling module
  `scripts/mcp_servers/file/write_security_validation.py`. `write_service.py` is already 343 lines,
  so adding the validator there would put it past the 400-line split trigger in `skills/DESIGN.md`.
  The Plan's frozen table was amended so this row's file is the sibling module, which keeps the
  table and the procedure document in agreement.
- `_atomic_write()` is a `@staticmethod` (`:137`), so the validator does not need a service instance.
- `auth_token` (`write_models.py:32`) is a Secret and is never inspected or reported by this
  validator; token presence is enforced by the server's auth middleware and by the Agent's
  `mcp_auth` check (`scripts/agent/startup_validation.py:70-81`).

## Compatibility considerations

- Additive change: no signature or exception-type changes, so `tests/mcp_servers/file/*` that assert
  `FileAuthorizationError` / `FileValidationError` messages keep passing.
- Behavior change is limited to startup and `/health`: file-write-mcp with an empty `allowed_dirs`,
  a non-positive `max_write_bytes`, or an unwritable allowed directory now reports a failed posture
  and `ready=false`. Its runtime behavior was already fail-closed.
- No `docs/*.md` change is in scope for this row; `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md:119,121`
  is listed as a follow-up in the Plan.

## Security considerations

- `REQ-009` / Plan `INV-05`: file-write-mcp validates its own configuration before Ready; the Agent
  never reads `file_write_mcp_server.toml`.
- `REQ-002` / Plan `INV-09`: allowed directory paths and extension allowlists must not appear in
  posture fields or messages.
- The posture must not claim enforcement that does not exist; `server.supported_extensions` is
  therefore `NOT_APPLICABLE` until the setting is actually enforced.

## Rollback considerations

- Revert this commit together with row `12` (shared base) and row `48` (call site). No config or data
  migration is involved.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Non-positive write limit | `uv run pytest tests/mcp_servers/file/test_file_security_validation.py` (new test file) | `server.max_write_bytes` `FAILED`, reason `config_invalid` |
| Unwritable allowed directory | same new test file | `server.write_dirs_writable` `FAILED`, reason `dependency_unreachable` |
| Unenforced setting stays visible | same new test file | `server.supported_extensions` is `NOT_APPLICABLE` for every configuration, never omitted |
| Deterministic check set | same new test file | the same five check ids appear for every configuration |
| Existing file suite | `uv run pytest tests/mcp_servers/file/` | passes, atomic-write assertions unchanged |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-005` for file-write: file-write-mcp validates its own configuration and returns the common
  posture.
- The five finalized check ids are always present, with `NOT_APPLICABLE` used instead of omission.
- No directory path or extension allowlist value appears in any posture field or message.

## Out of scope

- Editing `common.py` (row `12`), `read_security.py` (row `11`), `delete_service.py` (row `14`),
  `write_service.py`, or `write_server.py` (row `48`).
- Enforcing or removing `supported_extensions`.
- Changing atomic-write behavior or raised exception types.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `validate_file_write_security()` | Completed | 20261016-221106 | 20261016-221106 | check ids are Needs-confirmation validate_file_write_security() in the sibling module, check ids match the frozen posture contract |
| 2 | Decide single-file vs sibling module (Details) | Completed | 20261016-221106 | 20261016-221106 | sibling module needs a Plan amendment user chose the sibling split, Plan row 13 amended from write_service.py Modify to write_security_validation.py New |
| 3 | Add `tests/mcp_servers/file/test_file_security_validation.py` | Completed | 20261016-221106 | 20261016-221106 | shared with rows `11`, `12`, `14` 14 write tests appended, shared file now 36 tests |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-221106 | 20261016-221106 | ruff clean, mypy 422 files, lint-imports 6 kept 0 broken, bandit no findings in the changed files, mock targets clean, docstring clean, no bare except |

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
- **Requirement ID**: `REQ-009` (File Read/Write/Delete self-validation)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/file/write_security_validation.py`