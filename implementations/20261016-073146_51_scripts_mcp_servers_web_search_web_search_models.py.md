## Goal

Expose the Web Search server's configuration inputs for self-validation and add the validation
results, so web-search-mcp validates its own configuration and publishes the common Security Posture
instead of relying on the Agent's audit (`REQ-015`, `AC-005`).

## Scope

- One modified module `scripts/mcp_servers/web_search/web_search_models.py`: add a non-secret config
  view used for fingerprinting, and a Web Search self-validation function that produces
  `SecurityCheckResult` values.
- Publishing on `/health` and the Ready gate are row `52`
  (`scripts/mcp_servers/web_search/web_search_server.py:103-117`).

## Assumptions

- `REQ-015` and this row exist because of the user decision recorded 2026-10-16 in Plan `UNK-04`:
  `web_search` is an HTTP MCP server registered at `config/agent.toml:375-383`, so `REQ-012` posture
  validation and the `REQ-014` Tool Discovery gate apply to it, and it therefore needs a
  self-validation row.
- Current config model verified: `WebSearchConfig` at
  `scripts/mcp_servers/web_search/web_search_models.py:96` with `default_max_results` (`:99`),
  `max_results_limit` (`:100`), `search_timeout_sec` (`:101`), `browser_allowed_domains` (`:102`),
  `browser_max_response_kb` (`:103`), `browser_timeout_sec` (`:104`), and the Secret field
  `auth_token` (`:105`). `BrowserConfig` (`:162-176`) projects the three `browser_*` fields.
- `_validate_config_bounds()` (`:66-92`) already raises `ValueError` for `default_max_results`,
  `max_results_limit`, and `search_timeout_sec`, including the module ceilings
  `HARD_MAX_RESULTS_LIMIT = 100` (`:61`) and `HARD_SEARCH_TIMEOUT_SEC_LIMIT = 60.0` (`:63`). It
  validates neither `browser_max_response_kb` nor `browser_timeout_sec`, so
  `browser_timeout_sec = 0` or a negative value loads today even though the inline comment at `:137`
  notes "0 would cause instant timeout". This is the gap this row closes as a posture check.
- `from_dict()` (`:108`) fails closed on the removed `browser_auth_token` key (`:116-121`); this row
  does not change that.
- `load()` (`:157-159`) calls `ConfigLoader().load("web_search_mcp_server.toml")`. The process-level
  own-config restriction is applied later by `MCPServer.run_http()` at
  `scripts/mcp_servers/server.py:238-240`.
- Shipped config: `config/web_search_mcp_server.toml:15` `browser_allowed_domains = []` (deny-all)
  and `:27` `auth_token = "${ENV:MCP_WEB_SEARCH_AUTH_TOKEN}"`; `tests/conftest.py:29` sets
  `MCP_WEB_SEARCH_AUTH_TOKEN=""`.
- An empty `browser_allowed_domains` already disables `browser_fetch` through
  `_web_search_tool_availability()` at `scripts/mcp_servers/web_search/web_search_server.py:55-57`,
  and `_check_domain()` at `scripts/mcp_servers/web_search/search_provider.py:90-124` denies every
  hostname against an empty allowlist.
- `tests/mcp_servers/cicd/test_mcp_server_health_status.py:19-31` asserts web-search-mcp `/health`
  returns 200 with `ready is True` and `dependencies == {}` under the shipped config, so the posture
  for that config must be `validated=true`.
- Plan `UNK-01` / `UNK-03`: the per-server check granularity for Web Search is derived here because
  `memo2.md` is unrecoverable. **Needs confirmation**.

## Design decisions

- Add `WebSearchConfig.non_secret_view(self) -> dict[str, object]` (new method) that returns the
  config fields safe to hash and log, excluding `auth_token` (`:105`). This is the "expose config
  inputs" half of `REQ-015`: row `03` computes the posture fingerprint over a normalized non-secret
  view, and without a server-owned view the Agent would have to read
  `web_search_mcp_server.toml` itself, which `REQ-017` removes.
- Add `validate_web_search_security(cfg: WebSearchConfig) -> list[SecurityCheckResult]` (new
  module-level function).
