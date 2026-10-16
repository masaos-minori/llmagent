## Goal

Wire shell-mcp's own security validation (row `07`) into the shared startup flow (row `04`), publish
the resulting Security Posture on `/health` (row `06`), and refuse HTTP bind when the posture is not
validated (`REQ-002`, `REQ-003`, `REQ-005`).

## Scope

- One modified module `scripts/mcp_servers/shell/shell_server.py`: build the posture, pass it to
  `make_health_response()`, and gate `run_http()` on it.
- This row adds no validation rule of its own: the validator is row `07`, the envelope is row `03`,
  the ordering is row `04`, the payload key is row `06`.
- One new test file `tests/mcp_servers/shell/test_shell_health_posture.py` for the posture
  publication and the bind gate.
- `scripts/mcp_servers/server.py` is a reference file only; it is not a row in the Plan's frozen
  table and is not modified here.

## Assumptions

- Verified current source: `_cfg: ShellConfig = ShellConfig.load()` at `:53`,
  `_service: ShellService = build_service(load_shell_policy())` at `:54`,
  `_shell_tool_availability()` at `:57-62`, the empty-token `RuntimeError` at `:70-74`,
  `attach_auth_middleware(..., _cfg.auth_token)` at `:75`, the `/health` handler at `:116-127`
  (`deps` from `shutil.which("sh")` at `:119-121`, `details` at `:122-125`,
  `make_health_response(deps, details)` at `:126`), `class ShellMCPServer` at `:187` with
  `http_port = 8009` at `:192` and `own_config_file = "shell_mcp_server.toml"` at `:193`, and
  `if __name__ == "__main__": server = ShellMCPServer(); server.run_http()` at `:202-204`.
- Production starts this module as `__main__`: `config/agent.toml:361`
  `cmd = ["/opt/llm/bin/mcp_shell"]`, and `deploy/build_binaries.sh` builds that binary from the
  module entry. Verify the entry name against `deploy/build_binaries.sh` at implementation time.
- uvicorn 0.49.0 imports the app module before binding: `config.load()` at
  `.venv/lib/python3.14/site-packages/uvicorn/server.py:85-86` runs before `self.startup()` at
  `:94`. So an import-time failure would also block bind. This row does not rely on that ordering;
  the `__main__` gate is the control.
- `MCPServer.run_http()` (`scripts/mcp_servers/server.py:225-246`) already enforces loopback-only
  bind and `ConfigLoader.restrict_to(self.own_config_file)`, and raises `ConfigPermissionError`
  when `own_config_file` is falsy. The posture gate runs before that call.
- `MCP_SHELL_AUTH_TOKEN` is set to `"test-token"` by `tests/conftest.py:33-41`, so the flow's
  built-in `common.auth_token` check (row `04`) passes in the test suite for this server.
- `firejail` is present in this environment (`/usr/bin/firejail`), and `init_sandbox()` already
  raises when `firejail` is configured but missing (`scripts/mcp_servers/shell/shell_service_static_helpers.py:32-37`).
- **Needs confirmation**: `SecurityPosture.ready` (row `03`) and the payload `ready` computed in
  row `06` are two different values. This row reads only `SecurityPosture.validated` for the bind
  gate and never reads `posture.ready`; rows `03`/`04`/`06`/`17` must state which field is
  authoritative before row `17` validates a published posture.

## Design decisions

- Compute the posture once at module import into a module-level `_security_posture`, immediately
  after `_service` (`:54`). `/health` is polled repeatedly during Agent readiness polling, so
  re-running validation per probe would multiply the cost, and the bind gate needs the outcome
  before `run_http()` is called.
- Gate in the `if __name__ == "__main__":` block (`:202-204`): when `_security_posture.validated`
  is false, log the failed check ids with their reason codes and `raise SystemExit(1)` before
  constructing the server. `SystemExit` needs no new import and exits non-zero without a traceback.
- Do not raise while building the posture. A policy violation must become a `FAILED`
  `SecurityCheckResult` inside the posture, because every test that imports this module would
  otherwise fail at collection time with no indication of which check failed.
