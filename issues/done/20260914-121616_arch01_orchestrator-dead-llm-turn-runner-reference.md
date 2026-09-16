# Remove unused `Orchestrator._llm_runner` (dead `LLMTurnRunner` instance duplicated by `LlmTurnExecutor`)

## Priority
Medium

## Summary
`Orchestrator.__init__` (`scripts/agent/orchestrator.py`) constructs an `LLMTurnRunner` instance and stores it as `self._llm_runner`, but no code path in `Orchestrator` ever reads or calls `self._llm_runner`. The actual LLM turn execution runs through a second, independently constructed `LLMTurnRunner` instance created inside `LlmTurnExecutor` (`scripts/agent/llm_turn_executor.py`). This is a dead reference that also duplicates object construction and obscures which component actually owns `LLMTurnRunner`.

## Background
This issue follows an architecture responsibility-boundary review requested in this session, which fixed the following boundaries and is being recorded as a new ADR: Workflow Engine owns persistent task state, stage transitions, retries, and approval; Orchestrator arbitrates processing within a single turn; LLMTurnRunner owns the short-lived LLM/tool-call loop; ToolExecutor executes one tool call; MCP Server enforces technical safety of external operations. While verifying the implementation against this boundary, this dead reference was found in `Orchestrator`.

## Problem
Confirmed by direct reading:
- `scripts/agent/orchestrator.py` line 115: `self._llm_runner = LLMTurnRunner(ctx, self._guard, tracer=tracer)` is assigned in `__init__`.
- `grep -n "_llm_runner\b" scripts/agent/orchestrator.py` matches only that one line — `self._llm_runner` is never read anywhere else in the file.
- The turn actually executes via `self._workflow_adapter.execute_turn(...)` → `WorkflowEngineAdapter._process_turn()` → `self._llm_executor.handle_llm_turn(...)` (`scripts/agent/workflow_engine_adapter.py` line 386), where `self._llm_executor` is an `LlmTurnExecutor` instance (`scripts/agent/orchestrator.py` line 147).
- `LlmTurnExecutor` (`scripts/agent/llm_turn_executor.py` line 81) constructs its own `runner = LLMTurnRunner(...)` internally and uses that instance — not `Orchestrator._llm_runner`.

So two `LLMTurnRunner` instances are constructed per `Orchestrator` lifetime: one dead (`Orchestrator._llm_runner`), one live (inside `LlmTurnExecutor`).

## Reason for Change
An unused instance of a stateful, resource-holding class (`LLMTurnRunner` holds an SSE/streaming loop guard) sitting on `Orchestrator` misrepresents where the LLM/tool-call loop's responsibility actually lives, contrary to the responsibility boundary this session fixed (LLMTurnRunner's owner is the component that runs turns, not `Orchestrator` itself). It also wastes one object construction per `Orchestrator` instantiation and risks a future maintainer wiring new code against the wrong (dead) instance.

## Implementation Intent
Remove the dead `self._llm_runner` assignment and its construction from `Orchestrator.__init__`, provided no other code path (including tests) depends on the attribute's presence.

## Target Files or Areas
- `scripts/agent/orchestrator.py`

## Required Changes
- Delete the `self._llm_runner = LLMTurnRunner(ctx, self._guard, tracer=tracer)` assignment in `Orchestrator.__init__` (`scripts/agent/orchestrator.py` line 115) and the now-unused `LLMTurnRunner` import if nothing else in the file references it.
- Confirm via repository-wide search that no test or other module reads `Orchestrator._llm_runner` before deleting it; if one does, update it to use the `LlmTurnExecutor`-owned instance instead (or via `Orchestrator._llm_executor`) rather than keeping the dead duplicate.

## Constraints
Do not change `LlmTurnExecutor`'s own construction of its `LLMTurnRunner` instance — that is the live, correct path per the responsibility boundary; this issue only removes the unused duplicate on `Orchestrator`.

## Acceptance Criteria
- `Orchestrator.__init__` no longer constructs an unused `LLMTurnRunner` instance.
- `grep -n "_llm_runner\b" scripts/agent/orchestrator.py` returns no matches.
- Existing test suite for `scripts/agent/orchestrator.py` and `scripts/agent/llm_turn_executor.py` still passes unmodified (or updated only if a test directly referenced the removed attribute).

## Testing Expectations
Run the existing `tests/agent/test_orchestrator*.py` and `tests/agent/test_llm_turn_executor*.py` (exact file names to be confirmed at implementation time) after the removal; no new test is required since this removes dead code rather than changing behavior.

## Documentation Impact
None beyond the new ADR (tracked separately) that defines this responsibility boundary; this issue is an implementation-only cleanup.

## Out of Scope
- Any change to `LlmTurnExecutor`'s internal `LLMTurnRunner` construction.
- Any redesign of how `Orchestrator` and `LlmTurnExecutor` share state — this issue only removes an unused, redundant construction.

## Dependencies
N/A: none — this can be implemented independently of the new ADR's approval, though it is recorded there as a Known Deviation.

## Unresolved Questions
Whether `self._llm_runner` was left over from a prior refactor (per `llm_turn_runner.py`'s own docstring: "LLMTurnRunner.run() replaces _run_turn()") and simply never removed — resolve by checking git history at implementation time if relevant; does not block the fix itself.

## AI Implementation Instruction
Remove only the dead assignment (and import, if it becomes unused) described in Required Changes. Do not touch `LlmTurnExecutor`'s construction of its own `LLMTurnRunner`, and do not refactor `Orchestrator`'s other extracted-concern composition beyond this single removal.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-121616
- **Related target files**: scripts/agent/orchestrator.py
