## Goal

Gate `RuntimeToolRegistry` registration on a validated posture, so a tool from an MCP server whose
posture is missing, rejected, or failed can never be discovered or called (`REQ-014`, `AC-007`).

## Scope

- One modified module `scripts/shared/runtime_tool_registry.py`: add a posture-gate input to the
  registry constructor and extend the existing exclusion rule to consult it.
- The gate value is produced by row `18` (`allowed_server_keys()` in
  `scripts/agent/services/mcp_health.py`) and passed by row `50`
  (`scripts/agent/services/mcp_tool_discovery.py:402`), the only production construction site.

## Assumptions

- Current module verified: `RuntimeToolRegistry` at
  `scripts/shared/runtime_tool_registry.py:33`, `__init__(tools, unavailable_servers, server_configs)`
  at `:40-53` (constructor-time filtering at `:49-53`), `_is_excluded_server()` at `:55-65` (excludes
  `unavailable_servers` members and configs with `is_disabled`), `unavailable_servers` property at
  `:67-70`, `resolve()` at `:72-80` (unknown names return `None`), `get()` at `:82-91` (raises
  `KeyError` for unregistered tools), `all_tools()` at `:94`, `llm_tool_definitions()` at `:98-113`,
  `apply_policy()` at `:153-183`, `diagnostics()` at `:185-218`.
- There is no `register()` method: population happens only in `__init__`, so registration gating is
  constructor gating.
- Production construction: `scripts/agent/services/mcp_tool_discovery.py:402`
  (`RuntimeToolRegistry(tools=built)`), reached from `scripts/agent/startup_validation.py:100-103`,
  which stores the registry in `ctx.services_required.runtime_tools` and wires it into
  `ToolExecutor.set_runtime_registry()`.
- Downstream consumers treat a missing registry entry as "no route":
  `scripts/shared/route_resolver.py:59-84` raises `ValueError` when the registry has no entry
  (`:72-77`), and `scripts/shared/tool_executor.py:64-65` is the wiring point.
- `startup_reporter.py:94-114` already reports `runtime_tools.unavailable_servers`.
- Import contract: `shared` is a leaf (`.importlinter:19-28`), and the module docstring at `:12-16`
  records that `apply_policy()` takes duck-typed primitives instead of Agent config types for exactly
  this reason. The posture gate must therefore arrive as plain primitives.

## Design decisions

- Add one keyword parameter to `__init__`: `allowed_servers: frozenset[str] | None = None`.
  `None` means "no posture gate supplied", which preserves today's behavior for every existing call
  site. A provided frozenset is authoritative: a `server_key` not in it is excluded.
- Extend `_is_excluded_server()` with one rule, evaluated after the existing two: when
  `allowed_servers is not None` and `server_key not in allowed_servers`, the server is excluded.
  Keeping the new rule inside the existing predicate means one place decides exclusion, and the
  constructor's existing filter loop (`:49-53`) needs no change.
- `allowed_servers=frozenset()` excludes every tool. That is the fail-closed reading and is the
  intended behavior when the Agent cannot validate a posture: no MCP tool is registered.
- Add `posture_excluded_servers` (new property) returning the keys excluded by the posture rule,
  distinct from `unavailable_servers` (`:67-70`). The two exclusion causes must stay separable:
  `REQ-013` classifies them differently, and `startup_reporter.py:94-114` reports only unreachable
  servers today.
- The gate is a `frozenset[str]` of server keys, not posture objects: `shared` must not import
  `shared.security` DTOs here just to filter a key, and row `18` already reduces the posture to a
  gate decision. **Needs confirmation**: whether the project wants the reason codes to reach
  diagnostics too, which would require passing a mapping instead of a set.
- Log one warning line at construction naming the excluded keys (`RuntimeToolRegistry: posture-excluded
  servers: git, cicd`). Server keys are not secrets and are already logged elsewhere
  (`startup_reporter.py:112-114`); no posture field or fingerprint is logged.

## Alternatives considered

- Add a `register(tool)` method and gate there — rejected: no caller registers tools one at a time
  today, so a new public method would add an API surface with no user.
- Gate in `ToolRouteResolver.resolve()` or `ToolExecutor` instead — rejected: those are the routing and
  execution layers, and `ADR-003` Decision #8 makes `RuntimeToolRegistry` the sole routing authority;
  leaving an ungated registry populated would let `agent/tool_policy.classify_operation_type()` and the
  scheduler still see the tool.
- Gate inside `McpToolDiscoveryService` by filtering its `built` dict — rejected: that would make the
  gate a discovery-only concern, while the registry is the authority every consumer reads. Recorded as
  row `50`, which only passes the gate in.
- Reuse `unavailable_servers` to carry posture failures — rejected: it would erase the
  Availability-versus-Safety/Integrity distinction `REQ-013` requires and would make
  `startup_reporter.py`'s "Unreachable servers" line lie.

