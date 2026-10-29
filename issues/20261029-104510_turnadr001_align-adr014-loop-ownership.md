# Align ADR-014 control-plane responsibility wording with the current LLM turn implementation

## Priority
Low

## Summary
Restate ADR-014's ownership of the LLM and tool round-trip loop so it matches how the code is structured today (an `Orchestrator`-created `LlmTurnExecutor` that creates an `LLMTurnRunner` per turn), describing logical ownership and instance lifecycle instead of a method or class name that may move, and update the related Agent flow documents and the test that guards against duplicate executor instances.

## Background
Source: `memo-issue.md` item L-02 (original task L-04), re-verified against current source on 2026-10-29.
- ADR-014 assigns the loop to `LlmTurnExecutor`: it is "responsible for the short loop between the LLM and Tool Calls (streaming and Tool call round-trips within a turn)" (`docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md:58`, `Documentation only`).
- ADR-014 INV-02 reads: "Creation of `LlmTurnExecutor` instances is centralized in the one component that actually drives the LLM/Tool Call round-trip loop. No other component holds unused or duplicate `LlmTurnExecutor` instances." (`adr_02_02_014_agent-control-plane-responsibility-boundaries.md:128`).
- In code, `Orchestrator` constructs one `LlmTurnExecutor` (`scripts/agent/orchestrator.py:120`) and passes it to `WorkflowEngineAdapter` (line 150), which stores it and calls `handle_llm_turn` (`scripts/agent/workflow_engine_adapter.py:98, 341`). `LlmTurnExecutor` itself creates an `LLMTurnRunner` (`scripts/agent/llm_turn_executor.py:84`), and `LLMTurnRunner` is the class defined in `scripts/agent/llm_turn_runner.py:40` (`Explicit in code`). So construction is in `Orchestrator`, the call path runs through the adapter, and the per-turn loop body sits in the runner.
- There is exactly one `LlmTurnExecutor` construction site under `scripts/agent/` (`rg` for the class name, `Explicit in code`), so no unused duplicate exists today.
- `tests/agent/test_orchestrator.py` passes `orch._llm_executor` into adapter-related setups (lines 287, 1058, 1224, 1322) (`Verified by test` only for those usages); whether any test asserts that no duplicate or unused executor exists is not established (`Needs confirmation`).
- Documents that mention the two classes include `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md`, `docs/23_agent/agent_03_01_turn-processing-flow-overview.md`, `docs/23_agent/agent_02_runtime-architecture.md`, and the reference documents.

## Problem
ADR-014's wording equates the loop with `LlmTurnExecutor`, while the loop body lives in `LLMTurnRunner` and the creation site is `Orchestrator`, not the component that drives the loop. INV-02's phrase "the one component that actually drives" can be read either way, and stale wording can lead future code to create a second loop owner or to place responsibilities in the wrong component.

## Reason for Change
This is a documentation and guard-test consistency issue with no behavior defect today. Priority is Low (a non-critical documentation and code mismatch that misleads understanding). It is not time-sensitive; it should be done when ADR-014 or the turn-processing documents are next touched.

## Implementation Intent
First trace the production call path (Orchestrator, then WorkflowEngineAdapter, then LlmTurnExecutor, then LLMTurnRunner) and name the logical loop owner, the object-construction owner, and the per-turn runner lifecycle. Then reword ADR-014 Decision Details, Implementation Notes, and INV-02 to distinguish ownership from delegation and to avoid depending on method names, update the related Agent flow documents, and add or adjust a regression test that fails when a second or unused executor is retained. Keep persistent workflow decisions outside both turn classes, as ADR-014 INV-01 requires.

## Target Files or Areas
- `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`
- `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md`, `docs/23_agent/agent_03_01_turn-processing-flow-overview.md`, `docs/23_agent/agent_02_runtime-architecture.md`
- `scripts/agent/orchestrator.py`, `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/llm_turn_executor.py`, `scripts/agent/llm_turn_runner.py` (read for the trace; edit only if the trace shows a real defect)
- `tests/agent/test_orchestrator.py`, `tests/agent/test_llm_turn_runner.py`

## Required Changes
- Trace the production call path and identify the logical loop owner, the construction owner, and the per-turn runner lifecycle.
- Update ADR-014 Decision Details, Implementation Notes, and INV-02 wording so ownership and delegation are distinct and resilient to refactoring.
- Update the related Agent flow documents and replace stale method or class references.
- Add or update a regression test that detects duplicate or unused loop-owner instances.
- Confirm that persistent workflow decisions remain outside `LlmTurnExecutor` and `LLMTurnRunner`.

## Constraints
- No behavior change to the production turn path; edit scripts only if the trace reveals a real defect, and then report it.
- Do not weaken ADR-014 INV-01 to INV-03; an invariant wording change that alters its meaning needs an approval record.
- Documentation follows `skills/DESIGN.md` Docs content policy: responsibility and lifecycle, not implementation locations or signatures.

## Acceptance Criteria
- Exactly one component logically owns the LLM and tool round-trip loop, and the documented call path matches the production implementation.
- Delegation to `LLMTurnRunner` does not create a second authority in the text.
- A test fails if `Orchestrator` or another component retains an unused duplicate executor.
- No persistent workflow-state responsibility is moved into the turn loop.

## Testing Expectations
- A regression test asserting a single constructed executor and no unused instance (for example, counting construction through a patched factory), added to `tests/agent/test_orchestrator.py`.
- `uv run pytest tests/agent/test_orchestrator.py tests/agent/test_llm_turn_runner.py`, `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_adr_preservation.py`, `uv run python tools/check_docs_consistency.py --domain agent`.

## Documentation Impact
Yes. ADR-014 and the Agent flow documents must state logical ownership, construction ownership, and per-turn lifecycle accurately; per `tools/check_adr_preservation.py`, a rewording of an ADR must not change its decisions.

## Out of Scope
- Merging or restructuring `LlmTurnExecutor`, `LLMTurnRunner`, or `ToolExecutor` (a redesign listed as out of scope in ADR-014).
- Changing the Workflow Engine's mandatoriness (ADR-001) or the persistent-state rules.
- Unrelated refactoring or formatting-only changes.

## Dependencies
N/A: none. No open issue or in-flight plan under `issues/` or `plans/` targets these files (checked with `rg -l` on the target paths).

## Unresolved Questions
- `Needs confirmation`: whether INV-02's "the one component that actually drives the loop" is intended to be `Orchestrator` (the creator) or `WorkflowEngineAdapter` (the caller); this decides the replacement wording.
- `Needs confirmation`: whether any existing test already asserts that no duplicate or unused executor exists.
- `Needs confirmation`: which Agent flow documents beyond the three named above carry stale wording (reference documents are generated and should be regenerated, not hand-edited).

## AI Implementation Instruction
- Read ADR-014, ADR-001, and the four scripts before editing; trace the call path first and cite what it shows.
- Change wording and tests only; do not alter ADR-014's invariants' meaning or the production code.
- Stop and report open questions about INV-02's intended owner instead of choosing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-104510
- **Related target files**: `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`, `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md`, `docs/23_agent/agent_03_01_turn-processing-flow-overview.md`, `docs/23_agent/agent_02_runtime-architecture.md`, `scripts/agent/orchestrator.py`, `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/llm_turn_executor.py`, `scripts/agent/llm_turn_runner.py`, `tests/agent/test_orchestrator.py`, `tests/agent/test_llm_turn_runner.py`
