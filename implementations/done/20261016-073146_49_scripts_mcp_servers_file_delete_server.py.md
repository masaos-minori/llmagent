## Goal

Wire File Delete self-validation (row `14`) into the shared startup flow (row `04`), publish the resulting
Security Posture on `/health` through the shared file-server health helper (rows `12`, `06`), and refuse
HTTP bind when the posture is not validated (`REQ-002`, `REQ-003`, `REQ-009`).

## Scope

- One modified module `scripts/mcp_servers/file/delete_server.py`: build the posture, pass it to
  `_health()`, and gate `run_http()` on it.
- This row adds no validation rule of its own: the validator is row `14`, the shared base checks are row
  `12`, the envelope is row `03`, the ordering is row `04`, the payload key is row `06`.
- One new test file `tests/mcp_servers/file/test_file_delete_health_posture.py`.
- `scripts/mcp_servers/file/common.py`, `scripts/mcp_servers/file/delete_service.py`, and
  `scripts/mcp_servers/server.py` are reference files only; `common.py` and `delete_service.py` are rows
  `12` and `14` and are not modified here, `server.py` is not a row at all.

## Assumptions

- Verified current source: `_cfg = FileDeleteConfig.load()` at `:55`,
  `_service: DeleteFileService = build_service(_cfg)` at `:56`,
  `attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token)` at `:69`, the `/health` handler at
  `:108-112` whose whole body is `result: JSONResponse = await _health(_cfg.allowed_dirs)` at `:111`,
  `class FileDeleteMCPServer(MCPServer)` at `:177` with `http_port = 8008` at `:182`,
  `own_config_file = "file_delete_mcp_server.toml"` at `:183`,
  `app_module = "mcp_servers.file.delete_server:app"` at `:184`, and
  `if __name__ == "__main__": server = FileDeleteMCPServer(); server.run_http()` at `:192-194`.
- The `/health` payload is built by `_health()` in `scripts/mcp_servers/file/common.py:143-146`, which
  calls `make_health_response(deps, {})`. Row `12` adds the optional `posture` parameter to `_health()`;
  this row is the caller that supplies it.
- The audit-log path is not a configurable value: `config/file_delete_mcp_server.toml:11-15` records that
  the `audit_log_path` key was removed in 2026-07-13 because `FileDeleteConfig` never parsed it, and the
  live value is the literal `"/opt/llm/logs/delete_audit.log"` in `delete_service.py:230`. Row `14`
  extracts that literal into the module-level constant `AUDIT_LOG_PATH`, which this row imports so the
  posture validates the value the service actually writes to.
- Production starts this module as `__main__`: `config/agent.toml:391`
  `cmd = ["/opt/llm/bin/mcp_file_delete"]`. Verify the entry name against `deploy/build_binaries.sh` at
  implementation time.
- uvicorn 0.49.0 imports the app module before binding (`config.load()` at
  `.venv/lib/python3.14/site-packages/uvicorn/server.py:85-86` before `self.startup()` at `:94`); this
  row does not rely on that ordering, the `__main__` gate is the control.
- `MCP_FILE_DELETE_AUTH_TOKEN` is set to `"test-token"` by `tests/conftest.py:38-46`, so the flow's
  built-in `common.auth_token` check passes in the test suite for this server.
- `/opt/llm/storage` and `/opt/llm/logs` both exist and are writable by the service user in this
  environment, and `config/file_delete_mcp_server.toml` ships `allowed_dirs = ["/opt/llm/storage"]`
  (`:4`), so with row `14`'s check set the shipped configuration produces `validated=true`.
- `_service = build_service(_cfg)` (`:56`) runs before the gate, because the gate is in the `__main__`
  block. `build_service()` only logs a warning when `allowed_dirs` is empty
  (`delete_service.py:225-227`) and performs no filesystem action, so constructing it on a failing
  posture is harmless.
- **Needs confirmation**: `SecurityPosture.ready` (row `03`) versus the payload `ready` computed in row
  `06`. This row reads only `SecurityPosture.validated` for the bind gate.

## Design decisions

- Compute the posture once at module import into a module-level `_security_posture`, immediately after
  `_service` (`:56`). The Agent polls `/health` repeatedly during readiness polling, and the bind gate
  needs the outcome before `run_http()`.
- Gate in the `if __name__ == "__main__":` block (`:192-194`): when `_security_posture.validated` is
  false, log the failed check ids with their reason codes and `raise SystemExit(1)` before constructing
  the server. For a delete server this is the decisive control: refusing to bind is the only way to
  guarantee that no deletion happens without a writable audit trail.
