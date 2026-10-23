---
title: "Agent Turn Processing Flow - LLM and Tool Loop"
area: agent
tags:
  - agent
  - turn-processing
  - llm-tool-loop
related:
  - agent_03_01_turn-processing-flow-overview.md
  - agent_03_03_turn-processing-flow-workflow-engine.md
  - agent_00_document-guide.md
  - agent_04_01_state-and-persistence-state-model.md
  - agent_02_runtime-architecture.md
---
# Agent Turn Processing Flow - LLM and Tool Loop

- Runtime Architecture → [agent_02_runtime-architecture.md](agent_02_runtime-architecture.md)

## Purpose

To document the processing flow for LLM invocation and the tool loop. This includes collecting streaming responses, handling multiple tool calls, and describing the guard mechanisms.

## Design Intent

### Role and Design of ToolLoopGuard

Within the tool loop, an LLM may potentially call the same tool infinitely. To prevent this, `ToolLoopGuard` sequentially executes the following guards:

1. **Cycle Detection** — If the same set of tool calls is repeated within the last N rounds.
2. **Deduplication** — If the same `(name, args)` is detected more than a certain number of times.
3. **Retry Suppression** — If a failed tool call is invoked again with the same arguments.
4. **Consecutive Errors** — If all tools in a round fail consecutively for a certain number of rounds.
5. **Empty Result Repeat** — If the same tool returns empty results repeatedly within a single turn.

If any guard is triggered, subsequent checks are skipped and the loop terminates. After a guard is triggered, a fallback attempt is made to generate a final answer without calling any further tools.

### Two-Layer Retry Landscape

The turn loop has two independent retry mechanisms at different granularities:

| Layer | Config field | Scope | Relationship to other layers |
|---|---|---|---|
| ToolLoopGuard retry suppression | `tool_error_retry_max` | Per-turn, per-(tool, args) pair within a single LLM turn's tool loop | Independent from WorkflowEngine retry; prevents same (tool, args) from being retried within one turn |
| WorkflowEngine stage-level retry | `workflow_engine.retry_policy.max_attempts` | Stage-level across turns; retries entire workflow stages on failure | Independent from ToolLoopGuard; operates across turns at the workflow level |

**Key distinction**: These mechanisms do NOT compose. A ToolLoopGuard retry block does NOT reduce WorkflowEngine retry budget, They operate at orthogonal levels of the stack.

### Isolation of Incomplete Outputs

If a transport error occurs during LLM streaming resulting in a partial completion, that output is isolated from the regular conversation history. This prevents polluting subsequent LLM context. Partial content is stored in the `session_diagnostics` table and can be inspected via the `/stats` command.

## Responsibility Boundary

### LLM Invocation and Tool Loop

`LlmTurnExecutor.handle_llm_turn(llm_url)` manages the internal loop:

- Constructs payload: `history + tool_definitions + temperature + max_tokens + stream=True`
- Sends to LLM via SSE streaming.
- Collects `content_parts` (text) and `tool_calls_map` (function calls).
- If `finish_reason == "tool_calls"`: Execute tools → Add results → Re-send to LLM.
  - Repeats up to `max_tool_turns` times.
- If `finish_reason == "stop"` or `max_tool_turns` exceeded: Return final answer.

### Adding to History

`ctx.conv.append_message()` is a validated method; history must only be modified through this method rather than raw `list.append()` (the method validates the message and, on failure, sanitizes it or drops it) (Explicit in code — `scripts/agent/context.py::append_message`).

### Final Answer Fallback on Guard Trigger

When a guard is triggered, the system attempts to re-invoke the LLM by injecting a temporary system message:

- The injected system message instructs the model to answer using only information already in the conversation history.
- Executes LLM call with `tool_defs=[]`.
- If `finish_reason != "tool_calls"`: Returns the answer text.
- If `finish_reason == "tool_calls"`: Returns failure.

A guard trip before the assistant message is persisted writes nothing: the unexecuted assistant message is not persisted. A round that fails after the persist leaves a complete round: the assistant message plus one `role='tool'` row per declared `tool_call_id`, the missing ones synthesized by `execute_all_tool_calls()`.

### Hints on Guard Triggering

Upon each guard trigger (cycle, dedup, retry, empty_result_repeat), a hint describing the detected pattern is saved to `session_diagnostics` with `kind='guard_hint'`.

These hints are stored exclusively for offline diagnostics and are NOT injected into `ctx.conv.history`. They are distinct from the short messages displayed to the user at the end of the loop.

## Key Constraints

### Message Type Whitelist

Messages constructed by the LLM client's streaming aggregation logic consist only of `role`/`content`/`tool_calls`, ensuring validation always succeeds. The saved content remains consistent with previous raw `.append()` calls.

### Handling Incomplete Outputs

- When a transport error occurs, if `partial_text` is not empty, it is persisted to `session_diagnostics` with an `[INCOMPLETE: {kind}]` prefix.
- It is NOT added to `ctx.conv.history`.
- After each turn, the REPL compares `stat_partial_completions`; if it has increased, a warning is issued.

### Consecutive Tool Errors

- If all tools in a round fail `tool_error_max_consecutive` times consecutively, the tool loop exits.
- For partial failures (only some tools fail), the counter is maintained and reset upon a fully successful round.

## Operational Notes

- Guard-trigger fallback, incomplete-output inspection via `/stats`, and the opt-in thresholds are described in Final Answer Fallback on Guard Trigger, Isolation of Incomplete Outputs, and Known Limitations.

## Known Limitations

- Cycle detection is fingerprint-based, so tool calls that are functionally equivalent but have different orderings might not be detected as the same pattern.
- Retry suppression is effective only if `tool_error_retry_max > 0`, and empty result repeat detection only if `tool_empty_result_max_repeats > 0`. The tool loop guard logs the effective on/off state of both once at startup (`agent.tool_loop_guard startup diagnostic`). See `scripts/agent/tool_loop_guard.py`.

## Keywords

- LLM invocation and tool loop
- TurnLoopState
- guard methods
- error handling
- validated history append
- append_message
