## Goal

Extend the file-read server's existing security guards into a self-validation entry point that
returns the common Security Posture, so file-read-mcp validates its own configuration instead of
being audited by the Agent (`REQ-009`, `AC-005`).

## Scope

- One modified module `scripts/mcp_servers/file/read_security.py`: add a file-read self-validation
  function built on the shared base added in row `12`.
- Existing guard behavior and raised exception types are unchanged.
- `/health` publication for all three file servers happens in `scripts/mcp_servers/file/common.py`
  (`_health()` at `scripts/mcp_servers/file/common.py:143-146`), which is row `12`; this row adds no
  separate wiring.

## Assumptions

- Current module verified: `ReadSecurityGuards(FileSecurityMixin)` at
  `scripts/mcp_servers/file/read_security.py:23`, `__init__(allowed_dirs, max_read_bytes)` at
  `:26-33`, `allowed_dirs` property at `:35-37`. It imports `FileSecurityMixin` and
  `check_size_limit` from `mcp_servers.file.common` at `:17-20`.
- `FileReadConfig` is the server's own config model
  (`scripts/mcp_servers/file/read_models.py:25`), and `allowed_dirs` is a `list[str]` there
  (`scripts/mcp_servers/file/delete_models.py:29` is the same shape in the delete config).
- The file servers' runtime fail-closed behavior is already in `common.py`: `resolve_safe()` denies
  anything outside `allowed_dirs` (`:28-40`), and `availability_flags()` reports
  `allowed_dirs is empty` as disabled (`:101-105`).
- **Needs confirmation**: the file-read check ids below are finalized here from `REQ-009`;
  `memo2.md`'s original list is unrecoverable (Plan `UNK-01`).

## Design decisions

- Add `validate_file_read_security(cfg: FileReadConfig) -> list[SecurityCheckResult]` (new
  module-level function) that delegates the shared part to `validate_file_security_base()` (row
  `12`) and appends the read-specific checks. Delegation keeps one definition of the
  allowed-dirs/size rules for all three file servers, which is why row `12` exists in the Plan.
- Check ids (finalized here, Needs confirmation):
  - `server.allowed_dirs_configured` — empty `allowed_dirs` is `FAILED` with reason
    `allowlist_empty`. `availability_flags()` already treats an empty list as "server disabled"
    (`common.py:101-105`), so a disabled server must not report Ready.
  - `server.allowed_dirs_exist` — a configured directory that does not exist or is not a directory
    is `FAILED` with reason `allowed_dir_invalid`, matching the existing `/health` dependency check
    in `_build_health_deps()` (`common.py:108-141`).
  - `server.max_read_bytes` — `max_read_bytes <= 0` is `FAILED` with reason `config_invalid`; a
    non-positive limit makes `check_size_limit()` reject every read, which is a configuration error
    rather than a policy choice.
- Read-specific checks are separated from the shared base so that a change to write or delete policy
  cannot silently change what file-read-mcp reports.
- The function is pure: it stats configured directories but never creates, writes, or deletes
  anything, so validation cannot alter the filesystem it is validating.

## Alternatives considered

- Put all file checks in `common.py` only — rejected: `REQ-009` names `read_security.py` as a target
  row, and the read server's byte limit is a read-only concern that does not belong in the shared
  base.
- Validate inside `ReadSecurityGuards.__init__` — rejected: raising in a constructor cannot produce
  the posture, and `REQ-002` requires the failure to be visible on `/health`.
- Treat an empty `allowed_dirs` as `NOT_APPLICABLE` because the server then simply refuses
  everything — rejected: the server would advertise `ready=true` while being unable to serve any
  request, which is exactly the fail-open shape `REQ-013` is meant to reject.

## Implementation
### Target file

`scripts/mcp_servers/file/read_security.py` (modify)

### Procedure

1. Import `SecurityCheckResult` from `shared.security.result_dto` (row `02`) and
   `validate_file_security_base` from `mcp_servers.file.common` (row `12`).
2. Add `validate_file_read_security()` (new) after the class.
3. Keep `__init__`, the `allowed_dirs` property, and every inherited guard unchanged.

### Method

- Fixed check order: the shared base results first (`server.allowed_dirs_configured`,
  `server.allowed_dirs_exist`), then `server.max_read_bytes`. Row `12` fixes the base order so the
  three file servers produce a stable, comparable prefix.
- Directory existence uses `Path.is_dir()` on the already-configured value; no `resolve()` call is
  added here because `resolve_safe()` performs resolution at request time.
