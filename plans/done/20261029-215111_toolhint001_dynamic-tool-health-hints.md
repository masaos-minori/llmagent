## Goal
- Give the LLM and operators an advisory dynamic tool-availability hint (normalized reason, circuit state, optional `retry_after_seconds`) and bound repeated selection of the same unavailable tool in the turn loop, while `RuntimeToolRegistry` remains the sole routing authority and static LLM tool visibility never changes.

## Priority
Medium

## Scope
- **In-Scope**:
  - Advisory hint contract (normalized reason, circuit state, optional `retry_after_seconds`) carried on structured tool results, not on `RuntimeTool` static fields.
  - `ToolLoopGuard` bound for repeated selection of the same unavailable tool (reusing the existing empty-result repeat settings).
  - Hint removal after health recovery.
  - Diagnostics displaying static availability and dynamic health separately.
  - Prompt-cache/context-size impact measurement, recorded before the hint is widened.
  - Tests asserting dynamic health never mutates routing ownership or static visibility.
- **Out-of-Scope**:
  - Changing circuit-breaker thresholds or the half-open policy.
  - Making dynamic health a routing input or removing unavailable tools from the LLM tool list.
  - Unrelated refactoring or formatting-only changes.
- **Dependencies**:
  - Related: `mcpgate001` (construction-time health/posture gating) and `toolexec001` (generation identifiers); the issue states no ordering is required and re-verification confirms no in-flight `implementations/` procedure targets any file in this plan's table (active procedures cover tests/eventbus and mdq files only).
  - After `adrauth001` lands, ADR-003's advisory-hint wording must remain consistent with the ADR-016 authority matrix (matrix records ADR-003 as primary for routing/visibility/health already; no matrix change needed unless wording conflicts).

## Background
Verified against current source (2026-10-29): ADR-003 explicitly separates static availability from dynamic health ("Dynamic Health state must not automatically change LLM visibility"; `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`). `scripts/shared/mcp_health.py` holds `McpServerHealthRegistry` with states `HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN/UNKNOWN`, failure threshold 3, half-open cooldown 30s, and `_unavailable_since`. `scripts/shared/tool_transport_invoker.py` returns `_error_result` (`ToolCallResult` from `scripts/shared/transport_dto.py`) with fixed free text "MCP server 'X' is currently unavailable (health check failed)" and "HALF_OPEN trial already in progress"; no retry timing or structured reason (`tool_transport_invoker.py:141-195`). `scripts/agent/tool_loop_guard.py` guards empty-result repeats (`record_tool_result`, `check_empty_result_repeat`, config `tool_empty_result_max_repeats`) and error limits (`check_error_limit`); `scripts/agent/llm_turn_runner.py` wires both. Absence search re-confirmed: no `retry_after`/availability-hint concept exists in either file. Operator health surface exists at `scripts/agent/services/mcp_status.py`.

## Problem
The LLM sees identical tool definitions regardless of server reachability and learns of unavailability only from free-text errors after each attempt, so a long-unavailable tool can be selected repeatedly — wasting turns and contributing to tool-loop failures. Operators cannot see static exclusion vs dynamic failure in one place.

## Reason for Change
A bounded advisory signal reduces wasted turns without creating a second routing authority. Medium: robustness cost only, no correctness/safety incident cited. Prompt-cache and context-size cost of any hint is unknown and must be measured before placement is widened.

## Implementation Intent
Define the hint as a separate advisory contract carried on the structured tool result (`ToolCallResult`), never on `RuntimeTool` static fields and never by removing tool definitions. Derive `retry_after_seconds` from the registry's `_unavailable_since` and the existing half-open cooldown — computed, not stored in new state. Teach `ToolLoopGuard` a bounded per-tool unavailable-repeat counter that reuses the existing `tool_empty_result_max_repeats` settings, emits a system hint (same `_save_guard_hint` pattern as empty-result repeats), and clears counts when health returns to `HEALTHY`/`HALF_OPEN` trial success. Extend `mcp_status` diagnostics to show static availability and dynamic health as separate columns. Health logic stays in `McpServerHealthRegistry`; routing stays in `RuntimeToolRegistry`.

