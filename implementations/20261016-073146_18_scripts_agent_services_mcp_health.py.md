## Goal

Classify MCP server failures by kind and gate Tool Discovery on a validated posture, so the Agent
stops treating a security-validation failure as an ordinary health warning (`REQ-013`, `REQ-014`,
`AC-007`).

## Scope

- One modified module `scripts/agent/services/mcp_health.py`:
  - add MCP-server posture collection and failure classification;
  - extend `check_service_health()` (`scripts/agent/services/mcp_health.py:70-107`) and
    `check_readiness()` (`:110-126`) so posture failures become pipeline fatals through the existing
    `readiness` source;
  - expose the set of server keys allowed to register tools, consumed by row `19`.
- No change to `scripts/agent/startup_validation.py` (row `22`) or
  `scripts/agent/services/mcp_tool_discovery.py`: the existing `readiness` step at
  `startup_validation.py:81-91` already maps a `check_readiness()` failure to a FATAL outcome.

## Assumptions

- Current module verified: `_probe_mcp_health_detail()` at `scripts/agent/services/mcp_health.py:24-67`
  (never raises; `reachable=False` on network failure at `:39-46`, `parse_failed=True` on JSON failure
  at `:47-58`); `check_service_health()` at `:70-107` (checks list at `:81-84`, required-failure to
  `errors` and optional-failure to `warnings` at `:100-106`); `check_readiness()` at `:110-126`
  (raises `RuntimeError` when `result.errors` is non-empty at `:118-126`).
- `ctx.services_required.http` is the shared probe client and is required (`:78-79`).
- The Agent knows every configured MCP server key and token presence without reading server configs:
  `ctx.cfg.mcp.mcp_servers` is already used by the `mcp_auth` check at
  `scripts/agent/startup_validation.py:70-81`.
- `McpStatusService` already probes each server and keeps the raw body
  (`scripts/agent/services/mcp_status.py:121`, `:156`); this row does not duplicate that status view.
- Issue `REQ-013` classification (`issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md:100-112`):
  an unreachable or unresponsive server is an Availability failure; a server that answers with a failed
  or unusable posture is a Safety/Integrity failure.
- `web_search` is gated in this row: rows `51` and `52` were added 2026-10-16 resolving Plan
  `UNK-04`, so web-search-mcp publishes a posture and a missing or invalid one is classified here like
  any other HTTP server's.

## Design decisions

- `ServerFailureClass` (new enum in this module) with `AVAILABILITY`, `SAFETY`, `INTEGRITY`. It lives
  here rather than in `agent/shared/health_models.py` because that file is not a row in the Plan's
  frozen table.
- `collect_server_postures(ctx: AgentContext) -> dict[str, PostureGate]` (new): for every HTTP
  transport server in `ctx.cfg.mcp.mcp_servers`, probe `/health` with `_probe_mcp_health_detail()`
  (`:24-67`) and validate the body with `parse_posture()` / `validate_posture()` (row `17`).
  `PostureGate` (new frozen dataclass) holds `server_key`, `required`, `reachable`,
  `posture_accepted`, `ready`, `validated`, `reason_code`.
- Classification rule (fixed order, first match wins):
  1. probe unreachable or body parse failure -> `AVAILABILITY`;
  2. posture rejected with `posture_missing` -> `INTEGRITY` (a server that answers without stating its
     security posture is not trusted);
  3. posture rejected with `contract_version_mismatch`, `check_set_mismatch`,
     `fingerprint_mismatch`, `server_key_mismatch`, or `config_invalid` -> `INTEGRITY`;
  4. posture accepted but `validated=false` -> `SAFETY`;
  5. posture accepted, `validated=true`, but `ready=false` -> `AVAILABILITY`;
  6. otherwise no failure.
- Required-versus-optional mapping reuses the existing shape: `required` servers contribute to
  `HealthCheckResult.errors`, optional ones to `warnings` (`:100-106`). A server is `required` when
  `ctx.cfg.mcp.mcp_servers[key]` is configured for Tool Call; **Needs confirmation**: whether the
  config model already carries a per-server `required` flag, otherwise every configured HTTP MCP
  server is treated as required, which is the fail-closed reading.