## Implementation
### Target file

`scripts/shared/runtime_tool_registry.py` (modify)

### Procedure

1. Add `allowed_servers: frozenset[str] | None = None` to `__init__` (`:40-45`) and store it.
2. Extend `_is_excluded_server()` (`:55-65`) with the posture rule and record posture exclusions in a
   `self._posture_excluded: set[str]` as tools are filtered.
3. Add the `posture_excluded_servers` property returning `frozenset(self._posture_excluded)`.
4. Keep `resolve()`, `get()`, `all_tools()`, `llm_tool_definitions()`, `tool_spec_map()`,
   `tool_spec_for_call()`, `apply_policy()`, and `diagnostics()` unchanged.

### Method

- Exclusion is recorded during construction rather than recomputed later, so the reported set is
  exactly the set that was dropped.
- `diagnostics()` (`:185-218`) is left alone: it describes registered tools, and a posture-excluded
  tool is not registered, so it cannot appear there. The new property is the observability surface.
- The gate is read once at construction. A posture that changes after startup does not retroactively
  remove tools; re-running discovery is the documented way to re-evaluate. **Needs confirmation**:
  whether a runtime re-gate is required, which is a separate design question outside this Plan.

### Details

- The module is 218 lines; the addition is roughly 20 lines.
- `server_configs` (`:44`, `:62-64`) stays as the `is_disabled` source; the posture gate does not
  replace a deliberately disabled server, and a disabled server is excluded before the gate is
  consulted.
- Existing tests construct the registry with 1-3 positional/keyword arguments
  (`tests/shared/test_runtime_tool_registry.py:21`, `:250-290`, `tests/shared/test_tool_routing_validation.py:14`);
  the new parameter is keyword-only in practice because it is added last, so all of them keep working.

## Compatibility considerations

- Additive and default-off: `mcp_tool_discovery.py:402` and every test construction keep their current
  behavior until row `50` passes `allowed_servers`.
- Behavior change once row `50` lands: tools from a server with a non-green gate are absent from the
  registry, so `resolve()` returns `None` (`:72-80`), `get()` raises `KeyError` (`:91`), and
  `route_resolver.py:72-77` raises `ValueError` for a call attempt. That is the Tool Call gate.
- `llm_tool_definitions()` (`:98-113`) stops offering gated tools to the LLM, which is the Tool
  Discovery half of `REQ-014`.
- No `docs/*.md` change is in scope for this row; `docs/23_agent/agent_06_*` tool-routing docs are a
  follow-up.

## Security considerations

- `REQ-014` / Plan `INV-06`: registration is the enforcement point, so a gated server's tools are
  unavailable to discovery, routing, scheduling, and risk classification at once.
- Fail-closed by default when a gate is supplied: unknown server keys are excluded, not allowed.
- The gate stays `None` only when a caller explicitly declines to gate (tests, and any construction
  site not yet migrated), which is why row `50` is required for the production path.

## Rollback considerations

- Revert this commit together with row `50`, which is the only production caller that supplies a gate.
  Reverting row `19` alone leaves row `50`'s argument unmatched and fails at import/call time, so the
  two must move together.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Gate excludes a server | `uv run pytest tests/shared/test_runtime_tool_registry.py` | tools from a key absent from `allowed_servers` are not registered, and `posture_excluded_servers` names that key |
| Empty gate excludes everything | same existing test file (new cases) | `all_tools()` is empty and `resolve()` returns `None` for every name |
| No gate supplied keeps behavior | same existing test file | `allowed_servers=None` registers every tool as today |
| Causes stay separable | same existing test file | an unavailable server appears in `unavailable_servers` and not in `posture_excluded_servers` |
| Routing gate | `uv run pytest tests/shared/test_route_resolver.py tests/shared/test_tool_executor_routing.py` | a gated tool raises `ValueError` / returns no route |
| Existing registry suite | `uv run pytest tests/shared/test_runtime_tool_registry.py` | passes, `apply_policy()` and `diagnostics()` assertions unchanged |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean, no `shared -> agent` import introduced |

## Completion criteria

- Plan `AC-007` for `REQ-014`: a tool from a server without a validated posture is neither offered to
  the LLM nor routable.
- Posture exclusions and availability exclusions are separately observable.
- No construction site changes behavior before row `50` lands.

## Out of scope

- Producing the gate (row `18`) and passing it at the discovery call site (row `50`).
- Runtime re-gating after startup.
- Changing `apply_policy()`, `diagnostics()`, or routing behavior.
- `docs/*.md` updates.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `allowed_servers` and extend `_is_excluded_server()` | Pending | — | — | depends on row `18` gate |
| 2 | Add `posture_excluded_servers` property | Pending | — | — | |
| 3 | Extend `tests/shared/test_runtime_tool_registry.py` | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-014` (Tool Discovery and Tool Call gating)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/shared/runtime_tool_registry.py`
