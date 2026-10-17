## Goal

Wire git-mcp's own security validation (row `08`) into the shared startup flow (row `04`), publish
the resulting Security Posture on `/health` (row `06`), and refuse HTTP bind when the posture is not
validated (`REQ-002`, `REQ-003`, `REQ-006`).

## Scope

- One modified module `scripts/mcp_servers/git/git_server.py`: build the posture, pass it to
  `make_health_response()`, and gate `run_http()` on it.
- This row adds no validation rule of its own: the validator is row `08`, the envelope is row `03`,
  the ordering is row `04`, the payload key is row `06`.
- One new test file `tests/mcp_servers/git/test_git_health_posture.py`.
- `scripts/mcp_servers/server.py` is a reference file only; it is not a row in the Plan's frozen
  table and is not modified here.

## Assumptions

- Verified current source: `_cfg = GitConfig.load()` at `:54`, `_service = build_service(_cfg)` at
  `:55`, `attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token or "")` at `:126`, the
  `/health` handler at `:296-310` (`deps` from `shutil.which("git")` inside a `try/except OSError`
  at `:299-304`, `details` with `service` and `audit_failure_count` at `:305-308`,
  `make_health_response(deps, details)` at `:309`), `class GitMCPServer` at `:318` with
  `http_port = 8014` at `:323` and `own_config_file = "git_mcp_server.toml"` at `:324`, and
  `if __name__ == "__main__": server = GitMCPServer(); server.run_http()` at `:329-331`.
- `GitService` (`scripts/mcp_servers/git/git_service.py:67-83`) does not inherit
  `GitSecurityGuards` (`git_security.py:63`); it holds its own `_allowed_repo_paths` and
  `_is_within_allowed_paths()`. So the wiring calls row `08`'s module-level
  `validate_git_security(allowed_repo_paths, read_only)`, not the instance-level
  `GitSecurityGuards.validate_security()`.
- Production starts this module as `__main__`: `config/agent.toml:373`
  `cmd = ["/opt/llm/bin/mcp_git"]`. Verify the entry name against `deploy/build_binaries.sh` at
  implementation time.
- uvicorn 0.49.0 imports the app module before binding (`config.load()` at
  `.venv/lib/python3.14/site-packages/uvicorn/server.py:85-86` before `self.startup()` at `:94`);
  this row does not rely on that ordering, the `__main__` gate is the control.
- `config/git_mcp_server.toml` ships `allowed_repo_paths = ["~/llmagent"]` (`:7`),
  `read_only = true`, and `allowed_remote_urls = []` (`:14`), so with row `08`'s check set the
  shipped configuration produces `validated=true`.
- **Blocker, Needs confirmation**: `tests/conftest.py:28` sets `MCP_GIT_AUTH_TOKEN=""`, and
  `attach_auth_middleware()` accepts every request when the token is empty
  (`scripts/mcp_servers/server.py:100-113`). The flow's built-in `check_auth_token_present()`
  (row `04`) mirrors the Agent-side FATAL rule at `scripts/agent/startup_validation.py:71-81`, so
  as written it reports `FAILED` in the test environment, which makes `validated=false`, turns
  `/health` into 503, and breaks `tests/mcp_servers/git/test_git_security_compliance.py:2342-2346`
  (asserts 200). Resolve before implementing step 4; see Needs confirmation.
- **Needs confirmation**: `SecurityPosture.ready` (row `03`) versus the payload `ready` computed in
  row `06`. This row reads only `SecurityPosture.validated` for the bind gate.

## Design decisions

- Compute the posture once at module import into a module-level `_security_posture`, immediately
  after `_service` (`:55`). The Agent polls `/health` repeatedly during readiness polling, and the
  bind gate needs the outcome before `run_http()`.
- Gate in the `if __name__ == "__main__":` block (`:329-331`): when `_security_posture.validated`
  is false, log the failed check ids with their reason codes and `raise SystemExit(1)` before
  constructing the server.