- Check ids (finalized here, Needs confirmation):
  - `server.results_bounds` — mirrors the `default_max_results` / `max_results_limit` rules already
    enforced by `_validate_config_bounds()` (`:74-86`): a violation is `FAILED` with reason
    `config_invalid`, otherwise `OK`. It is unreachable through `load()` but must still appear in the
    posture, because `SearchRequest` publishes those same bounds in its inputSchema
    (`:215-216`) and `get_max_results_limit()` (`:192-199`) exposes `max_results_limit` to
    `web_search_tools.py`; the posture has to state what the server enforces.
  - `server.search_timeout_valid` — mirrors the `search_timeout_sec` rule at `:87-92`: outside
    `(0, HARD_SEARCH_TIMEOUT_SEC_LIMIT]` is `FAILED` with reason `config_invalid`, otherwise `OK`.
  - `server.browser_timeout_valid` — `browser_timeout_sec <= 0` is `FAILED` with reason
    `config_invalid`: an outbound fetch with a zero or negative timeout either fails instantly or
    hangs with no bound. `> HARD_BROWSER_TIMEOUT_SEC_LIMIT` (new module constant, proposed `120`) is
    `FAILED` with reason `config_invalid`, mirroring `HARD_SEARCH_TIMEOUT_SEC_LIMIT` (`:63`).
  - `server.browser_response_limit` — `browser_max_response_kb <= 0` is `FAILED` with reason
    `config_invalid` (the extracted-text cap would truncate every response to nothing);
    `> HARD_BROWSER_MAX_RESPONSE_KB` (new module constant, proposed `4096`) is `FAILED` with reason
    `config_invalid`, because the cap is what keeps page text inside the tool-response size budget.
  - `server.browser_allowlist` — empty `browser_allowed_domains` is `NOT_APPLICABLE` with reason
    `not_applicable`, never `FAILED`; a non-empty list containing an entry that is not a lowercase
    hostname shape (contains a scheme, `/`, `:`, whitespace, or an uppercase character) is `WARNING`
    with reason `allowlist_invalid`; otherwise `OK`.
- `server.browser_allowlist` is the one web-search check that is not `FAILED` when the allowlist is
  empty, and this is the row's central decision. For Shell and the File servers an empty allowlist
  widens nothing and means the guard is absent, so `REQ-005` / `REQ-009` report `FAILED`. For
  web-search-mcp an empty `browser_allowed_domains` removes a capability:
  `_web_search_tool_availability()` (`web_search_server.py:55-57`) reports `browser_fetch` as
  disabled, and `_check_domain()` (`search_provider.py:121-123`) denies every hostname. Reporting
  `FAILED` would make the shipped deny-all configuration (`config/web_search_mcp_server.toml:15`)
  refuse to bind and would break
  `tests/mcp_servers/cicd/test_mcp_server_health_status.py:19-31`. `NOT_APPLICABLE` keeps the check
  present in the check set for every configuration, as row `03` requires.
- A malformed allowlist entry is `WARNING`, not `FAILED`, because the runtime is already fail-closed:
  `_check_domain()` lowercases the URL hostname (`search_provider.py:101`) and compares it verbatim
  to the allowlist set (`:121`), so a bad entry matches nothing and denies everything. The `WARNING`
  exists to tell the operator that the intended allow is not in effect.
- `_validate_config_bounds()` is not extended. Adding the browser bounds there would change
  config-load behavior and every existing `WebSearchConfig.from_dict()` test; enforcing them in the
  posture keeps this row additive and routes the failure through the row `52` bind gate, which is the
  `REQ-003` fail-closed path.
- No check inspects or reports a token value or an allowlist value. Token presence is enforced by the
  server's auth middleware (`web_search_server.py:67-70`), by the flow's built-in
  `check_auth_token_present()` (row `04`, `WARNING` / `auth_token_missing` per Plan `UNK-06`), and by
  the Agent's `mcp_auth` check (`scripts/agent/startup_validation.py:70-81`).
- The function is pure: it reads only the fields of the passed config and issues no network call, so
  validation cannot contact the search provider or fetch a page.

## Alternatives considered

