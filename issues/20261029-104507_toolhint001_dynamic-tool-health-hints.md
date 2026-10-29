# Expose dynamic tool-health guidance without changing static visibility or routing authority

## Priority
Medium

## Summary
Add an advisory dynamic-availability hint (normalized reason, circuit state, optional `retry_after_seconds`) that the LLM and operators can see for a temporarily unavailable MCP server's tools, and bound repeated selection of the same unavailable tool in the tool loop, while `RuntimeToolRegistry` stays the sole routing authority and static LLM visibility never changes.

## Background
Source: `memo-issue.md` item M-02 (original task M-04), re-verified against current source on 2026-10-29.
- ADR-003 separates static availability from dynamic health on purpose: "Dynamic Health state must not automatically change LLM visibility" and `RuntimeToolRegistry` is the sole authority for LLM visibility, static availability, dynamic health, approval state, and execution eligibility as distinct concepts (`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md:36, 48, 81-82`, `Documentation only`).
- Dynamic health exists as `McpServerHealthRegistry` with states `HEALTHY`, `DEGRADED`, `UNAVAILABLE`, `HALF_OPEN`, `UNKNOWN`, a failure threshold of 3, and a half-open cooldown of 30 seconds (`scripts/shared/mcp_health.py:11-37`), and it records when a server became unavailable (`_unavailable_since`) (`Explicit in code`).
- When a tool is called on an unavailable server, `ToolTransportInvoker` returns an error result with the fixed text "MCP server 'X' is currently unavailable (health check failed)" and `error_type="tool"`; a second concurrent HALF_OPEN call gets "a HALF_OPEN trial already in progress" (`scripts/shared/tool_transport_invoker.py:160-195`). No retry timing or structured reason is carried (`Explicit in code`).
- `ToolLoopGuard` (`scripts/agent/tool_loop_guard.py:85`) detects repeated empty results (`record_tool_result`, `check_empty_result_repeat`); a search finds no handling of repeated calls to an unavailable tool, and `llm_turn_runner.py` and `tool_loop_guard.py` contain no `retry_after` or availability-hint concept (`Explicit by absence search`).

## Problem
The LLM sees the same tool definitions whether or not the server is currently reachable, and learns of unavailability only from a free-text error after each attempt. A long-unavailable tool can therefore be selected repeatedly, wasting turns and contributing to tool-loop failures, and operators cannot distinguish a static exclusion from a dynamic failure in one place.

## Reason for Change
A bounded, advisory signal reduces wasted turns without turning dynamic health into a second routing authority. Priority is Medium: the cost is robustness and wasted turns, with no correctness or safety impact and no incident cited. Not time-sensitive. The prompt-cache and context-size cost of any hint is unknown and must be measured.

## Implementation Intent
Define a dynamic availability hint as a separate, advisory contract that is not stored in `RuntimeTool` static fields: normalized reason, current circuit state, and optional `retry_after_seconds` derived from the registry's unavailable-since timestamp and cooldown. Surface it through the turn context or the structured tool error, never by removing tool definitions. Teach `ToolLoopGuard` to bound repeated selection of the same unavailable tool, remove stale hints after recovery, and show static availability and dynamic health separately in diagnostics. Keep the health logic in `McpServerHealthRegistry` and routing in `RuntimeToolRegistry`.

## Target Files or Areas
- `scripts/agent/llm_turn_runner.py`, `scripts/agent/tool_loop_guard.py`
- `scripts/shared/mcp_health.py`, `scripts/shared/tool_transport_invoker.py`
- The LLM request builder and the structured tool error type (locations to be confirmed)
- Runtime-tool and health tests under `tests/shared/` and `tests/agent/` (names to be confirmed)
- ADR-003 and the tool-execution and diagnostics documents under `docs/`

## Required Changes
- Define the dynamic availability-hint contract (normalized reason, circuit state, optional `retry_after_seconds`), separate from `RuntimeTool` static fields.
- Add the hint to turn context or to structured tool errors without removing tool definitions.
- Teach `ToolLoopGuard` to bound repeated selection of the same unavailable tool; remove or update hints after health recovery.
- Display static availability and dynamic health separately in diagnostics.
- Measure prompt-cache and context-size impact of the hint.
- Add tests that dynamic health never mutates routing ownership or static LLM visibility.

## Constraints
- `RuntimeToolRegistry` remains the sole routing authority and the static tool-definition contract is unchanged (ADR-003 decisions 11 and 12).
- The hint is advisory only: it must not block, reroute, or retry calls by itself, and must not add a fallback that no Accepted ADR authorizes.
- No new volatile content may be placed where it invalidates the prompt cache without the measured impact being recorded.

## Acceptance Criteria
- `RuntimeToolRegistry` remains the only routing authority and dynamic health never changes static ownership or visibility fields.
- The LLM receives an observable unavailable-tool signal; repeated unavailable-tool loops are bounded.
- Health recovery removes stale guidance.
- Operators can distinguish a static exclusion from a dynamic failure in diagnostics.

## Testing Expectations
- Unit tests for the hint contract and its removal after recovery; tests for the loop bound with a repeatedly unavailable tool; tests asserting static fields are unchanged when health changes.
- `uv run pytest tests/agent tests/shared`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, and the docs checkers in `routing.md` for doc edits.

## Documentation Impact
Yes. ADR-003 and the tool-execution documents must describe the advisory hint, its relation to static availability and dynamic health, and the loop bound; document intent and boundaries, not implementation locations (`skills/DESIGN.md` Docs content policy).

## Out of Scope
- Changing circuit-breaker thresholds or the half-open policy.
- Making dynamic health a routing input or removing unavailable tools from the LLM tool list.
- Unrelated refactoring or formatting-only changes.

## Dependencies
- Related: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md` (health and posture gating at construction) and `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md` (generation identifiers); no ordering required. No in-flight plan targets these files (checked in `plans/`).

## Unresolved Questions
- `Needs confirmation`: where to place the hint (turn context versus structured tool error) given the prompt-cache impact; the impact is not yet measured.
- `Needs confirmation`: the bound for repeated selection of the same unavailable tool, and whether it should reuse the existing empty-result repeat settings.
- `Needs confirmation`: where the structured tool-error type and the LLM request builder live (the memo names them without paths).

## AI Implementation Instruction
- Read ADR-003, `scripts/shared/mcp_health.py`, and `scripts/agent/tool_loop_guard.py` before editing.
- Keep dynamic health out of `RuntimeTool` and out of routing; stop and report if the design requires either.
- Measure and report the context-size impact; stop and report open questions instead of choosing placement or bounds.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-104507
- **Related target files**: `scripts/agent/llm_turn_runner.py`, `scripts/agent/tool_loop_guard.py`, `scripts/shared/mcp_health.py`, `scripts/shared/tool_transport_invoker.py`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`
