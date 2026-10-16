## Goal

Wire cicd-mcp's own security validation (row `10`) into the shared startup flow (row `04`), publish
the resulting Security Posture on `/health` (row `06`), and refuse HTTP bind when the posture is not
validated (`REQ-002`, `REQ-003`, `REQ-008`).

## Scope

- One modified module `scripts/mcp_servers/cicd/cicd_server.py`: build the posture, pass it to
  `make_health_response()`, and gate `run_http()` on it.
- This row adds no validation rule of its own: the validator is row `10`, the envelope is row `03`,
  the ordering is row `04`, the payload key is row `06`.
- One new test file `tests/mcp_servers/cicd/test_cicd_health_posture.py`.
- `scripts/mcp_servers/server.py` is a reference file only; it is not a row in the Plan's frozen
  table and is not modified here.

## Assumptions

- Verified current source: `_cfg = CicdConfig.load()` at `:56`,
  `_service: CiCdService = build_service(_cfg)` at `:57`, `_cicd_tool_availability()` at `:60-66`,
  `app = FastAPI(` at `:69`, `attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token or "")`
  at `:75`, the `/health` handler at `:139-151` (`deps["github_token"]` from
  `os.environ.get("GITHUB_TOKEN", "")` inside a `try/except (RuntimeError, OSError)` at `:142-148`,
  `details` at `:149`, `make_health_response(deps, details)` at `:150`), `class CiCdMCPServer` at
  `:159` with `own_config_file = "cicd_mcp_server.toml"` at `:165`, and
  `if __name__ == "__main__": server = CiCdMCPServer(); server.run_http()` at `:174-176`.
- `CiCdService(CiCdGuards)` (`scripts/mcp_servers/cicd/cicd_service_business.py:26`) inherits the
  guard mixin that stores `self._backend` (`cicd_service_guards.py:29`), so the backend row `10`'s
  `validate_cicd_security(backend, repo_allowlist, workflow_allowlist)` needs is reachable as
  `_service._backend`. `CiBackend` is a Protocol (`cicd_service_defs.py:31`) with no availability
  method, so `server.backend_available` is `NOT_APPLICABLE` for the shipped backend (row `10`).
- Production starts this module as `__main__`: `config/agent.toml:435`
  `cmd = ["/opt/llm/bin/mcp_cicd"]`. Verify the entry name against `deploy/build_binaries.sh` at
  implementation time.
- uvicorn 0.49.0 imports the app module before binding (`config.load()` at
  `.venv/lib/python3.14/site-packages/uvicorn/server.py:85-86` before `self.startup()` at `:94`);
  this row does not rely on that ordering, the `__main__` gate is the control.
- `config/cicd_mcp_server.toml` ships `repo_allowlist = ["masaos-minori/llmagent"]` (`:6`),
  `workflow_allowlist = ["ci.yml"]` (`:16`), `github_token = ""` (`:28`), and
  `auth_token = "${ENV:MCP_CICD_AUTH_TOKEN}"` (`:24`), so with row `10`'s check set the two
  allowlist checks are `OK` and `server.backend_available` is `NOT_APPLICABLE`.
- **Blocker, Needs confirmation**: `tests/conftest.py:29` sets `MCP_CICD_AUTH_TOKEN=""`, and
  `attach_auth_middleware()` accepts every request when the token is empty
  (`scripts/mcp_servers/server.py:100-113`). The flow's built-in `check_auth_token_present()`
  (row `04`) mirrors the Agent-side FATAL rule at `scripts/agent/startup_validation.py:71-81`, so
  as written it reports `FAILED` in the test environment, which makes `validated=false`, turns
  `/health` into 503, and breaks `tests/mcp_servers/cicd/test_mcp_server_health_status.py:25-33`
  (asserts 200 and `ready is True`). Resolve before implementing step 4; see Needs confirmation.
- **Needs confirmation**: `SecurityPosture.ready` (row `03`) versus the payload `ready` computed in
  row `06`. This row reads only `SecurityPosture.validated` for the bind gate.

## Design decisions

- Compute the posture once at module import into a module-level `_security_posture`, immediately
  after `_service` (`:57`). The Agent polls `/health` repeatedly during readiness polling, and the
  bind gate needs the outcome before `run_http()`.
