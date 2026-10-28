## Goal
- Make the MCP execution path fully wired by construction (health registry required, runtime registry settable only to a real registry, posture allowlist required at registry building) and give routing failures one documented `ToolCallResult` contract.

## Priority
Medium

## Scope
- **In-Scope**:
  - Require `allowed_servers` in the registry builder functions of `scripts/agent/services/mcp_tool_discovery_registry.py`; an empty set stays fail-closed.
  - Make the health registry a required constructor input of `ToolTransportInvoker` / `ToolExecutor`; remove the `None` state and its guards.
  - Reject `None` in `ToolExecutor.set_runtime_registry()` / `ToolRouteResolver.set_runtime_registry()`.
  - Normalize routing failures (registry not ready, unknown tool, posture-excluded, server unavailable at discovery) into `ToolCallResult` at `ToolExecutor.execute()`, keeping the resolver's `ValueError` behavior.
  - Remove the resolver `strict_mode` and `warn_on_missing` options, which differ only in message wording or logging.
  - Update tests and the MCP routing and diagnosis docs.
- **Out-of-Scope**: the Health type re-export and the `posture_gates=None` default of `McpToolDiscoveryService` (mcpcompat001); legacy `resource_scope` handling (mcpcompat003); per-server concurrency defaults (mcpinv004); the dead startup-mode guard (mcpinv002); making the `RuntimeToolRegistry` constructor's `allowed_servers` required (UNK-02); changes to `UNAVAILABLE` / `HALF_OPEN` handling.
- **Dependencies**: Implement after the mcpcompat001, mcpinv002 and mcpinv004 work, whose implementation procedures are still `Pending` under `implementations/` (for example `implementations/20261028-013216_06_scripts_agent_services_mcp_tool_discovery.py.md` and `implementations/20261028-004831_02_scripts_shared_tool_executor.py.md`): they edit `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py` and the discovery side of the posture gate. Their Plans are consumed (`plans/done/20261027-115908_mcpcompat001_remove-mcp-compat-paths.md`, `plans/done/20261027-103047_mcpinv002_remove-dead-check-startup-mode-guard.md`, `plans/done/20261027-104612_mcpinv004_unbounded-per-server-concurrency-default.md`); rebase this Plan's procedures on whatever they have landed.

## Background
`ToolExecutor` builds its `ToolRouteResolver` with no registry and receives the `RuntimeToolRegistry` later through `set_runtime_registry()` from `scripts/agent/startup_validation.py`, because discovery needs the application context that already holds the executor. The health registry is created in `scripts/agent/factory.py` right after the executor and attached with `set_health_registry()`. `ToolTransportInvoker` skips every health gate and record when its registry is `None`.

## Problem
- The health registry is optional: when it is `None` the dynamic `UNAVAILABLE` / `HALF_OPEN` gating is silently skipped. Production wires it immediately, so this is a test-only state that the code still permits.
- `set_runtime_registry()` is typed to take a registry but `ToolRouteResolver.set_runtime_registry()` accepts `None` and the resolver's constructor allows it, so the not-ready state is indistinguishable from an unknown tool.
- Registry building takes `allowed_servers=None`, which means "no posture gate".
- `ToolExecutor.execute()` does not normalize resolver failures: the `ValueError` propagates and is converted only by the per-call boundary in `scripts/agent/tool_runner.py`. Other callers of `execute()` receive the exception.
- Tools of unavailable, disabled or posture-excluded servers are dropped at registry construction, so `resolve()` returns `None` for them exactly as for an unknown name.

## Reason for Change
Security-relevant gating should not depend on startup order or on a `None` default. Production wires everything correctly today, so the priority is Medium; the change removes unreachable permissive states and makes the failure contract explicit.

## Implementation Intent
Construct an executable stack only with its health registry; keep the runtime registry as a setter because it cannot exist at construction, but make the unwired state explicit and fail-closed. Keep the resolver raising `ValueError` (ADR-003 INV-02) through a subclass that carries a failure kind, and convert it to a documented `ToolCallResult` at the executor boundary.

