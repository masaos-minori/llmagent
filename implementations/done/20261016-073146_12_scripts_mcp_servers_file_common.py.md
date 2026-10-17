## Goal

Make `scripts/mcp_servers/file/common.py` the shared self-validation base and the shared `/health`
publication point for the three file servers, so file-read/write/delete-mcp each validate their own
configuration and publish the common Security Posture (`REQ-009`, `REQ-002`, `AC-005`).

## Scope

- One modified module `scripts/mcp_servers/file/common.py`:
  - add `validate_file_security_base()` (new) — the allowed-directories checks shared by all three
    file servers;
  - extend `_health()` (`scripts/mcp_servers/file/common.py:143-146`) so it can publish a posture
    through `make_health_response()` (row `06`).
- The three file servers' `/health` handlers pass their own posture; those one-line call-site
  changes are rows `47`-`49`.

## Assumptions

- Current module verified: `FileAuthorizationError` at `scripts/mcp_servers/file/common.py:21`,
  `FileValidationError` at `:24`, `resolve_safe()` at `:28-40` (denies anything outside
  `allowed_dirs`), `require_file()` at `:43-48`, `require_dir()` at `:51-56`, `FileSecurityMixin` at
  `:64-71` (`_allowed_dirs: list[Path]` at `:67`, `_resolve_and_validate()` at `:70-71`),
  `check_size_limit` (used by `read_security.py:19`), `availability_flags()` at `:101-105`
  (`allowed_dirs is empty` reports the server disabled), `_build_health_deps()` at `:108-141`,
  `_make_error_handler()` handlers at `:138-140`, `_health()` at `:143-146` calling
  `make_health_response(deps, {})`.
- Call sites of `_health()`: `scripts/mcp_servers/file/read_server.py:245-248`,
  `scripts/mcp_servers/file/write_server.py:151`, `scripts/mcp_servers/file/delete_server.py:111`;
  each passes only `_cfg.allowed_dirs`.
- `make_health_response(deps, details)` is the shared builder
  (`scripts/mcp_servers/health_response.py:41-51`) and `ready = len(deps) == 0` at `:38`.
- **Needs confirmation**: the shared check ids below are finalized here from `REQ-009`; `memo2.md`'s
  original list is unrecoverable (Plan `UNK-01`).

## Design decisions

- Add `validate_file_security_base(allowed_dirs: Sequence[str]) -> list[SecurityCheckResult]` (new
  module-level function) that produces exactly two checks:
  - `server.allowed_dirs_configured` — empty is `FAILED` with reason `allowlist_empty`, matching
    `availability_flags()`'s existing "server disabled" verdict (`:101-105`).
  - `server.allowed_dirs_exist` — a configured entry that does not exist or is not a directory is
    `FAILED` with reason `allowed_dir_invalid`, matching what `_build_health_deps()` already reports
    as a dependency failure (`:108-141`).
  Each file server appends its own limit checks (rows `11`, `13`, `14`), so the shared base holds
  only what all three genuinely share.
- `_health()` gains an optional third parameter: `_health(allowed_dirs: list[str], posture: SecurityPosture | None = None) -> JSONResponse`.
  Keeping it optional means the existing one-argument call sites keep compiling until rows
  `47`-`49` land, so this row cannot break a file server that has not been wired yet.
- When a posture is supplied, `_health()` passes it to `make_health_response()` (row `06`), which
  adds the `security` key and ANDs `posture.validated` into `ready`. `_health()` does not compute
  `ready` itself; the payload-level Ready rule stays in one place.
- The existing `details` dict stays `{}`. Posture data is not folded into `details` — row `03`
  rejects that because `details` is free-form per-server diagnostic space.
- `_build_health_deps()` is left as the availability view. Posture validation and dependency probing
  stay separate concerns: a missing directory appears in `deps` (availability) and as a failed check
  (security), which is intentional duplication of one fact across two channels, not two rules.

## Alternatives considered

