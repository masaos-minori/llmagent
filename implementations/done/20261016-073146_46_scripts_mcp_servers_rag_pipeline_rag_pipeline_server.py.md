## Goal

Wire rag-pipeline-mcp's own security validation (row `15`) into the shared startup flow (row `04`),
publish the resulting Security Posture on `/health` (row `06`), and refuse HTTP bind when the posture
is not validated (`REQ-002`, `REQ-003`, `REQ-010`).

## Scope

- One modified module `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`: build the posture,
  pass it to `make_health_response()`, and gate `run_http()` on it.
- This row adds no validation rule of its own: the validator is row `15`, the envelope is row `03`,
  the ordering is row `04`, the payload key is row `06`.
- One new test file `tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py`.
- `scripts/mcp_servers/server.py` and `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` are
  reference files only; neither is a row in the Plan's frozen table and neither is modified here.

## Assumptions

- Verified current source: `_cfg: RagPipelineConfig = RagPipelineConfig.load()` at `:61`, `_service`
  imported from `mcp_servers.rag_pipeline.rag_pipeline_service` at `:42-44` (a module-level
  singleton, not built in this file), `async def _lifespan()` at `:79-84` which calls
  `svc.start()` / `svc.stop()`, `app = FastAPI(..., lifespan=_lifespan)` at `:87-92`,
  `attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token or "")` at `:94`,
  `def _check_health_deps()` at `:147-159`, the `/health` handler at `:162-168`
  (`deps = _check_health_deps()` at `:165`, `details` at `:166`,
  `make_health_response(deps, details)` at `:167`), `class RagPipelineMCPServer` at `:219` with
  `http_port = 8010` at `:224`, `own_config_file = "rag_pipeline_mcp_server.toml"` at `:225`,
  `app_module = "mcp_servers.rag_pipeline.rag_pipeline_server:app"` at `:226`, and
  `if __name__ == "__main__": server = RagPipelineMCPServer(); server.run_http()` at `:234-236`.
- This server already has its own config validator: `RagPipelineConfig.load()`
  (`rag_pipeline_models.py:98-104`) runs `RagConfigValidator().validate(raw_cfg)` and logs warnings,
  raising on failure. That is the existing `SCHEMA_VALIDATION` stage of `REQ-003`. Row `15`'s
  `validate_rag_pipeline_security(cfg)` is the separate `SERVER_SECURITY_VALIDATION` stage; this row
  does not merge them.
- `_check_health_deps()` re-reads the config through `ConfigLoader().load("rag_pipeline_mcp_server.toml")`
  on every probe (`:150-152`) and maps a failure to `deps["config"] = "check failed"` inside a
  broad `except Exception` (`:156`). That per-probe behavior is unchanged by this row; the posture is
  computed once at import and is not affected by a probe-time config failure.
- Production starts this module as `__main__`: `config/agent.toml:395`
  `cmd = ["/opt/llm/bin/mcp_rag_pipeline"]`. Verify the entry name against `deploy/build_binaries.sh`
  at implementation time.
- uvicorn 0.49.0 imports the app module before binding (`config.load()` at
  `.venv/lib/python3.14/site-packages/uvicorn/server.py:85-86` before `self.startup()` at `:94`);
  this row does not rely on that ordering, the `__main__` gate is the control. The `_lifespan`
  `svc.start()` call runs after the gate, so a posture failure prevents the service from ever being
  started.
- `MCP_RAG_PIPELINE_AUTH_TOKEN` is set to `"test-token"` by `tests/conftest.py:38-46`, so the flow's
  built-in `common.auth_token` check passes in the test suite for this server.
- `/opt/llm/sqlite-vec/vec0.so` and `/opt/llm/db/rag.sqlite` exist in this environment, and
  `config/rag_pipeline_mcp_server.toml` ships `embed_url` (`:10`), `llm_url` (`:7`),
  `rag_db_path` (`:13`), `sqlite_vec_so` (`:16`), `top_k_search = 20` (`:48`),
  `top_k_rerank = 15` (`:51`), `rag_top_k = 5` (`:54`), `rag_min_score = 2.0` (`:57`), and
  `use_refiner = false` (`:42`), so with row `15`'s check set the shipped configuration produces
  `validated=true` with `server.refiner_limits` as `NOT_APPLICABLE`.
- **Needs confirmation**: `SecurityPosture.ready` (row `03`) versus the payload `ready` computed in
  row `06`. This row reads only `SecurityPosture.validated` for the bind gate.