- Report empty `browser_allowed_domains` as `FAILED` with reason `allowlist_empty`, matching Shell and
  File — rejected: it turns the shipped deny-all configuration into a startup refusal and breaks
  `tests/mcp_servers/cicd/test_mcp_server_health_status.py:19-31`, and it reports a security posture
  that is stricter than the server's actual behavior.
- Omit `server.browser_allowlist` when `browser_fetch` is disabled — rejected: row `03` requires the
  check set to be identical across configurations so row `17` can compare it, and omitting the id
  would make a disabled capability indistinguishable from a missing check.
- Move the browser bounds into `_validate_config_bounds()` so config load raises — rejected for this
  row: it changes existing load behavior and the tests that pin it (`tests/mcp_servers/web_search/`),
  and the posture gate already refuses to bind.
- Compute the fingerprint from the raw config dict — rejected: the raw dict contains `auth_token`, so
  a fingerprint over it would be derived from a Secret; `non_secret_view()` is the boundary that keeps
  it out.
- Put the validator in `web_search_service.py` — rejected: `REQ-015` names the models module, and the
  validator is a function of the config shape, not of provider execution.

## Implementation
### Target file

`scripts/mcp_servers/web_search/web_search_models.py` (modify)

### Procedure

1. Import `SecurityCheckResult`, `SecurityCheckStatus`, and the reason-code constants from
   `shared.security.result_dto` (row `02`).
2. Add `HARD_BROWSER_TIMEOUT_SEC_LIMIT: int = 120` and `HARD_BROWSER_MAX_RESPONSE_KB: int = 4096`
   next to the existing ceilings (`:61-63`).
3. Add `non_secret_view()` (new) to `WebSearchConfig` after the field definitions (`:105`).
4. Add `validate_web_search_security()` (new) after `BrowserConfig` (`:176`), before the Pydantic
   schema section.
5. Leave `WebSearchConfig.from_dict()`, `load()`, `_validate_config_bounds()`, `BrowserConfig`,
   `get_max_results_limit()`, `SearchRequest`, `SearchResult`, `SearchResponse`, and the domain
   exceptions unchanged.

### Method

- Fixed check order: `server.results_bounds`, `server.search_timeout_valid`,
  `server.browser_timeout_valid`, `server.browser_response_limit`, `server.browser_allowlist`.
- `non_secret_view()` returns
  `{"own_config_file": "web_search_mcp_server.toml", "default_max_results", "max_results_limit",
  "search_timeout_sec", "browser_max_response_kb", "browser_timeout_sec",
  "browser_allowlist_count": len(browser_allowed_domains), "auth_token_present": bool(auth_token)}`
  — scalars plus a list count and a presence boolean, with no token value and no domain value. It is
  the single source used by both the fingerprint computation (row `03`) and the validator, so the two
  cannot diverge.
- Messages name the setting and its state (`browser_timeout_sec must be positive`,
  `browser_allowed_domains contains an entry that cannot match a hostname`); allowlist entries are
  reported by count, never by value (`REQ-004`).

### Details

- The module is 268 lines; the addition is roughly 55 lines. If the file would exceed its size
  convention, the validator moves to a new sibling module
  `scripts/mcp_servers/web_search/web_search_security.py` while `non_secret_view()` stays here.
  **Needs confirmation**: the Plan's frozen table names only `web_search_models.py`, so a sibling
  module requires a Plan amendment.
- `WebSearchConfig` is a plain dataclass (not frozen) and `browser_allowed_domains` is a mutable
  list, so `non_secret_view()` must build a new dict and a count rather than expose the list itself.
- The lowercase-hostname shape test for `server.browser_allowlist` is a local helper
  (`_is_hostname_shape(value: str) -> bool`), not a change to `_check_domain()` in
  `scripts/mcp_servers/web_search/search_provider.py`, which stays the runtime authority.
- `SearchRequest` reads `_cfg` at import (`:215-216`), so a config that violates
  `server.results_bounds` cannot reach this function through `load()`; the check exists for configs
  constructed directly, which is how the new tests exercise the failure paths.

## Compatibility considerations

- Additive change: no field, default, type, or `from_dict()` behavior changes, so
  `tests/mcp_servers/web_search/test_web_search_models.py` (including the `browser_*` defaults at
  `:126-128` and the overrides at `:141-149`) keeps passing.