- Have `_health()` load the server's own config and compute the posture itself — rejected: `_health()`
  is shared by three servers with three different config files and three different limit settings, so
  it cannot know which validator to run without importing all three config models into the shared
  file, which would couple `common.py` to every file server's model shape.
- Make the posture parameter required — rejected: it would force this row to edit three
  `*_server.py` files that are separate Plan rows, and would break any not-yet-migrated caller.
- Drop `availability_flags()` and derive availability from the posture — rejected: `availability_flags()`
  gates tool registration (`read_server.py`, `delete_server.py:146`), which is a different decision
  from `/health` readiness, and `REQ-014` gates Tool Discovery through the posture instead.

## Implementation
### Target file

`scripts/mcp_servers/file/common.py` (modify)

### Procedure

1. Import `SecurityCheckResult`, `SecurityCheckStatus`, and the reason-code constants from
   `shared.security.result_dto` (row `02`), and `SecurityPosture` from
   `shared.security.posture_contract` (row `03`).
2. Add `validate_file_security_base()` (new) near `availability_flags()` (`:101`).
3. Add the optional `posture` parameter to `_health()` (`:143`) and forward it to
   `make_health_response()`.
4. Leave `resolve_safe()`, `require_file()`, `require_dir()`, `FileSecurityMixin`,
   `check_size_limit()`, `availability_flags()`, `_build_health_deps()`, and the error handlers
   unchanged.

### Method

- Fixed base check order: `server.allowed_dirs_configured`, then `server.allowed_dirs_exist`. Rows
  `11`, `13`, `14` append their own checks after this prefix so the three file servers produce a
  stable, comparable check set (row `05` compares check ids).
- Existence uses `Path(entry).is_dir()` on the configured string; no `resolve()` is added, because
  symlink resolution is a request-time concern already handled by `resolve_safe()` (`:30`).
- Messages report counts and state only (`allowed_dirs is empty`,
  `allowed_dirs entry 1 of 2 is not a directory`). Directory paths are sensitive paths under
  `REQ-002` and must not appear in a posture message, even though `_build_health_deps()` already
  puts some path detail into `deps` today.

### Details

- The module is about 146 lines; the addition is roughly 35 lines and stays under the 200-line
  convention.
- `FileSecurityMixin` itself is not modified: it is the runtime guard base for the services, while
  the new function is the startup-time validator. Both read the same configured values.
- `_health()` is `async` today (`:143`) although it performs no await; the signature keeps `async`
  so the three call sites' `await` stays valid.

## Compatibility considerations

- The new parameter is optional, so `read_server.py:247`, `write_server.py:151`, and
  `delete_server.py:111` keep compiling unchanged until rows `47`-`49` land.
- `tests/mcp_servers/file/*` that assert `FileAuthorizationError` / `FileValidationError` messages
  keep passing; no guard behavior changes.
- Behavior change is limited to startup and `/health`: a file server with an empty or invalid
  `allowed_dirs` now reports a failed posture and `ready=false` (HTTP 503 through the existing
  handler contract). Its runtime denial behavior was already fail-closed (`:38-40`).
- No `docs/*.md` change is in scope for this row; `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md:119,121`
  is listed as a follow-up in the Plan.

## Security considerations

- `REQ-009` / Plan `INV-05`: each file server validates its own configuration before Ready; the
  Agent never reads `file_*_mcp_server.toml`.
- `REQ-002` / Plan `INV-09`: allowed directory paths are sensitive paths; only counts appear in
  posture fields and messages.
- Keeping `ready` derived inside `make_health_response()` (row `06`) means the three file servers
  cannot each invent their own Ready rule.

## Rollback considerations

- Revert this commit together with rows `11`, `13`, `14` (callers of the new base function) and rows
  `47`-`49` (callers of the new `_health()` parameter). No config or data migration is involved.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Empty allowed dirs | `uv run pytest tests/mcp_servers/file/test_file_security_validation.py` (new test file) | `server.allowed_dirs_configured` `FAILED`, reason `allowlist_empty` |
