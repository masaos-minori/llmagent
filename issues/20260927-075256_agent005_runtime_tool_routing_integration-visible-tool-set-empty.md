# runtime_tool_routing_integration visible tool set empty

## Priority
Medium

## Summary
`tests/agent/services/test_runtime_tool_routing_integration.py::TestDiscoveryToLlmVisibilityEndToEnd::test_disabled_discovered_tool_excluded_from_llm_payload` expects `'visible_tool'` to be present in the set of tools visible to the LLM, but the observed set is empty.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
`AssertionError: assert 'visible_tool' in set()` — the end-to-end discovery-to-LLM-visibility pipeline produces no visible tools at all in this test, when at least one (`'visible_tool'`) should remain after a disabled tool is excluded.

## Reason for Change
An empty visible-tool set (rather than the disabled tool being correctly excluded while others remain) suggests either the discovery step itself is not finding any tools in this test's setup, or the visibility-filtering step is over-filtering (excluding everything, not just the disabled tool). This affects whether the agent can see any tools at all in a runtime-routing/discovery scenario, which is central to tool-calling functionality.

## Implementation Intent
Reproduce with verbose output to see whether the discovery step returns any tools at all before filtering, and where in the discovery→filter→LLM-payload pipeline the tool set becomes empty.

## Target Files or Areas
- `tests/agent/services/test_runtime_tool_routing_integration.py`
- Tool discovery/routing service module (confirm exact path, likely `scripts/agent/services/` runtime tool routing/discovery)

## Required Changes
- Trace the pipeline stage where the tool set becomes empty (discovery vs. filtering).
- Fix the identified stage so a non-disabled discovered tool remains visible.

## Constraints
Preserve the exclusion of genuinely disabled tools — the fix must not simply make all tools visible unconditionally.

## Acceptance Criteria
- The listed test passes: the disabled tool is excluded and `'visible_tool'` remains visible.

## Testing Expectations
Run `tests/agent/services/test_runtime_tool_routing_integration.py`; run full suite once after the fix.

## Documentation Impact
N/A: unless the discovery/visibility pipeline's contract changed and needs documenting (Needs confirmation).

## Out of Scope
Other unrelated failing tests from the same full-suite run.

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: at which exact pipeline stage (discovery vs. filtering) the tool set becomes empty — not yet traced in this investigation.

## AI Implementation Instruction
Add temporary tracing/print statements (or a debugger) to see the tool set at each pipeline stage before deciding which stage to fix. Do not assume the filtering step is at fault without confirming discovery itself returns tools.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/agent/services/test_runtime_tool_routing_integration.py