- Gate in the `if __name__ == "__main__":` block (`:174-176`): when `_security_posture.validated`
  is false, log the failed check ids with their reason codes and `raise SystemExit(1)` before
  constructing the server.
- Do not raise while building the posture. Row `10`'s entry point returns results instead of
  raising, and a posture failure must stay reportable on `/health`.
- Pass `_service._backend` to `validate_cicd_security()`. It is same-package access to an attribute
  the guard mixin already owns; this row adds no public accessor and does not widen the service API.
- Keep the existing `deps` semantics unchanged (`os.environ.get("GITHUB_TOKEN", "")` at `:144-146`).
  The GitHub API token is an availability signal in `dependencies`, not a security-validation
  result. The pre-existing inconsistency between this handler and `build_service()`
  (`cicd_service_init.py:26`, which falls back to `cfg.github_token`) is left as it is; fixing it is
  not in this row's scope.
- Supply only the `SERVER_SECURITY_VALIDATION` stage to `run_startup_validation()`; the flow's
  built-in `check_own_config_only()`, `check_auth_token_present()`, and
  `check_published_tools_declared()` cover the common and tool-capability stages. `CONFIG_LOAD` and
  `SCHEMA_VALIDATION` reuse the already-loaded `_cfg`.
- This row defines the normalized non-secret view hashed by `compute_config_fingerprint()` (row
  `03`), because rows `07`-`16` define check ids but no fingerprint view:
  `{"own_config_file": "cicd_mcp_server.toml", "repo_allowlist_count",
  "workflow_allowlist_count", "max_log_size_kb"}` — scalars and counts only. `auth_token` and
  `github_token` (`cicd_models.py:29,33`) are excluded; both are Secrets.
- The existing `logger.warning` calls for empty allowlists (`cicd_service_guards.py:35-42`) stay
  unchanged: they are the operator-facing availability signal, the posture is the machine-readable
  security result (row `10`).

## Alternatives considered

- Put the gate inside `MCPServer.run_http()` — rejected: `scripts/mcp_servers/server.py` is not a
  row in the Plan's frozen table, and a base-class gate would apply to servers whose validators
  have not landed yet.
- Add a public `CiCdService.backend` accessor so the wiring does not touch `_backend` — rejected
  for this row: it widens the service API, and row `10`'s procedure does not add such an accessor.
  Recorded as Needs confirmation.
- Compute the posture lazily on the first `/health` probe — rejected: the gate must decide before
  bind.
- Raise at import time when validation fails — rejected: it breaks every test that imports the
  module and produces no posture for the Agent to classify.
- Add a posture check for `GITHUB_TOKEN` presence — rejected: it is already the `dependencies`
  entry the `/health` contract defines, and a Secret-derived value must not enter the posture.

## Implementation
### Target file

`scripts/mcp_servers/cicd/cicd_server.py` (modify)

### Procedure

1. Import `run_startup_validation` and `StartupStage` from `shared.security.startup_flow` (row `04`),
   `SecurityPosture` and `compute_config_fingerprint` from `shared.security.posture_contract`
   (row `03`), and `validate_cicd_security` from `mcp_servers.cicd.cicd_service_guards` (row `10`).
2. Add `_cicd_security_view(cfg: CicdConfig) -> dict[str, object]` (new private function) returning
   the normalized view described above.
3. Add `_build_security_posture() -> SecurityPosture` (new private function) that calls
   `run_startup_validation()` with `server_key="cicd"`, `own_config_file="cicd_mcp_server.toml"`,
   the `SERVER_SECURITY_VALIDATION` stage callable
   (`validate_cicd_security(_service._backend, _cfg.repo_allowlist, _cfg.workflow_allowlist)`), and
   the fingerprint view.
4. Assign `_security_posture: SecurityPosture = _build_security_posture()` after `_service` (`:57`).
5. Change `:150` to `make_health_response(deps, details, security=_security_posture)`.
6. Add the gate to `:174-176`: log the failed check ids and reason codes, then
   `raise SystemExit(1)` before `CiCdMCPServer()` is constructed.
7. Add `tests/mcp_servers/cicd/test_cicd_health_posture.py`.

### Method

- Build the posture after `_cfg` and `_service` exist and before `app = FastAPI(` (`:69`), so the
  posture exists before the middleware is attached and before any route can be hit.
