## Goal

Wire File Write self-validation (row `13`) into the shared startup flow (row `04`), publish the resulting
Security Posture on `/health` through the shared file-server health helper (rows `12`, `06`), and refuse
HTTP bind when the posture is not validated (`REQ-002`, `REQ-003`, `REQ-009`).

## Scope

- One modified module `scripts/mcp_servers/file/write_server.py`: build the posture, pass it to `_health()`,
  and gate `run_http()` on it.
- This row adds no validation rule of its own: the validator is row `13`, the shared base checks are row
  `12`, the envelope is row `03`, the ordering is row `04`, the payload key is row `06`.
- One new test file `tests/mcp_servers/file/test_file_write_health_posture.py`.
- `scripts/mcp_servers/file/common.py`, `scripts/mcp_servers/file/write_service.py`, and
  `scripts/mcp_servers/server.py` are reference files only; `common.py` and `write_service.py` are rows
  `12` and `13` and are not modified here, `server.py` is not a row at all.

## Assumptions

- Verified current source: `_cfg = FileWriteConfig.load()` at `:61`,
  `_service: WriteFileService = build_service(_cfg)` at `:62`,
  `attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token)` at `:75`, the `/health` handler at
  `:148-152` whose whole body is `result: JSONResponse = await _health(_cfg.allowed_dirs)` at `:151`,
  `class FileWriteMCPServer(MCPServer)` at `:217` with `http_port = 8007` at `:222`,
  `own_config_file = "file_write_mcp_server.toml"` at `:223`,
  `app_module = "mcp_servers.file.write_server:app"` at `:224`, and
  `if __name__ == "__main__": server = FileWriteMCPServer(); server.run_http()` at `:232-234`.
- The `/health` payload is built by `_health()` in `scripts/mcp_servers/file/common.py:143-146`, which
  calls `make_health_response(deps, {})`. Row `12` adds the optional `posture` parameter to `_health()`;
  this row is the caller that supplies it.
- Production starts this module as `__main__`: `config/agent.toml:400`
  `cmd = ["/opt/llm/bin/mcp_file_write"]`. Verify the entry name against `deploy/build_binaries.sh` at
  implementation time.
- uvicorn 0.49.0 imports the app module before binding (`config.load()` at
  `.venv/lib/python3.14/site-packages/uvicorn/server.py:85-86` before `self.startup()` at `:94`); this
  row does not rely on that ordering, the `__main__` gate is the control.
- `MCP_FILE_WRITE_AUTH_TOKEN` is set to `"test-token"` by `tests/conftest.py:38-46`, so the flow's built-in
  `common.auth_token` check passes in the test suite for this server.
- `/opt/llm/storage` exists and is writable by the service user in this environment, and
  `config/file_write_mcp_server.toml` ships `allowed_dirs = ["/opt/llm/storage"]` (`:4`) and
  `max_write_bytes = 1000000` (`:7`), so with row `13`'s check set the shipped configuration produces
  `validated=true` with `server.supported_extensions` as `NOT_APPLICABLE`.
- `supported_extensions` is not present in `config/file_write_mcp_server.toml` at all, so the value the
  posture reports is the dataclass default. Row `13` reports it as `NOT_APPLICABLE` because nothing
  enforces it.
- **Needs confirmation**: `SecurityPosture.ready` (row `03`) versus the payload `ready` computed in row
  `06`. This row reads only `SecurityPosture.validated` for the bind gate.

## Design decisions

- Compute the posture once at module import into a module-level `_security_posture`, immediately after
  `_service` (`:62`). The Agent polls `/health` repeatedly during readiness polling, and the bind gate
  needs the outcome before `run_http()`.
- Gate in the `if __name__ == "__main__":` block (`:232-234`): when `_security_posture.validated` is
  false, log the failed check ids with their reason codes and `raise SystemExit(1)` before constructing
  the server.
- Do not raise while building the posture. Row `13`'s entry point returns results instead of raising, and
  a posture failure must stay reportable on `/health`.