## Requirements
- `REQ-001`: Dynamic availability-hint contract: normalized reason code, current circuit state, optional `retry_after_seconds`; advisory only — it must not block, reroute, or retry calls by itself, and adds no unauthorized fallback.
- `REQ-002`: Hint is carried on structured tool results for UNAVAILABLE and HALF_OPEN-busy outcomes; LLM tool definitions and `RuntimeTool` static fields are unchanged.
- `REQ-003`: `ToolLoopGuard` bounds repeated selection of the same unavailable tool, reusing the existing empty-result repeat configuration; the bound emits an observable system hint.
- `REQ-004`: Health recovery removes stale hints/counters.
- `REQ-005`: Diagnostics display static availability and dynamic health separately.
- `REQ-006`: Prompt-cache and context-size impact of the hint is measured and recorded; no volatile content enters prompt-cached request regions.
- `REQ-007`: Tests prove dynamic health never mutates routing ownership or static visibility fields.
- `REQ-008`: ADR-003 and tool-execution/health documents describe the advisory hint and its boundaries (intent/boundaries only).

## Implementation Target Files
**Freeze status**: Frozen (Step 8 Implementation Target Files Validation passed on 2026-10-29: every row exists-or-is-new-with-evidence, is linked to a Plan requirement, and is `Verified`; `check_workitem_structure.py` and `check_plan_target_overlaps.py` report no findings. Re-verified 2026-10-29 against `HEAD c5a8285dd` after a tree reorganization landed during planning; all existing target paths re-confirmed present; evidence anchors and churn numbers re-checked against current source (no target-file row changes).)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/transport_dto.py` | Add advisory availability-hint field to `ToolCallResult` (default None; new hint dataclass lives here) | Structured tool error type named by the issue as "locations to be confirmed" — confirmed: `class ToolCallResult` is defined here | REQ-001, REQ-002 | `scripts/shared/transport_dto.py:8` `class ToolCallResult` | `tests/shared/test_transport_dto.py` | Verified |
| `scripts/shared/mcp_health.py` | Add normalized reason codes and a `retry_after_seconds` derivation from `_unavailable_since` + cooldown | Registry already stores `_unavailable_since`; derivation belongs beside it | REQ-001 | `scripts/shared/mcp_health.py:11-37` states/threshold/cooldown | `tests/shared/test_mcp_health.py` | Verified |
| `scripts/shared/tool_transport_invoker.py` | Attach the hint to UNAVAILABLE and HALF_OPEN-busy `_error_result`s | Today those results carry fixed free text only | REQ-001, REQ-002 | `tool_transport_invoker.py:141-195` `_error_result`, `_check_health` | `tests/shared/test_tool_transport_invoker.py` | Verified |
| `scripts/agent/tool_loop_guard.py` | Per-tool unavailable-repeat counter, bounded system hint, recovery clearing | Guard owns repeat detection today (`record_tool_result`, `check_empty_result_repeat`, `_save_guard_hint`) | REQ-003, REQ-004 | `tool_loop_guard.py:85-190` (`class ToolLoopGuard` :85, `report_effective_state` :111, `_save_guard_hint` :130, `record_tool_result` :158, `check_empty_result_repeat` :180) | `tests/agent/test_tool_loop_guard.py` | Verified |
| `scripts/agent/llm_turn_runner.py` | Feed unavailable-hinted results into the new guard counter and surface the hint to the turn | Runner wires guard checks today (`check_all`, `check_empty_result_repeat`, `check_error_limit`) | REQ-003 | `llm_turn_runner.py:18-131` guard wiring | `tests/agent/test_llm_turn_runner.py` | Verified |
| `scripts/agent/services/mcp_status.py` | Show static availability and dynamic health as separate fields | Operator diagnostics surface exists and already imports `McpServerHealthState` | REQ-005 | `scripts/agent/services/mcp_status.py:17-22` | `tests/agent/test_mcp_health_posture.py` | Verified |
| `tests/shared/test_transport_dto.py` | Extend: hint field contract, defaults, advisory-only shape | Issue Testing Expectations | REQ-001, REQ-002 | Existing file | — | Verified |
| `tests/shared/test_mcp_health.py` | Extend: reason normalization, `retry_after_seconds` derivation incl. cooldown boundary | Issue Testing Expectations | REQ-001 | Existing file | — | Verified |
| `tests/shared/test_tool_transport_invoker.py` | Extend: hint present on UNAVAILABLE/HALF_OPEN results; absent on healthy calls | Issue Testing Expectations | REQ-002 | Existing file | — | Verified |
| `tests/agent/test_tool_loop_guard.py` | Extend: unavailable-repeat bound, hint emission, recovery clearing; static fields unchanged when health changes | Issue Testing Expectations | REQ-003, REQ-004, REQ-007 | Existing file | — | Verified |
| `tests/agent/test_llm_turn_runner.py` | Extend: end-to-end turn behavior with a repeatedly unavailable tool; bound observed; definitions unchanged | Issue Testing Expectations | REQ-002, REQ-003 | Existing file | — | Verified |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Record the advisory-hint contract and its non-authority boundary; decisions 11/12 unchanged | Issue Documentation Impact | REQ-008 | ADR-003 static/dynamic separation text verified present | docs checkers | Verified |
| `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` | Describe the loop bound and hint behavior for tool execution | Tool-execution doc per issue Documentation Impact | REQ-008 | `docs/23_agent/agent_06_01_*` exists (churn 12/30d) | docs checkers | Verified |
| `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md` | Describe normalized health reason codes and static-vs-dynamic display | MCP health-reasons doc; matches "normalized reason" contract | REQ-008 | `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md` exists (churn 5/30d) | docs checkers | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Issue instruction: read ADR-003 before editing; constraint source for REQ-007 | REQ-007, REQ-008 |
| `scripts/shared/runtime_tool_registry.py` | Confirms the static fields the hint must NOT touch | REQ-002, REQ-007 |
| `scripts/agent/context.py` | `AgentContext` already carries `health_registry`; wiring path for the guard | REQ-003 (`scripts/agent/tool_loop_guard.py`) |
| `scripts/agent/config_dataclasses.py` | `tool_empty_result_max_repeats` setting reused as the bound (issue UNK-2 resolution) | REQ-003 |
| `scripts/shared/token_estimation.py`, `scripts/shared/token_counter.py` | Measurement tooling for REQ-006 impact numbers | REQ-006 |
| `docs/22_mcp/mcp_03_03_transport-and-health.md` | Existing transport/health semantics the reason codes must stay consistent with | REQ-008 |
| `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md` | HALF_OPEN trial semantics the hint describes | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-002, REQ-007): `RuntimeToolRegistry` remains the only routing authority; changing health state mutates no `RuntimeTool` static field and no tool definition; tests assert field-level immutability.
- AC-2 (REQ-001, REQ-003): The LLM receives an observable unavailable-tool signal on the structured result, and repeated selection of the same unavailable tool is bounded by the configured limit with an emitted system hint.
- AC-3 (REQ-004): Recovery to `HEALTHY` (or a successful HALF_OPEN trial) clears the counters and hint for that server's tools.
- AC-4 (REQ-005): Diagnostics output shows static availability and dynamic health as distinct, separately-labeled values.
- AC-5 (REQ-006): Measured prompt/context impact is recorded in this Plan's Execution Status notes before any hint placement widens; no volatile content in prompt-cached request regions.

## Tests
- Unit (REQ-001/REQ-002): hint contract shape; `retry_after_seconds` derivation at cooldown boundaries; hint attached on UNAVAILABLE/HALF_OPEN, absent on healthy.
- Unit (REQ-003/REQ-004): repeat-bound triggering at the configured limit, system hint emitted once per bound hit, counters cleared on recovery.
- Unit (REQ-007): snapshot `RuntimeTool` static fields before/after health transitions — equality asserted.
- Integration (REQ-002/REQ-003): `llm_turn_runner` turn with a persistently unavailable tool terminates via the bound, not via unbounded retries.
- Commands: `uv run pytest tests/agent tests/shared`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, docs checkers from `routing.md`.

## Documentation Impact
Yes. ADR-003 (`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`) records the advisory-hint boundary; `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` covers the loop bound; `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md` covers reason codes and static-vs-dynamic display. Named via `docs/00_index.md` Agent spec / MCP spec task rows. Intent and boundaries only, no implementation locations (`skills/DESIGN.md` Docs content policy).

## Assumptions
- Placement decision (issue UNK-1): the hint rides on structured tool results (tool-error channel), not in turn-context prompt content — this keeps volatile content out of prompt-cached request regions; turn-context surfacing may be added later only with recorded measurement (AC-5).
- Bound decision (issue UNK-2): reuse the existing `tool_empty_result_max_repeats` configuration as the per-tool unavailable-repeat bound rather than adding a new config key; a dedicated key can be introduced later if operators need a separate dial.
- Normalized reason codes are a small closed enum owned by `scripts/shared/mcp_health.py` (server_unavailable, half_open_trial_in_progress); free text stays for humans but consumers key on the code.
- `retry_after_seconds` is computed from `_unavailable_since` + cooldown at result-build time; no new persistent state.
- The hint is per call result; "removing stale hints" means clearing loop-guard counters, not deleting a stored hint.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Prompt-cache/context-size impact numbers for the structured-result hint | No measurement exists | Phase 2 measurement step using `token_estimation` on representative payloads; numbers recorded in Execution Status notes (plan chose the tool-error channel precisely to make this cost near-zero; widening placement later requires the recorded numbers) | False |
| UNK-02 | Whether operators need a separate unavailable-repeat bound distinct from empty-result repeats | No usage data | Start with reuse; revisit if `report_effective_state` output shows conflicting pressure | False |
| UNK-03 | `scripts/agent/tool_runner.py::_run_prepared_call` is the only call site that hands a `ToolCallResult` to `ToolLoopGuard` (`guard.record_tool_result(name, text)` at `tool_runner.py:229`), but `tool_runner.py` is not a Frozen-plan target row; the guard cannot observe `availability_hint` without one call-site line there (re-verified 2026-10-30 at HEAD `124e340b4`) | No target row covers the wiring call site | Needs confirmation: rows 04/05 procedures include one disclosed supporting call-site edit in `tool_runner.py` (`guard.observe_availability(result)`); alternative (returning results from `execute_all_tool_calls`) edits the same file | True (blocking only for rows 04/05 wiring) |
| UNK-04 | REQ-005 display fields: "each server row gains explicit `static_visibility` ... and `dynamic_health`" requires a field addition on `McpProbeResult` (`scripts/agent/services/models.py:49`) and renderer lines in `scripts/agent/commands/cmd_mcp.py` — neither file is a target row (re-verified 2026-10-30 at HEAD `124e340b4`) | No target row covers the row-model or renderer | Needs confirmation: row 06 procedure includes disclosed supporting edits in `models.py` (one field) and `cmd_mcp.py` (renderer lines), verified by the row's own Related Tests file `tests/agent/test_mcp_health_posture.py` (also a disclosed supporting test edit) | True (blocking only for row 06 display) |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/transport_dto.py` | DTO field addition (default None) | Every tool-call path in agent + MCP layers consumes this DTO | 5 | High (single author) | Synced by `deploy.sh` rsync of `scripts/`; service restarts required |
| `scripts/shared/tool_transport_invoker.py` | Error-result enrichment | All MCP tool invocations | 7 | High (single author) | Synced by rsync |
| `scripts/shared/mcp_health.py` | Reason codes + derivation | Health consumers (`mcp_status`, invoker, startup) | 1 | High (single author) | Synced by rsync |
| `scripts/agent/tool_loop_guard.py` | New counter + hint | Agent turn loop for all sessions | 3 | High (single author) | Synced by rsync |
| `scripts/agent/llm_turn_runner.py` | Guard wiring | Turn execution path | 4 | High (single author) | Synced by rsync |
| `scripts/agent/services/mcp_status.py` | Display change | Operator diagnostics only | 2 | High (single author) | Synced by rsync |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Boundary wording | ADR referenced by many plans | 4 | High (single author) | N/A: docs only |
| `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` | Behavior wording | Agent spec | 12 | High (single author) | N/A: docs only |
| `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md` | Reason-code wording | MCP spec | 5 | High (single author) | N/A: docs only |
| Test rows | Extensions | Own suites | 1–7 | High (single author) | N/A: tests not deployed |