- Do not raise while building the posture. Row `14`'s entry point returns results instead of raising, and
  a posture failure must stay reportable on `/health`.
- Supply only the `SERVER_SECURITY_VALIDATION` stage
  (`validate_file_delete_security(_cfg, AUDIT_LOG_PATH)` from row `14`) to `run_startup_validation()`;
  the flow's built-in `check_own_config_only()`, `check_auth_token_present()`, and
  `check_published_tools_declared()` cover the common and tool-capability stages. Row `14` already
  delegates the two shared base checks to row `12`'s `validate_file_security_base()`, so this row does
  not call the base itself.
- Pass the posture through `_health()` rather than calling `make_health_response()` directly: the three
  file servers share one health builder, and bypassing it would fork the payload shape for one server.
- Import `AUDIT_LOG_PATH` from `mcp_servers.file.delete_service` rather than repeating the literal here,
  so the validated path and the written path cannot drift apart.
- This row defines the normalized non-secret view hashed by `compute_config_fingerprint()` (row `03`),
  because rows `07`-`16` define check ids but no fingerprint view. The view is
  `{"own_config_file": "file_delete_mcp_server.toml", "allowed_dirs_count": len(_cfg.allowed_dirs),
  "audit_log_path_configured": bool(AUDIT_LOG_PATH)}` — scalars and presence flags only; the audit path
  itself is a deployment path and is not hashed.
- The bind gate is startup-only. There is no re-validation on a later `/health` probe and no Hot
  Rediscovery path (ADR-003 Static Availability), so a log directory that becomes unwritable after
  startup is not detected by this row; `_write_audit_log()`'s existing log-and-continue behavior
  (`delete_service.py:70-71`) remains the runtime behavior.

## Alternatives considered

- Put the gate inside `MCPServer.run_http()` — rejected: `scripts/mcp_servers/server.py` is not a row in
  the Plan's frozen table, and a base-class gate would apply to servers whose validators have not landed
  yet.
- Put the gate inside `_health()` in `common.py` — rejected: a health handler cannot refuse a bind, and
  `common.py` is shared by three servers with three different validators.
- Make `_write_audit_log()` raise when the audit log is unwritable — rejected for this row: that is a
  runtime behavior change owned by row `14`'s out-of-scope note, and this row's control is the startup
  gate.
- Read the audit path from `_service._audit_log_path` — rejected: private attribute access across modules;
  row `14` exposes the constant instead.
- Raise at import time when validation fails — rejected: it breaks every test that imports the module and
  produces no posture for the Agent to classify.

## Implementation
### Target file

`scripts/mcp_servers/file/delete_server.py` (modify)

### Procedure

1. Import `run_startup_validation` and `StartupStage` from `shared.security.startup_flow` (row `04`),
   `SecurityPosture` and `compute_config_fingerprint` from `shared.security.posture_contract` (row `03`),
   and `validate_file_delete_security` plus `AUDIT_LOG_PATH` from `mcp_servers.file.delete_service`
   (row `14`).
2. Add `_delete_security_view(cfg: FileDeleteConfig) -> dict[str, object]` (new private function)
   returning the normalized view described above.
3. Add `_build_security_posture() -> SecurityPosture` (new private function) that calls
   `run_startup_validation()` with `server_key="file_delete"`,
   `own_config_file="file_delete_mcp_server.toml"`, the `SERVER_SECURITY_VALIDATION` stage callable
   (`validate_file_delete_security(_cfg, AUDIT_LOG_PATH)`), and the fingerprint view.
4. Assign `_security_posture: SecurityPosture = _build_security_posture()` after `_service` (`:56`).
5. Change `:111` to `await _health(_cfg.allowed_dirs, posture=_security_posture)`.
6. Add the gate to `:192-194`: log the failed check ids and reason codes, then `raise SystemExit(1)`
   before `FileDeleteMCPServer()` is constructed.
7. Add `tests/mcp_servers/file/test_file_delete_health_posture.py`.

### Method

- Build the posture after `_cfg` and `_service` exist and before `app = FastAPI(...)` is served, so the
  posture exists before the middleware is attached at `:69` and before any route can be hit.
- The gate log line is one line, format:
  `file-delete-mcp: security posture FAILED (<check_id>:<reason_code>, ...) — refusing to bind`.
  Only check ids and reason codes appear; allowed directory paths and the audit-log path are excluded
  (`REQ-002`, `REQ-004`).
