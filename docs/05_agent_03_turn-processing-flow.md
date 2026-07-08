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
- On LLM failure while over char limit: drops lowest-importance messages
  (tool-role first, then sorted by `classify_importance` ascending) until under limit
- Fallback count tracked in `stat_fallback_truncate_count`; visible via `/context` as "Fallback trunc"

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

### LLM Transport Error (pre-stream)

Condition: `LLMTransportError` raised before any content received (`partial_text == ""`).

Action:
- Do NOT save assistant message to history
- Pop the user message from history (prevents history contamination)
- Display error to user; REPL continues

### LLM Transport Error (partial completion)

Condition: `LLMTransportError` with non-empty `partial_text`.

Action:
- **Diagnostic channel only**: persist `[INCOMPLETE: {kind}]` prefixed message via `ctx.session.save_diagnostic()` — NOT added to `ctx.conv.history` (stored in `session_diagnostics` table via `DiagnosticStore`)
- `stat_partial_completions += 1`

Incomplete outputs are isolated from normal conversation history so they do not pollute future LLM context. The partial content remains accessible through DB queries on the `session_diagnostics` table.

After each turn, the REPL line dispatcher compares `stat_partial_completions` before and after `handle_turn()`. If it increased, a user-visible warning is printed:

```
[warn] Partial LLM completion stored. Use /stats to see count or query session_diagnostics table.
```

`/stats` also shows the count when > 0: `Partial compl : N  (stored in session_diagnostics)`.

### Tool Continuation Failure (turn > 0)

Condition: LLM transport error occurs during a tool continuation turn.

Action:
- Add synthetic `tool` role error message (`name="llm_transport_error"`) to history
- Store failure in `session_diagnostics`
- Conversation continues (LLM sees the error as a tool result)

### Consecutive Tool Errors

Condition: every tool in a round fails `tool_error_max_consecutive` times in a row.

Action:
- Break out of tool loop
- Return `"Too many consecutive tool errors."` message

---

## Partial-Completion Model

A partial completion occurs when the LLM response stream is interrupted before all content is received.

| Trigger | Stored where | Visible via | `stat_partial_completions` |
|---|---|---|---|
| `LLMTransportError` with non-empty `partial_text` | `session_diagnostics` table | `/stats` | +1 |
| `LLMTransportError` with empty `partial_text` (pre-stream) | Not stored (user message popped from history) | User-visible error message | no change |

**Key invariant:** partial content is NEVER added to `ctx.conv.history`. It is isolated in the diagnostic channel so it cannot pollute future LLM context.

After each turn, the REPL line dispatcher checks if `stat_partial_completions` increased. If so:

```
[warn] Partial LLM completion stored. Use /stats to see count or query session_diagnostics table.
```

See §LLM Transport Error (partial completion) above for implementation details.
For persistence behavior → [05_agent_04 §Message save rules](05_agent_04_state-and-persistence.md).
For operator monitoring → [05_agent_10 §Interpreting /stats](05_agent_10_operations-and-observability.md).

---

## WorkflowEngine Integration

`Orchestrator.handle_turn()` runs via `WorkflowEngine` when `config/workflows/default.json`
exists and workflow DB is available. Workflow state is the primary execution model;
conversation history is maintained as a subordinate concern.

Each turn creates a `task` / `attempt` / `processed_event` record in `workflow.sqlite`:
- `tasks` — one per turn; status: `pending → running → [pending_approval →] completed | halted | failed`
- `attempts` — one per stage execution (plan/execute/verify), with retry tracking
- `processed_events` — idempotency enforcement; prevents duplicate stage execution
- `approvals` — one per approval gate; status: `pending → approved | rejected`
- `artifacts` — URIs produced by stage callbacks

Workflow stages (defined in `default.json`):
- `plan` — LLM generates initial plan; required
- `execute` — LLM executes the plan; required
- `verify` — LLM verifies execution results; required
- `retry` — optional transport error retry gate after `execute`; `retryable: false`; presence not required for `WorkflowEngine` operation

Each stage has a `StageDefinition`:
- `id` — unique stage identifier (e.g., "plan", "execute")
- `description` — human-readable description
- `timeout_sec` — maximum execution time in seconds
- `retryable` — whether the stage can be retried on failure