| Missing configured directory | same new test file | `server.allowed_dirs_exist` `FAILED`, reason `allowed_dir_invalid` |
| Posture published on `/health` | `uv run pytest tests/mcp_servers/file/test_file_health_posture.py` (new test file) | response body carries the `security` key and `ready=false` when the posture is failed |
| Backward-compatible call | same new test file | calling `_health(allowed_dirs)` with no posture publishes no `security` key and keeps today's `ready` value |
| Existing file suite | `uv run pytest tests/mcp_servers/file/` | passes |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-005` for the file servers: the shared allowed-directories validation exists once, in the
  shared base, and each file server publishes the common posture on `/health`.
- `_health()` publishes the `security` key only when a posture is supplied, and `ready` is derived
  only by `make_health_response()`.
- No directory path appears in any posture field or message.

## Out of scope

- Editing `read_security.py` (row `11`), `write_service.py` (row `13`), `delete_service.py`
  (row `14`), or the three `*_server.py` handlers (rows `47`-`49`).
- Changing runtime guard behavior, `availability_flags()` semantics, or raised exception types.
- Agent-side validation and classification (rows `17`-`18`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `validate_file_security_base()` | Completed | 20261016-212717 | 20261016-212717 | check ids are Needs-confirmation Check ids finalized as the two shared ids present in REQUIRED_CHECK_IDS for all three file servers: server.allowed_dirs_configured and server.allowed_dirs_exist. Empty allowed_dirs is FAILED with allowlist_empty, matching availability_flags. A configured entry that is empty or not a directory is FAILED with allowed_dir_invalid, matching what _build_health_deps reports as a dependency failure. The empty-entry rule is hardening beyond the Method text: Path of an empty string resolves to the current working directory, which is not a configured boundary. Existence uses Path.is_dir on the configured string with no resolve call, so symlink handling stays the request-time concern of resolve_safe. An empty allowlist yields NOT_APPLICABLE for the existence check so the check set never changes. Messages report counts only. Module is 241 lines. |
| 2 | Add the optional `posture` parameter to `_health()` | Completed | 20261016-212717 | 20261016-212717 | depends on row `06` signature _health now takes an optional posture and forwards it as the security argument of make_health_response. deps and details are unchanged, so posture data is never folded into details and ready is derived by row 06 rather than by each file server. The parameter is optional so a file server that is not wired yet publishes exactly today's payload. |
| 3 | Add the two new file test files | Completed | 20261016-212717 | 20261016-212717 | shared with rows `11`, `13`, `14` tests/mcp_servers/file/test_file_security_validation.py holds 13 tests for this row and is shared with rows 11, 13 and 14. tests/mcp_servers/file/test_file_health_posture.py holds 7 tests. Covers the empty allowlist, a missing directory, an entry that is a file, an empty entry, the not_applicable case, the count-only failure message, the shared ids appearing in all three file-server contracts, fixed order, identical check sets across four configurations, and no path in any message. On the health side: unchanged payload without a posture, the security block carrying exactly the seven contract keys, an unvalidated posture making an available server not ready, deps still degrading a validated server, and details staying empty. No test writes outside tmp_path. |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-212717 | 20261016-212717 | Full validation sequence: ruff clean, mypy clean on 421 source files, lint-imports 6 kept 0 broken, bandit reports no finding in file/common.py while the file package keeps 1 pre-existing Low finding elsewhere and no High, check_mock_patch_targets no findings, check_docstrings reports no finding in the changed file after the module docstring separator was added, no bare except. Full suite covering rows 12 and 11: 8723 passed, 19 skipped, 9 failed, and all 9 are the pre-existing tests/agent/test_startup_rollback.py schema-version failures. Coverage and diff-cover are deferred to the end of the procedure batch. |

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
- **Requirement ID**: `REQ-009` (File Read/Write/Delete self-validation), `REQ-002` (posture published on `/health`)
- **Source issue**: `issues/done/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/file/common.py`, `scripts/mcp_servers/file/read_server.py`, `scripts/mcp_servers/file/write_server.py`, `scripts/mcp_servers/file/delete_server.py`