- Supply only the `SERVER_SECURITY_VALIDATION` stage (`validate_file_write_security(_cfg)` from row `13`)
  to `run_startup_validation()`; the flow's built-in `check_own_config_only()`,
  `check_auth_token_present()`, and `check_published_tools_declared()` cover the common and
  tool-capability stages. Row `13` already delegates the two shared base checks to row `12`'s
  `validate_file_security_base()`, so this row does not call the base itself.
- Pass the posture through `_health()` rather than calling `make_health_response()` directly: the three
  file servers share one health builder, and bypassing it would fork the payload shape for one server.
- This row defines the normalized non-secret view hashed by `compute_config_fingerprint()` (row `03`),
  because rows `07`-`16` define check ids but no fingerprint view. The view is
  `{"own_config_file": "file_write_mcp_server.toml", "allowed_dirs_count": len(_cfg.allowed_dirs),
  "max_write_bytes": _cfg.max_write_bytes, "supported_extensions_count": len(_cfg.supported_extensions)}`
  — scalars and counts only.
- The bind gate is startup-only. There is no re-validation on a later `/health` probe and no Hot
  Rediscovery path (ADR-003 Static Availability).

## Alternatives considered

- Put the gate inside `MCPServer.run_http()` — rejected: `scripts/mcp_servers/server.py` is not a row in
  the Plan's frozen table, and a base-class gate would apply to servers whose validators have not landed
  yet.
- Put the gate inside `_health()` in `common.py` — rejected: a health handler cannot refuse a bind, and
  `common.py` is shared by three servers with three different validators.
- Compute the posture lazily on the first `/health` probe — rejected: the gate must decide before bind.
- Raise at import time when validation fails — rejected: it breaks every test that imports the module and
  produces no posture for the Agent to classify.
- Probe writability by creating a temporary file in each allowed directory — rejected: row `13` uses
  `os.access(dir, os.W_OK)` so validation performs no filesystem mutation, which matters for a server
  whose whole purpose is writing.

## Implementation
### Target file

`scripts/mcp_servers/file/write_server.py` (modify)

### Procedure

1. Import `run_startup_validation` and `StartupStage` from `shared.security.startup_flow` (row `04`),
   `SecurityPosture` and `compute_config_fingerprint` from `shared.security.posture_contract` (row `03`),
   and `validate_file_write_security` from `mcp_servers.file.write_service` (row `13`).
2. Add `_write_security_view(cfg: FileWriteConfig) -> dict[str, object]` (new private function) returning
   the normalized view described above.
3. Add `_build_security_posture() -> SecurityPosture` (new private function) that calls
   `run_startup_validation()` with `server_key="file_write"`,
   `own_config_file="file_write_mcp_server.toml"`, the `SERVER_SECURITY_VALIDATION` stage callable
   (`validate_file_write_security(_cfg)`), and the fingerprint view.
4. Assign `_security_posture: SecurityPosture = _build_security_posture()` after `_service` (`:62`).
5. Change `:151` to `await _health(_cfg.allowed_dirs, posture=_security_posture)`.
6. Add the gate to `:232-234`: log the failed check ids and reason codes, then `raise SystemExit(1)`
   before `FileWriteMCPServer()` is constructed.
7. Add `tests/mcp_servers/file/test_file_write_health_posture.py`.

### Method

- Build the posture after `_cfg` and `_service` exist and before `app = FastAPI(...)` is served, so the
  posture exists before the middleware is attached at `:75` and before any route can be hit.
- The gate log line is one line, format:
  `file-write-mcp: security posture FAILED (<check_id>:<reason_code>, ...) — refusing to bind`.
  Only check ids and reason codes appear; allowed directory paths and extension lists are excluded
  (`REQ-002`, `REQ-004`).
- `_build_security_posture()` must not call `FileWriteConfig.load()` again; it reuses `_cfg`.
- Keep `_health()`'s `deps` semantics unchanged: `_build_health_deps()` (`common.py:108-141`) still
  reports filesystem availability, and `details` stays `{}` for the file servers.
