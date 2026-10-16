## Goal

Pass the posture-derived server allowlist into the only production `RuntimeToolRegistry` construction site,
so a server whose Security Posture the Agent did not accept contributes no tool to Tool Discovery or Tool
Call (`REQ-014`, `AC-008`).

## Scope

- One modified module `scripts/agent/services/mcp_tool_discovery.py`: accept posture gates, reduce them to
  a server-key allowlist, and pass that allowlist to `RuntimeToolRegistry`.
- This row adds no gate logic of its own: the gate decision is row `18` (`collect_server_postures()`,
  `allowed_server_keys()`), the exclusion rule is row `19` (`RuntimeToolRegistry`), the posture contract is
  row `03`, and the production caller that supplies the gates is row `22`
  (`scripts/agent/startup_validation.py:100`).
- One new test file `tests/agent/services/test_mcp_tool_discovery_posture_gate.py`.
- `scripts/shared/runtime_tool_registry.py`, `scripts/agent/services/mcp_health.py`, and
  `scripts/agent/startup_validation.py` are rows `19`, `18`, and `22`; none is modified here.

## Assumptions

- Verified current source: `class McpToolDiscoveryService` at `:293` with
  `def __init__(self, ctx: AgentContext) -> None:` at `:296`, `async def discover_all()` at `:299`, the
  HTTP-transport filter at `:305-306` (`cfg.transport != TransportType.HTTP or not cfg.url or
  cfg.is_disabled`), `unavailable_keys = frozenset(unreachable)` at `:328`,
  `self._dedupe_and_build(entries, unavailable_keys)` at `:329`, `_dedupe_and_build()` at `:404-425` which
  calls `self._build_runtime_tools(unique_entries, unavailable_servers)` at `:423`, and
  `_build_runtime_tools()` at `:377-402` which skips `unavailable_servers` at `:385-386` and ends with
  `return RuntimeToolRegistry(tools=built)` at `:402`.
- `scripts/agent/startup_validation.py:100` is the only production construction site of
  `McpToolDiscoveryService` (verified: every other call site is under `tests/`).
- A server that refuses to bind because its own posture failed (rows `42`-`49`) is already excluded here
  through the existing unreachable path (`:310-313`, `:328`, `:385-386`). This row's gate covers the
  remaining case: a server that answers `/v1/tools` while publishing a posture the Agent rejected, which
  is the state during the Shadow Validation window (row `16`) and for any server whose bind gate has not
  landed yet.
- `tests/agent/services/test_mcp_tool_discovery.py` mocks `httpx.AsyncClient` with `AsyncMock` and canned
  `/v1/tools` bodies (2218 lines, e.g. `:120`, `:159`, `:199`). Those mocks return no `security` body, so
  this row must not probe `/health` inside `discover_all()`; gates arrive only from the caller.
- `_dedupe_and_build()` and `_build_runtime_tools()` are private and are not called from any test or other
  module (verified by search over `scripts/` and `tests/`), so adding a keyword parameter to each is
  contained.

## Design decisions

- Add one keyword parameter to `__init__`: `posture_gates: Mapping[str, PostureGate] | None = None`.
  `None` means "no posture gate supplied", which preserves today's behavior for every existing call site,
  including all 2218 lines of `tests/agent/services/test_mcp_tool_discovery.py`.
- Reduce gates to plain keys inside `discover_all()`:
  `allowed_servers = None if self._posture_gates is None else frozenset(allowed_server_keys(self._posture_gates))`.
  The registry then receives a `frozenset[str]` (row `19`), so no `shared.security` DTO crosses into
  `scripts/shared/` and the import-layer contract in `skills/DESIGN.md` Shared Vocabulary is untouched.
- Thread `allowed_servers` through `_dedupe_and_build()` and `_build_runtime_tools()` as a keyword
  parameter, mirroring how `unavailable_servers` already travels, and pass it at `:402` as
  `RuntimeToolRegistry(tools=built, allowed_servers=allowed_servers)`.