## Design
- Hint model: `DynamicAvailabilityHint(reason: Literal["server_unavailable", "half_open_trial_in_progress"], circuit_state: McpServerHealthState, retry_after_seconds: int | None)` in `scripts/shared/transport_dto.py`; `ToolCallResult` gains `availability_hint: DynamicAvailabilityHint | None = None`. Absence means "no dynamic availability signal" — identical today's behavior for healthy calls.
- Derivation in `scripts/shared/mcp_health.py`: `retry_after_seconds = max(0, cooldown_remaining(server_key))` from `_unavailable_since` and the half-open cooldown; no new storage.
- Invoker: `_check_health` attaches the hint to the existing `_error_result`s; free-text message preserved for backward compatibility with existing tests/operators.
- Guard: `ToolLoopGuard.record_tool_result` inspects `availability_hint` on the result; a per-server_key unavailable counter increments; at the configured bound the guard injects one system hint via `_save_guard_hint` (existing pattern) and further identical calls within the same turn are refused by the guard the same way empty-result repeats are. A successful (non-hinted) call for that server resets the counter — this is both "recovery clearing" and false-positive protection for a server that just recovered.
- Authority invariants: guard and hint never consult or mutate `RuntimeToolRegistry`; tests assert static fields of `RuntimeTool` instances byte-equal across health transitions.
- Diagnostics (`mcp_status`): each server row gains explicit `static_visibility` (from registry static availability) and `dynamic_health` (registry state + reason + retry_after) shown as separate values.
- Measurement (REQ-006): a test-time comparison of serialized turn payloads with and without hinted results using `token_estimation`; delta recorded in Execution Status notes. Because hints ride on tool-result messages (already variable content), the cached system/tool-definition region is untouched by construction.