- Type the posture as `SecurityPosture`, not `dict[str, object]`.

### Details

- `server_key` is `"file_write"`, matching the value the `/v1/tools` payload already attaches
  (`write_server.py:175`) and `[mcp_servers.file_write]` in `config/agent.toml`.
- `REQUIRED_CHECK_IDS["file_write"]` (row `03`) must list exactly row `13`'s ids
  (`server.allowed_dirs_configured`, `server.allowed_dirs_exist`, `server.max_write_bytes`,
  `server.write_dirs_writable`, `server.supported_extensions`) plus the flow's built-in common ids, or
  row `17` reports `check_set_mismatch`.
- `server.supported_extensions` is `NOT_APPLICABLE` in every configuration today (row `13`); it is
  reported rather than omitted so the enforcement gap stays visible in the posture and in row `05`'s
  check-set comparison.
- `server.write_dirs_writable` (row `13`) and `_build_health_deps()`'s `deps["filesystem"]` entry describe
  the same configured value from two layers: the posture reports it as a validation result and blocks
  bind, `dependencies` reports it as a live availability signal and only degrades the payload. Both stay.
- The module is about 234 lines, already above the 200-line convention. The roughly 30 added lines stay
  in this file; do not split it as a side effect of this row.

## Compatibility considerations

- Existing `/health` assertions keep passing: `tests/mcp_servers/file/test_file_server_auth.py:74-76` and
  `:117-119` assert the auth-middleware status codes on `/health`, which this row does not touch.
- With the shipped config every file-write check is `OK` or `NOT_APPLICABLE`, so `validated` stays `true`
  and the payload `ready` stays `true`.
- The `security` key is additive (row `06`); no existing file-server test enumerates payload keys.
- Behavior change is limited to startup and `/health`: a config with an empty `allowed_dirs`, a
  non-existent or unwritable allowed directory, or `max_write_bytes <= 0` now exits non-zero before
  binding instead of starting and rejecting every write at call time.
- No `docs/*.md` edit is in scope for this row; `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` and
  `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` are Plan follow-ups.

## Security considerations

- `REQ-009` / Plan `INV-05`: file-write-mcp validates its own configuration before Ready, and the Agent
  stops reading `file_write_mcp_server.toml` (`REQ-017`).
- `REQ-002` / Plan `INV-09`: the fingerprint view excludes `auth_token` and every `allowed_dirs` and
  `supported_extensions` element; only counts are hashed. Allowed directory paths are sensitive paths and
  appear in no posture message.
- `REQ-011`: the Agent-side empty-`auth_token` rejection stays at
  `scripts/agent/startup_validation.py:71-81` (`mcp_auth`, not removed by row `22`); this server has no
  server-side equivalent today — `attach_auth_middleware(..., _cfg.auth_token)` (`:75`) installs the
  accept-all fallback when the token is empty (`scripts/mcp_servers/server.py:100-113`). The flow's
  built-in `check_auth_token_present()` is the posture-level copy; it reports `WARNING` with reason
  `auth_token_missing` and keeps `validated=true` (Plan `UNK-06`, resolved 2026-10-16; row `04`).
- `REQ-004`: the gate log line and every posture message carry reason codes only.

## Rollback considerations

- Revert this commit together with rows `06` (payload parameter), `13` (validator), `12` (`_health()`
  parameter), and `04` (flow). No config or data migration is involved.
- The gate is the only statement that can make a previously-startable file-write config unstartable;
  reverting the `__main__` block restores today's behavior without touching `/health`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Posture published | `uv run pytest tests/mcp_servers/file/test_file_write_health_posture.py` (new test file) | `/health` body carries the `security` key with `server_key == "file_write"` and `contract_version == SECURITY_CONTRACT_VERSION` |
