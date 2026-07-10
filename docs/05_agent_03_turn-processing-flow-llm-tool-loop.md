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

ansport Error (pre-stream)

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
For persistence behavior → [05_agent_04 §Message save rules](05_agent_04_state-and-persistence-state-model.md).
For operator monitoring → [05_agent_10 §Interpreting /stats](05_agent_10_operations-and-observability-startup-and-health.md).

---

## WorkflowEngine Integration

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
