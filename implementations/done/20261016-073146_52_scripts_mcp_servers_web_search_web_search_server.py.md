## Goal

Wire Web Search self-validation into web-search-mcp's `/health` posture publication and its Ready
gate, so the server publishes a Security Posture and refuses to bind when its own validation fails
(`REQ-002`, `REQ-003`, `REQ-015`).

## Scope

- One modified module `scripts/mcp_servers/web_search/web_search_server.py`: build the posture once at
  import, pass it to `make_health_response()`, and gate the HTTP bind in the `__main__` block.
- The validator and the non-secret config view it consumes come from row `51`
  (`scripts/mcp_servers/web_search/web_search_models.py`).
- New test file `tests/mcp_servers/web_search/test_web_search_health_posture.py`. It is not a row of
  the Plan's frozen `Implementation Target Files` table; the Plan lists `web /health tests` as this
  row's test surface.

## Assumptions

- Current wiring verified: `_cfg: WebSearchConfig = WebSearchConfig.load()` at
  `scripts/mcp_servers/web_search/web_search_server.py:49`; `_web_search_tool_availability()` at
  `:52-58`; `app = FastAPI(` at `:63`; `attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token
  or "")` at `:67-70`; `/health` handler at `:103-117` with `make_health_response(deps, details)` at
  `:116`; `/v1/tools` at `:187-202`; `class WebSearchMCPServer(MCPServer)` at `:280` with
  `http_port = 8004` (`:285`), `own_config_file = "web_search_mcp_server.toml"` (`:286`),
  `app_module = "mcp_servers.web_search.web_search_server:app"` (`:287`), `mcp_tools = TOOL_LIST`
  (`:288`); `if __name__ == "__main__":` at `:295-297`.
- `TOOL_LIST` (`scripts/mcp_servers/web_search/web_search_tools.py:12`) declares `search_web` and
  `browser_fetch`; `/v1/tools` already annotates each with `enabled` and `disabled_reason` from
  `_web_search_tool_availability()` (`:191-199`) and reports the server key `"web_search"` (`:199`).
- `MCPServer.run_http()` (`scripts/mcp_servers/server.py:225-246`) enforces loopback-only bind and
  calls `ConfigLoader.restrict_to(self.own_config_file)` at `:238-240`; `WebSearchMCPServer` supplies
  `own_config_file`, so that enforcement already applies to this server.
- uvicorn 0.49.0 imports the app module before binding: `config.load()` at
  `.venv/lib/python3.14/site-packages/uvicorn/server.py:85-86` runs before `self.startup()` at `:94`.
  This row does not rely on that ordering; the `__main__` gate is the control.
- Production launches the Nuitka onefile binary `/opt/llm/bin/mcp_web_search`
  (`config/agent.toml:382`), which reaches this module through the `__main__` block. Verify the entry
  name against `deploy/build_binaries.sh` at implementation time.
- `tests/conftest.py:29` sets `MCP_WEB_SEARCH_AUTH_TOKEN=""`, so the shipped test posture carries
  `common.auth_token` as `WARNING` / `auth_token_missing` (Plan `UNK-06`, resolved 2026-10-16) and
  `validated` stays `true`.
- Existing assertions that must keep passing:
  `tests/mcp_servers/cicd/test_mcp_server_health_status.py:19-31` (200, `ready is True`,
  `dependencies == {}`, `restart_recommended is False`, `operator_action_required is False`),
  `tests/mcp_servers/web_search/test_web_search_health.py:113-115` (200, `dependencies == {}`),
  `:127-129` and `:208-213` (503 through the provider-degradation `deps` keys), `:257` and `:321-327`
  (auth matrix).

## Design decisions

- Compute the posture once at module import into a module-level `_security_posture` and never recompute
  it per request. This matches rows `42`-`49`: the posture describes the configuration the process
  started with, and a per-request recomputation would make `/health` depend on config I/O.
- Supply only the `SERVER_SECURITY_VALIDATION` stage (`validate_web_search_security()` from row `51`)
  to `run_startup_validation()` (row `04`); the flow's built-in `check_own_config_only()`,
  `check_auth_token_present()`, and `check_published_tools_declared()` cover the common and
  tool-capability stages. `CONFIG_LOAD` and `SCHEMA_VALIDATION` reuse the already-loaded `_cfg`; the
  flow is not given a callable that re-reads the config.