- `check_service_health()` appends the MCP posture results after the existing LLM/embed checks, so the
  existing `("llm", ..., True)` / `("embed-llm", ..., False)` behavior is untouched.
- `check_readiness()` keeps its single rule — raise when `result.errors` is non-empty (`:118-126`) —
  and its message gains the classification label and a remediation line, so the FATAL that
  `startup_validation.py:89-91` records is actionable without editing that file.
- `allowed_server_keys(gates: Mapping[str, PostureGate]) -> set[str]` (new): the keys whose gate has
  `reachable and posture_accepted and ready and validated`. It takes the gates `collect_server_postures()`
  produced rather than a context, so no consumer re-probes `/health`. Row `50`
  (`scripts/agent/services/mcp_tool_discovery.py`) passes the result to row `19`'s
  `RuntimeToolRegistry(allowed_servers=...)`, which is where `REQ-014`'s Tool Discovery and Tool Call
  gate is enforced.

## Alternatives considered

- Add a new `mcp_posture` source to `startup_validation.py` — rejected for this row: that file is row
  `22`'s target, and routing posture failures through the existing `readiness` source needs no edit
  there. Recorded as a follow-up if a separate severity row is wanted in the Readiness Summary.
- Classify a missing posture as `AVAILABILITY` because the server is clearly up — rejected: `REQ-013`
  treats an absent security statement as an Integrity failure, and treating it as Availability would
  let an un-migrated server keep serving tools.
- Gate Tool Discovery inside `mcp_tool_discovery.py` — rejected: that module is not a row in the Plan's
  frozen table, and gating at registration (row `19`) covers both discovery and call paths with one
  enforcement point.
- Reuse `McpStatusService` probes instead of probing here — rejected for the startup path:
  `McpStatusService` is the status/observability view (`mcp_status.py:59-162`) with its own reason
  derivation, and `check_readiness()` must decide startup outcomes from its own probe.

## Implementation
### Target file

`scripts/agent/services/mcp_health.py` (modify)

### Procedure

1. Import `parse_posture`, `validate_posture`, `PostureValidationResult` from
   `agent.services.posture_validator` (row `17`).
2. Add `ServerFailureClass` (new) and `PostureGate` (new).
3. Add `collect_server_postures()` (new) and `allowed_server_keys()` (new).
4. Extend `check_service_health()` to append posture-derived `ServiceWarning` entries, and extend
   `check_readiness()`'s error message with the classification label and remediation text.
5. Keep `_probe_mcp_health_detail()` unchanged.

### Method

- `collect_server_postures()` is the only place that decides a gate; `check_service_health()`,
  `check_readiness()`, and `allowed_server_keys()` all read gates produced by it, so the three
  consumers cannot disagree.
- Probing reuses `ctx.services_required.http` and `_probe_mcp_health_detail()`'s 5.0 s timeout
  (`:36-38`); no new timeout or client is created.
- `ServiceWarning.label` becomes `mcp:{server_key}` for posture entries, so the existing
  `warning_messages()` / `error_messages()` formatting (`:119`) stays readable and tests can select
  entries by label.
- Messages carry server key, class, and reason code only. Posture fingerprints and server-supplied
  check messages are never copied into Agent messages.

### Details

- The module is 126 lines; the addition is roughly 90 lines. If the file would exceed the 200-line
  convention, `ServerFailureClass` and `PostureGate` move to a new sibling module
  `scripts/agent/services/mcp_posture_gate.py`. **Needs confirmation**: the Plan's frozen table names
  only `mcp_health.py`, so a sibling module requires a Plan amendment.
- `check_service_health()` raises `RuntimeError("http service not initialized")` when
  `ctx.services_required.http is None` (`:78-79`); posture collection must run after that guard so it
  cannot hit a `None` client.