- Keep the existing `deps` semantics unchanged (`shutil.which("sh")` at `:119-121`). Dependency
  availability stays in the `dependencies` key; the posture carries only security-validation
  results. `ready` is derived inside `make_health_response()` (row `06`) from `deps` and
  `posture.validated`, so this server cannot invent its own Ready rule.
- Supply only the `SERVER_SECURITY_VALIDATION` stage (`validate_shell_security()` from row `07`) to
  `run_startup_validation()`; the flow's built-in `check_own_config_only()`,
  `check_auth_token_present()`, and `check_published_tools_declared()` cover the common and
  tool-capability stages. `CONFIG_LOAD` and `SCHEMA_VALIDATION` reuse the already-loaded `_cfg` and
  `load_shell_policy()` result; the flow is not given a callable that re-reads the config.
- This row defines the normalized non-secret view hashed by `compute_config_fingerprint()` (row
  `03`), because rows `07`-`16` define check ids but no fingerprint view. The view is
  `{"own_config_file": "shell_mcp_server.toml", "sandbox_backend": _cfg.shell_sandbox_backend,
  "command_allowlist_count": len(_cfg.command_allowlist),
  "cwd_allowed_dirs_count": len(_cfg.shell_cwd_allowed_dirs), "env_allowlist_count":
  len(_cfg.env_allowlist), "max_timeout_sec", "max_output_kb", "max_memory_mb", "kill_policy",
  "shell_sandbox_backend"}` — scalars and counts only.
- The bind gate is startup-only. There is no re-validation on a later `/health` probe and no
  Hot Rediscovery path (`REQ-014`, ADR-003 Static Availability).

## Alternatives considered

- Put the gate inside `MCPServer.run_http()` — rejected: `scripts/mcp_servers/server.py` is not a
  row in the Plan's frozen table, and a base-class gate would couple the rollout of all ten
  `MCPServer` subclasses, whose validators land in separate rows (`07`-`16` and `51`).
- Compute the posture lazily on the first `/health` probe — rejected: the gate must decide before
  bind, and a lazy posture makes the first probe pay the whole validation cost.
- Raise at import time when validation fails — rejected: it converts one failed check into an
  import failure for the whole module, breaks every test that imports it, and produces no posture
  for the Agent to classify.
- Let the server bind and rely on `ready=false` + HTTP 503 alone — rejected: Plan `REQ-003` and
  `AC-003` state that a server which fails validation does not bind HTTP, and a bound server with
  an unsandboxed Shell is exactly the state `REQ-005` forbids.
- Add a `DEPENDENCY_VALIDATION` stage that mirrors `shutil.which("sh")` as a posture check —
  rejected for this row: the fact is already published in `dependencies`, and a second copy in the
  posture would give the Agent two sources for one condition. Recorded as Needs confirmation
  because `REQ-003` lists Dependency Validation in the shared ordering.

## Implementation
### Target file

`scripts/mcp_servers/shell/shell_server.py` (modify)

### Procedure

1. Import `run_startup_validation` and `StartupStage` from `shared.security.startup_flow` (row `04`),
   `SecurityPosture` and `compute_config_fingerprint` from `shared.security.posture_contract`
   (row `03`), and `validate_shell_security` from `mcp_servers.shell.shell_service_static_helpers`
   (row `07`).
2. Add `_shell_security_view(cfg: ShellConfig) -> dict[str, object]` (new private function) that
   returns the normalized non-secret view described above.
3. Add `_build_security_posture() -> SecurityPosture` (new private function) that calls
   `run_startup_validation()` with `server_key="shell"`, `own_config_file="shell_mcp_server.toml"`,
   the `SERVER_SECURITY_VALIDATION` stage callable, and the fingerprint view.
4. Assign `_security_posture: SecurityPosture = _build_security_posture()` after `_service` (`:54`).
5. Change `:126` to `make_health_response(deps, details, security=_security_posture)`.
6. Add the gate to `:202-204`: log the failed check ids and reason codes, then
   `raise SystemExit(1)` before `ShellMCPServer()` is constructed.
7. Add `tests/mcp_servers/shell/test_shell_health_posture.py`.

### Method

- Order the statements so the posture is built after `_cfg` and `_service` exist and before
  `app = FastAPI(...)` (`:64`) is served; the existing empty-token `RuntimeError` at `:70-74` stays
  where it is, so an empty token still aborts import before the gate is ever reached.