- This row defines the normalized non-secret view hashed by `compute_config_fingerprint()` (row `03`),
  because rows `07`-`16` and `51` define check ids but no fingerprint view. The view is
  `{"own_config_file": "web_search_mcp_server.toml", "default_max_results", "max_results_limit",
  "search_timeout_sec", "browser_max_response_kb", "browser_timeout_sec",
  "browser_allowlist_count", "auth_token_present"}`: scalars plus a list count and a presence boolean.
  No token value and no allowlist entry value appear, so the fingerprint cannot be inverted into a
  Secret or into the allowlist contents.
- Publish through `make_health_response(deps, details, security=_security_posture)` (row `06`) rather
  than adding a `security` key by hand, so `ready` is derived in one place from `deps` and
  `posture.validated`.
- Gate the bind in the `if __name__ == "__main__":` block (`:295-297`) with a `logger.error(...)` line
  and `raise SystemExit(1)` before `WebSearchMCPServer()` is constructed. No new `import sys` is
  needed: `SystemExit` is a builtin. `scripts/mcp_servers/server.py` is not edited.
- `deps` semantics stay exactly as today: `web_search_provider` and `browser_fetch_provider` remain
  runtime degradation signals from `health.is_degraded()` / `health.is_browser_degraded()`
  (`:111-114`). A posture failure is not written into `deps`; it reaches `ready` through the posture.
- The empty-allowlist case is not a bind failure for this server. Row `51` reports
  `server.browser_allowlist` as `NOT_APPLICABLE` when `browser_allowed_domains` is empty, which is the
  shipped deny-all configuration (`config/web_search_mcp_server.toml:15`) and the state that
  `_web_search_tool_availability()` (`:55-57`) already reports to the Agent through `/v1/tools`.

## Alternatives considered

- Probe `/health` from the Agent for this server instead of publishing a posture — rejected: `REQ-012`
  validates a published contract, and row `18`'s `allowed_server_keys()` consumes gates collected from
  the published postures, not from live probes.
- Add the posture into `details` (for example `details["security"]`) — rejected: row `06` defines the
  posture as a sibling top-level key, and `details` already carries provider health and metrics whose
  shape existing tests assert.
- Raise at import when the posture is invalid — rejected: an import-time exception would break every
  test that imports `app` (`tests/mcp_servers/cicd/test_mcp_server_health_status.py:21`,
  `tests/mcp_servers/web_search/test_web_search_health.py`) for a config problem that is only fatal to
  the bind, and row `04` specifies that a stage failure becomes a `FAILED` check, never an exception.
- Gate inside `WebSearchMCPServer.run_http()` — rejected: that is `scripts/mcp_servers/server.py`,
  shared by all ten `MCPServer` subclasses and not a Plan row.

## Implementation
### Target file

`scripts/mcp_servers/web_search/web_search_server.py` (modify)

### Procedure

1. Import `run_startup_validation` and `StartupStage` from `shared.security.startup_flow` (row `04`),
   `SecurityPosture` and `compute_config_fingerprint` from `shared.security.posture_contract`
   (row `03`), and `validate_web_search_security` from `mcp_servers.web_search.web_search_models`
   (row `51`).
2. Add `_web_search_security_view(cfg: WebSearchConfig) -> dict[str, object]` (new private function)
   returning the normalized view described above.
3. Add `_build_security_posture() -> SecurityPosture` (new private function) that calls
   `run_startup_validation()` with `server_key="web_search"`,
   `own_config_file="web_search_mcp_server.toml"`, the `SERVER_SECURITY_VALIDATION` stage callable
   (`validate_web_search_security(_cfg)`), and the fingerprint view.
4. Assign `_security_posture: SecurityPosture = _build_security_posture()` after `_cfg` (`:49`) and
   before `app = FastAPI(` (`:63`).
5. Change `:116` to `make_health_response(deps, details, security=_security_posture)`.
6. Add the gate to `:295-297`: log the failed check ids and reason codes, then `raise SystemExit(1)`
   before `WebSearchMCPServer()` is constructed.
7. Add `tests/mcp_servers/web_search/test_web_search_health_posture.py`.

### Method

- Order the statements so the posture exists before the auth middleware is attached (`:67-70`) and
  before any route can be hit. Unlike Shell (`scripts/mcp_servers/shell/shell_server.py:70-74`), this
  module has no import-time refusal for an empty token, so the posture is the first place an empty
  `auth_token` becomes visible — as a `WARNING`, not a failure.