- Do not probe `/health` in this module: `collect_server_postures()` (row `18`) is the only prober, and
  calling it here would add a second probe pass per discovery and would make every existing discovery
  test depend on posture bodies.
- Keep `unavailable_servers` and the posture gate as separate inputs. Reusing `unavailable_servers` would
  erase the Availability-versus-Safety/Integrity distinction `REQ-013` requires and would make
  `startup_reporter.py:94-114`'s "Unreachable servers" line report posture failures as outages.
- This row adds no new `StartupCheckOutcome` findings. Posture failures are already reported by row `18` as
  `ServiceWarning` entries routed through the `readiness` source, and row `19` logs the posture-excluded
  keys at registry construction. Adding a third copy here would give one failure three messages.
- Resolved 2026-10-17 (user decision): `posture_gates=None` stays a permitted migration-window value after
  rows `42`-`49` and `52` land. Row `22` pins the production wiring with its own test so the only
  production caller always passes gates; `None` remains valid for tests and for callers that deliberately
  opt out.
- Resolved 2026-10-17 (user decision): `ready` stays in the tool-gate predicate. `allowed_server_keys()`
  requires `reachable`, `posture_accepted`, `ready`, and `validated`, so a serving-but-degraded server
  loses its tools. This is the fail-closed reading, and it matches row `18`'s already-implemented and
  already-tested behavior.
- Resolved 2026-10-17 (user decision, row `19`): reason codes do not reach registry diagnostics; this row
  passes `frozenset[str]` only. Reason codes already reach the Agent through row `18`'s `ServiceWarning`
  message.
- Resolved 2026-10-17 (row `18` decision): `PostureGate` and `ServerFailureClass` stay in
  `agent.services.mcp_health`; the sibling `mcp_posture_gate.py` was not created, so this import is final.
- Resolved 2026-10-17: this module logs and reports nothing new, per `Method` above. Runtime re-gating
  stays out of scope and is recorded as an open item in row `19`.

## Alternatives considered

- Gate inside `McpToolDiscoveryService` by filtering its `built` dict before constructing the registry —
  rejected: the registry is the authority every consumer reads, and row `19`'s exclusion predicate is the
  single place that decides exclusion.
- Call `collect_server_postures(ctx)` inside `discover_all()` — rejected: it breaks every existing
  discovery test (their mocked bodies carry no posture) and doubles startup probing. Recorded as a
  Needs-confirmation alternative for row `22`, which is the row that decides where gates are collected.
- Store gates on `AgentContext` so discovery can read them without a parameter — rejected:
  `scripts/agent/context.py` is not a row in the Plan's frozen table.
- Read gates from the `HealthCheckResult` that `check_readiness()` returns — rejected for this row:
  `check_readiness()`
  raises when posture errors exist (`agent/services/mcp_health.py:118-126`), and the discovery step still
  runs after that `except` (`startup_validation.py:91-92`); the gate must exist on exactly that failure
  path. Row `22` collects gates directly for this reason.
- Raise when gates are missing — rejected: `None` is the documented migration-window value while rows
  `42`-`49` and `52` land server by server; making it fatal would break startup before every server publishes a
  posture.

## Implementation
### Target file

`scripts/agent/services/mcp_tool_discovery.py` (modify)

### Procedure

1. Import `PostureGate`, `collect_server_postures`, and `allowed_server_keys` from
   `agent.services.mcp_health` (row `18`). `collect_server_postures` is imported only if row `22`'s
   collection moves here; the default design imports `PostureGate` and `allowed_server_keys` only.
2. Add the `posture_gates` keyword parameter to `__init__` (`:296`) and store it as `self._posture_gates`.
3. In `discover_all()`, compute `allowed_servers` from `self._posture_gates` and pass it to
   `_dedupe_and_build(entries, unavailable_keys, allowed_servers=allowed_servers)` (`:329`).