- Behavior change appears only once row `52` publishes the posture: web-search-mcp with
  `browser_timeout_sec <= 0`, a non-positive `browser_max_response_kb`, or a value above a new
  ceiling reports `ready=false` (HTTP 503 through the existing handler contract) and refuses to bind.
  Today such a configuration loads and runs.
- The shipped configuration keeps `validated=true`, so
  `tests/mcp_servers/cicd/test_mcp_server_health_status.py:19-31` and
  `tests/mcp_servers/web_search/test_web_search_health.py:113-115` keep passing unchanged.
- No `docs/*.md` change is in scope for this row.

## Security considerations

- `REQ-015` / Plan `INV-05`: web-search-mcp validates its own configuration before Ready; the Agent
  never reads `web_search_mcp_server.toml`.
- `REQ-002` / Plan `INV-09`: `auth_token` is a Secret and is excluded from `non_secret_view()`, the
  fingerprint, and every message; allowlist entries are reported by count only.
- Keeping the fingerprint derived from a server-owned non-secret view is what makes row `17`'s
  fingerprint comparison possible without a cross-config read.
- The deny-all default stays deny-all: this row never turns an empty allowlist into a permission, and
  `_check_domain()` remains the runtime gate for `browser_fetch`.

## Rollback considerations

- Revert this commit together with row `52`, which imports both new symbols. No config or data
  migration is involved.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Browser timeout bounds | `uv run pytest tests/mcp_servers/web_search/test_web_search_security_validation.py` (new test file) | `browser_timeout_sec=0` and `-1` yield `server.browser_timeout_valid` `FAILED`, reason `config_invalid`; `> HARD_BROWSER_TIMEOUT_SEC_LIMIT` likewise |
| Response size bounds | same new test file | `browser_max_response_kb=0` yields `server.browser_response_limit` `FAILED`, reason `config_invalid` |
| Deny-all is not a failure | same new test file | `browser_allowed_domains=[]` yields `server.browser_allowlist` `NOT_APPLICABLE`, reason `not_applicable`, and the posture stays `validated=true` |
| Malformed allowlist entry | same new test file | `["Example.com"]` or `["https://example.com"]` yields `WARNING`, reason `allowlist_invalid`, and `validated` stays `true` |
| Result-count bounds | same new test file | a directly constructed config with `default_max_results > max_results_limit` yields `server.results_bounds` `FAILED` |
| Non-secret view excludes secrets | same new test file | `non_secret_view()` contains no `auth_token` key, carries only `auth_token_present`, and `assert_non_secret()` accepts every value |
| Deterministic check set | same new test file | the same five check ids appear for every configuration |
| Existing web search suite | `uv run pytest tests/mcp_servers/web_search/` | passes |
| Cross-server health contract | `uv run pytest tests/mcp_servers/cicd/test_mcp_server_health_status.py` | passes unchanged |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-005` for Web Search: web-search-mcp validates its own configuration and returns the common
  posture.
- A server-owned non-secret config view exists and is the only source of the posture fingerprint
  input.
- The five check ids appear for every configuration, and the shipped deny-all configuration yields
  `validated=true`.
- No token value or allowlist value appears in any posture field or message.

## Out of scope

- Editing `scripts/mcp_servers/web_search/web_search_server.py` (row `52`),
  `search_provider.py`, `web_search_service.py`, `health.py`, or `metrics.py`.
- Changing `_validate_config_bounds()`, `from_dict()`, or the `browser_auth_token` removal guard.
- Enabling `browser_fetch` by populating `browser_allowed_domains` in any config file.
- Agent-side validation and classification (rows `17`-`18`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `non_secret_view()` | Pending | — | — | required by row `03` fingerprint input |
| 2 | Implement `validate_web_search_security()` | Pending | — | — | check ids are Needs-confirmation (Plan `UNK-01` / `UNK-03`) |
| 3 | Decide single-file vs sibling module (Details) | Pending | — | — | sibling module needs a Plan amendment |
| 4 | Add `tests/mcp_servers/web_search/test_web_search_security_validation.py` | Pending | — | — | |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-015` (Web Search self-validation)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/web_search/web_search_models.py`