- The gate log line is one line, format:
  `shell-mcp: security posture FAILED (<check_id>:<reason_code>, ...) — refusing to bind`.
  Only check ids and reason codes appear; no configured value, path, or token (`REQ-004`).
- `_build_security_posture()` passes the already-loaded config objects; it must not call
  `ShellConfig.load()` or `load_shell_policy()` again.
- Keep `details` exactly as today (`service`, `sandbox_backend` at `:122-125`); the posture is a
  sibling key, not a `details` entry (row `06`).
- Type the posture as `SecurityPosture`, not `dict[str, object]`, so mypy catches a wrong
  `contract_version` or `server_key`.

### Details

- `server_key` is `"shell"`, matching the `[mcp_servers.shell]` key the Agent uses
  (`scripts/agent/startup_validation.py:71-73`), so identity comparison in row `17` is string
  equality.
- `REQUIRED_CHECK_IDS["shell"]` (row `03`) must list exactly the four ids row `07` defines
  (`server.sandbox_backend`, `server.sandbox_binary`, `server.command_allowlist`,
  `server.resource_limits`) plus the flow's built-in common ids, or row `17` will report
  `check_set_mismatch`.
- For Shell there are two enforcement points, and this row does not remove the first one:
  `init_sandbox()` raises at import for a backend it cannot prove safe (row `07` extends it to
  `"none"`, `""`, and unknown values), so a bad backend never reaches the posture. The posture gate
  is the enforcement point for `server.command_allowlist` and `server.resource_limits`, and it is
  the only place the Shell posture becomes observable to the Agent.
- The module is about 205 lines; the addition is roughly 30 lines. If the file grows past the
  200-line convention, the posture build and the view helper move to a sibling module
  (`scripts/mcp_servers/shell/shell_posture.py`) and that module must be added to the Plan as an
  additional target row rather than folded in here.

## Compatibility considerations

- Existing `/health` assertions keep passing as long as the shipped `config/shell_mcp_server.toml`
  produces a validated posture: `command_allowlist` is non-empty (`:4`) and
  `shell_sandbox_backend = "firejail"` (`:30`) with the binary present, so all four checks are
  `OK` and `ready` stays `true`. `tests/mcp_servers/shell/test_shell_server_auth.py:40-42` and
  `tests/mcp_servers/shell/test_shell_mcp_service.py:750` are the assertions to re-run.
- The `security` key is additive (row `06`), and `tests/mcp_servers/shell/*` do not enumerate
  payload keys, so no existing assertion changes.
- Behavior change is limited to startup and `/health`: a Shell config with an empty
  `command_allowlist` now exits non-zero before binding instead of starting and denying every call
  (`:59-60`). Runtime denial behavior is unchanged.
- No `docs/*.md` edit is in scope for this row; `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md:119,121`
  and `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` are listed as Plan follow-ups.

## Security considerations

- `REQ-005` / Plan `INV-05`: Shell cannot reach Ready with an unsandboxed or unvalidated backend,
  and cannot reach Ready with an empty command allowlist.
- `REQ-002` / Plan `INV-09`: the fingerprint view excludes `auth_token`, `audit_log_path`,
  `default_cwd`, `execution_user`, `shell_path`, and every allowlist element; only counts and
  scalars are hashed, and `SecurityCheckResult.__post_init__` / `SecurityPosture.__post_init__`
  (rows `02`/`03`) are the enforcement points.
- `REQ-011`: the Agent-side empty-`auth_token` rejection stays at
  `scripts/agent/startup_validation.py:71-81` (`mcp_auth`, not removed by row `22`); this row's
  posture adds the server-side copy through the flow's built-in `check_auth_token_present()`.
  Shell already refuses to import with an empty token (`:70-74`).
- `REQ-004`: the gate log line and every posture message carry reason codes only.

## Rollback considerations

- Revert this commit together with rows `06` (payload parameter), `07` (validator), and `04`
  (flow). No config or data migration is involved; reverting this row alone leaves row `07`'s
  validator unused.