## Implementation steps
1. **Phase 1: Hint contract (shared layer)**
   - [ ] Define `DynamicAvailabilityHint` + DTO field (REQ-001, REQ-002; `scripts/shared/transport_dto.py`)
   - [ ] Reason codes and `retry_after_seconds` derivation (REQ-001; `scripts/shared/mcp_health.py`)
   - [ ] Attach hints in invoker health path (REQ-002; `scripts/shared/tool_transport_invoker.py`)
   - [ ] Shared-layer tests (REQ-001, REQ-002, REQ-007; `tests/shared/test_transport_dto.py`, `tests/shared/test_mcp_health.py`, `tests/shared/test_tool_transport_invoker.py`)
2. **Phase 2: Loop bound and measurement (agent layer)**
   - [ ] Guard counter, hint emission, recovery reset (REQ-003, REQ-004; `scripts/agent/tool_loop_guard.py`)
   - [ ] Runner wiring of hinted results into the guard (REQ-003; `scripts/agent/llm_turn_runner.py`)
   - [ ] Agent tests incl. static-field immutability and bounded unavailable loop (REQ-002, REQ-003, REQ-007; `tests/agent/test_tool_loop_guard.py`, `tests/agent/test_llm_turn_runner.py`)
   - [ ] Run prompt/context impact measurement via `token_estimation` and record numbers in Execution Status notes (REQ-006; `tests/agent/test_llm_turn_runner.py`)
