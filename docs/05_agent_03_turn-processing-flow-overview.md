---
title: "Agent Turn Processing Flow"
category: agent
tags:
  - agent
  - agent
  - turn
  - processing
  - flow
  - orchestrator
related:
  - 05_agent_00_document-guide.md
---

# Agent Turn Processing Flow

```
User input (line)
  │
  ├─ line.startswith("/")
  │    └─ CommandRegistry.dispatch(line)     — slash command; no LLM call
  │
  └─ Orchestrator.handle_turn(line)
       │
       ① Turn start handling
       │    → generate UUID4 current_turn_id
       │    → emit audit log: turn_start
       │
       ② Memory injection                       [if use_memory_layer=True]
       │    → MemoryInjectionService.on_user_prompt(query, session_id)
       │    → inject memory snippets as "system" role messages
       │          → sets memory_injected flag
       │
       ③ Append user message
        │    → append user message to ctx.conv.history
        │    → AgentSession.save("user", content)
        │    → (first turn only) asyncio.create_task for session title generation
        │
        ④ Handle history compression
       │    → HistoryManager.compress(history)
       │    → replaces oldest turns with LLM summary if over char/token limit
       │
       ⑤ LLM turn handling
       │    → LLMTurnRunner.run(llm_url)
       │         ├─ LLMClient.stream(url, history, tool_defs)
       │         │    → SSE streaming → on_token callbacks → CLIView.write_token()
       │         │    → collect content_parts + tool_calls_map
       │         │
       │         └─ Tool loop (inner, up to max_tool_turns=5):
       │              → execute_all_tool_calls()
       │                   → parallel (asyncio.gather) unless side-effect tools present
       │                   → ToolExecutor.execute(tool_name, args)
       │                   → append tool results to history as "tool" role
       │              → re-send history to LLM
       │              → ToolLoopGuard: dedup / cycle / retry / consecutive-error guards
       │
       ⑥ Turn end handling
            → emit audit log: turn_end (elapsed_ms, token counts, reconnect count, etc.)
            → ctx.turn.current_turn_id = None
```

---

## Memory Injection Detail

-

 Triggered at step ② when `AgentConfig.use_memory_layer=True`
- `MemoryInjectionService.on_user_prompt()` retrieves relevant memories (FTS5 + optional KNN)
- Injected as a `"system"` role message prepended to the turn
- `/undo` removes these injected messages along with the user+assistant turn

---

## History Compression Detail



- Triggered at step ④ every turn (no-op if below threshold)
- `HistoryManager.compress()` checks `context_char_limit` (chars) AND `context_token_limit` (tokens)
- `HistorySelectionPolicy` selects oldest turns by importance score and category:
  - `temporary` (tool role) → lowest retention priority
  - `temporary_reasoning` (assistant with tool_calls) → low priority
  - `factual` (system) → preserved
  - `history` (user/assistant text) → normal priority
- Most recent `history_protect_turns` (default 2) turn pairs are always protected
- On success: `CLIView.write_compress_notice(n)` displays compression notice
- On LLM failure while over char limit: drops lowest-importance messages
  (tool-role first, then sorted by `classify_importance` ascending) until under limit
- Fallback count tracked in `stat_fallback_truncate_count`; visible via `/context` as "Fallback trunc"

---

## LLM Invocation and Tool Lo

op

`LLMTurnRunner.run(llm_url)` manages the inner loop:

1. Build payload: `history + tool_definitions + temperature + max_tokens + stream=True`
2. Send to LLM via SSE streaming
3. Collect `content_parts` (text) and `tool_calls_map` (function calls)
4. If `finish_reason == "tool_calls"`:
   - Execute tools → append results → re-send to LLM
   - Repeat up to `max_tool_turns` times
5. If `finish_reason == "stop"` or `max_tool_turns` exceeded: return final answer



`ToolLoopGuard` guards during each tool loop iteration:
- **Dedup:** same `(name, args)` seen ≥ `tool_dedup_max_repeats` times → terminate loop;
  user sees `"Repeated tool call detected."`; hint stored in `session_diagnostics`
  (`kind='guard_hint'`, `guard_type='dedup'`).
- **Cycle detection:** same tool-call fingerprint repeated in the last
  `tool_cycle_detect_window` rounds → terminate loop;
  user sees `"Cyclic tool call pattern detected."`;
  hint stored in `session_diagnostics` (`kind='guard_hint'`, `guard_type='cycle'`).
- **Retry:** errored `(name, args)` called again → terminate loop;
  user sees `"Repeated failed tool call detected."`;
  hint stored in `session_diagnostics` (`kind='guard_hint'`, `guard_type='retry'`).
- **Consecutive error:** all tools in a round errored `tool_error_max_consecutive` times
   → terminate loop; user sees `"Too many consecutive tool errors."`.

### TurnLoopState dataclass

Holds per-turn loop state:

| Field | Type | Description |
|---|---|---|
| `seen_calls` | `set[str]` | Tool call fingerprints seen in current turn |
| `failed_calls` | `set[str]` | Failed tool call fingerprints |
| `consecutive_errors` | `int` | Count of consecutive rounds where all tools failed |
| `round_fingerprints` | `list[str]` | Fingerprints from last N rounds (cycle detection window) |

### Guard methods

| Method | Responsibility |
|---|---|
| `check_all(seen_calls, round_fingerprints, failed_calls, message)` | Run dedup, cycle, and retry checks; return hint if any guard triggers |
| `check_error_limit(consecutive_errors)` | Check consecutive error limit; return message if exceeded |

### Guard constants

| Constant | Value | Purpose |
|---|---|---|
| `DEDUP_HINT` | `"Repeated tool call detected. Use /context to see conversation."` | Dedup guard hit message |
| `CYCLE_HINT` | `"Cyclic tool call pattern detected."` | Cycle detection guard hit message |
| `RETRY_HINT` | `"Repeated failed tool call detected."` | Retry guard hit message |

> **Note:** Guard hints (`DEDUP_HINT`, `CYCLE_HINT`, `RETRY_HINT`) are stored in
> `session_diagnostics` under `kind='guard_hint'` for offline diagnostics only.
> They are **not** injected into `ctx.conv.history` and the LLM does not see them.
> The loop terminates immediately on any guard hit.

---

## Error Handling

### LLM Tr

## Related Documents

- `agent`
- `turn`
- `processing`

## Keywords

agent
turn
processing
flow
orchestrator
