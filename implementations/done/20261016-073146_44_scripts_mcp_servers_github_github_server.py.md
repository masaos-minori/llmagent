## Goal

Wire github-mcp's own security validation (row `09`) into the shared startup flow (row `04`),
publish the resulting Security Posture on `/health` (row `06`), and refuse HTTP bind when the
posture is not validated (`REQ-002`, `REQ-003`, `REQ-007`).

## Scope

- One modified module `scripts/mcp_servers/github/github_server.py`: build the posture, pass it to
  `make_health_response()`, and gate `run_http()` on it.
- This row adds no validation rule of its own: the validator is row `09`, the envelope is row `03`,
  the ordering is row `04`, the payload key is row `06`.
- One new test file `tests/mcp_servers/github/test_github_health_posture.py`.
- `scripts/mcp_servers/server.py` is a reference file only; it is not a row in the Plan's frozen
  table and is not modified here.

## Assumptions

- Verified current source: `_GITHUB_TOKEN` imported from `mcp_servers.github.github_service_init`
  at `:53` (the GitHub API token, assigned at `github_service_init.py:20`),
  `_cfg = GitHubConfig.load()  # noqa: F821` at `:69`, `_service: GitHubService = build_service(_cfg)`
  at `:70`, `_github_tool_availability()` at `:72-80`, `app = FastAPI(` at `:84`, the empty-token
  `RuntimeError` at `:90-94`, `attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token)` at
  `:95`, `_include_routers()` at `:118`, the `/health` handler at `:126-134` (`deps["github_token"]`
  from `if not _GITHUB_TOKEN` at `:129-131`, `details` at `:132`,
  `make_health_response(deps, details)` at `:133`), `class GithubMCPServer` at `:206` with
  `http_port = 8006` at `:211` and `own_config_file = "github_mcp_server.toml"` at `:212`, and
  `if __name__ == "__main__": server = GithubMCPServer(); server.run_http()` at `:221-223`.
- Two different tokens exist in this module and only one of them is a server auth token:
  `_GITHUB_TOKEN` is the GitHub API token the tools use (`:53`, and the `/health` dependency signal
  at `:129-131`), while `_cfg.auth_token` is the Bearer token the middleware checks (`:95`). The
  posture's `common.auth_token` check reads `_cfg.auth_token`; `_GITHUB_TOKEN` never enters the
  posture.
- Production starts this module as `__main__`: `config/agent.toml:426`
  `cmd = ["/opt/llm/bin/mcp_github"]`. Verify the entry name against `deploy/build_binaries.sh` at
  implementation time.
- uvicorn 0.49.0 imports the app module before binding (`config.load()` at
  `.venv/lib/python3.14/site-packages/uvicorn/server.py:85-86` before `self.startup()` at `:94`);
  this row does not rely on that ordering, the `__main__` gate is the control.
- `MCP_GITHUB_AUTH_TOKEN` is set to `"test-token"` by `tests/conftest.py:33-41`, and this module
  already refuses to import with an empty `auth_token` (`:90-94`), so the flow's built-in
  `common.auth_token` check cannot be the failing check in the test suite.
- `config/github_mcp_server.toml` ships `allowed_repos = ["masaos-minori/llmagent"]` (`:16`),
  `protected_branches = ["main", "release/*"]` (`:19`), `allow_force_push = false` (`:22`),
  `require_pr_review = true` (`:25`), and `path_denylist = []` (`:28`), so with row `09`'s check set
  the shipped configuration produces `validated=true` with two `NOT_APPLICABLE` checks.
- **Needs confirmation**: `SecurityPosture.ready` (row `03`) versus the payload `ready` computed in
  row `06`. This row reads only `SecurityPosture.validated` for the bind gate.

## Design decisions

- Compute the posture once at module import into a module-level `_security_posture`, immediately
  after `_service` (`:70`). The Agent polls `/health` repeatedly during readiness polling, and the
  bind gate needs the outcome before `run_http()`.