3. **Phase 3: Diagnostics & Deployment & Verification**
   - [ ] `mcp_status` static-vs-dynamic display (REQ-005; `scripts/agent/services/mcp_status.py`)
   - [ ] Deployment validation: confirm `deploy.sh` rsync syncs all six changed scripts and the agent services are restarted after deploy (scripts/configs sync check; all REQ)
   - [ ] Full validation: `uv run pytest tests/agent tests/shared`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports` (all REQ)
4. **Phase 4: Documentation**
   - [ ] ADR-003 boundary wording update (no decision change) (REQ-008; `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`)
   - [ ] Tool-execution and health-reason docs (REQ-008; `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`, `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md`)
   - [ ] Docs checkers from `routing.md` (REQ-008)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/transport_dto.py`, `scripts/shared/mcp_health.py` | Unit | `uv run pytest tests/shared/test_transport_dto.py tests/shared/test_mcp_health.py` | Hint contract + derivation pass, cooldown boundary correct |
| `scripts/shared/tool_transport_invoker.py` | Unit | `uv run pytest tests/shared/test_tool_transport_invoker.py` | Hints on UNAVAILABLE/HALF_OPEN only |
| `scripts/agent/tool_loop_guard.py`, `scripts/agent/llm_turn_runner.py` | Unit + integration | `uv run pytest tests/agent/test_tool_loop_guard.py tests/agent/test_llm_turn_runner.py` | Bound fires; recovery clears; static fields unchanged |
| Authority invariants | Architecture | `PYTHONPATH=scripts uv run lint-imports` | No new cross-layer imports; guard never imports registry routing internals |
| Types | Static | `uv run mypy --no-namespace-packages scripts/ tests/eventbus` | Clean |
| Docs rows | Docs checks | checkers named in `routing.md` | Green |
| REQ-006 | Measurement | token-estimation comparison test | Delta recorded in Execution Status notes |