- Do not raise while building the posture. A policy violation becomes a `FAILED`
  `SecurityCheckResult`, so the failure is reportable on `/health` (row `08` states the same rule
  for its own entry points).
- Keep the existing `deps` semantics unchanged (`shutil.which("git")` and its `OSError` fallback at
  `:299-304`), and keep `details["audit_failure_count"]` (`:307`) exactly as today: it is the git
  server's own runtime audit counter, not the removed Agent audit, and
  `tests/mcp_servers/git/test_git_security_compliance.py:2346` asserts it.
- Supply only the `SERVER_SECURITY_VALIDATION` stage to `run_startup_validation()`; the flow's
  built-in `check_own_config_only()`, `check_auth_token_present()`, and
  `check_published_tools_declared()` cover the common and tool-capability stages. `CONFIG_LOAD` and
  `SCHEMA_VALIDATION` reuse the already-loaded `_cfg`.
- This row defines the normalized non-secret view hashed by `compute_config_fingerprint()` (row
  `03`), because rows `07`-`16` define check ids but no fingerprint view:
  `{"own_config_file": "git_mcp_server.toml", "allowed_repo_paths_count", "read_only",
  "protected_branches_count", "allowed_remote_urls_count", "allow_detached_head",
  "max_log_entries"}` — scalars and counts only.
- Empty `allowed_remote_urls` is not a posture check (row `08` defines no such id), so the shipped
  empty remote allowlist does not block Ready; `server.read_only_mode` is `NOT_APPLICABLE` while
  `read_only=true`.

## Alternatives considered

- Put the gate inside `MCPServer.run_http()` — rejected: `scripts/mcp_servers/server.py` is not a
  row in the Plan's frozen table, and a base-class gate would apply to servers whose validators
  have not landed yet.
- Validate through `GitSecurityGuards.validate_security()` on a guards instance — rejected: no
  guards instance exists in this module (`GitService` does not inherit the mixin), and building one
  would require a `RepositoryState` object that does not exist at import time.
- Compute the posture lazily on the first `/health` probe — rejected: the gate must decide before
  bind.
- Raise at import time when validation fails — rejected: it breaks every test that imports the
  module and produces no posture for the Agent to classify.
- Let the server bind and rely on `ready=false` + 503 — rejected: Plan `REQ-003` / `AC-003` state
  that a server which fails validation does not bind HTTP.

## Implementation
### Target file

`scripts/mcp_servers/git/git_server.py` (modify)

### Procedure

1. Import `run_startup_validation` and `StartupStage` from `shared.security.startup_flow` (row `04`),
   `SecurityPosture` and `compute_config_fingerprint` from `shared.security.posture_contract`
   (row `03`), and `validate_git_security` from `mcp_servers.git.git_security` (row `08`).
2. Add `_git_security_view(cfg: GitConfig) -> dict[str, object]` (new private function) returning
   the normalized view described above.
3. Add `_build_security_posture() -> SecurityPosture` (new private function) that calls
   `run_startup_validation()` with `server_key="git"`,
   `own_config_file="git_mcp_server.toml"`, the `SERVER_SECURITY_VALIDATION` stage callable
   (`validate_git_security(list(_cfg.allowed_repo_paths), _cfg.read_only)`), and the fingerprint
   view.
4. Assign `_security_posture: SecurityPosture = _build_security_posture()` after `_service` (`:55`).
5. Change `:309` to `make_health_response(deps, details, security=_security_posture)`.
6. Add the gate to `:329-331`: log the failed check ids and reason codes, then
   `raise SystemExit(1)` before `GitMCPServer()` is constructed.
7. Add `tests/mcp_servers/git/test_git_health_posture.py`.

### Method

- Build the posture after `_cfg` and `_service` exist and before the class and `__main__` block, so
  the `/health` handler at `:296` can close over `_security_posture`.
- The gate log line is one line, format:
  `git-mcp: security posture FAILED (<check_id>:<reason_code>, ...) — refusing to bind`. Only
  check ids and reason codes appear; configured repository roots are sensitive paths (`REQ-002`).
