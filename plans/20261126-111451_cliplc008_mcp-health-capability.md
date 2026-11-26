## Goal
- Make MCP health a single, versioned contract (liveness, ready, degraded reason codes, capabilities) that the Agent applies with per-server timeouts bounded by the lifecycle deadline and one documented authentication model, so that optional capability loss disables only the dependent tools, required capability loss blocks startup, and RuntimeTool diagnostics read explicit metadata instead of status text.

## Priority
Medium

## Scope
- **In-Scope**:
  - Apply the effective per-server health timeout to the startup poll, the periodic liveness check, the post-startup verification, `/mcp status`, and discovery; cap each startup request by the remaining lifecycle deadline; remove zero-means-unlimited for `health_timeout`.
  - Document and enforce one health authentication model: the existing single per-server `auth_token`, sent through one helper (owner decision, see Design D-1).
  - Add a shared health contract (`liveness`, `ready`, degraded reason codes, per-capability state, schema version) with a strict parser, backward compatible with servers that report only `liveness`/`ready`; emit it from `make_health_response()` and from the GitHub server.
  - Stop treating `liveness=true` alone as readiness; require the server's required capability to be proven by its health report; disable only the tools that depend on a degraded optional capability.
  - Add explicit `config_dependent` to `RuntimeTool`, parsed strictly from the discovery entry; generate `/mcp status` tool rows from explicit fields.
  - Make the registry immutable after construction with atomic publication; an availability change requires a restart (owner decision, see Design D-2).
  - Reconcile `config/tool_catalog.toml` capability identifiers with the canonical capability model.
  - Update the MCP design docs for health schema, authentication, capability semantics, and timeout rules.
- **Out-of-Scope**:
  - Launch spec and credential isolation, process ownership, and log/stderr redaction (sibling issues of the same backlog).
  - A distinct `health_auth_token` and its secret registration (rejected by the owner decision D-1).
  - Live registry rebuild and swap (rejected by the owner decision D-2).
  - Adding safety, preview, or resource metadata to the discovery schema (already merged under tool metadata schema 2.1; this Plan adds no discovery schema field).
  - Migrating servers other than `github` to emit a per-capability health block; they keep the legacy `liveness`/`ready` body and are read through the legacy fallback (D-6).
  - Removing `McpServerConfig.tool_names`: the field no longer exists (see Background).
- **Dependencies**: The staged-reload, launch-spec, and process-ownership work this issue was ordered after is archived and merged, so no ordering dependency remains. This Plan blocks the redaction/diagnostics and API field cleanup work of the same backlog, and shares the `RuntimeTool` and discovery schema (field set version 2.1) with the tool-catalog and runtime-tool-metadata work, which is already merged; no new schema version is introduced.

## Background
- Source: consolidated CLI REPL and MCP lifecycle backlog, Issue 8. The earlier health-hint and mandatory-construction work is archived.
- Verified current state (Step 2/3 adversarial verification):
  - Health timeout: `McpServerConfig.health_timeout` exists (`scripts/shared/mcp_config.py:122`) and `get_effective_health_timeout()` returns 5.0 when unset and `None` (unlimited) when 0 (`scripts/shared/mcp_config.py:292-298`). Only discovery fetch (`mcp_tool_discovery_fetch.py:54`) and the `/mcp status` client constructor (`mcp_status.py:104`) use it.
  - The startup poll receives the global constant `MCPSERVER_HEALTH_TIMEOUT = 5.0` (`http_lifecycle.py:50,314`), not the per-server value. The periodic check `HealthChecker.verify_running_async` defaults to 5.0 (`http_lifecycle_health_checker.py:241-248`). `startup_mcp_starter.py:150,238` hard-code `timeout=5.0`. `_probe_mcp_health_detail` passes `timeout=5.0` per request (`mcp_health.py:52,54`), which overrides the client-level per-server timeout that `/mcp status` builds.
  - A request is bounded by `min(health timeout, startup_timeout_sec)` only (`http_lifecycle_health_checker.py:101,172`), not by the remaining deadline, so one request can outlive the poll deadline.
  - Authentication: one `auth_token` is sent as Bearer to `/health` and to tool calls through `McpServerConfig.auth_headers()`; `control_auth_token` covers control paths only. `HealthChecker.verify_running_async` also rebuilds the header from `cfg.auth_token` (`http_lifecycle_health_checker.py:264-268`), a second header path.
  - Readiness: a 503 body with `liveness is True` counts as ready at startup (`http_lifecycle_health_checker.py:104-126,199-205`; `startup_mcp_starter.py:153,212`). The Security Posture gate is `ready=validated` (`scripts/shared/security/startup_flow.py:229`), independent of dependency failures, so a missing `GITHUB_TOKEN` (`github_server.py:185-186`) leaves the gate green and the GitHub tools absent from `/v1/tools` without a capability-level report.
  - Health body: `make_health_response()` emits `status`, `ready`, `liveness`, `restart_recommended`, `operator_action_required`, `dependencies` (a dict), `details`, `security`; it has no capability or degraded-reason field. `interpret_health_body()` casts `dependencies` to a list (`health_models.py:180`), so a dict body iterates keys and loses the status text.
  - Capability model: `config/tool_catalog.toml` declares one `required_capability` per server and says cliplc008 defines the canonical schema (header note). `_check_required_tools` is inert until some tool declares `capabilities` (`mcp_tool_discovery.py:279-281`), and no production server declares any (`docs/22_mcp/mcp_08_tool_capability_naming_convention.md:86`), so required capability loss does not block startup today.
  - `McpServerConfig` has no `tool_names` field; the removal was completed by the tool-catalog work. This Requirement of the issue is already satisfied.
  - `config_dependent` derivation (Unknown in the issue): `RuntimeToolRegistry.diagnostics()` computes `config_dependent = tool.status != "active"` (`runtime_tool_registry.py:281`), although every discovery entry carries an explicit `config_dependent` bool (`scripts/mcp_servers/models.py:244`). The runtime schema gate does not validate that field (`validate_tool_schema_v2` in `scripts/shared/resource_scope.py` does not check it), and `RuntimeTool` drops it.
  - Registry lifecycle: the registry is built once and published at startup (`startup_validation.py:232-234`); the only later mutation is `apply_policy`, which rebinds `self._tools` to a new mapping (`runtime_tool_registry.py:248`).

## Problem
- Per-server health timeout and authentication are applied inconsistently; a 503 with `liveness=true` is accepted as ready without any capability proof; required capability loss does not block startup because the capability check is inert; optional dependency loss cannot disable only the affected tools; `config_dependent` in `/mcp status` is inferred from status text while the explicit field is discarded.

## Reason for Change
- Availability and diagnostic correctness after the configuration, launch, and process-state work are merged. No data-loss risk.

## Implementation Intent
- Define the health body contract once in `shared` (a leaf both the Agent and the servers may import), parse it strictly in the Agent, and let the Agent decide required versus optional from `config/tool_catalog.toml` and the server `required` flag. Resolve one effective timeout per server and cap startup requests by the remaining deadline. Keep one auth path. Carry explicit `config_dependent` and capability dependencies on `RuntimeTool`, exclude tools of degraded optional capabilities at registry construction, and treat the registry as immutable after construction.