## Risks
- **Risk**: Frozen Plan `plans/20261029-233524_toolexec001_*` also targets `scripts/agent/llm_turn_runner.py` and `tests/agent/test_llm_turn_runner.py` (pending-call control-message injection at turn entry). **Mitigation**: distinct wiring points (guard wiring vs. turn-entry message injection); whichever plan lands first, the other rebases against it before its Phase 2.
- **Risk**: DTO field addition touches every tool-call path. **Mitigation**: field defaults to None; characterization tests run first (all existing suites green before behavior changes).
- **Risk**: Guard counter misclassifies transient single failures as repeated unavailability. **Mitigation**: counter keys on the hint's normalized reason per server; any successful call resets it.
- **Risk**: ADR-003 wording edits conflict with concurrent ADR work (`dbmig001`, `adrauth001` doc phases touch the same ADR set). **Mitigation**: land code phases first; re-edit ADR-003 against current HEAD; run ADR checkers after.
- **Risk**: Hint text becomes a prompt-injection surface if server-controlled strings leak into reason codes. **Mitigation**: closed enum of reason codes; server free-text stays in the human-facing message only.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Hint contract (shared layer) | Completed | — | 20261030-204034 | rows 01-03,07-09 done: hint contract, reason codes/retry_after, invoker attachment + tests |
| 2 | Phase 2: Loop bound and measurement | Completed | — | 20261030-205803 | Record REQ-006 measurement numbers here REQ-006 measured (test_availability_hint...): tool-result-region delta=0 tokens (hint is structured DTO metadata; legacy rejection text byte-identical), once-per-turn bound-summary cost=12 tokens; system+tool_calls cached-region counts identical (AC-5 gate satisfied) |
| 3 | Phase 3: Diagnostics & Deployment & Verification | Completed | — | 20261030-203727 | row 06 done: static_visibility field + Availability display block in /mcp status |
| 4 | Phase 4: Documentation | Completed | — | 20261030-205825 | rows 12-14 done: ADR-003 Decision 17; agent_06_01 Design Intent subsection; mcp_06_10 reason-codes + static-vs-dynamic display sections + Keywords; docs checkers green |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261030-083821_01_scripts_shared_transport_dto.py.md` | 1 | Procedure | Completed | — | 20261030-205825 |
| `implementations/20261030-083821_02_scripts_shared_mcp_health.py.md` | 1 | Procedure | Completed | — | 20261030-205825 |
| `implementations/20261030-083821_03_scripts_shared_tool_transport_invoker.py.md` | 1 | Procedure | Completed | — | 20261030-205825 |
| `implementations/20261030-083821_04_scripts_agent_tool_loop_guard.py.md` | 2 | Procedure | Completed | — | 20261030-205825 |
| `implementations/20261030-083821_05_scripts_agent_llm_turn_runner.py.md` | 2 | Procedure | Completed | — | 20261030-205825 |
| `implementations/20261030-083821_06_scripts_agent_services_mcp_status.py.md` | 3 | Procedure | Completed | — | 20261030-205825 |
| `implementations/20261030-083821_07_tests_shared_test_transport_dto.py.md` | 1 | Procedure | Completed | — | 20261030-205825 |
| `implementations/20261030-083821_08_tests_shared_test_mcp_health.py.md` | 1 | Procedure | Completed | — | 20261030-205825 |
| `implementations/20261030-083821_09_tests_shared_test_tool_transport_invoker.py.md` | 1 | Procedure | Completed | — | 20261030-205825 |
| `implementations/20261030-083821_10_tests_agent_test_tool_loop_guard.py.md` | 2 | Procedure | Completed | — | 20261030-205825 |
| `implementations/20261030-083821_11_tests_agent_test_llm_turn_runner.py.md` | 2 | Procedure | Completed | — | 20261030-205825 |
| `implementations/20261030-083821_12_docs_10_adr_adr_02_02_003_agent-runtime-tool-registry-routing-authority.md.md` | 4 | Procedure | Completed | — | 20261030-205825 |
| `implementations/20261030-083821_13_docs_23_agent_agent_06_01_tool-execution-and-approval-execution.md.md` | 4 | Procedure | Completed | — | 20261030-205825 |
| `implementations/20261030-083821_14_docs_22_mcp_mcp_06_10_health-reasons-and-error-kinds.md.md` | 4 | Procedure | Completed | — | 20261030-205825 |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261029-104507_toolhint001_dynamic-tool-health-hints.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261029-215111
- **Related target files**: `scripts/shared/transport_dto.py`, `scripts/shared/mcp_health.py`, `scripts/shared/tool_transport_invoker.py`, `scripts/agent/tool_loop_guard.py`, `scripts/agent/llm_turn_runner.py`, `scripts/agent/services/mcp_status.py`, `tests/shared/test_transport_dto.py`, `tests/shared/test_mcp_health.py`, `tests/shared/test_tool_transport_invoker.py`, `tests/agent/test_tool_loop_guard.py`, `tests/agent/test_llm_turn_runner.py`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`, `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (hint contract) | `scripts/shared/transport_dto.py` | Phase 1 | AC-2 | `tests/shared/test_transport_dto.py` | Explicit in issue |
| REQ-001 | Required Changes | `scripts/shared/mcp_health.py` | Phase 1 | AC-2 | `tests/shared/test_mcp_health.py` | Explicit in issue |
| REQ-002 | Required Changes (error channel) | `scripts/shared/tool_transport_invoker.py` | Phase 1 | AC-1, AC-2 | `tests/shared/test_tool_transport_invoker.py` | Explicit in issue |
| REQ-003 | Required Changes (loop bound) | `scripts/agent/tool_loop_guard.py` | Phase 2 | AC-2 | `tests/agent/test_tool_loop_guard.py` | Explicit in issue |
| REQ-003 | Background (runner wiring) | `scripts/agent/llm_turn_runner.py` | Phase 2 | AC-2 | `tests/agent/test_llm_turn_runner.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes (recovery removal) | `scripts/agent/tool_loop_guard.py` | Phase 2 | AC-3 | `tests/agent/test_tool_loop_guard.py` | Explicit in issue |
| REQ-005 | Required Changes (diagnostics) | `scripts/agent/services/mcp_status.py` | Phase 3 | AC-4 | `tests/agent/test_mcp_health_posture.py` | Confirmed by repository evidence |
| REQ-006 | Constraints (prompt cache) | `tests/agent/test_llm_turn_runner.py` | Phase 2 | AC-5 | token-estimation comparison | Explicit in issue |
| REQ-007 | Acceptance Criteria (authority) | `tests/agent/test_tool_loop_guard.py` | Phase 2 | AC-1 | static-field equality test | Explicit in issue |
| REQ-008 | Documentation Impact | `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Phase 4 | AC-1 | docs/ADR checkers | Explicit in issue |
| REQ-008 | Documentation Impact | `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` | Phase 4 | AC-2 | docs checkers | Explicit in issue |
| REQ-008 | Documentation Impact | `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md` | Phase 4 | AC-4 | docs checkers | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261030-083821 -->