- Messages report counts and setting names only (`allowed_dirs is empty`,
  `allowed_dirs entry 1 of 2 does not exist`). Directory paths are sensitive paths under `REQ-002`
  and must not appear in a posture message.

### Details

- The module is 68 lines; the addition is roughly 25 lines.
- `ReadSecurityGuards` is constructed with `list[Path]` while the config model stores `list[str]`;
  the validator takes the config model, so it does not depend on which form the service holds.
- `check_size_limit` is imported at `:19` and stays untouched; the validator only inspects the
  configured limit, it does not call the guard.

## Compatibility considerations

- Additive change: no signature or exception-type changes, so `tests/mcp_servers/file/*` that
  assert `FileAuthorizationError` / `FileValidationError` behavior keep passing.
- Behavior change is limited to startup: file-read-mcp with an empty `allowed_dirs` now reports a
  failed posture and cannot report `ready=true` (row `12` / row `06`). Its runtime denial behavior
  was already fail-closed (`common.py:38-40`).
- No `docs/*.md` change is in scope for this row.

## Security considerations

- `REQ-009` / Plan `INV-05`: file-read-mcp validates its own configuration before Ready; the Agent
  never reads `file_read_mcp_server.toml`.
- `REQ-002` / Plan `INV-09`: allowed directory paths are sensitive paths and must not appear in the
  posture or messages; only counts are reported.
- Empty allowlists stay deny-all at runtime and become a startup failure, so the fail-closed
  semantics are preserved and strengthened.

## Rollback considerations

- Revert this commit together with row `12`, which provides the shared base it calls. No config or
  data migration is involved.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Empty allowed dirs | `uv run pytest tests/mcp_servers/file/test_file_security_validation.py` (new test file) | `server.allowed_dirs_configured` `FAILED`, reason `allowlist_empty` |
| Missing configured directory | same new test file | `server.allowed_dirs_exist` `FAILED`, reason `allowed_dir_invalid` |
| Non-positive byte limit | same new test file | `server.max_read_bytes` `FAILED`, reason `config_invalid` |
| Deterministic check set | same new test file | the same three check ids appear for every configuration |
| Existing file suite | `uv run pytest tests/mcp_servers/file/` | passes, guard assertions unchanged |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-005` for file-read: file-read-mcp validates its own configuration and returns the common
  posture.
- The three finalized check ids are always present, with `NOT_APPLICABLE` used instead of omission.
- No directory path appears in any posture field or message.

## Out of scope

- Editing `scripts/mcp_servers/file/common.py` (row `12`), `write_service.py` (row `13`),
  `delete_service.py` (row `14`), or any `*_server.py`.
- Changing runtime guard behavior or raised exception types.
- Agent-side validation and classification (rows `17`-`18`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `validate_file_read_security()` | Completed | 20261016-212741 | 20261016-212741 | check ids are Needs-confirmation Check ids finalized as the three frozen ids in REQUIRED_CHECK_IDS for file_read: the two shared base ids plus server.max_read_bytes. The shared part is delegated to validate_file_security_base so one definition of the allowed-dirs rules serves all three file servers. A non-positive max_read_bytes is FAILED with config_invalid because check_size_limit would then reject every read while the server still advertises itself. The validator takes FileReadConfig, the server own config model, so it does not depend on whether the service holds Path values or strings. Pure: it stats configured directories and never creates, writes or deletes anything. Module is 114 lines. Row 12 was executed before this row because this row calls the base it adds; the user approved the swap. |
| 2 | Add `tests/mcp_servers/file/test_file_security_validation.py` | Completed | 20261016-212741 | 20261016-212741 | shared with rows `12`-`14` 9 read-specific tests were added to tests/mcp_servers/file/test_file_security_validation.py, the file shared with rows 12, 13 and 14. They cover a zero limit, a negative limit, a positive limit, the limit being reported even when the directories are valid, the frozen id set, the shared prefix coming first, identical check sets across four configurations, never raising, and no directory path in any message. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-212741 | 20261016-212741 | Full validation sequence: ruff clean, mypy clean on 421 source files, lint-imports 6 kept 0 broken, bandit reports no finding in read_security.py, check_mock_patch_targets no findings, check_docstrings reports no finding in the changed file after the module docstring separator was added, no bare except. Full suite covering rows 12 and 11: 8723 passed, 19 skipped, 9 failed, and all 9 are the pre-existing tests/agent/test_startup_rollback.py schema-version failures. Coverage and diff-cover are deferred to the end of the procedure batch. |

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
- **Related target files**: `scripts/mcp_servers/file/read_security.py`