## Goal

Wire File Read self-validation (row `11`) into the shared startup flow (row `04`), publish the resulting
Security Posture on `/health` through the shared file-server health helper (rows `12`, `06`), and refuse
HTTP bind when the posture is not validated (`REQ-002`, `REQ-003`, `REQ-009`).

## Scope

- One modified module `scripts/mcp_servers/file/read_server.py`: build the posture, pass it to
  `_health()`, and gate `run_http()` on it.
- This row adds no validation rule of its own: the validator is row `11`, the shared base checks are row
  `12`, the envelope is row `03`, the ordering is row `04`, the payload key is row `06`.
- One new test file `tests/mcp_servers/file/test_file_read_health_posture.py`.
- `scripts/mcp_servers/file/common.py` and `scripts/mcp_servers/server.py` are reference files only;
  `common.py` is row `12`'s target and is not modified here, `server.py` is not a row at all.

## Assumptions

- Verified current source: `_cfg = FileReadConfig.load()` at `:74`,
  `_service: ReadFileService = build_service(_cfg)` at `:75`,
  `attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token)` at `:88`, the `/health` handler at
  `:244-248` whose whole body is `result: JSONResponse = await _health(_cfg.allowed_dirs)` at `:247`,
  `class FileReadMCPServer(MCPServer)` at `:313` with `http_port = 8005` at `:318`,
  `own_config_file = "file_read_mcp_server.toml"` at `:319`,
  `app_module = "mcp_servers.file.read_server:app"` at `:320`, and
  `if __name__ == "__main__": server = FileReadMCPServer(); server.run_http()` at `:328-330`.
- The `/health` payload is built by `_health()` in `scripts/mcp_servers/file/common.py:143-146`, which
  calls `make_health_response(deps, {})`. Row `12` adds the optional `posture` parameter to `_health()`;
  this row is the caller that supplies it.
- Production starts this module as `__main__`: `config/agent.toml:409`
  `cmd = ["/opt/llm/bin/mcp_file_read"]`. Verify the entry name against `deploy/build_binaries.sh` at
  implementation time.
- uvicorn 0.49.0 imports the app module before binding (`config.load()` at
  `.venv/lib/python3.14/site-packages/uvicorn/server.py:85-86` before `self.startup()` at `:94`); this
  row does not rely on that ordering, the `__main__` gate is the control.
- `MCP_FILE_READ_AUTH_TOKEN` is set to `"test-token"` by `tests/conftest.py:38-46`, so the flow's
  built-in `common.auth_token` check passes in the test suite for this server.
- `/opt/llm` and `/opt/llm/storage` both exist in this environment, and
  `config/file_read_mcp_server.toml` ships `allowed_dirs = ["/opt/llm", "/opt/llm/storage"]` (`:4`) and
  `max_read_bytes = 1000000` (`:7`), so with row `11`'s check set the shipped configuration produces
  `validated=true`.
- **Needs confirmation**: `SecurityPosture.ready` (row `03`) versus the payload `ready` computed in row
  `06`. This row reads only `SecurityPosture.validated` for the bind gate.

## Design decisions

- Compute the posture once at module import into a module-level `_security_posture`, immediately after
  `_service` (`:75`). The Agent polls `/health` repeatedly during readiness polling, and the bind gate
  needs the outcome before `run_http()`.
- Gate in the `if __name__ == "__main__":` block (`:328-330`): when `_security_posture.validated` is
  false, log the failed check ids with their reason codes and `raise SystemExit(1)` before constructing
  the server.
- Do not raise while building the posture. Row `11`'s entry point returns results instead of raising, and
  a posture failure must stay reportable on `/health`.
- Supply only the `SERVER_SECURITY_VALIDATION` stage (`validate_file_read_security(_cfg)` from row `11`)
  to `run_startup_validation()`; the flow's built-in `check_own_config_only()`,
  `check_auth_token_present()`, and `check_published_tools_declared()` cover the common and
  tool-capability stages. Row `11` already delegates the two shared base checks to row `12`'s
  `validate_file_security_base()`, so this row does not call the base itself.
- Pass the posture through `_health()` rather than calling `make_health_response()` directly: the three
  file servers share one health builder, and bypassing it would fork the payload shape for one server.