- `_build_security_posture()` must not call `FileDeleteConfig.load()` again; it reuses `_cfg`.
- Keep `_health()`'s `deps` semantics unchanged: `_build_health_deps()` (`common.py:108-141`) still
  reports filesystem availability, and `details` stays `{}` for the file servers.
- Type the posture as `SecurityPosture`, not `dict[str, object]`.

### Details

- `server_key` is `"file_delete"`, matching the value the `/v1/tools` payload already attaches
  (`delete_server.py:135`) and `[mcp_servers.file_delete]` in `config/agent.toml`.
- `REQUIRED_CHECK_IDS["file_delete"]` (row `03`) must list exactly row `14`'s ids
  (`server.allowed_dirs_configured`, `server.allowed_dirs_exist`, `server.allowed_root_protected`,
  `server.audit_log_writable`) plus the flow's built-in common ids, or row `17` reports
  `check_set_mismatch`.
- `server.audit_log_writable` is `FAILED` in row `14` (not `WARNING`), so an unwritable audit directory
  blocks bind. That status is a Needs-confirmation item in row `14`; if the project chooses `WARNING`,
  this row's gate no longer covers that case and the audit-trail guarantee is lost, which must be stated
  in the ADR rows (rows `36`-`41`).
- `build_service()`'s existing `"ALLOWED_DIRS is empty"` warning (`delete_service.py:226-227`) and the
  posture's `allowlist_empty` reason describe the same condition from two layers; this row does not
  remove the warning.
- The module is about 194 lines. The roughly 30 added lines push it past the 200-line convention;
  **Needs confirmation**: whether to extract the posture-building block into a sibling module
  `scripts/mcp_servers/file/delete_posture.py`, which the Plan's frozen table does not list and therefore
  requires a Plan amendment.

## Compatibility considerations

- Existing `/health` assertions keep passing: `tests/mcp_servers/file/test_file_server_auth.py:74-76` and
  `:117-119` assert the auth-middleware status codes on `/health`, which this row does not touch.
- With the shipped config every file-delete check is `OK`, so `validated` stays `true` and the payload
  `ready` stays `true`.
- The `security` key is additive (row `06`); no existing file-server test enumerates payload keys.
- Behavior change is limited to startup and `/health`: a config with an empty `allowed_dirs`, a
  non-existent allowed directory, an `allowed_dirs` entry that resolves to `/`, or an unwritable audit-log
  parent directory now exits non-zero before binding instead of starting and rejecting each delete at call
  time, or deleting with no audit trail.
- No `docs/*.md` edit is in scope for this row; `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` and
  `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` are Plan follow-ups.

## Security considerations

- `REQ-009` / Plan `INV-05`: file-delete-mcp validates its own configuration before Ready, and the Agent
  stops reading `file_delete_mcp_server.toml` (`REQ-017`).
- `REQ-002` / Plan `INV-09`: the fingerprint view excludes `auth_token`, every `allowed_dirs` element, and
  the audit-log path value; only counts and a presence flag are hashed.
- `REQ-011`: the Agent-side empty-`auth_token` rejection stays at
  `scripts/agent/startup_validation.py:71-81` (`mcp_auth`, not removed by row `22`); this server has no
  server-side equivalent today — `attach_auth_middleware(..., _cfg.auth_token)` (`:69`) installs the
  accept-all fallback when the token is empty (`scripts/mcp_servers/server.py:100-113`). The flow's
  built-in `check_auth_token_present()` is the posture-level copy; it reports `WARNING` with reason
  `auth_token_missing` and keeps `validated=true` (Plan `UNK-06`, resolved 2026-10-16; row `04`).
- `REQ-004`: the gate log line and every posture message carry reason codes only.

## Rollback considerations

- Revert this commit together with rows `06` (payload parameter), `14` (validator and `AUDIT_LOG_PATH`),
  `12` (`_health()` parameter), and `04` (flow). No config or data migration is involved.
- The gate is the only statement that can make a previously-startable file-delete config unstartable;
  reverting the `__main__` block restores today's behavior without touching `/health`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Posture published | `uv run pytest tests/mcp_servers/file/test_file_delete_health_posture.py` (new test file) | `/health` body carries the `security` key with `server_key == "file_delete"` and `contract_version == SECURITY_CONTRACT_VERSION` |