| Validated shipped config | same new test file | `_security_posture.validated is True` against `config/file_write_mcp_server.toml`, with `server.supported_extensions` present as `NOT_APPLICABLE` |
| Empty allowlist blocks bind | same new test file | with `allowed_dirs` patched to `[]`, `server.allowed_dirs_configured` is `FAILED` with reason `allowlist_empty`, `validated is False`, `/health` returns 503 with `ready is False`, and the `__main__` gate raises `SystemExit` |
| Unwritable allowed dir | same new test file | `server.write_dirs_writable` is `FAILED` with reason `dependency_unreachable` |
| Existing file suite | `uv run pytest tests/mcp_servers/file/` | passes, including `test_file_server_auth.py` |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-002`: file-write-mcp publishes the posture on `/health` with no Secret, path, or config body in
  it.
- Plan `AC-003`: file-write-mcp runs the shared ordering and does not bind HTTP when validation fails.
- Plan `AC-005` for File Write: the rules live in `write_service.py` and `common.py` (rows `13`, `12`);
  this file contains wiring only.

## Out of scope

- Adding or changing File Write check ids (rows `13`, `12`), including enforcing or removing
  `supported_extensions`.
- Changing `_health()` or `make_health_response()` (rows `12`, `06`).
- Agent-side posture validation, classification, and Tool Discovery gating (rows `17`-`19`, `50`).
- Changing `_build_health_deps()`, `FileSecurityMixin`, or `WriteFileService`.
- Splitting `write_server.py` into smaller modules.

## Confirmation outcomes

- Resolved 2026-10-17: the File Write fingerprint view defined in `Design decisions` is retained as
  written. Counts only detect a changed number of allowed directories or extensions, not changed values;
  row `05` compares check ids and statuses, and row `17`'s `compare_fingerprint()` is not consumed by the
  row `18` gate.
- Resolved 2026-10-16 (Plan `UNK-06`): the flow's built-in `check_auth_token_present()` reports an empty
  `auth_token` as `WARNING` with reason `auth_token_missing`, identical in rows `04`, `42`-`49`, and `52`.
- Resolved 2026-10-17: the bind gate reads `SecurityPosture.validated` only. The payload `ready` is
  derived in `make_health_response()` from `deps` plus `validated`, and `SecurityPosture.ready` is never
  read, so no second Ready rule exists.
- Resolved 2026-10-17: a server that exits before publishing a posture is classified as an unreachable
  server. Row `18`'s `classify_server_failure()` reports an unreachable or unparseable posture as
  `AVAILABILITY`, so the `SystemExit` path needs no posture reason code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import the shared flow, contract, and row `13` validator | Completed | 2026-10-17 | 2026-10-17 | StartupStage import not needed |
| 2 | Add `_write_security_view()` and `_build_security_posture()` | Completed | 2026-10-17 | 2026-10-17 | view carries own_config_file, allowed_dirs_count, supported_extensions_count, and max_write_bytes |
| 3 | Pass the posture to `_health()` at `:151` | Completed | 2026-10-17 | 2026-10-17 | posture forwarded through the row 12 _health parameter instead of calling make_health_response directly |
| 4 | Add the `__main__` bind gate at `:232-234` | Completed | 2026-10-17 | 2026-10-17 | gate extracted into _enforce_posture_gate |
| 5 | Add `tests/mcp_servers/file/test_file_write_health_posture.py` | Completed | 2026-10-17 | 2026-10-17 | FileWriteConfig is frozen so a failing posture is built with dataclasses.replace, caplog needs propagate re-enabled because shared.logger disables it |
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
- **Requirement ID**: `REQ-002` (posture published on `/health`), `REQ-003` (shared startup ordering, validation failure blocks bind), `REQ-009` (File Write self-validation)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/file/write_server.py`, `scripts/mcp_servers/file/write_service.py`, `scripts/mcp_servers/file/common.py`, `scripts/mcp_servers/health_response.py`, `scripts/shared/security/startup_flow.py`, `scripts/shared/security/posture_contract.py`