## Requirements
- `REQ-001`: The effective per-server health timeout MUST apply to the startup poll, the periodic liveness check, the post-startup verification, `/mcp status` probing, and discovery. `health_timeout` MUST be strictly greater than 0; the zero-means-unlimited behavior is removed and 0 is rejected at config load and at direct construction.
- `REQ-002`: During the startup poll, each health request timeout MUST be `min(effective health timeout, remaining time to the lifecycle deadline)`, and no request may start after the deadline.
- `REQ-003`: Health authentication MUST follow one documented model: the per-server `auth_token` is sent as a Bearer header on every health request through `McpServerConfig.auth_headers()` only; no second header-building path remains, and the token never appears in a health log line or error message.
- `REQ-004`: A shared health contract MUST define `liveness`, `ready`, degraded reason codes from a closed vocabulary, per-capability state (`ok`, `degraded`, `unavailable`), and a health schema version; the Agent MUST parse it strictly and treat a body without the new fields as a legacy body; `make_health_response()` MUST emit the new fields additively without removing any existing key; `interpret_health_body()` MUST read `dependencies` as the dict servers emit.
- `REQ-005`: `liveness=true` alone MUST NOT be treated as readiness. A 503 body is accepted at startup only when the health report proves the server's required capability is `ok`; discovery MUST fail startup (FATAL) when a required server's required capability is not proven `ok`, using the health report as the proof; `config/tool_catalog.toml` capability identifiers MUST be reconciled with the capability model.
- `REQ-006`: When an optional capability is `degraded` or `unavailable`, only the tools that depend on it MUST be excluded from the registry, with exclusion reason `capability`; the GitHub server MUST report token loss as the optional capability `github.api` while its required capability `github.operations` stays `ok`.
- `REQ-007`: `RuntimeTool` MUST carry an explicit `config_dependent` bool parsed strictly from the discovery entry (a non-bool entry value rejects that entry with a finding); `RuntimeToolRegistry.diagnostics()` and `/mcp status` MUST use the explicit field and the capability dependency, and MUST NOT infer configuration dependency from `status`.
- `REQ-008`: `RuntimeToolRegistry` MUST be immutable after construction apart from the single-rebinding policy application, so a reader sees either the old or the new tool mapping in full; a change in tool availability MUST be reported by `/mcp status` as requiring a restart, with no live swap.
- `REQ-009`: The MCP design docs MUST describe the health schema, authentication model, capability semantics (required versus optional), timeout rules, and the restart-required registry rule.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/shared/mcp_health_contract.py | Create: shared health body contract, reason-code and capability-state vocabularies, strict parser | New module so the Agent and the MCP servers share one schema without `mcp_servers` importing `agent` (import-linter contract) | REQ-004, REQ-005, REQ-006; AC-04 | `lint-imports` 6 contracts kept incl. "mcp_servers must not import from agent" (checked in Step 3); no existing health contract module in `scripts/shared/` (`ls scripts/shared`, checked in Step 3) | tests/shared/test_mcp_health_contract.py | Verified |
| scripts/shared/mcp_config.py | Modify: reject `health_timeout <= 0`; `get_effective_health_timeout()` returns a positive float; document the single-token model on `auth_headers()` | Remove zero-means-unlimited and give one resolver | REQ-001, REQ-003; AC-01, AC-03 | `mcp_config.py:122,220-223,281-298` (checked in Step 2) | tests/shared/test_mcp_config_validation.py | Verified |
| scripts/agent/http_lifecycle_health_checker.py | Modify: per-server timeout and remaining-deadline cap in `poll_until_ready`; per-server timeout and single auth path in `verify_running_async`; replace `is_degraded_but_live` with report-based readiness | The poll uses the global 5.0 constant and accepts `liveness` alone | REQ-001, REQ-002, REQ-003, REQ-005; AC-01, AC-02, AC-03, AC-05 | `http_lifecycle_health_checker.py:92-126,172-205,241-286` (checked in Step 2) | tests/agent/test_http_lifecycle_health_check.py | Verified |
| scripts/agent/http_lifecycle.py | Modify: pass the per-server timeout to the poll and to the periodic check; stop using the global constant for requests | `request_timeout_sec=MCPSERVER_HEALTH_TIMEOUT` and the 5.0 default in the periodic check | REQ-001; AC-01 | `http_lifecycle.py:50,113-130,314` (checked in Step 2) | tests/agent/test_http_lifecycle_health_check.py | Verified |
| scripts/agent/startup_mcp_starter.py | Modify: post-startup verification uses the per-server timeout, `cfg.auth_headers()`, and report-based readiness | Hard-coded `timeout=5.0` and `liveness`-only acceptance in two places | REQ-001, REQ-005; AC-01, AC-05 | `startup_mcp_starter.py:150,153,212,238` (checked in Step 2) | tests/agent/test_startup_mcp_starter.py | Verified |
| scripts/agent/services/mcp_health.py | Modify: `_probe_mcp_health_detail` takes the per-server timeout; `PostureGate` carries the parsed health report; classify capability loss | The per-request `timeout=5.0` overrides the per-server client timeout; gates ignore capability state | REQ-001, REQ-004, REQ-005, REQ-006; AC-01, AC-04, AC-05 | `mcp_health.py:40-83,94-118,178-237` (checked in Step 2) | tests/agent/test_repl_health.py, tests/agent/test_mcp_health_posture.py | Verified |
| scripts/agent/services/mcp_status.py | Modify: pass the per-server timeout into the probe; show report fields | `/mcp status` ignores the effective timeout in the request | REQ-001, REQ-007; AC-01, AC-07 | `mcp_status.py:104,211,287` (checked in Step 2) | tests/agent/services/test_agent_mcp_status.py | Verified |
| scripts/agent/shared/health_models.py | Modify: `interpret_health_body` parses through the shared contract and reads `dependencies` as a dict | The list cast loses the status text of a dict body | REQ-004; AC-04 | `health_models.py:164-205` and `mcp_servers/github/github_server.py:185-186` emitting a dict (checked in Step 2) | tests/agent/shared/test_mcp_health_interpretation.py | Verified |
| scripts/agent/services/mcp_tool_discovery.py | Modify: load the catalog before registry construction; prove the required capability from the health report; pass degraded optional capabilities to the registry | The capability check is inert and the catalog is loaded after the registry is built | REQ-005, REQ-006; AC-05, AC-06 | `mcp_tool_discovery.py:102-139,260-328` (checked in Step 2) | tests/agent/services/test_mcp_tool_discovery.py, tests/agent/services/test_mcp_tool_discovery_posture_gate.py | Verified |
| scripts/agent/services/mcp_tool_discovery_fetch.py | Modify: strict bool check of `config_dependent`; per-server timeout stays the request timeout | The runtime schema gate does not validate `config_dependent` | REQ-007; AC-07 | `mcp_tool_discovery_fetch.py:54,94-118,227-245`; `scripts/shared/resource_scope.py` validator has no `config_dependent` check (checked in Step 3) | tests/agent/services/test_mcp_tool_discovery.py | Verified |
| scripts/agent/services/mcp_tool_discovery_registry.py | Modify: pass `config_dependent` and the catalog-derived capability dependency into `build_runtime_tool`; pass the degraded-capability map to the registry | `RuntimeTool` drops the explicit field and no capability dependency is applied | REQ-006, REQ-007; AC-06, AC-07 | `mcp_tool_discovery_registry.py:60-131` (checked in Step 2) | tests/agent/services/test_mcp_tool_discovery.py | Verified |
| scripts/shared/runtime_tool.py | Modify: add `config_dependent: bool = False` to `RuntimeTool` and `build_runtime_tool` | Carry the explicit producer-declared value (default only for non-discovery construction, see Design D-7) | REQ-007; AC-07 | `runtime_tool.py:44-105,108-198` (checked in Step 2); 14 test files call `build_runtime_tool` (checked in Step 3) | tests/shared/test_runtime_tool.py | Verified |
| scripts/shared/runtime_tool_registry.py | Modify: exclusion reason `capability`; `diagnostics()` reads the explicit field and capability dependency; document immutability and restart-required | Status-derived `config_dependent` and no capability exclusion | REQ-006, REQ-007, REQ-008; AC-06, AC-07, AC-08 | `runtime_tool_registry.py:46-101,208-248,265-298` (checked in Step 2) | tests/shared/test_runtime_tool_registry.py | Verified |
| scripts/agent/commands/cmd_mcp.py | Modify: render explicit config dependency, capability state, and the restart-required notice | `/mcp status` shows the status-derived value | REQ-007, REQ-008; AC-07, AC-08 | `cmd_mcp.py:54-62,167-185,355-368` (checked in Step 2) | tests/agent/commands/test_cmd_mcp.py | Verified |
| scripts/mcp_servers/health_response.py | Modify: emit `health_schema_version`, `degraded_reasons`, `capabilities` additively | The producer side of the shared contract | REQ-004; AC-04 | `health_response.py:31-65` (checked in Step 2) | tests/mcp_servers/test_health_response.py | Verified |
| scripts/mcp_servers/github/github_server.py | Modify: report token loss as degraded optional capability `github.api`; tools depend on it | Issue names GitHub-token loss; `github_token` is only a `dependencies` entry today | REQ-006; AC-06 | `github_server.py:117,135-139,181-196` (checked in Step 2) | tests/mcp_servers/github/test_github_health_posture.py | Verified |
| config/tool_catalog.toml | Modify: reconcile `required_capability` identifiers; declare the optional `github.api` capability; remove the "reconcile with cliplc008" note | The header note defers the canonical schema to this Plan | REQ-005, REQ-006; AC-05, AC-06 | `config/tool_catalog.toml:18-20,113-138` (checked in Step 3) | tests/agent/services/test_mcp_tool_discovery.py | Verified |
| tests/shared/test_mcp_health_contract.py | Create: contract parser and vocabulary tests | New contract needs strict-parse and legacy-body tests | REQ-004; AC-04 | New file; `tests/shared/` exists (checked in Step 3) | tests/shared/test_mcp_health_contract.py | Verified |
| tests/shared/test_mcp_config_validation.py | Modify: zero and negative `health_timeout` rejected; effective timeout positive | Existing health timeout tests assert 5.0 and 15.0 only | REQ-001; AC-01 | `test_mcp_config_validation.py:234-268` (checked in Step 3) | tests/shared/test_mcp_config_validation.py | Verified |
| tests/agent/test_http_lifecycle_health_check.py | Modify: per-server timeout, deadline cap, one auth path, report-based readiness, token not logged | Existing tests pin `is_degraded_but_live` branches (`:392-467`) | REQ-001, REQ-002, REQ-003, REQ-005; AC-01, AC-02, AC-03, AC-05 | `test_http_lifecycle_health_check.py:392-467` (checked in Step 3) | tests/agent/test_http_lifecycle_health_check.py | Verified |
| tests/agent/test_startup_mcp_starter.py | Modify: replace the `is_degraded_but_live` patch with report-based cases | The test patches the replaced predicate (`:250`) | REQ-005; AC-05 | `test_startup_mcp_starter.py:240-250` (checked in Step 3) | tests/agent/test_startup_mcp_starter.py | Verified |
| tests/agent/test_repl_health.py | Modify: probe passes the per-server timeout per request | `_probe_mcp_health_detail` tests call the old signature | REQ-001; AC-01 | `test_repl_health.py:19,52-89` (checked in Step 3) | tests/agent/test_repl_health.py | Verified |
| tests/agent/test_mcp_health_posture.py | Modify: gate carries the parsed report and capability classification | `PostureGate` gains fields | REQ-004, REQ-005; AC-04, AC-05 | listed by `rg PostureGate\(` (checked in Step 3) | tests/agent/test_mcp_health_posture.py | Verified |
| tests/agent/services/test_agent_mcp_status.py | Modify: `health_timeout=0` case becomes a rejection; probe uses the per-server timeout | The REQ-006 zero-timeout test asserts the removed behavior (`:145-151`) | REQ-001; AC-01 | `test_agent_mcp_status.py:145-151` (checked in Step 3) | tests/agent/services/test_agent_mcp_status.py | Verified |
| tests/agent/shared/test_mcp_health_interpretation.py | Modify: dict `dependencies` body keeps status text | Covers the latent list-cast loss | REQ-004; AC-04 | listed by `rg interpret_health_body` (checked in Step 3) | tests/agent/shared/test_mcp_health_interpretation.py | Verified |
| tests/agent/services/test_mcp_tool_discovery.py | Modify: required capability proof, optional capability exclusion, strict `config_dependent`, catalog-load order | Covers the discovery behavior changes | REQ-005, REQ-006, REQ-007; AC-05, AC-06, AC-07 | `test_mcp_tool_discovery.py` exists (checked in Step 3) | tests/agent/services/test_mcp_tool_discovery.py | Verified |
| tests/agent/services/test_mcp_tool_discovery_posture_gate.py | Modify: gate-plus-capability interaction | The gate fixture changes shape with `PostureGate` | REQ-005; AC-05 | `test_mcp_tool_discovery_posture_gate.py` and `_discovery_gates.py` exist (checked in Step 3) | tests/agent/services/test_mcp_tool_discovery_posture_gate.py | Verified |
| tests/shared/test_runtime_tool.py | Modify: `config_dependent` field and default | New dataclass field | REQ-007; AC-07 | `test_runtime_tool.py` exists (checked in Step 3) | tests/shared/test_runtime_tool.py | Verified |
| tests/shared/test_runtime_tool_registry.py | Modify: capability exclusion, explicit diagnostics, atomic policy application under concurrent reads | Covers REQ-006/007/008 | REQ-006, REQ-007, REQ-008; AC-06, AC-07, AC-08 | `test_runtime_tool_registry.py:314` asserts the status-derived row (checked in Step 3) | tests/shared/test_runtime_tool_registry.py | Verified |
| tests/agent/commands/test_cmd_mcp.py | Modify: table headers and rows from explicit metadata, restart-required notice | Pins diagnostic row shape (`:1006`) | REQ-007, REQ-008; AC-07, AC-08 | `test_cmd_mcp.py:1006` (checked in Step 3) | tests/agent/commands/test_cmd_mcp.py | Verified |
| tests/mcp_servers/test_health_response.py | Modify: new fields emitted, old keys unchanged | Producer contract test | REQ-004; AC-04 | `test_health_response.py` exists (checked in Step 3) | tests/mcp_servers/test_health_response.py | Verified |
| tests/mcp_servers/github/test_github_health_posture.py | Modify: token-loss capability report | GitHub health body test | REQ-006; AC-06 | `test_github_health_posture.py` exists (checked in Step 3) | tests/mcp_servers/github/test_github_health_posture.py | Verified |
| docs/22_mcp/mcp_02_02_startup-modes-and-health.md | Modify: health schema, readiness rule, timeout rules | Currently documents `status`/`ready`/`dependencies` only | REQ-009; AC-09 | `mcp_02_02_startup-modes-and-health.md:26-40` (checked in Step 3) | `uv run python tools/run_validation_gates.py` | Verified |
| docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md | Modify: degraded reason-code vocabulary | Reason codes become part of the contract | REQ-009; AC-09 | file exists; reason catalog belongs here (checked in Step 3) | `uv run python tools/run_validation_gates.py` | Verified |
| docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md | Modify: explicit `config_dependent`, capability dependency, restart-required registry | Documents the status-derived behavior being replaced | REQ-009; AC-09 | `mcp_03_06...md:25-53` (checked in Step 3) | `uv run python tools/run_validation_gates.py` | Verified |
| docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md | Modify: `health_timeout` must be greater than 0 | Field rule change | REQ-009; AC-09 | file exists (checked in Step 3) | `uv run python tools/run_validation_gates.py` | Verified |
| docs/22_mcp/mcp_06_14_mcp-authentication-setup.md | Modify: one-token health authentication model | Documents the chosen model | REQ-009; AC-09 | file exists (checked in Step 3) | `uv run python tools/run_validation_gates.py` | Verified |
| docs/22_mcp/mcp_08_tool_capability_naming_convention.md | Modify: required versus optional capability and the health state mapping | Its line 86 states no server declares capabilities | REQ-009; AC-09 | `mcp_08...md:86` (checked in Step 3) | `uv run python tools/run_validation_gates.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/startup_validation.py | Registry publication point (`:232-234`) and the readiness-then-discovery order that reuses one gate set | REQ-005, REQ-008 |
| scripts/shared/security/startup_flow.py | `ready=validated` posture definition (`:229`) that makes the gate independent of dependency failures | REQ-005 |
| scripts/shared/security/posture_contract.py | `SecurityPosture` shape that the health report must coexist with | REQ-004 |
| scripts/mcp_servers/models.py | `McpTool` TypedDict (`config_dependent: Required[bool]`, `:244`) | REQ-007 |
| scripts/shared/resource_scope.py | `validate_tool_schema_v2` (confirms `config_dependent` is not validated) | REQ-007 |
| scripts/shared/tool_metadata.py | Field set version `2.1` that stays unchanged | REQ-007 |
| scripts/agent/lifecycle_router.py | Callers of the periodic check (`:86,135,263`) | REQ-001 |
| scripts/agent/config_dataclasses.py | Loading path of `[mcp_servers.<key>]` into `McpServerConfig` | REQ-001 |
| .importlinter | Import contracts the new shared module must satisfy | REQ-004 |
| rules/env.md | deploy.sh behavior (`scripts/` rsynced, `config/*.toml` individually copied) | Affected areas |

## Acceptance Criteria
- `AC-01` (REQ-001): `health_timeout` of 0 or a negative value is rejected at load and at construction; the startup poll, periodic check, post-startup verification, `/mcp status` probe, and discovery fetch each issue requests with the server's effective timeout; a test asserts a non-default value reaches each of the five request sites.
- `AC-02` (REQ-002): In the startup poll, a request issued with `T` seconds left to the deadline has timeout `min(effective, T)`; no request starts once the deadline has passed; a hanging server cannot extend the poll beyond the deadline by more than the termination timeout.
- `AC-03` (REQ-003): Every health request carries `Authorization: Bearer <auth_token>` built only by `McpServerConfig.auth_headers()`; a server without a token sends no header; no log line or exception message produced by a health failure contains the token.
- `AC-04` (REQ-004): The contract parser accepts a full body and a legacy body (`liveness`/`ready` only), rejects a body with a wrong-typed field, a reason code outside the vocabulary, or an unknown capability state; `make_health_response()` output keeps every previous key and adds the new ones; a dict `dependencies` body keeps each dependency's status text in `interpret_health_body()`.
- `AC-05` (REQ-005): A 503 body with `liveness=true` and no proof of the required capability does not pass startup; the same body with the required capability `ok` passes; a required server whose required capability is `degraded` or `unavailable` produces a FATAL discovery finding; a legacy body falls back to `ready`.
- `AC-06` (REQ-006): With `GITHUB_TOKEN` unset, the GitHub health body reports `github.api` degraded and `github.operations` ok, startup is not blocked, and the registry excludes exactly the tools dependent on `github.api` with exclusion reason `capability`; tools of other servers stay registered.
- `AC-07` (REQ-007): `RuntimeTool.config_dependent` equals the discovery entry value; a non-bool entry value rejects that entry with a finding; `diagnostics()` and `/mcp status` show the explicit value, and a tool with `status != "active"` and `config_dependent=False` shows `False`.
- `AC-08` (REQ-008): Concurrent readers during `apply_policy` observe either the complete old or the complete new mapping; `/mcp status` states that a change in tool availability needs a restart.
- `AC-09` (REQ-009): The listed docs describe the contract, auth model, capability semantics, timeout rules, and restart-required rule, and the documentation gates report no finding.

## Tests
- T-01 (REQ-001, AC-01): config validation for zero, negative, and positive `health_timeout`; a parametrized test that a distinct value reaches each of the five request sites.
- T-02 (REQ-002, AC-02): poll test with a fake clock and a server that never answers; assert request timeout equals the remaining time and no request starts after the deadline.
- T-03 (REQ-003, AC-03): header test for token present and absent; caplog assertion that a failing probe logs no token (secret registration unchanged).
- T-04 (REQ-004, AC-04): contract parser tests (full, legacy, wrong type, unknown code, unknown state); producer test for additive keys; dict-dependencies interpretation test.
- T-05 (REQ-005, AC-05): readiness tests (liveness-only, required capability ok, degraded, unavailable, legacy fallback); discovery FATAL test for a required server.
- T-06 (REQ-006, AC-06): GitHub-token-loss case and a synthetic other-optional-dependency case; assert only dependent tools are excluded and a required dependency failure blocks startup.
- T-07 (REQ-007, AC-07): strict `config_dependent` parse, diagnostics from the explicit field, `/mcp status` row rendering.
- T-08 (REQ-008, AC-08): candidate-mapping rebinding under active reads (threaded reader loop during `apply_policy`); restart notice rendering.
- T-09 (REQ-009, AC-09): documentation gates from `rules/tool-gates.md`.
- Run ruff, mypy, and the full test suite (`uv run python tools/run_validation_gates.py --full`).

## Documentation Impact
- Yes. REQ-009 drives updates to the MCP docs listed under `Implementation Target Files` (health schema and timeouts, reason codes, runtime availability metadata, `health_timeout` field rule, authentication model, capability naming), selected through `docs/00_index.md` "Document References by Task" (MCP rows). The docs are written in English.

## Assumptions
- Capability identifiers follow `docs/22_mcp/mcp_08_tool_capability_naming_convention.md` (`{domain}.{action}`): the optional capability for GitHub API tools is `github.api`, next to the existing required `github.operations`.
- The Agent decides required versus optional: a capability is required only when it equals the `required_capability` of a server configured `required=true`; every other reported capability is optional. Servers report state only.
- `github` is a subprocess server and therefore always `required=true` (`mcp_config.py:208-212`), so its token loss must be modelled as an optional capability, not as server loss.
- A tool's capability dependency is the catalog `capabilities` of its owning server unless the discovery entry declares `capabilities`; the GitHub tools use `github.api` through the catalog.
- No `health_timeout` is set in any `config/*.toml` (`rg health_timeout config/*.toml` returned no match, checked in Step 3), so rejecting 0 breaks no production configuration.
- Field set version `2.1` and `MCP_TOOL_SCHEMA_VERSION` stay unchanged: `config_dependent` and `capabilities` are already part of the discovery entry.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which tools of each non-GitHub server would justify a per-tool optional capability (for example `browser_fetch` of the web search server) | No live inventory of per-tool optional dependencies beyond GitHub | Follow-up migration of other servers after this Plan; legacy fallback covers them meanwhile | False |
| UNK-02 | Whether any deployed server returns a `/health` 503 with `ready=false` and no capability block while `required=true`, which the legacy fallback would now block at startup | No production health sample | Check `/opt/llm` logs and each server's `deps` producers during the implementation procedure; if one exists, add its capability block in a follow-up | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/shared/mcp_health_contract.py | Create | Low (new leaf module; importers are the files below) | N/A (new) | N/A (new) | not applicable (rsynced) |
| scripts/shared/mcp_config.py | Modify | High (imported by agent, lifecycle, tool executor) | 10 | 4 authors | not applicable (rsynced) |
| scripts/agent/http_lifecycle_health_checker.py | Modify | Medium | 4 | 2 authors (high) | not applicable (rsynced) |
| scripts/agent/http_lifecycle.py | Modify | Medium | 4 | 4 authors | not applicable (rsynced) |
| scripts/agent/startup_mcp_starter.py | Modify | Medium | 5 | 2 authors (high) | not applicable (rsynced) |
| scripts/agent/services/mcp_health.py | Modify | High (gate consumed by readiness and discovery) | 3 | 2 authors (high) | not applicable (rsynced) |
| scripts/agent/services/mcp_status.py | Modify | Low | 6 | 4 authors | not applicable (rsynced) |
| scripts/agent/shared/health_models.py | Modify | Low | 0 | 3 authors | not applicable (rsynced) |
| scripts/agent/services/mcp_tool_discovery.py | Modify | High (startup pipeline) | 4 | 3 authors | not applicable (rsynced) |
| scripts/agent/services/mcp_tool_discovery_fetch.py | Modify | Medium | 1 | 1 author (high) | not applicable (rsynced) |
| scripts/agent/services/mcp_tool_discovery_registry.py | Modify | Medium | 2 | 2 authors (high) | not applicable (rsynced) |
| scripts/shared/runtime_tool.py | Modify | High (14 test files and several modules build tools) | 2 | 3 authors | not applicable (rsynced) |
| scripts/shared/runtime_tool_registry.py | Modify | High (routing authority) | 7 | 3 authors | not applicable (rsynced) |
| scripts/agent/commands/cmd_mcp.py | Modify | Low | 3 | 3 authors | not applicable (rsynced) |
| scripts/mcp_servers/health_response.py | Modify | High (every MCP server's `/health`) | 1 | 3 authors | not applicable (rsynced) |
| scripts/mcp_servers/github/github_server.py | Modify | Medium | N/A (not measured) | N/A (not measured) | not applicable (rsynced) |
| config/tool_catalog.toml | Modify | Medium (read at every discovery) | N/A (not measured) | N/A (not measured) | not applicable (rsynced) |
| tests/shared/test_mcp_health_contract.py | Create | Low | N/A (new) | N/A (new) | not applicable (rsynced) |
| tests/shared/test_mcp_config_validation.py | Modify | Low | N/A | N/A | not applicable (rsynced) |
| tests/agent/test_http_lifecycle_health_check.py | Modify | Low | N/A | N/A | not applicable (rsynced) |
| tests/agent/test_startup_mcp_starter.py | Modify | Low | N/A | N/A | not applicable (rsynced) |
| tests/agent/test_repl_health.py | Modify | Low | N/A | N/A | not applicable (rsynced) |
| tests/agent/test_mcp_health_posture.py | Modify | Low | N/A | N/A | not applicable (rsynced) |
| tests/agent/services/test_agent_mcp_status.py | Modify | Low | N/A | N/A | not applicable (rsynced) |
| tests/agent/shared/test_mcp_health_interpretation.py | Modify | Low | N/A | N/A | not applicable (rsynced) |
| tests/agent/services/test_mcp_tool_discovery.py | Modify | Low | N/A | N/A | not applicable (rsynced) |
| tests/agent/services/test_mcp_tool_discovery_posture_gate.py | Modify | Low | N/A | N/A | not applicable (rsynced) |
| tests/shared/test_runtime_tool.py | Modify | Low | N/A | N/A | not applicable (rsynced) |
| tests/shared/test_runtime_tool_registry.py | Modify | Low | N/A | N/A | not applicable (rsynced) |
| tests/agent/commands/test_cmd_mcp.py | Modify | Low | N/A | N/A | not applicable (rsynced) |
| tests/mcp_servers/test_health_response.py | Modify | Low | N/A | N/A | not applicable (rsynced) |
| tests/mcp_servers/github/test_github_health_posture.py | Modify | Low | N/A | N/A | not applicable (rsynced) |
| docs/22_mcp/mcp_02_02_startup-modes-and-health.md | Modify | Low | N/A | N/A | not applicable (rsynced) |
| docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md | Modify | Low | N/A | N/A | not applicable (rsynced) |
| docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md | Modify | Low | N/A | N/A | not applicable (rsynced) |
| docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md | Modify | Low | N/A | N/A | not applicable (rsynced) |
| docs/22_mcp/mcp_06_14_mcp-authentication-setup.md | Modify | Low | N/A | N/A | not applicable (rsynced) |
| docs/22_mcp/mcp_08_tool_capability_naming_convention.md | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path B (more than 3 files; public/runtime interface change). Baselines (checked in Step 5): `lint-imports` 6 contracts kept; `vulture` reports only unrelated pre-existing findings in `scripts/rag/ingestion/document_manager.py`, `scripts/shared/mcp_call_state_contract.py`, `scripts/shared/runtime_paths.py`; `bandit` pre-existing findings are outside the target files; `radon cc -n C` reported no block of complexity C or worse in the three core target files; the diff-cover baseline was not measured here (it needs the full coverage run) and the implementation phase records it under `rules/toolchain.md` section 7.

Decisions (each lists alternatives and compatibility impact):
- **D-1 Health token model (owner decision, 2026-11-26): keep one token.** The per-server `auth_token` is the health credential. Alternative: a distinct `health_auth_token` with secret registration, redaction, reload payload and server-side authentication (rejected: larger surface, no current need). Compatibility: none; no new config key. The existing `register_secret` of `auth_token` already covers redaction. Work reduces to one header helper and tests.
- **D-2 Registry change model (owner decision, 2026-11-26): restart required, no live swap.** Alternative: rebuild and atomically swap a candidate registry across `ToolExecutor`, `ToolRouteResolver`, and `ctx.services_required` (rejected: several holders of the reference, wide change). Atomicity is met by the existing single-rebinding of `self._tools` in `apply_policy` and by one publication at startup; `/mcp status` states that an availability change needs a restart.
- **D-3 Zero timeout.** `health_timeout` must be greater than 0 and the resolver returns a float. Alternative: keep zero as unlimited and cap it by the deadline (rejected: an unlimited probe contradicts the deadline rule and every consumer then needs a `None` branch). Compatibility: no `config/*.toml` sets the key, so no production config changes; tests asserting zero change.
- **D-4 Deadline cap.** Startup request timeout is `min(effective, remaining)`; post-startup checks have no lifecycle deadline and use the effective timeout only. Alternative: leave `min(effective, startup_timeout_sec)` (rejected: a request can still outlive the deadline).
- **D-5 Health contract location and shape.** A new `scripts/shared/mcp_health_contract.py` (shared is a leaf; `mcp_servers` must not import `agent`, `.importlinter`). Fields: `health_schema_version` (int, 1), `liveness`, `ready`, `degraded_reasons` (closed code list), `capabilities` (map of capability name to state `ok|degraded|unavailable` plus optional reason code). Existing keys stay; the new keys are additive. Alternative: put the DTO under `agent` (rejected: the servers produce it).
- **D-6 Legacy fallback and required versus optional.** A body without `capabilities` is legacy: every capability of that server is read as `ok` when `ready` is true and as unproven otherwise. The Agent derives required from the catalog `required_capability` of a `required=true` server; all other reported capabilities are optional. Servers report state only. Alternative: servers declare required-ness (rejected: it duplicates the catalog and the mandatoriness registry).
- **D-7 `config_dependent` field.** Added to `RuntimeTool` with default `False` and to `build_runtime_tool` as an optional keyword; discovery always passes the strictly validated producer value. Alternative: a required keyword with no default (rejected: it would force edits in 14 test files that construct tools directly, for a diagnostic-only field). The default applies only to non-discovery construction.
- **D-8 Optional capability exclusion point.** `McpToolDiscoveryService` passes the set of degraded capabilities per server to the registry, which drops dependent tools with reason `capability`, in the same construction step as the existing `unavailable` and `posture` exclusions. This keeps one publication and no mutation after construction.
- **D-9 Catalog load order.** Discovery loads `tool_catalog.toml` before building the registry (today it loads after, `mcp_tool_discovery.py:111-129`) so that capability dependencies are known at construction; a missing catalog stays FATAL.

Consumer scan (`tools/scan_change_consumers.py`, checked in Step 3): `get_effective_health_timeout` consumers are `mcp_status.py` and `mcp_tool_discovery_fetch.py` (targets) plus `tests/shared/test_mcp_config_validation.py` (target) and `tests/agent/services/test_agent_mcp_status.py` (target); `config_dependent` consumers are `cmd_mcp.py` and `runtime_tool_registry.py` (targets), the producer tool modules (`not affected: they already emit the field`), `tests/shared/test_tool_routing_validation.py:225` and `tests/agent/services/test_runtime_tool_routing_integration.py` (`not affected: assert existing rows with config_dependent False; revisit if the explicit field changes a row value`); `HEALTH_RECHECK_INTERVAL_SEC` and `MCPSERVER_HEALTH_TIMEOUT` consumers are `http_lifecycle.py` and `http_lifecycle_health_checker.py` (targets); ADR documents that cite these tests (`docs/10_adr/*`) are `not affected: cite test node ids that this Plan keeps`.

Predictable fallout check (checked in Step 3): module size gate 24576 B: `mcp_config.py` 19605 B, `http_lifecycle.py` 17851 B, `cmd_mcp.py` 15960 B, `mcp_health.py` 15157 B, `mcp_tool_discovery.py` 14858 B, `runtime_tool_registry.py` 12964 B are below the gate; the implementation phase re-checks `wc -c` after editing (the contract lives in a new module to avoid growing `mcp_health.py`). Pinned counts: no test pins a count of the changed lists found by this scan (`not affected`). Tool inventory: no `tools/*.py` added (`not affected`). Generated blocks: `docs/22_mcp` field tables may be generated; the implementation phase runs `uv run python tools/generate_reference_table.py --check`.

Persisted schema check: `not applicable` (no SQLite DDL, schema version, or migration).

## Implementation steps
1. **Phase 1: Shared health contract and producer (additive)**
   - [ ] Create the contract module with vocabularies, dataclass, and strict legacy-tolerant parser (REQ-004; scripts/shared/mcp_health_contract.py, tests/shared/test_mcp_health_contract.py)
   - [ ] Emit the new keys from `make_health_response()` and keep all existing keys (REQ-004; scripts/mcp_servers/health_response.py, tests/mcp_servers/test_health_response.py)
   - [ ] Read `dependencies` as a dict in `interpret_health_body()` through the contract (REQ-004; scripts/agent/shared/health_models.py, tests/agent/shared/test_mcp_health_interpretation.py)
2. **Phase 2: Per-server timeout, deadline cap, single auth path**
   - [ ] Reject `health_timeout <= 0` and make the resolver return a float; document the single-token model on `auth_headers()` (REQ-001, REQ-003; scripts/shared/mcp_config.py, tests/shared/test_mcp_config_validation.py)
   - [ ] Apply the per-server timeout and the remaining-deadline cap in the startup poll and the periodic check, and route auth through `auth_headers()` only (REQ-001, REQ-002, REQ-003; scripts/agent/http_lifecycle_health_checker.py, scripts/agent/http_lifecycle.py, tests/agent/test_http_lifecycle_health_check.py)
   - [ ] Apply the per-server timeout to post-startup verification, the readiness probe, and `/mcp status` (REQ-001; scripts/agent/startup_mcp_starter.py, scripts/agent/services/mcp_health.py, scripts/agent/services/mcp_status.py, tests/agent/test_startup_mcp_starter.py, tests/agent/test_repl_health.py, tests/agent/services/test_agent_mcp_status.py)
3. **Phase 3: Readiness and capability model**
   - [ ] Replace the `liveness`-only predicate with report-based readiness in the poll and post-startup verification (REQ-005; scripts/agent/http_lifecycle_health_checker.py, scripts/agent/startup_mcp_starter.py, tests/agent/test_http_lifecycle_health_check.py, tests/agent/test_startup_mcp_starter.py)
   - [ ] Carry the parsed report on `PostureGate` and classify capability loss (REQ-004, REQ-005; scripts/agent/services/mcp_health.py, tests/agent/test_mcp_health_posture.py)
   - [ ] Reconcile catalog identifiers and declare `github.api` (REQ-005, REQ-006; config/tool_catalog.toml)
   - [ ] Report GitHub token loss as the degraded optional capability (REQ-006; scripts/mcp_servers/github/github_server.py, tests/mcp_servers/github/test_github_health_posture.py)
   - [ ] Load the catalog before registry construction; prove the required capability from the report; pass degraded optional capabilities to the registry (REQ-005, REQ-006; scripts/agent/services/mcp_tool_discovery.py, scripts/agent/services/mcp_tool_discovery_registry.py, tests/agent/services/test_mcp_tool_discovery.py, tests/agent/services/test_mcp_tool_discovery_posture_gate.py)
4. **Phase 4: Explicit RuntimeTool metadata and registry rules**
   - [ ] Add `config_dependent` to `RuntimeTool` and `build_runtime_tool`; validate it strictly in the fetch layer and pass it through the registry builder (REQ-007; scripts/shared/runtime_tool.py, scripts/agent/services/mcp_tool_discovery_fetch.py, scripts/agent/services/mcp_tool_discovery_registry.py, tests/shared/test_runtime_tool.py)
   - [ ] Add exclusion reason `capability`, explicit diagnostics, and the immutability/restart-required note; test atomic policy application under concurrent reads (REQ-006, REQ-007, REQ-008; scripts/shared/runtime_tool_registry.py, tests/shared/test_runtime_tool_registry.py)
   - [ ] Render explicit metadata and the restart notice in `/mcp status` (REQ-007, REQ-008; scripts/agent/commands/cmd_mcp.py, tests/agent/commands/test_cmd_mcp.py)
5. **Phase 5: Documentation**
   - [ ] Update the MCP docs (REQ-009; docs/22_mcp/mcp_02_02_startup-modes-and-health.md, docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md, docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md, docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md, docs/22_mcp/mcp_06_14_mcp-authentication-setup.md, docs/22_mcp/mcp_08_tool_capability_naming_convention.md)
6. **Phase 6: Deployment & Verification**
   - [ ] Run `uv run python tools/run_validation_gates.py --full`, `lint-imports`, and the documentation gates; record the diff-cover number (REQ-001 to REQ-009; all rows)
   - [ ] Hand off to `skills/deploy/SKILL.md` once the change is committed and pushed; deploying is the user's decision and has an approval gate. `scripts/` is rsynced and `config/tool_catalog.toml` already exists, so `deploy.sh` needs no change; the deployed servers and the Agent restart together because the health contract is shared (REQ-004, REQ-008; config/tool_catalog.toml)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/mcp_health_contract.py | Unit: strict and legacy parse | `uv run pytest tests/shared/test_mcp_health_contract.py` | Pass |
| scripts/shared/mcp_config.py | Unit: timeout validation | `uv run pytest tests/shared/test_mcp_config_validation.py tests/shared/test_mcp_config.py` | Pass |
| scripts/agent/http_lifecycle_health_checker.py, scripts/agent/http_lifecycle.py | Unit and integration: timeout, deadline, auth, readiness | `uv run pytest tests/agent/test_http_lifecycle_health_check.py tests/agent/test_http_lifecycle_integration.py` | Pass |
| scripts/agent/startup_mcp_starter.py, scripts/agent/services/mcp_health.py, scripts/agent/services/mcp_status.py | Unit | `uv run pytest tests/agent/test_startup_mcp_starter.py tests/agent/test_repl_health.py tests/agent/test_mcp_health_posture.py tests/agent/services/test_agent_mcp_status.py` | Pass |
| scripts/agent/services/mcp_tool_discovery*.py, config/tool_catalog.toml | Unit: required proof, optional exclusion, strict field | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py tests/agent/services/test_mcp_tool_discovery_posture_gate.py` | Pass |
| scripts/shared/runtime_tool.py, scripts/shared/runtime_tool_registry.py, scripts/agent/commands/cmd_mcp.py | Unit: field, exclusion, concurrent reads, rendering | `uv run pytest tests/shared/test_runtime_tool.py tests/shared/test_runtime_tool_registry.py tests/agent/commands/test_cmd_mcp.py` | Pass |
| scripts/mcp_servers/health_response.py, scripts/mcp_servers/github/github_server.py | Unit | `uv run pytest tests/mcp_servers/test_health_response.py tests/mcp_servers/github/test_github_health_posture.py tests/mcp_servers/test_tool_schema.py` | Pass |
| All changed Python | Format, lint, type, architecture, security | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml` | No new finding |
| Full suite and coverage | Regression | `uv run python tools/run_validation_gates.py --full`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | Pass, changed-line coverage at or above 90% |
| docs/22_mcp files | Documentation consistency | `rules/tool-gates.md` "When to run which tool" checkers; `uv run python tools/generate_reference_table.py --check` | No finding |

## Risks
- **Risk**: A required server returns 503 with `ready=false` and no capability block, and the legacy fallback now blocks startup (likelihood: low-medium) → **Mitigation**: UNK-02 check during the implementation procedure; the legacy rule reads `ready` only, and a migrated capability block is the remedy; a staging start of every server before deploy.
- **Risk**: Rejecting `health_timeout = 0` breaks an operator config outside the repository (likelihood: low) → **Mitigation**: no repository config sets the key; the load error names the field and the accepted range; docs state the rule.
- **Risk**: Changing the shared health body breaks servers or the Agent when they are deployed out of step (likelihood: medium) → **Mitigation**: additive keys only, a version field, a legacy-tolerant parser, and one `deploy` of both sides.
- **Risk**: Adding `config_dependent` to a frozen dataclass with a default changes equality in tests that compare tools (likelihood: low) → **Mitigation**: the default keeps existing constructions valid; run the full suite.
- **Risk**: Excluding tools by capability hides tools without a visible reason (likelihood: medium) → **Mitigation**: `exclusion_reason` returns `capability` and `/mcp status` lists the excluded tools and the degraded capability reason code.
- **Risk**: `mcp_config.py` and `runtime_tool_registry.py` have high blast radius and churn (10 and 7 commits in 30 days) (likelihood: medium) → **Mitigation**: independently revertable phases, each with its tests; rebase before each phase.
- **Risk**: The startup order change (catalog before registry) alters the FATAL path when the catalog is missing (likelihood: low) → **Mitigation**: keep the existing FATAL message and add a test for the missing-catalog path.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Shared health contract and producer (additive) | Pending | — | — | |
| 2 | Per-server timeout, deadline cap, single auth path | Pending | — | — | |
| 3 | Readiness and capability model | Pending | — | — | |
| 4 | Explicit RuntimeTool metadata and registry rules | Pending | — | — | |
| 5 | Documentation | Pending | — | — | |
| 6 | Deployment & Verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-111451
- **Related target files**: scripts/shared/mcp_health_contract.py, scripts/shared/mcp_config.py, scripts/agent/http_lifecycle_health_checker.py, scripts/agent/http_lifecycle.py, scripts/agent/startup_mcp_starter.py, scripts/agent/services/mcp_health.py, scripts/agent/services/mcp_status.py, scripts/agent/shared/health_models.py, scripts/agent/services/mcp_tool_discovery.py, scripts/agent/services/mcp_tool_discovery_fetch.py, scripts/agent/services/mcp_tool_discovery_registry.py, scripts/shared/runtime_tool.py, scripts/shared/runtime_tool_registry.py, scripts/agent/commands/cmd_mcp.py, scripts/mcp_servers/health_response.py, scripts/mcp_servers/github/github_server.py, config/tool_catalog.toml, tests/shared/test_mcp_health_contract.py, tests/shared/test_mcp_config_validation.py, tests/agent/test_http_lifecycle_health_check.py, tests/agent/test_startup_mcp_starter.py, tests/agent/test_repl_health.py, tests/agent/test_mcp_health_posture.py, tests/agent/services/test_agent_mcp_status.py, tests/agent/shared/test_mcp_health_interpretation.py, tests/agent/services/test_mcp_tool_discovery.py, tests/agent/services/test_mcp_tool_discovery_posture_gate.py, tests/shared/test_runtime_tool.py, tests/shared/test_runtime_tool_registry.py, tests/agent/commands/test_cmd_mcp.py, tests/mcp_servers/test_health_response.py, tests/mcp_servers/github/test_github_health_posture.py, docs/22_mcp/mcp_02_02_startup-modes-and-health.md, docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md, docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md, docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md, docs/22_mcp/mcp_06_14_mcp-authentication-setup.md, docs/22_mcp/mcp_08_tool_capability_naming_convention.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; `mcp_config.py:281-298` | scripts/shared/mcp_config.py | Phase 2 | AC-01 | T-01 | Confirmed by repository evidence |
| REQ-001 | Required Changes bullet 1; `http_lifecycle.py:314` | scripts/agent/http_lifecycle.py | Phase 2 | AC-01 | T-01 | Confirmed by repository evidence |
| REQ-001 | Required Changes bullet 1; `startup_mcp_starter.py:150,238` | scripts/agent/startup_mcp_starter.py | Phase 2 | AC-01 | T-01 | Confirmed by repository evidence |
| REQ-001 | Required Changes bullet 1; `mcp_health.py:52,54` | scripts/agent/services/mcp_health.py | Phase 2 | AC-01 | T-01 | Confirmed by repository evidence |
| REQ-001 | Required Changes bullet 1; `mcp_status.py:104` | scripts/agent/services/mcp_status.py | Phase 2 | AC-01 | T-01 | Confirmed by repository evidence |
| REQ-002 | Required Changes bullet 1 (remaining lifecycle deadline); `http_lifecycle_health_checker.py:172-178` | scripts/agent/http_lifecycle_health_checker.py | Phase 2 | AC-02 | T-02 | Confirmed by repository evidence |
| REQ-003 | Required Changes bullet 1 (authentication model); `http_lifecycle_health_checker.py:264-268` | scripts/agent/http_lifecycle_health_checker.py | Phase 2 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Constraints (health tokens are secrets); owner decision D-1 | scripts/shared/mcp_config.py | Phase 2 | AC-03 | T-03 | Explicit in issue |
| REQ-004 | Required Changes bullet 2; `make_health_response()` keys | scripts/shared/mcp_health_contract.py | Phase 1 | AC-04 | T-04 | Derived from confirmed evidence |
| REQ-004 | Required Changes bullet 2; `health_response.py:31-65` | scripts/mcp_servers/health_response.py | Phase 1 | AC-04 | T-04 | Confirmed by repository evidence |
| REQ-004 | Evidence: `health_models.py:180` list cast of a dict body | scripts/agent/shared/health_models.py | Phase 1 | AC-04 | T-04 | Confirmed by repository evidence |
| REQ-005 | Required Changes bullet 2; `http_lifecycle_health_checker.py:104-126` | scripts/agent/http_lifecycle_health_checker.py | Phase 3 | AC-05 | T-05 | Confirmed by repository evidence |
| REQ-005 | Required Changes bullet 2; `startup_mcp_starter.py:153,212` | scripts/agent/startup_mcp_starter.py | Phase 3 | AC-05 | T-05 | Confirmed by repository evidence |
| REQ-005 | Required Changes bullets 2-3; `mcp_tool_discovery.py:260-328` | scripts/agent/services/mcp_tool_discovery.py | Phase 3 | AC-05 | T-05 | Confirmed by repository evidence |
| REQ-005 | Required Changes bullet 3; catalog header note | config/tool_catalog.toml | Phase 3 | AC-05 | T-05 | Confirmed by repository evidence |
| REQ-006 | Required Changes bullet 2; Testing Expectations (GitHub-token loss); `github_server.py:185-186` | scripts/mcp_servers/github/github_server.py | Phase 3 | AC-06 | T-06 | Confirmed by repository evidence |
| REQ-006 | Required Changes bullet 2 (disable only affected tools) | scripts/agent/services/mcp_tool_discovery_registry.py | Phase 3 | AC-06 | T-06 | Derived from confirmed evidence |
| REQ-006 | Required Changes bullet 2; `runtime_tool_registry.py:85-101` | scripts/shared/runtime_tool_registry.py | Phase 4 | AC-06 | T-06 | Confirmed by repository evidence |
| REQ-007 | Required Changes bullet 4; `runtime_tool_registry.py:281` | scripts/shared/runtime_tool.py | Phase 4 | AC-07 | T-07 | Confirmed by repository evidence |
| REQ-007 | Required Changes bullet 4 (parsed strictly from discovery); `mcp_tool_discovery_fetch.py:94-118` | scripts/agent/services/mcp_tool_discovery_fetch.py | Phase 4 | AC-07 | T-07 | Confirmed by repository evidence |
| REQ-007 | Required Changes bullet 4; `runtime_tool_registry.py:265-298` | scripts/shared/runtime_tool_registry.py | Phase 4 | AC-07 | T-07 | Confirmed by repository evidence |
| REQ-007 | Required Changes bullet 4 (generate `/mcp status` from explicit metadata); `cmd_mcp.py:167-185` | scripts/agent/commands/cmd_mcp.py | Phase 4 | AC-07 | T-07 | Confirmed by repository evidence |
| REQ-008 | Required Changes bullet 4 (atomic swap or restart); owner decision D-2; `runtime_tool_registry.py:248` | scripts/shared/runtime_tool_registry.py | Phase 4 | AC-08 | T-08 | Explicit in issue |
| REQ-008 | Required Changes bullet 4; owner decision D-2 | scripts/agent/commands/cmd_mcp.py | Phase 4 | AC-08 | T-08 | Explicit in issue |
| REQ-009 | Documentation Impact | docs/22_mcp/mcp_02_02_startup-modes-and-health.md | Phase 5 | AC-09 | T-09 | Explicit in issue |
| REQ-009 | Documentation Impact | docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md | Phase 5 | AC-09 | T-09 | Explicit in issue |
| REQ-009 | Documentation Impact | docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md | Phase 5 | AC-09 | T-09 | Explicit in issue |
| REQ-009 | Documentation Impact | docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md | Phase 5 | AC-09 | T-09 | Explicit in issue |
| REQ-009 | Documentation Impact | docs/22_mcp/mcp_06_14_mcp-authentication-setup.md | Phase 5 | AC-09 | T-09 | Explicit in issue |
| REQ-009 | Documentation Impact | docs/22_mcp/mcp_08_tool_capability_naming_convention.md | Phase 5 | AC-09 | T-09 | Explicit in issue |
