# Agent Turn Processing Flow - LLM and Tool Loop

- Runtime Architecture $\rightarrow$ [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## Purpose

To document the processing flow for LLM invocation and the tool loop. This includes collecting streaming responses, handling multiple tool calls, and describing the guard mechanisms.

## Design Intent

### Role and Design of ToolLoopGuard

Within the tool loop, an LLM may potentially call the same tool infinitely. To prevent this, `ToolLoopGuard` sequentially executes four guards:

1. **Cycle Detection** — If the same set of tool calls is repeated within the last $N$ rounds.
2. **Deduplication** — If the same `(name, args)` is detected more than a certain number of times.
3. **Retry Suppression** — If a failed tool call is invoked again with the same arguments.
4. **Consecutive Errors** — If all tools in a round fail consecutively for a certain number of rounds.

If any guard is triggered, subsequent checks are skipped and the loop terminates. After a guard is triggered, a fallback attempt is made to generate a final answer without calling any further tools.

### Isolation of Incomplete Outputs

If a transport error occurs during LLM streaming resulting in a partial completion, that output is isolated from the regular conversation history. This prevents polluting subsequent LLM context. Partial content is stored in the `session_diagnostics` table and can be inspected via the `/stats` command.

## Responsibility Boundary

### LLM Invocation and Tool Loop

`LLMTurnRunner.run(llm_url)` manages the internal loop:

- Constructs payload: `history + tool_definitions + temperature + max_tokens + stream=True`
- Sends to LLM via SSE streaming.
- Collects `content_parts` (text) and `tool_calls_map` (function calls).
- If `finish_reason == "tool_calls"`: Execute tools $\rightarrow$ Add results $\rightarrow$ Re-send to LLM.
  - Repeats up to `max_tool_turns` times.
- If `finish_reason == "stop"` or `max_tool_turns` exceeded: Return final answer.

### Adding to History

`ctx.conv.append_message()` is a validated method; history must only be modified through this method rather than raw `list.append()` (See [05_agent_04_01_state-and-persistence-state-model.md] Validated History Modification Methods).

### Final Answer Fallback on Guard Trigger

When a guard is triggered, the system attempts to re-invoke the LLM by injecting a temporary system message:

- System Message: "You are about to produce a final answer without calling any tools. Use only the information already available in the conversation history."
- Executes LLM call with `tool_defs=[]`.
- If `finish_reason != "tool_calls"`: Returns the answer text.
- If `finish_reason == "tool_calls"`: Returns failure.

The original unexecuted assistant message is not persisted.

### Hints on Guard Triggering

Upon each guard trigger, a hint is saved to `session_diagnostics` with `kind='guard_hint'`:

| Guard Type | Hint Content |
|---|---|
| cycle | "A cyclic planning pattern was detected: the same set of tool calls is being requested repeatedly across multiple rounds." |
| dedup | "The same tool was called with identical arguments multiple times." |
| retry | "A tool call that previously failed is being retried with the same arguments." |

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

- The final answer fallback after a guard trigger uses a temporary system message to prompt the LLM to respond without tools.
- Incomplete outputs can be checked via the `/stats` command but cannot be accessed via normal conversation history.

## Known Limitations

- Cycle detection is fingerprint-based, so tool calls that are functionally equivalent but have different orderings might not be detected as the same pattern.
- Retry suppression is only effective if `tool_error_retry_max > 0`.

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_03_01_turn-processing-flow-overview.md`
- `05_agent_03_03_turn-processing-flow-workflow-engine.md`
- `05_agent_04_01_state-and-persistence-state-model.md`

## Keywords

LLM invocation and tool loop
TurnLoopState
guard methods
error handling
validated history append
append_message