## Design decisions

- Compute the posture once at module import into a module-level `_security_posture`, immediately
  after `_cfg` (`:61`). The Agent polls `/health` repeatedly during readiness polling, and the bind
  gate needs the outcome before `run_http()`.
- Gate in the `if __name__ == "__main__":` block (`:234-236`): when `_security_posture.validated` is
  false, log the failed check ids with their reason codes and `raise SystemExit(1)` before
  constructing the server.
- Do not raise while building the posture. Row `15`'s entry point returns results instead of raising,
  and a posture failure must stay reportable on `/health`. `RagPipelineConfig.load()` keeps its own
  fail-fast behavior (`rag_pipeline_models.py:99-104`), which is a different, already-established
  rule.
- Keep the existing `deps` semantics unchanged, including the per-probe config re-read and its
  `except Exception` fallback (`:150-157`). Dependency and config availability stay in the
  `dependencies` key; the posture carries only row `15`'s checks plus the flow's built-in common
  checks. `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py:165-177` depends on
  that fallback producing 503 with `dependencies == {"config": "check failed"}`.
- Supply only the `SERVER_SECURITY_VALIDATION` stage (`validate_rag_pipeline_security(_cfg)` from row
  `15`) to `run_startup_validation()`; the flow's built-in `check_own_config_only()`,
  `check_auth_token_present()`, and `check_published_tools_declared()` cover the common and
  tool-capability stages. `CONFIG_LOAD` and `SCHEMA_VALIDATION` reuse the already-loaded `_cfg` and
  the `RagConfigValidator` pass that `load()` already performed.
- This row defines the normalized non-secret view hashed by `compute_config_fingerprint()` (row
  `03`), because rows `07`-`16` define check ids but no fingerprint view. Path- and host-valued
  fields are hashed as presence booleans only:
  `{"own_config_file": "rag_pipeline_mcp_server.toml", "embed_url_configured",
  "llm_url_configured", "rag_db_path_configured", "sqlite_vec_so_configured", "sqlite_timeout",
  "sqlite_busy_timeout_ms", "use_mqe", "use_rrf", "use_rerank", "use_refiner", "rrf_k",
  "top_k_search", "top_k_rerank", "rag_top_k", "rag_min_score", "max_chunks_per_doc",
  "refiner_max_tokens", "refiner_max_chars_per_chunk", "refiner_timeout", "mqe_n_queries"}`.
  `auth_token` and `mqe_prompt_template` are excluded.
- `server.sqlite_vec_available` (row `15`) checks that the configured `.so` path exists at import;
  `_lifespan`'s `svc.start()` (`:82`) is the point that actually loads the extension. This row keeps
  both and does not move the load earlier.

## Alternatives considered

- Put the gate inside `MCPServer.run_http()` — rejected: `scripts/mcp_servers/server.py` is not a
  row in the Plan's frozen table, and a base-class gate would apply to servers whose validators have
  not landed yet.
- Put the gate inside `_lifespan()` — rejected: `svc.start()` already runs there, and a lifespan
  failure surfaces as a uvicorn startup error after the bind decision rather than as a posture
  refusal before bind.
- Fold the posture into `_check_health_deps()` so one function reports both — rejected: `deps` is a
  per-probe availability map that must stay cheap and must not re-run validation, and row `06` fixes
  the payload shape.
- Compute the posture lazily on the first `/health` probe — rejected: the gate must decide before
  bind.
- Raise at import time when validation fails — rejected: it breaks every test that imports the module
  and produces no posture for the Agent to classify.
- Map `RagConfigValidator`'s warnings into posture `WARNING` results — deferred: it would give two
  sources for the same finding in this row. Recorded as Needs confirmation.

## Implementation
### Target file

`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` (modify)

### Procedure

1. Import `run_startup_validation` and `StartupStage` from `shared.security.startup_flow` (row `04`),
   `SecurityPosture` and `compute_config_fingerprint` from `shared.security.posture_contract`
   (row `03`), and `validate_rag_pipeline_security` from `mcp_servers.rag_pipeline.rag_pipeline_models`
   (row `15`).
2. Add `_rag_security_view(cfg: RagPipelineConfig) -> dict[str, object]` (new private function)
   returning the normalized view described above.
3. Add `_build_security_posture() -> SecurityPosture` (new private function) that calls
   `run_startup_validation()` with `server_key="rag_pipeline"`,
   `own_config_file="rag_pipeline_mcp_server.toml"`, the `SERVER_SECURITY_VALIDATION` stage callable
   (`validate_rag_pipeline_security(_cfg)`), and the fingerprint view.