| Validated shipped config | same new test file | `_security_posture.validated is True` against `config/file_delete_mcp_server.toml` |
| Empty allowlist blocks bind | same new test file | with `allowed_dirs` patched to `[]`, `server.allowed_dirs_configured` is `FAILED` with reason `allowlist_empty`, `validated is False`, `/health` returns 503 with `ready is False`, and the `__main__` gate raises `SystemExit` |
| Root-wide allowlist | same new test file | `allowed_dirs = ["/"]` yields `server.allowed_root_protected` `FAILED` with reason `config_invalid` |
| Unwritable audit log | same new test file | with `AUDIT_LOG_PATH` patched to a path whose parent directory does not exist, `server.audit_log_writable` is `FAILED` with reason `dependency_unreachable` |
| Existing file suite | `uv run pytest tests/mcp_servers/file/` | passes, including `test_file_server_auth.py` |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-002`: file-delete-mcp publishes the posture on `/health` with no Secret, path, or config body
  in it.
- Plan `AC-003`: file-delete-mcp runs the shared ordering and does not bind HTTP when validation fails.
- Plan `AC-005` for File Delete: the rules live in `delete_service.py` and `common.py` (rows `14`, `12`);
  this file contains wiring only.

## Out of scope

- Adding or changing File Delete check ids (rows `14`, `12`).
- Changing `_write_audit_log()`'s runtime failure behavior (row `14`, out of scope there too).
- Changing `_health()` or `make_health_response()` (rows `12`, `06`).
- Agent-side posture validation, classification, and Tool Discovery gating (rows `17`-`19`, `50`).
- Making `audit_log_path` configurable again.
- Splitting `delete_server.py` into smaller modules.

## Confirmation outcomes

- Resolved 2026-10-17: the File Delete fingerprint view defined in `Design decisions` is retained as
  written. It hashes the audit log path as a presence flag only, so a relocated audit log path is not
  detectable through the digest; row `05` compares check ids and statuses, and row `17`'s
  `compare_fingerprint()` is not consumed by the row `18` gate.
- Resolved 2026-10-17 (row `14` decision): `server.audit_log_writable` stays `FAILED` with reason
  `dependency_unreachable`, so an unwritable audit log blocks bind here.
- Resolved 2026-10-16 (Plan `UNK-06`): the flow's built-in `check_auth_token_present()` reports an empty
  `auth_token` as `WARNING` with reason `auth_token_missing`, identical in rows `04`, `42`-`49`, and `52`.
- Resolved 2026-10-17: the bind gate reads `SecurityPosture.validated` only. The payload `ready` is
  derived in `make_health_response()` from `deps` plus `validated`, and `SecurityPosture.ready` is never
  read, so no second Ready rule exists.
- Resolved 2026-10-17: the added statements stay in this file. The split trigger in `skills/DESIGN.md` is
  more than 400 lines plus multiple independent responsibilities, and this module stays a single
  FastAPI server module with one responsibility after the addition.
- Resolved 2026-10-17: a server that exits before publishing a posture is classified as an unreachable
  server. Row `18`'s `classify_server_failure()` reports an unreachable or unparseable posture as
  `AVAILABILITY`, so the `SystemExit` path needs no posture reason code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import the shared flow, contract, and row `14` validator plus `AUDIT_LOG_PATH` | Completed | 2026-10-17 | 2026-10-17 | StartupStage import not needed |
| 2 | Add `_delete_security_view()` and `_build_security_posture()` | Completed | 2026-10-17 | 2026-10-17 | view carries own_config_file, allowed_dirs_count, and audit log presence, the audit path is a parameter so a test can relocate it |
| 3 | Pass the posture to `_health()` at `:111` | Completed | 2026-10-17 | 2026-10-17 | posture forwarded through the row 12 _health parameter instead of calling make_health_response directly |
| 4 | Add the `__main__` bind gate at `:192-194` | Completed | 2026-10-17 | 2026-10-17 | gate extracted into _enforce_posture_gate |
| 5 | Add `tests/mcp_servers/file/test_file_delete_health_posture.py` | Completed | 2026-10-17 | 2026-10-17 | FileDeleteConfig is frozen so a failing posture is built with dataclasses.replace, caplog needs propagate re-enabled because shared.logger disables it |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-17 | 2026-10-17 | ruff and mypy clean, 395 passed in tests/mcp_servers/file |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 5 | New test files are not rows in the Plan's frozen table; the Plan must be amended or the assertions added to an existing `tests/mcp_servers/file/*` file | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (posture published on `/health`), `REQ-003` (shared startup ordering, validation failure blocks bind), `REQ-009` (File Delete self-validation)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/file/delete_server.py`, `scripts/mcp_servers/file/delete_service.py`, `scripts/mcp_servers/file/common.py`, `scripts/mcp_servers/health_response.py`, `scripts/shared/security/startup_flow.py`, `scripts/shared/security/posture_contract.py`