- The gate log line is one line, format:
  `web-search-mcp: security posture FAILED (<check_id>:<reason_code>, ...) — refusing to bind`.
  Only check ids and reason codes appear; no token, no allowlist entry, and no provider name value
  appears (`REQ-002`, `REQ-004`).
- `_build_security_posture()` must not call `WebSearchConfig.load()` again; it reuses `_cfg`, so no
  second `from_dict()` pass and no duplicated `_validate_config_bounds()` raise.
- Keep `details` exactly as today (`service` at `:106`, `provider` at `:107`, `metrics` at `:108`,
  `browser_provider` at `:109`, `browser_metrics` at `:110`); the posture is a sibling key, not a
  `details` entry (row `06`).
- Type the posture as `SecurityPosture`, not `dict[str, object]`, so mypy catches a wrong
  `contract_version` or `server_key`.

### Details

- `server_key` is `"web_search"`, matching `[mcp_servers.web_search]` (`config/agent.toml:375`) and
  the key `/v1/tools` already reports through `build_tools_response(..., "web_search", ...)` (`:199`),
  so identity comparison in row `17` is string equality.
- `REQUIRED_CHECK_IDS["web_search"]` (row `03`) must list exactly row `51`'s five ids
  (`server.results_bounds`, `server.search_timeout_valid`, `server.browser_timeout_valid`,
  `server.browser_response_limit`, `server.browser_allowlist`) plus the flow's built-in common ids, or
  row `17` reports `check_set_mismatch`.
- `check_own_config_only()` compares the declared `own_config_file` with the expected own-config file
  for `"web_search"`. The process-level `ConfigLoader.restrict_to()` call happens later, inside
  `run_http()` (`scripts/mcp_servers/server.py:238-240`), so at import time the check verifies the
  declared file name only; `server.py` remains the enforcement point for cross-config reads. This is
  the same ordering every wiring row in `42`-`49` has.
- The provider health and metrics values already in `details` are non-secret: `health.health_details()`
  (`scripts/mcp_servers/web_search/health.py:99-101`) and `browser_health_details()` (`:132-134`)
  return `ProviderHealth.as_dict()` (`:64-72`), whose keys are the provider label, timestamps, a
  consecutive-failure count, and an error category from `_classify_upstream_error()`
  (`scripts/mcp_servers/web_search/web_search_service.py:103`). This row adds nothing to them and
  copies no posture message into them.
- The module is 297 lines; the addition is roughly 30 lines. The added statements stay in this file;
  do not split it as a side effect of this row. Row `51` already carries the sibling-module question
  for `web_search_models.py`, and that decision belongs to row `51`.

## Compatibility considerations

- Existing `/health` assertions keep passing: with the shipped config every web-search check is `OK`
  or `NOT_APPLICABLE` and `common.auth_token` is `WARNING`, so `validated` stays `true`, `ready` stays
  `true`, and `restart_recommended` / `operator_action_required` stay `False` (row `06`).
- The `security` key is additive (row `06`); no existing web-search test enumerates payload keys.
  `scripts/agent/services/mcp_health.py:59-67` reads only `restart_recommended`,
  `operator_action_required`, and the whole body, so it keeps working.
- `/v1/tools` and `/v1/call_tool` behavior is unchanged, including the `enabled` / `disabled_reason`
  annotation (`:191-199`) and the call-time availability check (`:222`).
- Behavior change is limited to startup and `/health`: a web-search config with
  `browser_timeout_sec <= 0`, `browser_max_response_kb <= 0`, or a value above a row `51` ceiling now
  exits non-zero before binding instead of starting and failing (or hanging) at the first
  `browser_fetch` call.
- No `docs/*.md` edit is in scope for this row; `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`
  and `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` are Plan
  follow-ups.

## Security considerations

- `REQ-003`: web-search-mcp validates its own configuration before Ready and does not bind HTTP when
  validation fails.
- `REQ-002` / Plan `INV-09`: the posture carries no token value and no allowlist entry value; the
  fingerprint is computed over counts and presence booleans.
- `REQ-004`: the gate log line and every posture message carry reason codes only.
- The deny-all default is preserved: this row never turns an empty `browser_allowed_domains` into an
  allow, and `_check_domain()` (`scripts/mcp_servers/web_search/search_provider.py:90-124`) stays the
  runtime authority for `browser_fetch`.