4. Assign `_security_posture: SecurityPosture = _build_security_posture()` after `_cfg` (`:61`).
5. Change `:167` to `make_health_response(deps, details, security=_security_posture)`.
6. Add the gate to `:234-236`: log the failed check ids and reason codes, then
   `raise SystemExit(1)` before `RagPipelineMCPServer()` is constructed.
7. Add `tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py`.

### Method

- Build the posture after `_cfg` exists and before `app = FastAPI(` (`:87`), so the posture exists
  before the middleware is attached and before any route can be hit.
- The gate log line is one line, format:
  `rag-pipeline-mcp: security posture FAILED (<check_id>:<reason_code>, ...) — refusing to bind`.
  Only check ids and reason codes appear; database paths, the `.so` path, and the internal
  `llm_url` / `embed_url` hosts are excluded (`REQ-002`, `REQ-004`).
- `_build_security_posture()` must not call `RagPipelineConfig.load()` again; it reuses `_cfg`, so no
  second `RagConfigValidator` pass and no duplicated config warnings.
- Keep `details` exactly as today (`{"service": "rag-pipeline-mcp"}` at `:166`); the posture is a
  sibling top-level key (row `06`).
- Type the posture as `SecurityPosture`, not `dict[str, object]`.

### Details

- `server_key` is `"rag_pipeline"`, matching `[mcp_servers.rag_pipeline]`
  (`scripts/agent/startup_validation.py:71-73`) and the `server_key` the `/v1/tools` payload already
  reports (`tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py:186`).
- `REQUIRED_CHECK_IDS["rag_pipeline"]` (row `03`) must list exactly row `15`'s ids
  (`server.embed_url_configured`, `server.llm_url_configured`, `server.rag_db_path_configured`,
  `server.sqlite_vec_available`, `server.top_k_bounds`, `server.min_score_valid`,
  `server.refiner_limits`) plus the flow's built-in common ids, or row `17` reports
  `check_set_mismatch`.
- `server.embed_url_configured` and the existing `deps["embed_url"] = "not configured"`
  (`:154-155`) describe the same configured value from two layers: the posture reports it as a
  security validation result, `dependencies` reports it as a live availability signal. Both stay;
  the difference is that a posture `FAILED` blocks bind while a `deps` entry only degrades the
  payload.
- The module is about 236 lines, already above the 200-line convention. The roughly 30 added lines
  stay in this file; do not split it as a side effect of this row. Row `15` already carries a
  Needs-confirmation about a sibling module for `rag_pipeline_models.py`; that decision belongs to
  row `15`, not here.

## Compatibility considerations

- Existing `/health` assertions keep passing: with the shipped config every rag check is `OK` or
  `NOT_APPLICABLE`, so `validated` stays `true` and `ready` stays `true`.
  `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py:165-177` (503 through the
  config-failure `deps` fallback) keeps its exact assertion because `deps` logic is untouched.
- The `security` key is additive (row `06`); no existing rag test enumerates payload keys.
- Tests that patch `ConfigLoader` at probe time do not change the posture, because the posture is
  built from `_cfg` at import.
- Behavior change is limited to startup and `/health`: a rag config with an empty `embed_url`,
  `llm_url` (when rerank or refiner is enabled), `rag_db_path`, a missing `sqlite_vec_so` file, a
  non-positive top-k, a negative `rag_min_score`, or a refiner limit of `0` now exits non-zero before
  binding instead of starting and failing at the first pipeline call.
- No `docs/*.md` edit is in scope for this row; `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`
  and `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` are Plan
  follow-ups.

## Security considerations

- `REQ-010` / Plan `INV-05`: rag-pipeline-mcp validates its own configuration before Ready, and the
  Agent stops reading `rag_pipeline_mcp_server.toml` (`REQ-017`).
- `REQ-002` / Plan `INV-09`: the fingerprint view excludes `auth_token`, `mqe_prompt_template`, and
  every path- or host-valued field (`rag_db_path`, `sqlite_vec_so`, `llm_url`, `embed_url`), hashing
  them as presence booleans only.
- `REQ-011`: the Agent-side empty-`auth_token` rejection stays at
  `scripts/agent/startup_validation.py:71-81` (`mcp_auth`, not removed by row `22`); this server has
  no server-side equivalent today — `attach_auth_middleware(..., _cfg.auth_token or "")` (`:94`)
  installs the accept-all fallback when the token is empty (`scripts/mcp_servers/server.py:100-113`).
  The flow's built-in `check_auth_token_present()` is the posture-level copy; it reports `WARNING` with
  reason `auth_token_missing` and keeps `validated=true` (Plan `UNK-06`, resolved 2026-10-16; row `04`).