4. Add the matching keyword parameter to `_dedupe_and_build()` (`:404-407`) and forward it to
   `_build_runtime_tools()` (`:423`).
5. Add the matching keyword parameter to `_build_runtime_tools()` (`:377-380`) and change `:402` to
   `return RuntimeToolRegistry(tools=built, allowed_servers=allowed_servers)`.
6. Keep `_detect_duplicates()`, `ToolEntryValidator`, `_check_required_tools()`, `_build_drift_findings()`,
   `_build_write_classification_findings()`, `_check_tool_definitions_finding()`, and `DiscoveryResult`
   unchanged.
7. Add `tests/agent/services/test_mcp_tool_discovery_posture_gate.py`.

### Method

- `allowed_servers` is `frozenset[str] | None` at every hop; never a `dict` of gates, never a posture
  object.
- `frozenset()` (empty) is a valid value and means "no server is allowed": the registry then registers no
  MCP tool. That is the fail-closed reading row `19` documents.
- The gate is applied at construction only. There is no re-gating of an already-built registry, and
  `ToolExecutor` routing (`scripts/shared/tool_executor.py:64-65`) keeps reading the registry as today.
- Log nothing new in this module: row `19` already logs the posture-excluded keys, and this module's
  findings are schema, duplication, drift, and availability findings.

### Details

- `PostureGate` is imported for the type annotation only, alongside `allowed_server_keys` which is called
  at runtime. Row `18` kept both `PostureGate` and `ServerFailureClass` in `mcp_health.py`, so this import
  is final.
- Import contract: `agent.services` may import `agent.services` and `shared`; `mcp_tool_discovery.py`
  already imports `shared.runtime_tool_registry` and `agent.*`, so no `.importlinter` contract change is
  needed (row `25`).
- `_check_required_tools()` (`:331`) runs after the registry is built. When a posture-gated server provides
  a tool listed in the required-tool set, the Agent now reports both the posture error (row `18`,
  `readiness` source) and the missing-required-tool FATAL from this module. That double reporting is
  intended: one names the cause, the other names the consequence.
- Verified during implementation: this module constructs the registry as `RuntimeToolRegistry(tools=built,
  allowed_servers=allowed_servers)` and never passes `unavailable_servers`, so
  `registry.unavailable_servers` is already empty in production today and `DiscoveryResult.unreachable` is
  the value that carries unreachable servers. The gate does not change either; posture-excluded servers
  appear only in `registry.posture_excluded_servers`.
- The module is about 570 lines, far above the 200-line convention. The roughly 15 added lines stay in
  this file; do not split it as a side effect of this row.

## Compatibility considerations

- Additive and default-off: with `posture_gates=None` the produced registry is identical to today's, so
  `tests/agent/services/test_mcp_tool_discovery.py`,
  `tests/agent/services/test_runtime_tool_routing_integration.py:313,347`, and
  `tests/integration/test_production_security_regression.py:204,245` keep passing unchanged.
- Behavior change once row `22` passes gates: tools from a server whose gate is not
  `reachable and posture_accepted and ready and validated` are absent from the registry, so the LLM tool
  list shrinks and `route_resolver.py:72-77` raises `ValueError` for a call to such a tool instead of
  dispatching it.
- `DiscoveryResult.unreachable` and `registry.unavailable_servers` keep reporting only unreachable servers;
  posture-excluded servers appear in `registry.posture_excluded_servers` (row `19`).
- No `docs/*.md` edit is in scope for this row; `docs/23_agent/agent_06_*` tool-routing docs and
  `docs/23_agent/agent_08_04_*` classification table are Plan follow-ups.

## Security considerations

- `REQ-014` / Plan `INV-06`: no Tool Discovery or Tool Call for a server whose posture is missing,
  unsupported, mismatched, or `validated=false`.