- This row defines the normalized non-secret view hashed by `compute_config_fingerprint()` (row `03`),
  because rows `07`-`16` define check ids but no fingerprint view. The view is
  `{"own_config_file": "file_read_mcp_server.toml", "allowed_dirs_count": len(_cfg.allowed_dirs),
  "max_read_bytes": _cfg.max_read_bytes}` — scalars and counts only.
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
- Validate `allowed_dirs` existence here as well as in `_build_health_deps()` — rejected: row `12`'s
  `server.allowed_dirs_exist` already covers it, and `deps` keeps the live availability signal.

## Implementation
### Target file

`scripts/mcp_servers/file/read_server.py` (modify)

### Procedure

1. Import `run_startup_validation` and `StartupStage` from `shared.security.startup_flow` (row `04`),
   `SecurityPosture` and `compute_config_fingerprint` from `shared.security.posture_contract` (row `03`),
   and `validate_file_read_security` from `mcp_servers.file.read_security` (row `11`).
2. Add `_read_security_view(cfg: FileReadConfig) -> dict[str, object]` (new private function) returning
   the normalized view described above.
3. Add `_build_security_posture() -> SecurityPosture` (new private function) that calls
   `run_startup_validation()` with `server_key="file_read"`,
   `own_config_file="file_read_mcp_server.toml"`, the `SERVER_SECURITY_VALIDATION` stage callable
   (`validate_file_read_security(_cfg)`), and the fingerprint view.
4. Assign `_security_posture: SecurityPosture = _build_security_posture()` after `_service` (`:75`).
5. Change `:247` to `await _health(_cfg.allowed_dirs, posture=_security_posture)`.
6. Add the gate to `:328-330`: log the failed check ids and reason codes, then `raise SystemExit(1)`
   before `FileReadMCPServer()` is constructed.
7. Add `tests/mcp_servers/file/test_file_read_health_posture.py`.

### Method

- Build the posture after `_cfg` and `_service` exist and before `app = FastAPI(...)` is served, so the
  posture exists before the middleware is attached at `:88` and before any route can be hit.
- The gate log line is one line, format:
  `file-read-mcp: security posture FAILED (<check_id>:<reason_code>, ...) — refusing to bind`.
  Only check ids and reason codes appear; allowed directory paths are excluded (`REQ-002`, `REQ-004`).
- `_build_security_posture()` must not call `FileReadConfig.load()` again; it reuses `_cfg`.
- Keep `_health()`'s `deps` semantics unchanged: `_build_health_deps()` (`common.py:108-141`) still
  reports filesystem availability, and `details` stays `{}` for the file servers.
- Type the posture as `SecurityPosture`, not `dict[str, object]`.

### Details

- `server_key` is `"file_read"`, matching the value the `/v1/tools` payload already attaches
  (`read_server.py:271`) and `[mcp_servers.file_read]` in `config/agent.toml`.
- `REQUIRED_CHECK_IDS["file_read"]` (row `03`) must list exactly row `11`'s ids
  (`server.allowed_dirs_configured`, `server.allowed_dirs_exist`, `server.max_read_bytes`) plus the flow's
  built-in common ids, or row `17` reports `check_set_mismatch`.
- `server.allowed_dirs_exist` (row `12`) and `_build_health_deps()`'s `deps["filesystem"]` entry describe
  the same configured value from two layers: the posture reports it as a validation result and blocks
  bind, `dependencies` reports it as a live availability signal and only degrades the payload. Both stay.
- The module is about 330 lines, already above the 200-line convention. The roughly 30 added lines stay
  in this file; do not split it as a side effect of this row.

## Compatibility considerations

- Existing `/health` assertions keep passing: `tests/mcp_servers/file/test_file_server_auth.py:74-76` and
  `:117-119` assert the auth-middleware status codes on `/health`, which this row does not touch.
- With the shipped config every file-read check is `OK`, so `validated` stays `true` and the payload
  `ready` stays `true`.
- The `security` key is additive (row `06`); no existing file-server test enumerates payload keys.
- Behavior change is limited to startup and `/health`: a config with an empty `allowed_dirs`, a
  non-existent allowed directory, or `max_read_bytes <= 0` now exits non-zero before binding instead of
  starting and rejecting every request at call time.
- No `docs/*.md` edit is in scope for this row; `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` and
  `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` are Plan follow-ups.

## Security considerations

- `REQ-009` / Plan `INV-05`: file-read-mcp validates its own configuration before Ready, and the Agent
  stops reading `file_read_mcp_server.toml` (`REQ-017`).
- `REQ-002` / Plan `INV-09`: the fingerprint view excludes `auth_token` and every `allowed_dirs` element;
  only the count is hashed. Allowed directory paths are sensitive paths and appear in no posture message.
