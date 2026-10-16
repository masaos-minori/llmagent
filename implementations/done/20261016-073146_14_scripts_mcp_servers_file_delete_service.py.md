## Goal

Expose File Delete server self-validation results and the posture they produce, so file-delete-mcp
validates its own configuration instead of being audited by the Agent (`REQ-009`, `AC-005`).

## Scope

- One modified module `scripts/mcp_servers/file/delete_service.py`: add a file-delete self-validation
  function that combines the shared base (row `12`) with the delete-specific checks.
- Existing delete behavior, including `shutil.rmtree` recursion and the allowed-root protection, is
  unchanged.
- `/health` publication is row `12` (`_health()` in `scripts/mcp_servers/file/common.py`); the
  one-line call-site change is row `49` (`scripts/mcp_servers/file/delete_server.py:111`).

## Assumptions

- Current module verified: `DeleteFileService(FileSecurityMixin)` at
  `scripts/mcp_servers/file/delete_service.py:44`, `__init__(allowed_dirs, audit_log_path, ...)` at
  `:47-54`, `_write_audit_log()` at `:58-71` (append-mode open at `:68`, failure logged and swallowed
  at `:70-71`), `delete_file()` at `:85-104`, `_check_not_deleting_allowed_root()` at `:146-152`,
  `delete_directory()` at `:154-181` (`shutil.rmtree` at `:170`), `build_service(cfg)` at `:223-230`
  with `audit_log_path="/opt/llm/logs/delete_audit.log"` hardcoded at `:230`.
- `FileDeleteConfig` fields are `allowed_dirs` and `auth_token` only
  (`scripts/mcp_servers/file/delete_models.py:29-30`); the audit-log path is not configuration.
- **Needs confirmation**: the file-delete check ids below are finalized here from `REQ-009`;
  `memo2.md`'s original list is unrecoverable (Plan `UNK-01`).

## Design decisions

- Add `validate_file_delete_security(cfg: FileDeleteConfig, audit_log_path: str) -> list[SecurityCheckResult]`
  (new module-level function) that starts from `validate_file_security_base(cfg.allowed_dirs)` (row
  `12`) and appends the delete-specific checks. The audit-log path is a parameter rather than a
  module constant so the validator checks the value the service actually uses.
- Check ids (finalized here, Needs confirmation):
  - the two shared base checks from row `12` (`server.allowed_dirs_configured`,
    `server.allowed_dirs_exist`);
  - `server.allowed_root_protected` — an `allowed_dirs` entry that resolves to the filesystem root
    `/` is `FAILED` with reason `config_invalid`. `_check_not_deleting_allowed_root()` (`:146-152`)
    protects the allowed root from deletion, but a root-wide allowlist makes that the only directory
    the protection covers while still permitting deletion of everything beneath it; the Plan's
    fail-closed-empty-allowlist assumption implies an allowlist must also be bounded.
  - `server.audit_log_writable` — the parent directory of `audit_log_path` missing or unwritable is
    `FAILED` with reason `dependency_unreachable`, because `_write_audit_log()` currently logs the
    failure and continues (`:70-71`), so deletions would proceed with no audit trail.
- `server.audit_log_writable` is `FAILED` and not `WARNING`: the issue's requirement is that each
  server validates its own security-relevant dependencies before Ready, and a delete server that
  cannot record what it deleted has lost the control it depends on. **Resolved (user decision)**:
  `FAILED`, matching the same dependency that row `09` already reports `FAILED` for github-mcp, so
  the two audit-log dependencies are graded the same way.
- The validator does not change `_write_audit_log()`'s swallow-and-log behavior. Making that failure
  fatal at call time is a separate decision, recorded as out of scope.

## Alternatives considered

- Report `server.audit_log_writable` as `WARNING` to match today's tolerant behavior — rejected for
  the reason above, and recorded as Needs-confirmation so the choice is explicit rather than
  incidental.
- Add a check for `shutil.rmtree` recursion depth — rejected: there is no configured limit, so a
  check would assert a control that does not exist.
- Make `audit_log_path` a `FileDeleteConfig` field in this row — rejected: it changes the config
  schema and `config/file_delete_mcp_server.toml`, which is outside this row's target file. Recorded
  as a follow-up.

## Implementation
### Target file

`scripts/mcp_servers/file/delete_service.py` (modify)

### Procedure

1. Import `SecurityCheckResult`, `SecurityCheckStatus`, and the reason-code constants from
   `shared.security.result_dto` (row `02`), and `validate_file_security_base` from
   `mcp_servers.file.common` (row `12`).
2. Extract the hardcoded audit path into a module-level constant `AUDIT_LOG_PATH` with the current
   value `"/opt/llm/logs/delete_audit.log"`, and have `build_service()` (`:230`) use it. Row `49`
   validates the same value the service actually writes to, without duplicating the literal.