- The gate log line is one line, format:
  `cicd-mcp: security posture FAILED (<check_id>:<reason_code>, ...) — refusing to bind`. Only
  check ids and reason codes appear; repository and workflow names are allowlist entries
  (`REQ-002`).
- `_build_security_posture()` must not call `CicdConfig.load()` or `build_service()` again; it
  reuses `_cfg` and `_service`.
- Keep `details` exactly as today (`{"service": "cicd-mcp"}` at `:149`); the posture is a sibling
  top-level key (row `06`).
- Type the posture as `SecurityPosture`, not `dict[str, object]`.

### Details

- `server_key` is `"cicd"`, matching `[mcp_servers.cicd]` (`scripts/agent/startup_validation.py:71-73`).
- `REQUIRED_CHECK_IDS["cicd"]` (row `03`) must list exactly row `10`'s ids
  (`server.repo_allowlist`, `server.workflow_allowlist`, `server.workflow_pattern_valid`,
  `server.backend_available`) plus the flow's built-in common ids, or row `17` reports
  `check_set_mismatch`.
- `server.workflow_pattern_valid` is evaluated from the configured patterns, so a pattern containing
  `/` or `\` (which `_assert_allowed_workflow()` rejects on every call,
  `cicd_service_guards.py:68-71`) becomes a startup `FAILED` instead of a per-call denial. The
  shipped `["ci.yml"]` is valid.
- The module is about 176 lines; the addition is roughly 30 lines and stays under the 200-line
  convention.

## Compatibility considerations

- Existing `/health` assertions keep passing once the auth-token question is resolved: with the
  shipped config every cicd check is `OK` or `NOT_APPLICABLE`, so `validated` stays `true` and
  `ready` stays `true` (`tests/mcp_servers/cicd/test_mcp_server_health_status.py:25-33,84-92`).
- The degraded paths stay intact: `tests/mcp_servers/cicd/test_mcp_server_health_status.py:67-74`
  asserts 503 with `"github_token" in data["dependencies"]`, which is still produced by the
  unchanged `deps` logic.
- The `security` key is additive (row `06`); `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`
  and `test_mcp_server_health_status.py` do not enumerate payload keys.
- Behavior change is limited to startup and `/health`: a cicd config with an empty
  `repo_allowlist` or `workflow_allowlist` now exits non-zero before binding instead of starting
  and denying every call with the existing fail-closed messages (`cicd_service_guards.py:53-70`).
- No `docs/*.md` edit is in scope for this row; `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md:226`
  and `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` are Plan follow-ups.

## Security considerations

- `REQ-008` / Plan `INV-05`: cicd-mcp validates its own configuration before Ready, and the Agent
  stops reading `cicd_mcp_server.toml` (`REQ-017`).
- `REQ-002` / Plan `INV-09`: the fingerprint view excludes `auth_token`, `github_token`, and every
  `repo_allowlist` / `workflow_allowlist` value; only counts and scalars are hashed.
- `REQ-011`: the Agent-side empty-`auth_token` rejection stays at
  `scripts/agent/startup_validation.py:71-81` (`mcp_auth`, not removed by row `22`). cicd-mcp has
  no server-side equivalent today: `attach_auth_middleware(..., _cfg.auth_token or "")` (`:75`)
  installs the accept-all fallback. Whether the posture check becomes that equivalent is the
  Needs-confirmation decision recorded below; it must not be left enforced by neither side.
- `REQ-004`: the gate log line and every posture message carry reason codes only.

## Rollback considerations

- Revert this commit together with rows `06` (payload parameter), `10` (validator), and `04` (flow).
  No config or data migration is involved.
- The gate is the only statement that can make a previously-startable cicd config unstartable;
  reverting the `__main__` block restores today's behavior without touching `/health`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Posture published | `uv run pytest tests/mcp_servers/cicd/test_cicd_health_posture.py` (new test file) | `/health` body carries the `security` key with `server_key == "cicd"` and `contract_version == SECURITY_CONTRACT_VERSION` |
| Validated shipped config | same new test file | `_security_posture.validated is True` against `config/cicd_mcp_server.toml`, with `server.backend_available` present as `NOT_APPLICABLE` |
| Empty allowlist blocks bind | same new test file | with `repo_allowlist` or `workflow_allowlist` patched empty, `validated is False`, `/health` returns 503 with `ready is False`, and the `__main__` gate raises `SystemExit` |
| Invalid workflow pattern | same new test file | a pattern containing `/` yields `server.workflow_pattern_valid` `FAILED` with reason `config_invalid` |
| Existing cicd suite | `uv run pytest tests/mcp_servers/cicd/` | passes, including `test_mcp_server_health_status.py:25-33,67-74` |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-002`: cicd-mcp publishes the posture on `/health` with no Secret, allowlist element, or
  config body in it.
- Plan `AC-003`: cicd-mcp runs the shared ordering and does not bind HTTP when validation fails.
- Plan `AC-005` for CI/CD: the rules live in `cicd_service_guards.py` (row `10`); this file contains
  wiring only.

## Out of scope

- Adding or changing CI/CD check ids (row `10`).
- Changing `make_health_response()` or the payload shape (row `06`).
- Agent-side posture validation, classification, and Tool Discovery gating (rows `17`-`19`).
- Changing `_cicd_tool_availability()`, the backend Protocol, or the `GITHUB_TOKEN` resolution in
  `cicd_service_init.py:26`.
- Adding a public backend accessor to `CiCdService`.

## Needs confirmation

- Empty `auth_token` for cicd-mcp: RESOLVED 2026-10-16 (Plan `UNK-06`) as option A. Row `04`'s
  `check_auth_token_present()` reports `WARNING` with reason `auth_token_missing` and `validated` stays
  `true`, so `tests/conftest.py:29` (`MCP_CICD_AUTH_TOKEN=""`, "preserving these servers' pre-existing
  empty-token accept-all behavior that many tests rely on") keeps
  `tests/mcp_servers/cicd/test_mcp_server_health_status.py:25-33` passing, and the Agent's `mcp_auth`
  FATAL check at `scripts/agent/startup_validation.py:71-81` remains the production control. Option B
  (keep `FAILED` and amend the Plan to add `tests/conftest.py` plus the cicd HTTP tests that call
  endpoints without an `Authorization` header so they send `MCP_TEST_AUTH_HEADERS`
  (`tests/mcp_servers/_auth_headers.py`)) was not chosen. Option C (exempt `/health` from the auth
  middleware) remains rejected because it changes `scripts/mcp_servers/server.py`, which is not a Plan
  row.
- Whether row `10` should expose the backend publicly (or accept `None`) instead of this row reading
  `_service._backend`.
- The normalized fingerprint view for CI/CD is defined here because rows `07`-`16` define no view;
  confirm the field list before row `05` compares fingerprints.
- Whether `SecurityPosture.ready` is the bind-gate outcome or a duplicate of the payload `ready`
  (rows `03`/`04`/`06`/`17`).
- Whether the Agent classifies a server that exits before publishing any posture through the
  existing `StartupFailure`/stderr path or expects a posture reason code (rows `18`/`22`/`39`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import the shared flow, contract, and row `10` validator | Pending | — | — | rows `03`/`04`/`10` must land first |
| 2 | Add `_cicd_security_view()` and `_build_security_posture()` | Pending | — | — | `_service._backend` access is Needs-confirmation |
| 3 | Pass the posture to `make_health_response()` at `:150` | Pending | — | — | depends on row `06` signature |
| 4 | Add the `__main__` bind gate at `:174-176` | Pending | — | — | blocked on the empty-`auth_token` decision |
| 5 | Add `tests/mcp_servers/cicd/test_cicd_health_posture.py` | Pending | — | — | new file, not in the frozen table |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | `tests/conftest.py:29` sets `MCP_CICD_AUTH_TOKEN=""`; a `FAILED` `common.auth_token` check would flip existing cicd `/health` tests from 200 to 503 | No | — |
| 5 | New test files are not rows in the Plan's frozen table; the Plan must be amended or the assertions added to an existing `tests/mcp_servers/cicd/*` file | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (posture published on `/health`), `REQ-003` (shared startup ordering, validation failure blocks bind), `REQ-008` (CI/CD self-validation)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/cicd/cicd_server.py`, `scripts/mcp_servers/cicd/cicd_service_guards.py`, `scripts/mcp_servers/health_response.py`, `scripts/shared/security/startup_flow.py`, `scripts/shared/security/posture_contract.py`