- The gate is the only statement that can make a previously-startable Shell config unstartable; if
  a deployment must run while the posture contract is being fixed, reverting the `__main__` gate
  block restores today's behavior without touching `/health`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Posture published | `uv run pytest tests/mcp_servers/shell/test_shell_health_posture.py` (new test file) | `/health` body carries the `security` key with `server_key == "shell"` and `contract_version == SECURITY_CONTRACT_VERSION` |
| Validated shipped config | same new test file | `_security_posture.validated is True` against `config/shell_mcp_server.toml` |
| Empty allowlist blocks bind | same new test file | with `command_allowlist` patched empty, `validated is False`, `/health` returns 503 with `ready is False`, and the `__main__` gate raises `SystemExit` |
| Existing Shell suite | `uv run pytest tests/mcp_servers/shell/` | passes |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-002`: shell-mcp publishes the posture on `/health` with no Secret, allowlist element,
  path, or config body in it.
- Plan `AC-003`: shell-mcp runs the shared ordering and does not bind HTTP when validation fails.
- Plan `AC-005` for Shell: the validation rules live in row `07`'s module, and this file contains
  wiring only.

## Out of scope

- Changing `init_sandbox()` or adding Shell validation rules (row `07`).
- Changing `make_health_response()` or the payload shape (row `06`).
- Agent-side posture validation, classification, and Tool Discovery gating (rows `17`-`19`).
- Adding a `DEPENDENCY_VALIDATION` posture check for `sh` presence.
- `web_search` self-validation and wiring (rows `51`-`52`, added 2026-10-16 resolving Plan `UNK-04`).

## Confirmation outcomes

- Resolved 2026-10-17: the Shell fingerprint view defined in `Design decisions` is retained as written.
  It carries one `sandbox_backend` scalar, counts, and presence flags, so a changed allowlist entry with
  an unchanged count is not detectable through the digest; row `05` compares check ids and statuses, and
  row `17`'s `compare_fingerprint()` is not consumed by the row `18` gate.
- Resolved 2026-10-17: the bind gate reads `SecurityPosture.validated` only. The payload `ready` is
  derived in `make_health_response()` from `deps` plus `validated`, and `SecurityPosture.ready` is never
  read, so no second Ready rule exists.
- Resolved 2026-10-17: a server that exits before publishing a posture is classified as an unreachable
  server. Row `18`'s `classify_server_failure()` reports an unreachable or unparseable posture as
  `AVAILABILITY`, so the `SystemExit` path needs no posture reason code.
- Resolved 2026-10-17: no fixed marker string is added to the gate log line. The Agent classifies from
  the published posture and from probe availability, not from stderr text; the line exists for operators.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import the shared flow, contract, and row `07` validator | Completed | 2026-10-17 | 2026-10-17 | StartupStage import not needed because the flow takes server_checks as a callable |
| 2 | Add `_shell_security_view()` and `_build_security_posture()` | Completed | 2026-10-17 | 2026-10-17 | shell view carries sandbox_backend once instead of the duplicated pair the doc lists, plus counts and presence flags |
| 3 | Pass the posture to `make_health_response()` at `:126` | Completed | 2026-10-17 | 2026-10-17 | posture passed to make_health_response as a keyword argument |
| 4 | Add the `__main__` bind gate at `:202-204` | Completed | 2026-10-17 | 2026-10-17 | gate extracted into _enforce_posture_gate so a test can exercise it without starting uvicorn |
| 5 | Add `tests/mcp_servers/shell/test_shell_health_posture.py` | Completed | 2026-10-17 | 2026-10-17 | new test file with 11 tests, not a frozen-table row |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-17 | 2026-10-17 | ruff and mypy clean, tests/mcp_servers/shell green, full suite green except the 9 known baseline failures |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 5 | New test files are not rows in the Plan's frozen table; the Plan must be amended or the assertions added to an existing `tests/mcp_servers/shell/*` file | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (posture published on `/health`), `REQ-003` (shared startup ordering, validation failure blocks bind), `REQ-005` (Shell self-validation)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/shell/shell_service_static_helpers.py`, `scripts/mcp_servers/health_response.py`, `scripts/shared/security/startup_flow.py`, `scripts/shared/security/posture_contract.py`