- `_build_security_posture()` must not call `GitConfig.load()` again; it reuses `_cfg`.
- Keep `details` unchanged; the posture is a sibling top-level key, not a `details` entry (row `06`).
- Type the posture as `SecurityPosture`, not `dict[str, object]`.

### Details

- `server_key` is `"git"`, matching `[mcp_servers.git]` (`scripts/agent/startup_validation.py:71-73`).
- `REQUIRED_CHECK_IDS["git"]` (row `03`) must list exactly row `08`'s ids
  (`server.repo_allowlist`, `server.repo_allowlist_resolvable`, `server.read_only_mode`,
  `server.protected_branch_config`) plus the flow's built-in common ids, or row `17` reports
  `check_set_mismatch`.
- `server.protected_branch_config` must be evaluated from config values in the pure-function
  variant. Row `08` documents `FAILED` with reason `dependency_unreachable` for the *instance*
  variant when no repository state is wired; if the pure variant inherited that outcome, git-mcp's
  posture would be `FAILED` in every environment with no repository state at import, which no
  existing test can satisfy. Recorded in Needs confirmation.
- The module is about 331 lines, already above the 200-line convention. The roughly 30 added lines
  stay in this file; do not split it as a side effect of this row. A split would be a separate Plan
  row.

## Compatibility considerations

- Existing `/health` assertions keep passing once the auth-token question is resolved: with the
  shipped config all four Git checks are `OK` or `NOT_APPLICABLE`, so `validated` stays `true` and
  `ready` stays `true` (`tests/mcp_servers/git/test_git_security_compliance.py:2342-2346`).
- The `security` key is additive (row `06`); no existing git test enumerates payload keys.
- `tests/mcp_servers/git/test_tools_endpoint.py` already sends `MCP_TEST_AUTH_HEADERS`
  (`tests/mcp_servers/_auth_headers.py`), so it is unaffected by the posture change.
- Behavior change is limited to startup and `/health`: a git config with an empty
  `allowed_repo_paths` now exits non-zero before binding instead of starting and denying every call
  with `[DENIED] allowed_repo_paths is empty` (`git_security.py:45`), which stays unchanged.
- No `docs/*.md` edit is in scope for this row; `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`
  and `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` are Plan
  follow-ups.

## Security considerations

- `REQ-006` / Plan `INV-05`: git-mcp validates its own configuration before Ready, and the Agent
  never reads `git_mcp_server.toml` (`REQ-017` removes the audit loader that did).
- `REQ-002` / Plan `INV-09`: the fingerprint view excludes `auth_token`, `audit_log_path`, and every
  `allowed_repo_paths` / `allowed_remote_urls` value; only counts and scalars are hashed.
- `REQ-011`: the Agent-side empty-`auth_token` rejection stays at
  `scripts/agent/startup_validation.py:71-81` (`mcp_auth`, not removed by row `22`). Git currently
  has no server-side equivalent: `attach_auth_middleware(..., _cfg.auth_token or "")` (`:126`)
  installs the accept-all fallback. Whether the posture check becomes that equivalent is the
  Needs-confirmation decision recorded below; it must not be left enforced by neither side.
- `REQ-004`: the gate log line and every posture message carry reason codes only.

## Rollback considerations

- Revert this commit together with rows `06` (payload parameter), `08` (validator), and `04` (flow).
  No config or data migration is involved.
- The gate is the only statement that can make a previously-startable git config unstartable;
  reverting the `__main__` block restores today's behavior without touching `/health`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Posture published | `uv run pytest tests/mcp_servers/git/test_git_health_posture.py` (new test file) | `/health` body carries the `security` key with `server_key == "git"` and `contract_version == SECURITY_CONTRACT_VERSION` |