`WorkflowDef.get_stage(stage_id)` — returns the `StageDefinition` for the given id, or `None`.

Fallback: if `config/workflows/default.json` is missing or workflow DB is unavailable,
the traditional direct-execution flow is used.

Workflow package: `agent/workflow/` (models, workflow_loader, state_store, workflow_engine).

Default retry policy (applied when no `retry_policy` defined in `default.json`):
- `max_attempts`: 3
- `backoff`: "fixed"
- `backoff_sec`: 1

### Workflow Status

`Orchestrator.workflow_status()` returns a dict with two keys:
- `mode`: "auto" | "required" | "disabled" — from workflow policy
- `tracking`: "enabled" | "not_loaded" — "enabled" if workflow definition is set, "not_loaded" otherwise

### Approval Gate

When `WorkflowEngine(require_approval=True)`, the engine suspends after the execute stage
completes and before the verify stage runs:

1. Engine calls `store.request_approval(task_id)` → `ApprovalRecord` with `status=pending`
2. Task status → `pending_approval`
3. `WorkflowPendingApprovalError` raised → orchestrator stores `approval_id` in `ctx.turn.pending_approval_id`; logs WARNING: `[workflow] Approval required. Use /approve [reason] or /reject [reason].`

When the user runs `/approve [reason]` or `/reject [reason]`, the approval record is updated
in the DB. On the next workflow run with the same task, the gate checks the existing
approval record:

- `status=approved` → passes through to verify stage
- `status=rejected` → `WorkflowHaltError` raised; task halted
- `status=pending` → `WorkflowPendingApprovalError` re-raised (user has not yet responded)

If no existing approval record is found, a new one is created and the workflow is suspended.

### Workflow Exceptions

| Exception | When Raised |
|---|---|
| `WorkflowTimeoutError` | Stage execution exceeds `timeout_sec` |
| `WorkflowHaltError` | Task is halted (e.g., via `/halt` or after rejection) |
| `WorkflowPendingApprovalError` | Approval gate requires user action before proceeding |
| `WorkflowLoadError` | Workflow definition fails validation or loading |

### Retry Mechanism

When a stage is `retryable: true`, the engine uses the retry policy to determine retry behavior:
- `max_attempts`: Maximum number of attempts (default 3)
- `backoff`: Retry strategy — "fixed" or "exponential" (both use the same delay logic)
- `backoff_sec`: Delay between retries in seconds (default 1; always used as-is regardless of backoff type — both "fixed" and "exponential" apply the same constant delay)

### Workflow Loader Validation Rules

When loading a workflow definition from `config/workflows/*.json`:
- Required top-level keys: `name`, `version`, `stages`, `retry_policy`
- `stages` must be a non-empty list
- No duplicate stage IDs allowed
- Required stages: `plan`, `execute`, `verify` (must all be present)
- Each stage must have: `id`, `description`, `timeout_sec`, `retryable`
- `retry_policy.max_attempts` must be >= 1
- `retry_policy.backoff` must be "fixed" or "exponential"
- `retry_policy.backoff_sec` must be >= 0

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

## Turn-State Mutation Reference

| State field | Mutated When | Durable? | Notes |
|---|---|---|---|
| `ctx.conv.history` | Each LLM/tool round (append) | Yes — saved to SQLite per message | Also compressed by HistoryManager |
| `ctx.turn.current_turn_id` | TurnStart (UUID4) / TurnEnd (None) | No — in-memory only | Used for per-turn correlation |
| `ctx.turn.pending_approval_id` | Workflow approval gate suspension | No — in-memory; approval persisted in `workflow.sqlite` | Reset to None on next turn |
| `ctx.stats.stat_turns` | After each user message appended | No — in-memory (reported via `/stats`) | Reset on session restart |
| `ctx.stats.stat_partial_completions` | When LLM stream interrupted | No — in-memory; partial content in `session_diagnostics` | Reset on session restart |
| `session.title` | First turn (async background task) | Yes — SQLite `sessions.title` | Non-blocking; fallback to truncated first input on LLM failure |