3. Add `validate_file_delete_security()` (new) after `build_service()` (`:230`).
4. Keep `__init__`, `_write_audit_log()`, `delete_file()`, `delete_directory()`,
   `_check_not_deleting_allowed_root()`, `_scan_directory_for_dry_run()`, and the formatter methods
   unchanged.

### Method

- Fixed check order: the two base checks, then `server.allowed_root_protected`, then
  `server.audit_log_writable`. Rows `11`, `12`, `13` share the same base prefix so the three file
  servers produce a comparable check set (row `05`).
- Root detection compares `Path(entry).resolve()` with `Path("/")`; the check never walks or stats
  the tree, so validation cannot delete or modify anything.
- Audit-log writability uses `os.access(parent, os.W_OK)` on the parent directory; no probe file is
  written.
- Messages report counts and state only (`allowed_dirs contains the filesystem root`,
  `audit log parent directory is not writable`). Directory paths are sensitive paths under `REQ-002`.

### Details

- The module is about 230 lines; the addition is roughly 30 lines.
- `build_service()` (`:223-230`) is where the audit path is chosen, so the constant extracted there is
  the single source row `49` imports. `config/file_delete_mcp_server.toml:11-15` records that
  `audit_log_path` was removed from the config layer and is not a configurable value.
- The hardcoded path `/opt/llm/logs/delete_audit.log` (`:230`) is a deployment path, not a Secret; it
  may appear in operator logs but must not be copied into a posture message.

## Compatibility considerations

- Additive change: no signature or exception-type changes, so `tests/mcp_servers/file/*` that assert
  delete and dry-run behavior keep passing.
- Behavior change is limited to startup and `/health`: file-delete-mcp with an empty `allowed_dirs`,
  a root allowlist entry, or an unwritable audit-log parent now reports a failed posture and
  `ready=false`. Its runtime behavior was already fail-closed for paths outside `allowed_dirs`.
- No `docs/*.md` change is in scope for this row; `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md:119,121`
  is listed as a follow-up in the Plan.

## Security considerations

- `REQ-009` / Plan `INV-05`: file-delete-mcp validates its own configuration before Ready; the Agent
  never reads `file_delete_mcp_server.toml`.
- `REQ-002` / Plan `INV-09`: allowed directory paths and the audit-log path are sensitive paths and
  must not appear in posture fields or messages.
- This row makes an existing silent control failure (audit log unwritable) visible instead of
  leaving it as a logged-and-ignored error (`:70-71`).

## Rollback considerations

- Revert this commit together with row `12` (shared base) and row `49` (call site). No config or data
  migration is involved.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Root allowlist entry | `uv run pytest tests/mcp_servers/file/test_file_security_validation.py` (new test file) | `server.allowed_root_protected` `FAILED`, reason `config_invalid` |
| Unwritable audit-log parent | same new test file | `server.audit_log_writable` `FAILED`, reason `dependency_unreachable` |
| Deterministic check set | same new test file | the same four check ids appear for every configuration |
| Delete behavior unchanged | `uv run pytest tests/mcp_servers/file/` | passes, dry-run and allowed-root protection assertions unchanged |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-005` for file-delete: file-delete-mcp validates its own configuration and returns the
  common posture.
- The four finalized check ids are always present, with `NOT_APPLICABLE` used instead of omission.
- No directory path appears in any posture field or message.

## Out of scope

- Editing `common.py` (row `12`), `read_security.py` (row `11`), `write_service.py` (row `13`), or
  `delete_server.py` (row `49`).
- Making `audit_log_path` configurable, or changing `_write_audit_log()`'s error handling.
- Changing runtime delete behavior or raised exception types.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `validate_file_delete_security()` | Completed | 20261016-221106 | 20261016-221106 | check ids are Needs-confirmation validate_file_delete_security() plus the AUDIT_LOG_PATH constant, build_service now uses the constant |
| 2 | Confirm `FAILED` vs `WARNING` for `server.audit_log_writable` | Completed | 20261016-221106 | 20261016-221106 | decides whether such a server may start user chose FAILED, matching the same dependency row 09 reports FAILED for github-mcp |
| 3 | Add `tests/mcp_servers/file/test_file_security_validation.py` | Completed | 20261016-221106 | 20261016-221106 | shared with rows `11`, `12`, `13` 16 delete tests appended, shared file now 52 tests |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-221106 | 20261016-221106 | ruff clean, mypy 422 files, lint-imports 6 kept 0 broken, bandit Low 1 pre-existing outside the changed files, mock targets clean, docstring clean after adding the em dash separator, no bare except, full suite 8753 passed 19 skipped 9 pre-existing failures |

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
- **Related target files**: `scripts/mcp_servers/file/delete_service.py`