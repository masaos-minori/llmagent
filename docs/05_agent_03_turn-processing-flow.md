# Agent Turn Processing Flow

- Runtime architecture → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## Purpose

Document the exact sequence of operations in one conversation turn, including state
transitions, error handling paths, and partial completion behavior.

---

## One-Turn Processing Flow

```
User input (line)
  │
  ├─ line.startswith("/")
  │    └─ CommandRegistry.dispatch(line)     — slash command; no LLM call
  │
  └─ Orchestrator.handle_turn(line)
       │
       ① _handle_turn_start(line)
       │    → generate UUID4 current_turn_id
       │    → emit audit log: turn_start
       │
       ② _handle_memory_injection(line)        [if use_memory_layer=True]
       │    → MemoryInjectionService.on_user_prompt(query, session_id)
       │    → inject memory snippets as "system" role messages
       │    → set _memory_injected=True
       │
       ③ _append_user_message()
       │    → append user message to ctx.conv.history
       │    → AgentSession.save("user", content)
       │    → (first turn only) asyncio.create_task(_generate_session_title)
       │
       ④ _handle_history_compression()
       │    → HistoryManager.compress(history)
       │    → replaces oldest turns with LLM summary if over char/token limit
       │
       ⑤ _handle_llm_turn(llm_url)
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
       ⑥ _handle_turn_end(line, answer, turn_started_at, error_kind)
            → emit audit log: turn_end (elapsed_ms, token counts, reconnect count, etc.)
            → ctx.turn.current_turn_id = None
```

---

## Memory Injection Detail

- Triggered at step ② when `AgentConfig.use_memory_layer=True`
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

---

## LLM Invocation and Tool Loop

`LLMTurnRunner.run(llm_url)` manages the inner loop:

1. Build payload: `history + tool_definitions + temperature + max_tokens + stream=True`
2. Send to LLM via SSE streaming
3. Collect `content_parts` (text) and `tool_calls_map` (function calls)
4. If `finish_reason == "tool_calls"`:
   - Execute tools → append results → re-send to LLM
   - Repeat up to `max_tool_turns` times
5. If `finish_reason == "stop"` or `max_tool_turns` exceeded: return final answer

`ToolLoopGuard` guards during each tool loop iteration:
- **Dedup:** same `(name, args)` seen > `tool_dedup_max_repeats` times → inject hint
- **Cycle detection:** same tool sequence in last `tool_cycle_detect_window` rounds → warn
- **Retry:** errored `(name, args)` called again > `tool_error_retry_max` → block
- **Consecutive error:** all tools in a round errored `tool_error_max_consecutive` times → break loop

---

## Error Handling

### LLM Transport Error (pre-stream)

Condition: `LLMTransportError` raised before any content received (`partial_text == ""`).

Action:
- Do NOT save assistant message to history
- Pop the user message from history (prevents history contamination)
- Display error to user; REPL continues

### LLM Transport Error (partial completion)

Condition: `LLMTransportError` with non-empty `partial_text`.

Action:
- **Diagnostic channel only**: persist `[INCOMPLETE: {kind}]` prefixed message via `ctx.session.save_diagnostic()` — role `"diagnostic"`, NOT added to `ctx.conv.history`
- Save failure detail to `ctx.tool_result_store` (accessible via `/tool show llm_partial_completion`)
- `stat_partial_completions += 1`

Incomplete outputs are isolated from normal conversation history so they do not pollute future LLM context. The partial content remains accessible through `/tool show` and DB queries on the `messages` table (role = `"diagnostic"`).

### Tool Continuation Failure (turn > 0)

Condition: LLM transport error occurs during a tool continuation turn.

Action:
- Add synthetic `tool` role error message (`name="llm_transport_error"`) to history
- Store failure in `tool_result_store`
- Conversation continues (LLM sees the error as a tool result)

### Consecutive Tool Errors

Condition: every tool in a round fails `tool_error_max_consecutive` times in a row.

Action:
- Break out of tool loop
- Return `"Too many consecutive tool errors."` message

---

## WorkflowEngine Integration

`Orchestrator.handle_turn()` runs via `WorkflowEngine` when `config/workflows/default.json`
exists and workflow DB is available. Workflow state is the primary execution model;
conversation history is maintained as a subordinate concern.

Each turn creates a `task` / `attempt` / `event` record in `workflow.sqlite`:
- `tasks` — one per turn; status: `pending → running → [pending_approval →] completed | halted | failed`
- `attempts` — one per stage execution (plan/execute/verify), with retry tracking
- `approvals` — one per approval gate; status: `pending → approved | rejected`
- `artifacts` — URIs produced by stage callbacks

Fallback: if `config/workflows/default.json` is missing or workflow DB is unavailable,
the traditional direct-execution flow is used.

Workflow package: `agent/workflow/` (models, workflow_loader, state_store, workflow_engine).

### Approval Gate

When `WorkflowEngine(require_approval=True)`, the engine suspends after the execute stage
completes and before the verify stage runs:

1. Engine calls `store.request_approval(task_id)` → `ApprovalRecord` with `status=pending`
2. Task status → `pending_approval`
3. `WorkflowPendingApprovalError` raised → orchestrator stores `approval_id` in `ctx.turn.pending_approval_id`
4. User runs `/approve [reason]` or `/reject [reason]`
5. On next workflow run with the same task, engine checks approval status:
   - `approved` → continue to verify stage
   - `rejected` → `WorkflowHaltError` raised; task halted

---

## State Changes per Turn

| Stage | State mutated |
|---|---|
| ① TurnStart | `ctx.turn.current_turn_id` = UUID4 |
| ② Memory injection | `ctx.conv.history` prepended with system message |
| ③ User append | `ctx.conv.history` += user message; `ctx.stats.stat_turns += 1` |
| ④ Compression | `ctx.conv.history` oldest turns replaced with summary |
| ⑤ LLM + tools | `ctx.conv.history` += assistant + tool messages; stats updated |
| ⑥ TurnEnd | `ctx.turn.current_turn_id` = None |