- Gate in the `if __name__ == "__main__":` block (`:221-223`): when `_security_posture.validated`
  is false, log the failed check ids with their reason codes and `raise SystemExit(1)` before
  constructing the server.
- Do not raise while building the posture. Row `09`'s entry point already returns results instead
  of raising, and a posture failure must stay reportable on `/health`.
- Keep the existing `deps` semantics unchanged (`if not _GITHUB_TOKEN` at `:129-131`). The GitHub
  API token is an availability signal in `dependencies`, not a security-validation result; the
  posture carries only row `09`'s checks plus the flow's built-in common checks.
- Supply only the `SERVER_SECURITY_VALIDATION` stage (`validate_github_security(_cfg)` from row `09`)
  to `run_startup_validation()`; the flow's built-in `check_own_config_only()`,
  `check_auth_token_present()`, and `check_published_tools_declared()` cover the common and
  tool-capability stages. `CONFIG_LOAD` and `SCHEMA_VALIDATION` reuse the already-loaded `_cfg`.
- This row defines the normalized non-secret view hashed by `compute_config_fingerprint()` (row
  `03`), because rows `07`-`16` define check ids but no fingerprint view:
  `{"own_config_file": "github_mcp_server.toml", "allowed_repos_count",
  "protected_branches_count", "path_denylist_count", "allow_force_push", "require_pr_review",
  "max_file_size_kb", "default_per_page", "max_per_page", "llm_url_configured"}` — scalars and
  counts only.
- `WARNING`-level policy settings stay startable: `allow_force_push=true` and
  `require_pr_review=false` produce `WARNING` checks (row `09`), `validated` stays `true`, and the
  gate does not fire. This preserves the old audit's warning-only behavior (Plan `Assumptions`).

## Alternatives considered

- Put the gate inside `MCPServer.run_http()` — rejected: `scripts/mcp_servers/server.py` is not a
  row in the Plan's frozen table, and a base-class gate would apply to servers whose validators
  have not landed yet.
- Fold the posture into the existing `details` dict — rejected: row `06` fixes the payload shape,
  and `details` is free-form per-server space that row `17` cannot validate as a schema.
- Compute the posture lazily on the first `/health` probe — rejected: the gate must decide before
  bind.
- Raise at import time when validation fails — rejected: it breaks every test that imports the
  module and produces no posture for the Agent to classify. The existing empty-token `RuntimeError`
  at `:90-94` is a different, already-established rule and stays where it is.
- Report `_GITHUB_TOKEN` absence as a posture check — rejected: it is already the `dependencies`
  entry the `/health` contract defines, and duplicating it would give the Agent two sources for one
  condition while risking a Secret-derived value entering the posture.

## Implementation
### Target file

`scripts/mcp_servers/github/github_server.py` (modify)

### Procedure

1. Import `run_startup_validation` and `StartupStage` from `shared.security.startup_flow` (row `04`),
   `SecurityPosture` and `compute_config_fingerprint` from `shared.security.posture_contract`
   (row `03`), and `validate_github_security` from `mcp_servers.github.github_service_security`
   (row `09`).
2. Add `_github_security_view(cfg: GitHubConfig) -> dict[str, object]` (new private function)
   returning the normalized view described above.
3. Add `_build_security_posture() -> SecurityPosture` (new private function) that calls
   `run_startup_validation()` with `server_key="github"`,
   `own_config_file="github_mcp_server.toml"`, the `SERVER_SECURITY_VALIDATION` stage callable
   (`validate_github_security(_cfg)`), and the fingerprint view.
4. Assign `_security_posture: SecurityPosture = _build_security_posture()` after `_service` (`:70`).
5. Change `:133` to `make_health_response(deps, details, security=_security_posture)`.
6. Add the gate to `:221-223`: log the failed check ids and reason codes, then
   `raise SystemExit(1)` before `GithubMCPServer()` is constructed.
7. Add `tests/mcp_servers/github/test_github_health_posture.py`.

### Method