## Requirements
- `REQ-001`: `_build_runtime_tools()` and `_dedupe_and_build()` take `allowed_servers: frozenset[str]` as a required argument; an empty set registers nothing.
- `REQ-002`: `RuntimeToolRegistry` records, for every tool it drops, the exclusion reason (`unavailable`, `disabled`, `posture`) and exposes a lookup by tool name; resolution behavior and the constructor signature stay unchanged.
- `REQ-003`: `ToolRouteResolver` raises `ToolRoutingError`, a `ValueError` subclass with a `kind` of `not_ready`, `unknown_tool`, `posture_excluded` or `server_unavailable`; `set_runtime_registry(None)` raises `TypeError`; the `strict_mode` and `warn_on_missing` options are removed.
- `REQ-004`: `ToolExecutor.execute()` returns a `ToolCallResult` with `is_error=True`, `error_type="routing"` and an output that starts with `routing:<kind>:` for each `ToolRoutingError`; no other `ToolCallResult` field changes. Dynamic `UNAVAILABLE` / `HALF_OPEN` results keep their existing form.
- `REQ-005`: `ToolTransportInvoker` and `ToolExecutor` require `health_registry: McpServerHealthRegistry` at construction; the `None` branches and `set_health_registry()` are removed; `scripts/agent/factory.py` builds the registry before the executor and passes it.
- `REQ-006`: The dead `discovery.registry is not None` guard in `scripts/agent/startup_validation.py` is removed (`DiscoveryResult.registry` is not optional), and the `tool_runner.py` comments that describe the `ValueError` path match the new contract.
- `REQ-007`: Tests cover each routing failure kind, the not-ready state, and still cover `UNAVAILABLE`, `HALF_OPEN` and the release of a cancelled `HALF_OPEN` trial.
- `REQ-008`: The MCP dispatch and diagnosis docs describe the mandatory wiring order and the routing error contract and no longer present optional wiring as current behavior; ADR-003 is not edited (INV-02 still holds).

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/services/mcp_tool_discovery_registry.py` | Registry builder | Make `allowed_servers` required in `_build_runtime_tools` and `_dedupe_and_build` | REQ-001 / AC-1 | Both functions declare `allowed_servers: frozenset[str] \| None = None`; the docstring says `None` registers every tool (checked in Step 3) | `tests/agent/services/test_mcp_tool_discovery.py` | Verified |
| `scripts/shared/runtime_tool_registry.py` | Exclusion bookkeeping | Record the exclusion reason per dropped tool and add a lookup | REQ-002 / AC-2 | The constructor loop skips excluded tools (`_is_excluded_server`) and keeps only `_posture_excluded` server keys; `resolve()` returns `None` for any missing name (checked in Step 3) | `tests/shared/test_runtime_tool_registry.py` | Verified |
| `scripts/shared/route_resolver.py` | Routing resolver | Add `ToolRoutingError` with kinds; reject `None` in the setter; remove `strict_mode` and `warn_on_missing` | REQ-003 / AC-2, AC-3 | Both modes always raise `ValueError` and differ only in wording (module and class docstrings); `set_runtime_registry` accepts `None` (checked in Step 3) | `tests/shared/test_route_resolver.py` | Verified |
| `scripts/shared/tool_executor.py` | Executor | Convert `ToolRoutingError` to `ToolCallResult`; take `health_registry`; reject `None` in `set_runtime_registry` | REQ-003, REQ-004, REQ-005 / AC-2, AC-3, AC-4 | `_raw_execute` calls `self._resolver.resolve()` with no handler; `__init__` creates `ToolRouteResolver()` with no registry (checked in Step 3) | `tests/shared/test_tool_executor.py`, `tests/shared/test_tool_executor_routing.py` | Verified |
| `scripts/shared/tool_transport_invoker.py` | Invoker | Require `health_registry`; remove the `None` guards and `set_health_registry` | REQ-005, REQ-007 / AC-4, AC-5 | `self._health_registry: McpServerHealthRegistry \| None = None`; `_check_health`, `_record_success`, `_record_transport_error`, `_handle_lifecycle_error` and `_run_precall_gates` branch on `None` (checked in Step 3) | `tests/shared/test_tool_transport_invoker.py`, `tests/shared/test_tool_transport_invoker_merge.py` | Verified |
| `scripts/shared/transport_dto.py` | Result DTO | Document `error_type="routing"` in the field comment; no field change | REQ-004 / AC-3 | `error_type` is commented as `"transport" \| "tool" \| ""` (checked in Step 3) | `tests/shared/test_tool_executor_routing.py` | Verified |
| `scripts/agent/factory.py` | Executor construction | Create the health registry first and pass it to `ToolExecutor` | REQ-005 / AC-4 | `_build_tool_executor` builds `ToolExecutor(...)` then `McpServerHealthRegistry()` then `tools.set_health_registry(registry)`; it is the only production constructor (checked in Step 3) | `tests/agent/test_agent_factory.py` | Verified |
| `scripts/agent/startup_validation.py` | Discovery wiring | Remove the dead `registry is not None` guard around `set_runtime_registry` | REQ-006 / AC-5 | `DiscoveryResult.registry: RuntimeToolRegistry` is not optional; the guard wraps the only production `set_runtime_registry` call (checked in Step 3) | `tests/agent/services/test_runtime_tool_routing_integration.py` | Verified |
| `scripts/agent/tool_runner.py` | Runner comments | Align the comments that say an unregistered tool raises `ValueError` | REQ-006 / AC-5 | `_execute_prepared_call` docstring and inline note describe the `ValueError` guard and the `strict_mode` wording (checked in Step 3) | `tests/shared/test_tool_executor_routing.py` | Verified |
| `tests/shared/test_route_resolver.py` | Resolver tests | Drop mode tests; add kind and `None` rejection tests | REQ-003, REQ-007 / AC-2, AC-3 | `ToolRouteResolver(runtime_registry=...)` cases with `pytest.raises(ValueError, match="Unknown tool")` and a `RuntimeToolRegistry` message case (checked in Step 3) | itself | Verified |
| `tests/shared/test_runtime_tool_registry.py` | Registry tests | Add exclusion reason tests | REQ-002, REQ-007 / AC-2 | The file already tests posture exclusion at construction (checked in Step 3) | itself | Verified |
| `tests/shared/test_tool_executor.py` | Executor tests | Pass `health_registry` at construction; add routing result tests | REQ-004, REQ-005, REQ-007 / AC-3, AC-4 | `ToolExecutor(` constructed in 2 places and `set_health_registry(` called in many tests (checked in Step 3) | itself | Verified |
| `tests/shared/test_tool_executor_routing.py` | Routing tests | Pass `health_registry`; assert the four failure kinds | REQ-004, REQ-007 / AC-3 | `ToolExecutor(` constructed in 5 places (checked in Step 3) | itself | Verified |
| `tests/shared/test_tool_transport_invoker.py` | Invoker tests | Pass `health_registry` at construction | REQ-005 / AC-4 | One `ToolTransportInvoker(` construction (checked in Step 3) | itself | Verified |
| `tests/shared/test_tool_transport_invoker_merge.py` | Invoker merge tests | Pass `health_registry` at construction | REQ-005 / AC-4 | One construction (checked in Step 3) | itself | Verified |
| `tests/agent/services/test_runtime_tool_routing_integration.py` | Routing integration tests | Remove `strict_mode`/`warn_on_missing` cases; pass `health_registry` (no builder call exists in this file, only a comment) | REQ-003, REQ-005 / AC-2, AC-4 | `ToolRouteResolver(strict_mode=True ...)` and `warn_on_missing=True` cases and a `ToolExecutor(` construction; the only builder mention is a comment (re-checked in the procedure step: `_build_runtime_tools` / `_dedupe_and_build` calls are in `test_mcp_tool_discovery.py`) | itself | Verified |
| `tests/agent/services/test_mcp_tool_discovery.py` | Discovery tests | Pass `allowed_servers` to builder calls | REQ-001 / AC-1 | References `_build_runtime_tools` / `_dedupe_and_build` (checked in Step 3) | itself | Verified |
| `tests/agent/test_agent_factory.py` | Factory test | Replace the `set_health_registry` assertion with a constructor-argument assertion | REQ-005 / AC-4 | Asserts `tool_executor_instance.set_health_registry.assert_called_once()` (checked in Step 3) | itself | Verified |
| `tests/integration/test_agent_mcp_integration.py` | Integration test | Construct the executor with a health registry | REQ-005 / AC-4 | One `ToolExecutor(` construction and `executor.set_health_registry(health)` (checked in Step 3) | itself | Verified |
| `tests/integration/test_mcp_transport_crash.py` | Integration test | Construct the executor with a health registry | REQ-005 / AC-4 | One `ToolExecutor(` construction (checked in Step 3) | itself | Verified |
| `tests/integration/test_robustness_chaos.py` | Integration test | Construct executors with a health registry | REQ-005 / AC-4 | Six `ToolExecutor(` constructions (checked in Step 3) | itself | Verified |
| `tests/integration/test_rag_turn_integration.py` | Integration test | Construct the executor with a health registry | REQ-005 / AC-4 | One `ToolExecutor(` construction (checked in Step 3) | itself | Verified |
| `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Dispatch doc | Describe the wiring order and the routing error contract | REQ-008 / AC-6 | Describes the missing-registry failure mode as "Unknown tool" errors and the health gate (checked in Step 3) | `tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/22_mcp/mcp_06_07_mcp-failure-diagnosis.md` | Diagnosis doc | Replace the `ValueError` explanation with the result kinds | REQ-008 / AC-6 | Section "LLM sees a tool but execution fails with Unknown tool" says the error originates from `resolve()` raising `ValueError` and lists "set_runtime_registry() was not called" (checked in Step 3) | `tools/check_docs_consistency.py --domain mcp` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/services/mcp_tool_discovery.py` | `DiscoveryResult.registry` is non-optional; the service passes `allowed_servers` to the builder | REQ-001, REQ-006 |
| `scripts/agent/services/mcp_health.py` | Produces the posture gate set passed to the builder | REQ-001 |
| `scripts/shared/mcp_health.py` | `McpServerHealthRegistry` type and `UNAVAILABLE` / `HALF_OPEN` behavior | REQ-005, REQ-007 |
| `scripts/agent/repository_gateway.py` | A caller of `execute()` that does not catch exceptions | REQ-004 |
| `scripts/agent/tool_approval.py` | A caller of `execute()` for dry-run previews | REQ-004 |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | INV-02 requires `resolve()` to raise `ValueError`; not edited | REQ-003, REQ-008 |

## Acceptance Criteria
- AC-1 (REQ-001): The builder functions cannot be called without `allowed_servers`; an empty set registers no tools.
- AC-2 (REQ-002, REQ-003): The registry reports the exclusion reason for a dropped tool; the resolver raises `ToolRoutingError` (a `ValueError`) with the right kind for not-ready, unknown, posture-excluded and server-unavailable names; `set_runtime_registry(None)` raises `TypeError`.
- AC-3 (REQ-004): `ToolExecutor.execute()` returns the documented `routing` result for each kind and does not execute the tool; before `set_runtime_registry()` it returns the `not_ready` result.
- AC-4 (REQ-005): No `ToolExecutor` or `ToolTransportInvoker` can be constructed without a health registry; the factory passes it.
- AC-5 (REQ-006, REQ-007): `UNAVAILABLE`, `HALF_OPEN` and cancelled-trial regression tests pass; the dead guard and stale comments are gone.
- AC-6 (REQ-008): The MCP docs describe the wiring order and the result kinds; `tools/check_docs_consistency.py --domain mcp` passes.

## Tests
- Resolver: each `kind`, `None` rejection, `ValueError` compatibility (REQ-003, REQ-007).
- Registry: exclusion reason for unavailable, disabled and posture exclusions (REQ-002).
- Executor: not-ready before wiring, unknown, posture-excluded, server-unavailable results; no transport call occurs (REQ-004, REQ-007).
- Construction: health registry required; factory passes it (REQ-005).
- Regression: existing `UNAVAILABLE`, `HALF_OPEN` and cancelled `HALF_OPEN` trial tests stay green unchanged except for construction (REQ-007).
- Builder: required `allowed_servers`, empty set fail-closed (REQ-001).
- Run `uv run pytest tests/shared tests/agent tests/integration -q`, mypy, ruff, `PYTHONPATH=scripts uv run lint-imports`.

## Documentation Impact
Yes (REQ-008): the MCP dispatch and failure-diagnosis docs under `docs/22_mcp/` found through `docs/00_index.md` "Document References by Task". ADR-003 states INV-02 and the registry authority and is not edited. ADR-004 was not located by filename pattern; UNK-03 covers it. State current behavior only.

## Assumptions
- The open dependency on the mcpcompat001, mcpinv002 and mcpinv004 implementations is an ordering constraint, not a reason this Plan cannot be written: the dependency is stated in `Scope` and re-checked by `plan-to-implementation-procedure`, so UNK-01 is non-blocking.
- Keeping `ToolRoutingError` a `ValueError` subclass preserves ADR-003 INV-02 and the existing `pytest.raises(ValueError)` tests.
- `error_type="routing"` is an added documented kind; the `ToolCallResult` fields are unchanged.
- Overlap judgment (compatible): `plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md` also targets `tests/shared/test_runtime_tool_registry.py`; it only changes which builder the existing calls use, while this Plan adds exclusion-reason tests.
- Callers that previously caught `ValueError` from `execute()`: none found in `scripts/` (the per-call boundary in `tool_runner.py` catches `Exception` broadly).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Final shape of `tool_executor.py` and `tool_transport_invoker.py` after the pending mcpinv004 / mcpinv002 / mcpcompat001 implementations | Those procedures are `Pending` | Re-read both files when generating this Plan's procedures; ordering is in `Scope` Dependencies | False |
| UNK-02 | Whether `RuntimeToolRegistry.__init__` should also require `allowed_servers` | 35 test construction sites in 12 test files would change; the Issue names the builder | Follow-up Issue if the owner wants the constructor stricter | False |
| UNK-03 | Whether ADR-004 or other ADR text presents optional wiring as current behavior | ADR-004 file not located by filename pattern; ADR-003 has no such text | Search `docs/10_adr/` for `set_runtime_registry` and optional wiring wording during procedure generation; edit only Implementation Notes and run `tools/check_adr_preservation.py` | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/services/mcp_tool_discovery_registry.py` | Modify | Low | 1 | High (single author) | not applicable (rsynced) |
| `scripts/shared/runtime_tool_registry.py` | Modify | Medium | 2 | N/A | not applicable (rsynced) |
| `scripts/shared/route_resolver.py` | Modify | Medium | 1 | N/A | not applicable (rsynced) |
| `scripts/shared/tool_executor.py` | Modify | High | 1 | N/A | not applicable (rsynced) |
| `scripts/shared/tool_transport_invoker.py` | Modify | High | 4 | N/A | not applicable (rsynced) |
| `scripts/shared/transport_dto.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/agent/factory.py` | Modify | Medium | 5 | N/A | not applicable (rsynced) |
| `scripts/agent/startup_validation.py` | Modify | Medium | 5 | N/A | not applicable (rsynced) |
| `scripts/agent/tool_runner.py` | Modify | Low | 8 | N/A | not applicable (rsynced) |
| `tests/shared/test_route_resolver.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_runtime_tool_registry.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_tool_executor.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_tool_executor_routing.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_tool_transport_invoker.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_tool_transport_invoker_merge.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/services/test_runtime_tool_routing_integration.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/services/test_mcp_tool_discovery.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_agent_factory.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/integration/test_agent_mcp_integration.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/integration/test_mcp_transport_crash.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/integration/test_robustness_chaos.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/integration/test_rag_turn_integration.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_06_07_mcp-failure-diagnosis.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Path B (more than 3 files; changes a public executor construction contract and result contract). `shared` is a leaf package (see the registry docstring), so `ToolRoutingError` and the exclusion bookkeeping live in `shared` and `agent` imports them; `lint-imports` kept all 6 contracts earlier in this batch and must be re-run after the change. Callers: `ToolExecutor(` has one production construction (`scripts/agent/factory.py`) and nine test files; `RuntimeToolRegistry(` has 2 production and 35 test construction sites, which this Plan leaves unchanged.
- Decision 1, health registry: required constructor argument instead of a validated setter, because the registry can exist before the executor (the factory already creates it unconditionally). The lifecycle setter is untouched.
- Decision 2, runtime registry: keep the setter (the registry needs discovery, which needs the application context that already holds the executor), reject `None`, and make the unwired state the explicit `not_ready` kind that fails closed.
- Decision 3, error contract: the resolver keeps raising a `ValueError` subclass (ADR-003 INV-02); `ToolExecutor.execute()` converts it to `ToolCallResult(error_type="routing", output="routing:<kind>: ...")`. The four kinds are `not_ready`, `unknown_tool`, `posture_excluded`, `server_unavailable`; dynamic `UNAVAILABLE` / `HALF_OPEN` keep their existing result.
- Decision 4, distinguishing exclusions: dropped tools are remembered by name with a reason inside `RuntimeToolRegistry`; resolution still returns `None` for them, so no behavior changes for existing callers.
- Decision 5, resolver modes: `strict_mode` and `warn_on_missing` are removed; the failure message is a single wording per kind and the log line is emitted by the executor.

## Implementation steps
1. **Phase 1: Registry and resolver**
   - [ ] Record exclusion reasons in the registry and add the lookup (REQ-002; `scripts/shared/runtime_tool_registry.py`, `tests/shared/test_runtime_tool_registry.py`)
   - [ ] Add `ToolRoutingError`, reject `None`, remove the modes (REQ-003; `scripts/shared/route_resolver.py`, `tests/shared/test_route_resolver.py`)
   - [ ] Require `allowed_servers` in the builder functions (REQ-001; `scripts/agent/services/mcp_tool_discovery_registry.py`, `tests/agent/services/test_mcp_tool_discovery.py`)
2. **Phase 2: Executor and invoker**
   - [ ] Require `health_registry`, remove the `None` branches and the setter (REQ-005; `scripts/shared/tool_transport_invoker.py`, `tests/shared/test_tool_transport_invoker.py`, `tests/shared/test_tool_transport_invoker_merge.py`)
   - [ ] Convert routing failures to results and reject `None` in `set_runtime_registry` (REQ-003, REQ-004; `scripts/shared/tool_executor.py`, `scripts/shared/transport_dto.py`, `tests/shared/test_tool_executor.py`, `tests/shared/test_tool_executor_routing.py`)
3. **Phase 3: Wiring and callers**
   - [ ] Build the health registry before the executor and drop the dead guard and stale comments (REQ-005, REQ-006; `scripts/agent/factory.py`, `scripts/agent/startup_validation.py`, `scripts/agent/tool_runner.py`, `tests/agent/test_agent_factory.py`, `tests/agent/services/test_runtime_tool_routing_integration.py`)
   - [ ] Update the integration tests that construct executors (REQ-005, REQ-007; `tests/integration/test_agent_mcp_integration.py`, `tests/integration/test_mcp_transport_crash.py`, `tests/integration/test_robustness_chaos.py`, `tests/integration/test_rag_turn_integration.py`)
4. **Phase 4: Documentation**
   - [ ] Document the wiring order and result kinds (REQ-008; `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`, `docs/22_mcp/mcp_06_07_mcp-failure-diagnosis.md`)
5. **Phase 5: Deployment & Verification**
   - [ ] Run the validation plan; after commit and push, hand off to `skills/deploy/SKILL.md` (the user decides to deploy) because `scripts/` changes; confirm agent startup reaches `mcp_tool_discovery` OK (REQ-005; `scripts/agent/factory.py`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/route_resolver.py`, `scripts/shared/runtime_tool_registry.py` | Unit | `uv run pytest tests/shared/test_route_resolver.py tests/shared/test_runtime_tool_registry.py -q` | All pass |
| `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py` | Unit incl. `UNAVAILABLE` / `HALF_OPEN` regression | `uv run pytest tests/shared -q` | All pass |
| `scripts/agent/factory.py`, `scripts/agent/startup_validation.py`, builder | Unit and integration | `uv run pytest tests/agent tests/integration -q` | All pass |
| Architecture | Import contracts | `PYTHONPATH=scripts uv run lint-imports` | All contracts kept |
| Static | Lint, types, security | `uv run ruff check scripts/ tests/`; `uv run mypy --no-namespace-packages scripts/`; `uv run bandit -r scripts/ -c pyproject.toml` | Clean |
| Module size | Gate | `uv run python tools/check_module_size.py` | Exit 0 |
| Coverage | Baseline then raise | diff-cover sequence in `rules/toolchain.md` section 7 | At or above the Completion checklist threshold |
| Docs | Checkers | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_consistency.py --domain mcp` | No errors |

Baseline recorded in Step 5: `radon cc` reports `ToolTransportInvoker._run_precall_gates` C (11) and `StartupValidationPipeline.check_services` D (24) among the touched modules; `vulture scripts/ --min-confidence 80` earlier in this batch listed no finding in the touched modules; `bandit -r scripts/` reported no Medium or High finding.

## Risks
- **Risk**: Removing `set_health_registry` and requiring the constructor argument breaks nine test files and one mock-based factory test → **Mitigation**: change them in the same phase, using a shared `McpServerHealthRegistry()` per test, and run `uv run pytest tests/shared tests/agent tests/integration` before moving on.
- **Risk**: The pending mcpinv004 / mcpinv002 / mcpcompat001 implementations edit the same files → **Mitigation**: implement after them and re-read both executor files first (UNK-01).
- **Risk**: A caller starts to see `ToolCallResult` where it used to see `ValueError` → **Mitigation**: no caller catches `ValueError` from `execute()` today; the per-call boundary in `tool_runner.py` handles both forms.
- **Risk**: `error_type="routing"` is unknown to a consumer that switches on `"transport"` / `"tool"` → **Mitigation**: grep consumers of `error_type` in the procedure step and document the new kind in the DTO comment and the MCP docs.
- **Risk**: Posture-excluded and unavailable tools are now reported by name, which could reveal a server's exclusion to the LLM → **Mitigation**: the message names only the kind and the tool, not the server configuration.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Registry exclusion reasons, resolver error kinds, required `allowed_servers` | In Progress | — | — |  |
| 2 | Required health registry and routing-result conversion in the invoker and executor | In Progress | — | — |  |
| 3 | Factory, startup validation, runner comments and caller tests | In Progress | — | — |  |
| 4 | MCP dispatch and diagnosis docs | In Progress | — | — |  |
| 5 | Deployment and verification hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261028-115653_01_scripts_agent_services_mcp_tool_discovery_registry.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-115653_02_scripts_shared_runtime_tool_registry.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-115653_03_scripts_shared_route_resolver.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-115653_04_scripts_shared_tool_executor.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-115653_05_scripts_shared_tool_transport_invoker.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-115653_06_scripts_shared_transport_dto.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-115653_07_scripts_agent_factory.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-115653_08_scripts_agent_startup_validation.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-115653_09_scripts_agent_tool_runner.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-115653_10_tests_shared_test_route_resolver.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-115653_11_tests_shared_test_runtime_tool_registry.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-115653_12_tests_shared_test_tool_executor.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-115653_13_tests_shared_test_tool_executor_routing.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-115653_14_tests_shared_test_tool_transport_invoker.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-115653_15_tests_shared_test_tool_transport_invoker_merge.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-115653_16_tests_agent_services_test_runtime_tool_routing_integration.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-115653_17_tests_agent_services_test_mcp_tool_discovery.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-115653_18_tests_agent_test_agent_factory.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-115653_19_tests_integration_test_agent_mcp_integration.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-115653_20_tests_integration_test_mcp_transport_crash.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-115653_21_tests_integration_test_robustness_chaos.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-115653_22_tests_integration_test_rag_turn_integration.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-115653_23_docs_22_mcp_mcp_03_01_dispatch-and-routing.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261028-115653_24_docs_22_mcp_mcp_06_07_mcp-failure-diagnosis.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-093529
- **Related target files**: `scripts/agent/services/mcp_tool_discovery_registry.py`, `scripts/shared/runtime_tool_registry.py`, `scripts/shared/route_resolver.py`, `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py`, `scripts/shared/transport_dto.py`, `scripts/agent/factory.py`, `scripts/agent/startup_validation.py`, `scripts/agent/tool_runner.py`, `tests/shared/test_route_resolver.py`, `tests/shared/test_runtime_tool_registry.py`, `tests/shared/test_tool_executor.py`, `tests/shared/test_tool_executor_routing.py`, `tests/shared/test_tool_transport_invoker.py`, `tests/shared/test_tool_transport_invoker_merge.py`, `tests/agent/services/test_runtime_tool_routing_integration.py`, `tests/agent/services/test_mcp_tool_discovery.py`, `tests/agent/test_agent_factory.py`, `tests/integration/test_agent_mcp_integration.py`, `tests/integration/test_mcp_transport_crash.py`, `tests/integration/test_robustness_chaos.py`, `tests/integration/test_rag_turn_integration.py`, `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`, `docs/22_mcp/mcp_06_07_mcp-failure-diagnosis.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; builder defaults `allowed_servers=None` | `scripts/agent/services/mcp_tool_discovery_registry.py` | Step 1 | AC-1 | `tests/agent/services/test_mcp_tool_discovery.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1 | `tests/agent/services/test_mcp_tool_discovery.py` | Step 1 | AC-1 | `uv run pytest tests/agent -q` | Confirmed by repository evidence |
| REQ-005 | Required Changes 2; one `ToolExecutor(` construction in the file | `tests/agent/services/test_runtime_tool_routing_integration.py` | Step 3 | AC-4 | `uv run pytest tests/agent -q` | Confirmed by repository evidence |
| REQ-002 | Required Changes 3; excluded tools collapse into unknown | `scripts/shared/runtime_tool_registry.py` | Step 1 | AC-2 | `tests/shared/test_runtime_tool_registry.py` | Derived from confirmed evidence |
| REQ-002 | Required Changes 3 | `tests/shared/test_runtime_tool_registry.py` | Step 1 | AC-2 | `uv run pytest tests/shared -q` | Derived from confirmed evidence |
| REQ-003 | Required Changes 2 and 4; resolver modes differ only in wording | `scripts/shared/route_resolver.py` | Step 1 | AC-2 | `tests/shared/test_route_resolver.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 2 and 4 | `tests/shared/test_route_resolver.py` | Step 1 | AC-2 | `uv run pytest tests/shared -q` | Confirmed by repository evidence |
| REQ-003 | Required Changes 2 | `scripts/shared/tool_executor.py` | Step 2 | AC-2 | `tests/shared/test_tool_executor_routing.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 4 | `tests/agent/services/test_runtime_tool_routing_integration.py` | Step 3 | AC-2 | `uv run pytest tests/agent -q` | Confirmed by repository evidence |
| REQ-004 | Required Changes 3; `execute()` lets `ValueError` propagate | `scripts/shared/tool_executor.py` | Step 2 | AC-3 | `tests/shared/test_tool_executor_routing.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes 3 | `scripts/shared/transport_dto.py` | Step 2 | AC-3 | `tests/shared/test_tool_executor_routing.py` | Derived from confirmed evidence |
| REQ-004 | Required Changes 3 | `tests/shared/test_tool_executor.py` | Step 2 | AC-3 | `uv run pytest tests/shared -q` | Confirmed by repository evidence |
| REQ-004 | Required Changes 3 | `tests/shared/test_tool_executor_routing.py` | Step 2 | AC-3 | `uv run pytest tests/shared -q` | Confirmed by repository evidence |
| REQ-005 | Required Changes 2; `_health_registry` defaults to `None` | `scripts/shared/tool_transport_invoker.py` | Step 2 | AC-4 | `tests/shared/test_tool_transport_invoker.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes 2 | `scripts/shared/tool_executor.py` | Step 2 | AC-4 | `tests/shared/test_tool_executor.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes 2; factory wires after construction | `scripts/agent/factory.py` | Step 3 | AC-4 | `tests/agent/test_agent_factory.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes 2 | `tests/shared/test_tool_transport_invoker.py` | Step 2 | AC-4 | `uv run pytest tests/shared -q` | Confirmed by repository evidence |
| REQ-005 | Required Changes 2 | `tests/shared/test_tool_transport_invoker_merge.py` | Step 2 | AC-4 | `uv run pytest tests/shared -q` | Confirmed by repository evidence |
| REQ-005 | Required Changes 2 | `tests/agent/test_agent_factory.py` | Step 3 | AC-4 | `uv run pytest tests/agent -q` | Confirmed by repository evidence |
| REQ-005 | Required Changes 2 | `tests/integration/test_agent_mcp_integration.py` | Step 3 | AC-4 | `uv run pytest tests/integration -q` | Confirmed by repository evidence |
| REQ-005 | Required Changes 2 | `tests/integration/test_mcp_transport_crash.py` | Step 3 | AC-4 | `uv run pytest tests/integration -q` | Confirmed by repository evidence |
| REQ-005 | Required Changes 2 | `tests/integration/test_robustness_chaos.py` | Step 3 | AC-4 | `uv run pytest tests/integration -q` | Confirmed by repository evidence |
| REQ-005 | Required Changes 2 | `tests/integration/test_rag_turn_integration.py` | Step 3 | AC-4 | `uv run pytest tests/integration -q` | Confirmed by repository evidence |
| REQ-006 | Implementation Intent; `DiscoveryResult.registry` is non-optional | `scripts/agent/startup_validation.py` | Step 3 | AC-5 | `tests/agent/services/test_runtime_tool_routing_integration.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes 5; `tool_runner.py` comments describe the `ValueError` path | `scripts/agent/tool_runner.py` | Step 3 | AC-5 | `uv run pytest tests/agent -q` | Confirmed by repository evidence |
| REQ-007 | Testing Expectations; Constraints | `tests/shared/test_tool_transport_invoker.py` | Step 2 | AC-5 | `uv run pytest tests/shared -q` | Explicit in issue |
| REQ-008 | Documentation Impact; MCP docs describe missing-registry "Unknown tool" | `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Step 4 | AC-6 | `tools/check_docs_consistency.py --domain mcp` | Explicit in issue |
| REQ-008 | Documentation Impact; diagnosis doc cites `ValueError` | `docs/22_mcp/mcp_06_07_mcp-failure-diagnosis.md` | Step 4 | AC-6 | `tools/check_docs_consistency.py --domain mcp` | Explicit in issue |