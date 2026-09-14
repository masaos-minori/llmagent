# Document the relationship between WorkflowEngine's stage retry, ToolLoopGuard's retry-block counter, and LLM transport-level retry/reconnect

## Priority
Medium

## Summary
ADR-014 (Agent制御プレーンの責任境界) defines WorkflowEngine as the owner of "再試行" (retry). In practice, three independent components each hold a distinct notion of "retry" with their own configuration keys and no documented relationship to one another: `WorkflowEngine._run_stage_with_retry()` (persistent, stage-level, `retry_policy.max_attempts`), `ToolLoopGuard.check_retry()` (in-memory, per-turn, `tool_error_retry_max`, which *blocks* a repeated failing tool call rather than executing a retry), and LLM transport-level parameters (`llm_max_retries`, `sse_reconnect_max`, etc. in `config/agent.toml`) whose enforcing code location was not conclusively located during this issue's investigation. ADR-014's definition of WorkflowEngine as retry owner is not contradicted by any of these, but the relationship between the three is undocumented, which risks a future reader assuming ADR-014 means "no other component may have any retry-shaped logic" (too strict) or assuming these three are redundant/interchangeable (incorrect — they operate at different granularities for different purposes).

## Background
This issue follows a design review requested in this session covering six Agent/Workflow design questions (memo2.md), one of which was "retry ownerの一意化" (unique retry ownership). The investigating fork found three distinct retry-shaped mechanisms rather than one, and classified the finding as "not unified" but noted the granularities differ enough that this may be a documentation gap rather than an implementation defect — this issue is scoped accordingly (see Out of Scope).

## Problem
Confirmed by direct reading:
- `scripts/agent/workflow/workflow_engine.py` `_run_stage_with_retry()` (line ~231): retries a stage (`plan`/`execute`/`verify`) when `stage_def.retryable` is set, up to `self._wdef.retry_policy.max_attempts`, escalating to `WorkflowHaltError` on exhaustion. This is ADR-014's "Workflow Engine: ... 再試行" — persistent, cross-restart, one record per attempt via `begin_stage_if_new()`.
- `scripts/agent/tool_loop_guard.py` `check_retry()` (line ~281): tracks failed `(tool_name, args)` pairs in an in-memory, per-turn `TurnLoopState` and blocks (does not retry) a repeated tool call once `ctx.cfg.tool.tool_error_retry_max` (default 1) is exceeded. This guards against the LLM itself looping on a failing tool call — a different problem (runaway LLM behavior) from WorkflowEngine's stage-retry (recovering a transient stage failure).
- LLM transport-level retry/reconnect parameters (`llm_max_retries`, `llm_retry_base_delay`, `sse_reconnect_max` per `config/agent.toml`, referenced in ADR-002-adjacent documentation) were not found in `llm_turn_runner.py` or `llm_turn_executor.py` directly (0 grep hits); the actual enforcing code location is unresolved as of this issue's filing.
- No document (ADR, `docs/05_agent_*`, `docs/00_governance_03_issue-and-uncertainty-management.md`) states how these three interact — e.g. whether a stage-level retry can itself trigger a fresh `ToolLoopGuard` state, whether LLM transport reconnects count against `retry_policy.max_attempts`, or whether they are simply orthogonal and never compose.

## Reason for Change
An unstated relationship between three same-named ("retry") mechanisms at different layers is exactly the kind of ambiguity ADR-014 was written to close for WorkflowEngine/Orchestrator/LLMTurnRunner/ToolExecutor/MCP Server. Leaving `ToolLoopGuard`'s and the LLM transport layer's retry-shaped parameters undocumented relative to ADR-014 risks a future maintainer either duplicating WorkflowEngine's retry logic in one of these layers (violating ADR-014) or removing a layer's legitimate, differently-scoped guard on the mistaken belief that ADR-014 already prohibits it.