- Build the posture after `_cfg` and `_service` exist and before `app = FastAPI(` (`:84`), so the
  posture exists before the middleware and routers are attached and before any route can be hit.
- The gate log line is one line, format:
  `github-mcp: security posture FAILED (<check_id>:<reason_code>, ...) — refusing to bind`. Only
  check ids and reason codes appear; repository names are allowlist entries (`REQ-002`).
- `_build_security_posture()` must not call `GitHubConfig.load()` again; it reuses `_cfg`.
- Keep `details` exactly as today (`{"service": "github-mcp"}` at `:132`); the posture is a sibling
  top-level key (row `06`).
- Type the posture as `SecurityPosture`, not `dict[str, object]`.

### Details

- `server_key` is `"github"`, matching `[mcp_servers.github]`
  (`scripts/agent/startup_validation.py:71-73`).
- `REQUIRED_CHECK_IDS["github"]` (row `03`) must list exactly row `09`'s ids
  (`server.repo_allowlist`, `server.force_push_policy`, `server.pr_review_required`,
  `server.protected_branches`, `server.path_denylist`) plus the flow's built-in common ids, or row
  `17` reports `check_set_mismatch`.
- `_github_tool_availability()` (`:72-80`) and the flow's built-in `check_published_tools_declared()`
  are different checks: the first is per-call availability against `_GITHUB_TOKEN`, the second
  asserts that every name in the server's declared tool list is registered. This row does not
  change the first.
- The module is about 223 lines. The roughly 30 added lines stay in this file; do not split it as a
  side effect of this row. Row `09` already carries a Needs-confirmation about a sibling module for
  `github_service_security.py`; that decision belongs to row `09`, not here.

## Compatibility considerations

- Existing `/health` assertions keep passing: with the shipped config every GitHub check is `OK` or
  `NOT_APPLICABLE`, so `validated` stays `true` and `ready` stays `true`
  (`tests/mcp_servers/github/test_github_server_endpoints.py:159-174` asserts the degraded-by-token
  path and the healthy path, and `tests/mcp_servers/github/test_github_server_auth.py` asserts the
  401 path).
- The `security` key is additive (row `06`); no existing github test enumerates payload keys.
- Tests that monkeypatch `github_server._GITHUB_TOKEN` (`test_github_server_endpoints.py:52,174`)
  keep working: the posture is built from `_cfg`, not from `_GITHUB_TOKEN`, so patching the API
  token does not change `validated`.
- Behavior change is limited to startup and `/health`: a github config with an empty `allowed_repos`
  now exits non-zero before binding instead of starting with every repository denied.
- No `docs/*.md` edit is in scope for this row; `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md:226`
  and `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` are Plan follow-ups.

## Security considerations

- `REQ-007` / Plan `INV-05`: github-mcp validates its own policy before Ready, and the Agent stops
  reading `github_mcp_server.toml` (`REQ-017`).
- `REQ-002` / Plan `INV-09`: the fingerprint view excludes `auth_token`, `_GITHUB_TOKEN`,
  `audit_log_path`, and every `allowed_repos` / `protected_branches` / `path_denylist` value; only
  counts and scalars are hashed.
- `REQ-011`: the Agent-side empty-`auth_token` rejection stays at
  `scripts/agent/startup_validation.py:71-81` (`mcp_auth`, not removed by row `22`); github-mcp
  already refuses to import with an empty token (`:90-94`), and the flow's built-in
  `check_auth_token_present()` adds the posture-level copy.
- `REQ-004`: the gate log line and every posture message carry reason codes only.

## Rollback considerations

- Revert this commit together with rows `06` (payload parameter), `09` (validator), and `04` (flow).
  No config or data migration is involved.
- The gate is the only statement that can make a previously-startable github config unstartable;
  reverting the `__main__` block restores today's behavior without touching `/health`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Posture published | `uv run pytest tests/mcp_servers/github/test_github_health_posture.py` (new test file) | `/health` body carries the `security` key with `server_key == "github"` and `contract_version == SECURITY_CONTRACT_VERSION` |
