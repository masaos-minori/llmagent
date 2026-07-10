---
title: "Agent Operations and Observability"
category: agent
tags:
  - agent
  - agent
  - operations
  - observability
  - monitoring
related:
  - 05_agent_00_document-guide.md
---

# Agent Operations and Observability

ntics

**Note:** MCP server definitions (`transport`, `url`, `startup_mode`,
`healthcheck_mode`, `call_timeout_sec`, `startup_timeout_sec`, `tool_names`,
`auth_token`, `role`, `cmd`, `env`) are restart-time snapshots. `/reload`
detects changes to `[mcp_servers.*]` and reports them as restart-required
(`[RESTART] - mcp/<server>.<field>`), but never applies them to the running
process. `/mcp` / `/mcp status` always reflects the running (pre-restart)
server config, not pending `/reload` changes. Watchdog-triggered restarts
(`watchdog_loop()`) restart a failed subprocess using its *current* startup
config — this is health-driven recovery, not config reload, and does not
apply pending MCP server definition changes either. Only a full agent
restart applies a changed MCP server definition.

**Note:** MCP server definitions (`transport`, `url`, `startup_mode`,
`healthcheck_mode`, `call_timeout_sec`, `startup_timeout_sec`, `tool_names`,
`auth_token`, `role`, `cmd`, `env`) are restart-time snapshots. `/reload`
detects changes to `[mcp_servers.*]` and reports them as restart-required
(`[RESTART] - mcp/<server>.<field>`), but never applies them to the running
process. `/mcp` / `/mcp status` always reflects the running (pre-restart)
server config, not pending `/reload` changes. Watchdog-triggered restarts
(`watchdog_loop()`) restart a failed subprocess using its *current* startup
config — this is health-driven recovery, not config reload, and does not
apply pending MCP server definition changes either. Only a full agent
restart applies a changed MCP server definition.

---

## Interpreting `/context`

```
Conte

xt state:
  Messages        : 12
  Total chars     : 4,321
  Compress limit  : 8,000
  Remaining       : 3,679 chars until compression
  Compress count  : 1
  System prompt   : default
  System preview  : '...'
  Token estimate  : 1,080 (chars / 4)
  Token limit     : disabled
  Memory layer    : disabled
Budget breakdown:
  system        :    1,234 chars ( 38%)
   history       :    1,987 chars ( 62%)
```

- **Remaining:** distance from `context_char_limit` → compression trigger
- **Token estimate:** `chars / 4` unless `/tokenize` endpoint is configured
- **Token limit:** `disabled` when `context_token_limit` is not set; shows `200,000 tokens` (or configured value) when `context_token_limit` is configured
- **Memory layer:** `enabled (entries=N)` when `use_memory_layer=True`

---

## Interpreting `/stats`

```
Turns: 

5 | Tool calls: 12 | Errors: 1
LLM: retries=0, reconnects=0, HB timeouts=0, partials=0, parse_errors=0
Cache hits: 3 | Compress: 1 | Semantic cache hits: 0
Input tokens: 2,048 | Output tokens: 512
Latency (mean/max): llm=1.2s/2.1s, tools=0.3s/0.8s
```

- **Partial completions:** LLM responses interrupted mid-stream are recorded; check `session_diagnostics` (`kind=partial_completion`) for details. For the canonical partial-completion model → [05_agent_03 §Partial-Completion Model](05_agent_03_turn-processing-flow.md)
- **HB timeouts:** SSE heartbeat timeouts (possible LLM overload)
- **Cache hits:** tool result cache hits
- **Approval pending:** `Approval: PENDING — use /approve or /reject` line appears only when `ctx.workflow.approval_pending=True`. Shown when a workflow task is waiting for `/approve` or `/reject`.

---

## Partial Completion and Truncation 

Monitoring

| Condition | How to detect | Action |
|---|---|---|
| LLM stream interrupted (partial completion) | `/stats` shows `partials > 0`; agent log: `WARNING Partial LLM completion saved: {kind}` | Check `session_diagnostics` (`kind=partial_completion`) for details; check LLM endpoint stability |
| Context compression (HistoryManager) | `/stats` shows `Compress: N > 0`; agent log: `INFO Compressed history` | Increase `compression_char_threshold` or reduce context size |
| Max tool turns hit | Agent log: `WARNING max_tool_turns=N reached` | Increase `max_tool_turns` in `config/agent.toml` |

For the canonical partial-completion model → [05_agent_03 §Partial-Completion Model](05_agent_03_turn-processing-flow.md).

---

## Troubleshooting

| Symptom | Cause

## Related Documents

- `agent`
- `operations`
- `observability`

## Keywords

agent
operations
observability
monitoring