- The Agent-side `mcp_auth` FATAL check (`scripts/agent/startup_validation.py:70-81`) remains the
  production control for an empty `auth_token`; the server-side posture copy of that rule is a
  `WARNING` (Plan `UNK-06`, resolved 2026-10-16).

## Rollback considerations

- Revert this commit together with row `51`, which provides the imported validator and view. No config
  or data migration is involved. Reverting restores today's behavior: `/health` without a `security`
  key and an ungated bind.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Posture published | `uv run pytest tests/mcp_servers/web_search/test_web_search_health_posture.py` (new test file) | `/health` body contains a top-level `security` block with `contract_version`, `server_key == "web_search"`, `validated`, `fingerprint`, and the five row `51` check ids plus the built-in common ids |
| Shipped config stays ready | same new test file | shipped `web_search_mcp_server.toml` yields `validated=true`, `ready=true`, HTTP 200, and `dependencies == {}` |
| Failed check blocks ready | same new test file | a posture with `server.browser_timeout_valid` `FAILED` yields `ready=false`, `status="degraded"`, HTTP 503 |
| Bind gate | same new test file | with a patched invalid posture, running the `__main__` block raises `SystemExit` with code `1` and logs one line containing only check ids and reason codes |
| No secret in the gate log | same new test file | the captured log line contains no token value and no allowlist entry |
| Deps semantics unchanged | `uv run pytest tests/mcp_servers/web_search/test_web_search_health.py` | `:113-115`, `:127-129`, `:195-213`, `:257`, `:321-327` all pass unchanged |
| Cross-server health contract | `uv run pytest tests/mcp_servers/cicd/test_mcp_server_health_status.py` | passes unchanged |
| Existing web search suite | `uv run pytest tests/mcp_servers/web_search/` | passes |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-005` and `AC-002` for Web Search: `/health` carries the `security` block, and `ready=false`
  with HTTP 503 when the server's own validation fails.
- The process refuses to bind when `_security_posture.validated` is `false`.
- The shipped configuration keeps `validated=true`, and every existing web-search and cross-server
  `/health` test passes unchanged.
- No token value, allowlist entry, or provider secret appears in the posture, the `details` block, or
  the gate log line.

## Out of scope

- Editing `scripts/mcp_servers/server.py`, `scripts/mcp_servers/health_response.py` (row `06`),
  `web_search_models.py` (row `51`), `search_provider.py`, `web_search_service.py`, `health.py`,
  `metrics.py`, or `web_search_tools.py`.
- Changing `/v1/tools`, `/v1/call_tool`, the auth middleware call, or the provider degradation `deps`
  keys.
- Populating `browser_allowed_domains` in any config file, or changing `MCP_WEB_SEARCH_AUTH_TOKEN`.
- Agent-side posture validation, classification, and Tool Discovery gating (rows `17`-`19`, `50`).

## Confirmation outcomes

- Resolved 2026-10-17: row `04`'s built-in `check_published_tools_declared()` reports a declared tool the
  server marks disabled as `OK`. It checks only that the declared names are non-empty strings, so
  `browser_fetch` under the shipped empty allowlist keeps `common.published_tools` at `ok`, and the
  `enabled` and `disabled_reason` annotation on `/v1/tools` remains the place that gap is reported.
- Resolved 2026-10-17: `common.auth_token`'s `WARNING` is not surfaced in `details`. The published
  `checks` list already carries it, and the `details` shape is asserted by existing tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `_web_search_security_view()` and `_build_security_posture()` | Completed | 2026-10-17 | 2026-10-17 | no _web_search_security_view wrapper added, the posture consumes WebSearchConfig.non_secret_view from row 51 because row 51 owns the view definition |
| 2 | Pass the posture to `make_health_response()` at `:116` | Completed | 2026-10-17 | 2026-10-17 | posture passed to make_health_response |
| 3 | Add the `__main__` bind gate at `:295-297` | Completed | 2026-10-17 | 2026-10-17 | gate extracted into _enforce_posture_gate and called first in the main block |
| 4 | Add `tests/mcp_servers/web_search/test_web_search_health_posture.py` | Completed | 2026-10-17 | 2026-10-17 | new test file, not a frozen-table row |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-17 | 2026-10-17 | shipped posture is validated with common.auth_token warning and browser_allowlist not_applicable, 215 passed |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-015`
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/web_search/web_search_server.py`