| Validated shipped config | same new test file | `_security_posture.validated is True` against `config/github_mcp_server.toml`, with `server.protected_branches` and `server.path_denylist` present |
| Force-push warning stays startable | same new test file | `allow_force_push=True` yields status `WARNING`, `validated is True`, `/health` returns 200, and the gate does not fire |
| Empty allowlist blocks bind | same new test file | with `allowed_repos` patched empty, `validated is False`, `/health` returns 503 with `ready is False`, and the `__main__` gate raises `SystemExit` |
| Existing github suite | `uv run pytest tests/mcp_servers/github/` | passes |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-002`: github-mcp publishes the posture on `/health` with no Secret, allowlist element, or
  config body in it.
- Plan `AC-003`: github-mcp runs the shared ordering and does not bind HTTP when validation fails.
- Plan `AC-005` for GitHub: the rules live in `github_service_security.py` (row `09`); this file
  contains wiring only.

## Out of scope

- Adding or changing GitHub check ids (row `09`).
- Changing `make_health_response()` or the payload shape (row `06`).
- Agent-side posture validation, classification, and Tool Discovery gating (rows `17`-`19`).
- Changing `_github_tool_availability()`, the included domain routers, or the audit logging path.
- Splitting `github_server.py` into smaller modules.

## Confirmation outcomes

- Resolved 2026-10-17: the GitHub fingerprint view defined in `Design decisions` is retained as written.
  It carries scalars, counts, and presence flags, so a changed allowlist entry with an unchanged count is
  not detectable through the digest; row `05` compares check ids and statuses, and row `17`'s
  `compare_fingerprint()` is not consumed by the row `18` gate.
- Resolved 2026-10-17: the bind gate reads `SecurityPosture.validated` only. The payload `ready` is
  derived in `make_health_response()` from `deps` plus `validated`, and `SecurityPosture.ready` is never
  read, so no second Ready rule exists.
- Resolved 2026-10-17: a server that exits before publishing a posture is classified as an unreachable
  server. Row `18`'s `classify_server_failure()` reports an unreachable or unparseable posture as
  `AVAILABILITY`, so the `SystemExit` path needs no posture reason code.
- Resolved 2026-10-17 (row `23` decision): audit-only warnings stay non-fatal with `validated` true, and
  no posture line is added to the Agent's Readiness Summary. A warning reaches an operator through this
  server's published `checks` list only.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import the shared flow, contract, and row `09` validator | Completed | 2026-10-17 | 2026-10-17 | validator imported from the row 09 sibling module github_service_security |
| 2 | Add `_github_security_view()` and `_build_security_posture()` | Completed | 2026-10-17 | 2026-10-17 | view carries counts and presence flags, an empty path_denylist is published as not_applicable |
| 3 | Pass the posture to `make_health_response()` at `:133` | Completed | 2026-10-17 | 2026-10-17 | posture passed to make_health_response |
| 4 | Add the `__main__` bind gate at `:221-223` | Completed | 2026-10-17 | 2026-10-17 | gate extracted into _enforce_posture_gate |
| 5 | Add `tests/mcp_servers/github/test_github_health_posture.py` | Completed | 2026-10-17 | 2026-10-17 | new test file, tests patch the module global _GITHUB_TOKEN so no token value can leak |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-17 | 2026-10-17 | ruff and mypy clean, 302 passed in tests/mcp_servers/github |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 5 | New test files are not rows in the Plan's frozen table; the Plan must be amended or the assertions added to an existing `tests/mcp_servers/github/*` file | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (posture published on `/health`), `REQ-003` (shared startup ordering, validation failure blocks bind), `REQ-007` (GitHub self-validation)
- **Source issue**: `issues/done/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/github/github_server.py`, `scripts/mcp_servers/github/github_service_security.py`, `scripts/mcp_servers/health_response.py`, `scripts/shared/security/startup_flow.py`, `scripts/shared/security/posture_contract.py`