| Validated shipped config | same new test file | `_security_posture.validated is True` against `config/git_mcp_server.toml` |
| Empty allowlist blocks bind | same new test file | with `allowed_repo_paths` patched empty, `validated is False`, `/health` returns 503 with `ready is False`, and the `__main__` gate raises `SystemExit` |
| Existing git suite | `uv run pytest tests/mcp_servers/git/` | passes, including `test_git_security_compliance.py:2342-2346` |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-002`: git-mcp publishes the posture on `/health` with no Secret, allowlist element,
  repository path, or config body in it.
- Plan `AC-003`: git-mcp runs the shared ordering and does not bind HTTP when validation fails.
- Plan `AC-005` for Git: the rules live in `git_security.py` (row `08`); this file contains wiring
  only.

## Out of scope

- Adding or changing Git check ids (row `08`).
- Changing `make_health_response()` or the payload shape (row `06`).
- Agent-side posture validation, classification, and Tool Discovery gating (rows `17`-`19`).
- Changing `attach_auth_middleware()` or the accept-all fallback in `scripts/mcp_servers/server.py`.
- Splitting `git_server.py` into smaller modules.

## Confirmation outcomes

- Resolved 2026-10-16 (Plan `UNK-06`): an empty `auth_token` for git-mcp is reported by row `04`'s
  `check_auth_token_present()` as `WARNING` with reason `auth_token_missing` and `validated` stays
  `true`, so `tests/conftest.py:28` (`MCP_GIT_AUTH_TOKEN=""`) keeps
  `tests/mcp_servers/git/test_git_security_compliance.py:2342-2346` passing and the Agent's `mcp_auth`
  FATAL check at
  `scripts/agent/startup_validation.py:71-81` remains the production control. Option B (keep `FAILED`
  and amend the Plan for `tests/conftest.py` plus the git HTTP tests) was not chosen, and option C
  (exempt `/health` from the auth middleware) stays rejected because it edits `scripts/mcp_servers/server.py`.
- Resolved 2026-10-17 (row `08` decision): the pure-function variant used by this row reports `OK` for a
  configured protected-branch setting, and only the instance variant reports `FAILED` when it is `None`,
  so `dependency_unreachable` is not produced here.
- Resolved 2026-10-17: the Git fingerprint view defined in `Design decisions` is retained as written. It
  carries scalars, counts, and presence flags, so a changed allowlist entry with an unchanged count is
  not detectable through the digest; row `05` compares check ids and statuses, and row `17`'s
  `compare_fingerprint()` is not consumed by the row `18` gate.
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
| 1 | Import the shared flow, contract, and row `08` validator | Completed | 2026-10-17 | 2026-10-17 | StartupStage import not needed |
| 2 | Add `_git_security_view()` and `_build_security_posture()` | Completed | 2026-10-17 | 2026-10-17 | view carries repo allowlist count, read_only, and protected branch presence |
| 3 | Pass the posture to `make_health_response()` at `:309` | Completed | 2026-10-17 | 2026-10-17 | posture passed to make_health_response |
| 4 | Add the `__main__` bind gate at `:329-331` | Completed | 2026-10-17 | 2026-10-17 | gate extracted into _enforce_posture_gate, shipped test posture keeps common.auth_token as a warning so validated stays true |
| 5 | Add `tests/mcp_servers/git/test_git_health_posture.py` | Completed | 2026-10-17 | 2026-10-17 | new test file, not a frozen-table row |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-17 | 2026-10-17 | ruff and mypy clean, shell and git suites green |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | `tests/conftest.py:28` sets `MCP_GIT_AUTH_TOKEN=""`; a `FAILED` `common.auth_token` check would flip existing git `/health` tests from 200 to 503 | No | — |
| 5 | New test files are not rows in the Plan's frozen table; the Plan must be amended or the assertions added to an existing `tests/mcp_servers/git/*` file | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (posture published on `/health`), `REQ-003` (shared startup ordering, validation failure blocks bind), `REQ-006` (Git self-validation)
- **Source issue**: `issues/done/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/git/git_server.py`, `scripts/mcp_servers/git/git_security.py`, `scripts/mcp_servers/health_response.py`, `scripts/shared/security/startup_flow.py`, `scripts/shared/security/posture_contract.py`