- Fail-closed default inside the registry: `allowed_servers=frozenset()` registers nothing (row `19`).
  `None` is the only permissive value, and it exists solely for the migration window.
- `REQ-004`: nothing in this row logs posture bodies, fingerprints, or check messages; only server keys
  appear, and row `19`'s log line is the only new output.
- The gate is startup-time only. A server whose posture changes after startup is not re-gated here
  (ADR-003 Static Availability); **Needs confirmation**: whether the project wants runtime re-gating,
  which row `19` records as out of scope.

## Rollback considerations

- Revert this commit together with rows `18` (gate producer), `19` (registry parameter), and `22` (the
  caller that passes gates). Reverting this row alone restores today's registry construction even if gates
  are still collected.
- No config or data migration is involved.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Default off | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py` | all existing tests pass unchanged, no posture probing |
| Gate excludes a server | `uv run pytest tests/agent/services/test_mcp_tool_discovery_posture_gate.py` (new test file) | with a gate whose `validated` is false, that server's tools are absent and `registry.posture_excluded_servers` names the key |
| Empty allowlist | same new test file | `allowed_server_keys()` returning an empty set yields a registry with no MCP tool |
| Required-tool interaction | same new test file | a required tool supplied only by a posture-rejected server produces both the row `18` posture error and this module's missing-required-tool FATAL |
| Integration suites | `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py tests/integration/test_production_security_regression.py` | pass |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-008`: no tool from a server with `ready=false` or `validated=false` is discoverable or callable.
- Plan `AC-007`: the gate decision exists in one place (row `18`) and the exclusion decision in one place
  (row `19`); this file only transports keys between them.

## Out of scope

- Deciding which servers are allowed (row `18`).
- The exclusion predicate and `posture_excluded_servers` reporting (row `19`).
- Collecting gates and passing them at `startup_validation.py:100` (row `22`).
- Reporting posture-excluded servers in the Readiness Summary (row `23`).
- Runtime re-gating or Hot Rediscovery.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `posture_gates` parameter to `__init__` | Completed | 20261016-153329 | 20261016-153329 | row `18` landed; keyword-only default `None` keeps every existing call site |
| 2 | Thread `allowed_servers` through `_dedupe_and_build()` and `_build_runtime_tools()` | Completed | 20261016-153329 | 20261016-153329 | both are private and have no external callers; docstrings record that this module transports the gate |
| 3 | Pass `allowed_servers` at `:402` | Completed | 20261016-153329 | 20261016-153329 | now `:436`; `frozenset(allowed_server_keys(gates))` when gates are supplied, `None` otherwise |
| 4 | Add `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` | Completed | 20261016-153329 | 20261016-153329 | 11 tests in 4 classes; see Blocker Log for the frozen-table question |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-153329 | 20261016-153329 | ruff clean, mypy 425 files clean, lint-imports "Contracts: 6 kept, 0 broken", 11 new tests plus `tests/agent/services/` and `tests/shared/` 1349 passed; full suite deferred to the end of the batch per the standing decision |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | New test files are not rows in the Plan's frozen table; the Plan must be amended or the assertions added to `tests/agent/services/test_mcp_tool_discovery.py` | Yes | 20261016 |

Resolution: the frozen table lists modification targets, and this row's target is
`scripts/agent/services/mcp_tool_discovery.py`; a test file the row itself creates is part of that row's
test procedure, not a separate modification target. Rows `16`, `17`, and `18` of this Plan already created
new test files the same way. Appending a table row for every new test file would also contradict the
append-only amendment rule, which exists to keep existing ordinals stable.

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-014` (Tool Discovery and Tool Call gating)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/agent/services/mcp_tool_discovery.py`, `scripts/agent/services/mcp_health.py`, `scripts/shared/runtime_tool_registry.py`, `scripts/agent/startup_validation.py`, `scripts/shared/security/posture_contract.py`