- `REQ-011`: the Agent-side empty-`auth_token` rejection stays at
  `scripts/agent/startup_validation.py:71-81` (`mcp_auth`, not removed by row `22`); this server has no
  server-side equivalent today — `attach_auth_middleware(..., _cfg.auth_token)` (`:88`) installs the
  accept-all fallback when the token is empty (`scripts/mcp_servers/server.py:100-113`). The flow's
  built-in `check_auth_token_present()` is the posture-level copy; it reports `WARNING` with reason
  `auth_token_missing` and keeps `validated=true` (Plan `UNK-06`, resolved 2026-10-16; row `04`).
- `REQ-004`: the gate log line and every posture message carry reason codes only.

## Rollback considerations

- Revert this commit together with rows `06` (payload parameter), `11` (validator), `12` (`_health()`
  parameter), and `04` (flow). No config or data migration is involved.
- The gate is the only statement that can make a previously-startable file-read config unstartable;
  reverting the `__main__` block restores today's behavior without touching `/health`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Posture published | `uv run pytest tests/mcp_servers/file/test_file_read_health_posture.py` (new test file) | `/health` body carries the `security` key with `server_key == "file_read"` and `contract_version == SECURITY_CONTRACT_VERSION` |
| Validated shipped config | same new test file | `_security_posture.validated is True` against `config/file_read_mcp_server.toml` |
| Empty allowlist blocks bind | same new test file | with `allowed_dirs` patched to `[]`, `server.allowed_dirs_configured` is `FAILED` with reason `allowlist_empty`, `validated is False`, `/health` returns 503 with `ready is False`, and the `__main__` gate raises `SystemExit` |
| Non-existent allowed dir | same new test file | `server.allowed_dirs_exist` is `FAILED` with reason `allowed_dir_invalid` |
| Existing file suite | `uv run pytest tests/mcp_servers/file/` | passes, including `test_file_server_auth.py` |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-002`: file-read-mcp publishes the posture on `/health` with no Secret, path, or config body in
  it.
- Plan `AC-003`: file-read-mcp runs the shared ordering and does not bind HTTP when validation fails.
- Plan `AC-005` for File Read: the rules live in `read_security.py` and `common.py` (rows `11`, `12`);
  this file contains wiring only.

## Out of scope

- Adding or changing File Read check ids (rows `11`, `12`).
- Changing `_health()` or `make_health_response()` (rows `12`, `06`).
- Agent-side posture validation, classification, and Tool Discovery gating (rows `17`-`19`, `50`).
- Changing `_build_health_deps()`, `FileSecurityMixin`, or `ReadFileService`.
- Splitting `read_server.py` into smaller modules.

## Needs confirmation

- The normalized fingerprint view for File Read is defined here because rows `07`-`16` define no view;
  confirm the field list before row `05` compares fingerprints. Counts only detect a changed number of
  allowed directories, not a changed directory.
- The status of the flow's built-in `check_auth_token_present()` when `auth_token` is empty: RESOLVED
  2026-10-16 (Plan `UNK-06`) as `WARNING` with reason `auth_token_missing`, identical in rows `04`,
  `42`-`49`, and `52`.
- Whether `SecurityPosture.ready` is the bind-gate outcome or a duplicate of the payload `ready` (rows
  `03`/`04`/`06`/`17`).
- Whether the Agent classifies a server that exits before publishing any posture through the existing
  `StartupFailure`/stderr path or expects a posture reason code (rows `18`/`22`/`39`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import the shared flow, contract, and row `11` validator | Pending | — | — | rows `03`/`04`/`11`/`12` must land first |
| 2 | Add `_read_security_view()` and `_build_security_posture()` | Pending | — | — | view field list is Needs-confirmation |
| 3 | Pass the posture to `_health()` at `:247` | Pending | — | — | depends on row `12`'s new parameter |
| 4 | Add the `__main__` bind gate at `:328-330` | Pending | — | — | `raise SystemExit(1)` |
| 5 | Add `tests/mcp_servers/file/test_file_read_health_posture.py` | Pending | — | — | new file, not in the frozen table |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (posture published on `/health`), `REQ-003` (shared startup ordering, validation failure blocks bind), `REQ-009` (File Read self-validation)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/file/read_server.py`, `scripts/mcp_servers/file/read_security.py`, `scripts/mcp_servers/file/common.py`, `scripts/mcp_servers/health_response.py`, `scripts/shared/security/startup_flow.py`, `scripts/shared/security/posture_contract.py`