- `REQ-004`: the gate log line and every posture message carry reason codes only.

## Rollback considerations

- Revert this commit together with rows `06` (payload parameter), `15` (validator), and `04` (flow).
  No config or data migration is involved.
- The gate is the only statement that can make a previously-startable rag config unstartable;
  reverting the `__main__` block restores today's behavior without touching `/health`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Posture published | `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py` (new test file) | `/health` body carries the `security` key with `server_key == "rag_pipeline"` and `contract_version == SECURITY_CONTRACT_VERSION` |
| Validated shipped config | same new test file | `_security_posture.validated is True` against `config/rag_pipeline_mcp_server.toml`, with `server.refiner_limits` present as `NOT_APPLICABLE` |
| Missing extension blocks bind | same new test file | with `sqlite_vec_so` patched to a non-existent path, `server.sqlite_vec_available` is `FAILED` with reason `dependency_unreachable`, `validated is False`, `/health` returns 503 with `ready is False`, and the `__main__` gate raises `SystemExit` |
| Invalid top-k | same new test file | `rag_top_k` greater than `top_k_rerank` yields `server.top_k_bounds` `FAILED` with reason `config_invalid` |
| Existing rag suite | `uv run pytest tests/mcp_servers/rag_pipeline/` | passes, including `test_rag_pipeline_server_endpoints.py:165-177` |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-002`: rag-pipeline-mcp publishes the posture on `/health` with no Secret, path, host, or
  config body in it.
- Plan `AC-003`: rag-pipeline-mcp runs the shared ordering and does not bind HTTP when validation
  fails.
- Plan `AC-005` for RAG Pipeline: the rules live in `rag_pipeline_models.py` (row `15`); this file
  contains wiring only.

## Out of scope

- Adding or changing RAG Pipeline check ids (row `15`).
- Changing `make_health_response()` or the payload shape (row `06`).
- Agent-side posture validation, classification, and Tool Discovery gating (rows `17`-`19`).
- Changing `_check_health_deps()`, `_lifespan()`, `RagConfigValidator`, or the service singleton in
  `rag_pipeline_service.py`.
- Splitting `rag_pipeline_server.py` into smaller modules.

## Confirmation outcomes

- Resolved 2026-10-17: the RAG Pipeline fingerprint view defined in `Design decisions` is retained as
  written. It carries scalars, counts, and presence flags, so a changed URL or path value with an
  unchanged count is not detectable through the digest; row `05` compares check ids and statuses, and
  row `17`'s `compare_fingerprint()` is not consumed by the row `18` gate.
- Resolved 2026-10-17: `RagConfigValidator`'s existing warnings stay log-only. The posture reports its
  own checks, so one finding keeps one source instead of appearing as both a log line and a check.
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
| 1 | Import the shared flow, contract, and row `15` validator | Completed | 2026-10-17 | 2026-10-17 | validator imported from the row 55 sibling module rag_pipeline_security, not rag_pipeline_models as the doc states |
| 2 | Add `_rag_security_view()` and `_build_security_posture()` | Completed | 2026-10-17 | 2026-10-17 | view carries url presence flags, counts, and numeric bounds, server.refiner_limits is published as not_applicable |
| 3 | Pass the posture to `make_health_response()` at `:167` | Completed | 2026-10-17 | 2026-10-17 | posture passed to make_health_response |
| 4 | Add the `__main__` bind gate at `:234-236` | Completed | 2026-10-17 | 2026-10-17 | gate extracted into _enforce_posture_gate |
| 5 | Add `tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py` | Completed | 2026-10-17 | 2026-10-17 | new test file, not a frozen-table row |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-17 | 2026-10-17 | ruff and mypy clean, 132 passed in tests/mcp_servers/rag_pipeline |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 5 | New test files are not rows in the Plan's frozen table; the Plan must be amended or the assertions added to an existing `tests/mcp_servers/rag_pipeline/*` file | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (posture published on `/health`), `REQ-003` (shared startup ordering, validation failure blocks bind), `REQ-010` (RAG Pipeline self-validation)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`, `scripts/mcp_servers/health_response.py`, `scripts/shared/security/startup_flow.py`, `scripts/shared/security/posture_contract.py`