## Implementation Intent
Document, in each of the three components' own explanatory text (`workflow.md`-equivalent doc, code docstring, or a Known Issue/Review Trigger addition to ADR-014) what each layer's "retry"-shaped behavior actually does and why it does not conflict with WorkflowEngine's ownership of persistent-state retry per ADR-014. Locate and document the LLM transport-level retry/reconnect enforcement code path, which was not conclusively found during this issue's drafting.

## Target Files or Areas
- `docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md`
- `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md`
- `docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`
- `scripts/agent/tool_loop_guard.py`

## Required Changes
- Locate the actual code path enforcing `llm_max_retries`/`sse_reconnect_max`/`llm_retry_base_delay` (grep beyond `llm_turn_runner.py`/`llm_turn_executor.py` — check `scripts/shared/llm_sse_stream.py` and any lower-level LLM client/transport module) and record the finding.
- Add a short cross-reference note to ADR-014 (as a Review Trigger or Known Deviation, per which applies once the above is resolved) clarifying that `ToolLoopGuard.check_retry()` is a distinct, in-memory, per-turn *block* on LLM-repeated tool calls — not a retry executor — and does not compete with WorkflowEngine's stage-retry ownership.
- Add the same clarification to `docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md` near its existing `tool_error_retry_max` documentation (line ~49 per this issue's investigation).
- If the LLM transport-level retry is found to independently decide "give up" in a way that could compete with WorkflowEngine's stage-retry escalation (e.g. both independently deciding when to surface a terminal failure), flag that as a follow-up unresolved question rather than resolving it silently within this issue's scope.

## Constraints
Do not change `ToolLoopGuard`'s actual blocking behavior or `tool_error_retry_max`'s default value — this issue is documentation/clarification only unless the LLM transport-level investigation surfaces a genuine conflict requiring a design decision, in which case stop and raise it rather than silently implementing a fix.

## Acceptance Criteria
- ADR-014 or its Related Documents section links to updated documentation describing the three-layer retry landscape and why each is distinct from WorkflowEngine's retry ownership.
- The LLM transport-level retry/reconnect enforcement code path is located and cited by file path and function/class name.
- `docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`'s existing `tool_error_retry_max` documentation explicitly distinguishes it from `WorkflowEngine.retry_policy`.

## Testing Expectations
Not applicable for the documentation-only portion. If the LLM transport-level investigation surfaces a genuine behavioral conflict requiring a code change, that change (if any) would need its own test coverage — out of scope for this issue's initial documentation pass.

## Documentation Impact
This issue's entire initial scope is documentation (ADR-014, `docs/05_agent_03_02_*.md`, `docs/05_agent_06_03_*.md`).

## Out of Scope
- Redesigning `ToolLoopGuard` or unifying it with `WorkflowEngine`'s retry_policy — the investigation found no evidence this is currently causing incorrect behavior, only that the relationship is undocumented.
- The Tool Call-level idempotency/execution-ID gap — tracked separately (see related issue from the same design review).
- The Workflow/Agent/MCP timeout hierarchy — tracked separately (see related issue from the same design review).

## Dependencies
N/A: none — can be implemented independently, though it shares source context with the Tool Call idempotency and timeout-hierarchy issues filed from the same review.

## Unresolved Questions
Whether the LLM transport-level retry/reconnect parameters, once located, actually compose safely with WorkflowEngine's stage-retry escalation, or whether they can independently produce a conflicting "give up" decision — resolve during implementation by reading the actual enforcing code; if a genuine conflict is found, raise it as a follow-up rather than resolving it within this issue.

## AI Implementation Instruction
Locate the LLM transport-level retry code path first (this issue's primary open fact-finding item), then write the documentation changes described in Required Changes. Do not modify `ToolLoopGuard`'s or `WorkflowEngine`'s actual retry logic — this issue is scoped to documentation and cross-referencing, per Constraints.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-123659
- **Related target files**: docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md, docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md, docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md, scripts/agent/tool_loop_guard.py