- Tests that patch `agent.services.mcp_health.check_readiness`
  (`tests/agent/shared/test_startup_validation_pipeline.py:133-137` and siblings) keep working because
  the function name and signature are unchanged.
- `scripts/agent/repl_health.py` is coverage-excluded (`pyproject.toml:153`); `mcp_health.py` is not,
  so the new branches need test coverage to satisfy the repository's diff-coverage gate.

## Compatibility considerations

- `check_service_health()` and `check_readiness()` keep their names, signatures, and return types, so
  `startup_validation.py:81-91`, `tests/agent/test_repl_health.py` (`TestCheckServiceHealth` at
  `:289-367`, `TestCheckReadiness` at `:860-918`), and `tests/agent/test_startup_severity_classification.py`
  (`readiness` cases at `:206-245`) keep compiling.
- Behavior change: a configured MCP server that answers with a failed or missing posture now produces a
  FATAL `readiness` outcome instead of starting normally. This is the intended `REQ-013` change and is
  the highest-risk behavioral change in the Plan.
- `tests/agent/test_repl_health.py`'s `TestProbeMcpHealthDetail` cases (`:46-127`) are unaffected
  because `_probe_mcp_health_detail()` is unchanged.
- No `docs/*.md` change is in scope for this row; the severity-mapping table in
  `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` is a follow-up.

## Security considerations

- `REQ-013` / Plan `INV-06`: security-posture failures are Safety/Integrity failures, not warnings.
- `REQ-014`: Tool Discovery and Tool Call are reachable only for servers whose gate is fully green, and
  the gate is computed from the posture, not from a server's self-reported `status` string.
- Fail-closed default: an unknown classification path yields a failure, never a pass.

## Rollback considerations

- Revert this commit together with row `19` (which consumes `allowed_server_keys()`) and row `17`
  (which this row imports). Reverting row `18` alone restores today's behavior: posture data is
  published by servers but not consumed by the Agent.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Unreachable server | `uv run pytest tests/agent/test_mcp_health_posture.py` (new test file) | class `AVAILABILITY`; optional server produces a warning, required server an error |
| Missing posture block | same new test file | class `INTEGRITY` and reason `posture_missing` |
| Failed posture | same new test file | class `SAFETY` and `check_readiness()` raises |
| Contract mismatch | same new test file | class `INTEGRITY` |
| Gate set | same new test file | `allowed_server_keys()` excludes every server with a non-green gate |
| Existing readiness suite | `uv run pytest tests/agent/test_repl_health.py tests/agent/test_startup.py` | `TestCheckServiceHealth` and `TestCheckReadiness` assertions unchanged |
| Severity classification | `uv run pytest tests/agent/test_startup_severity_classification.py` | `readiness` FATAL/WARNING cases still produce their documented severities |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-007`: Availability failures and Safety/Integrity failures are classified differently, and a
  Safety/Integrity failure aborts startup.
- `allowed_server_keys()` returns only servers with a fully green gate, and row `19` enforces it.
- No posture fingerprint or server-supplied message text is copied into Agent messages or logs.

## Out of scope

- Registry registration gating (row `19`), posture parsing (row `17`).
- Editing `startup_validation.py` (row `22`) or `mcp_tool_discovery.py`.
- Adding the `web_search` self-validation rows (`51`, `52`) — resolved 2026-10-16 (Plan `UNK-04`).
- `docs/*.md` updates.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `ServerFailureClass` and `PostureGate` | Pending | — | — | depends on row `17` |
| 2 | Implement `collect_server_postures()` and `allowed_server_keys()` | Pending | — | — | per-server `required` flag is Needs-confirmation |
| 3 | Extend `check_service_health()` and `check_readiness()` | Pending | — | — | highest blast radius change |
| 4 | Add `tests/agent/test_mcp_health_posture.py` | Pending | — | — | |
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
- **Requirement ID**: `REQ-013` (failure classification), `REQ-014` (Tool Discovery and Tool Call gating)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/agent/services/mcp_health.py`
