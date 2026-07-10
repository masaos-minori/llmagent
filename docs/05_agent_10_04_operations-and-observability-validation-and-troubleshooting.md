---
title: "Agent Operations and Observability - Validation and Troubleshooting"
category: agent
tags:
  - agent
  - operations
  - startup-validation
  - mcp-reload
  - troubleshooting
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 05_agent_10_03_operations-and-observability-workflow-observability.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# Agent Operations and Observability

- Configuration → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## Workflow Startup Validation

The agent unconditionally validates that a workflow definition file exists before
initializing the orchestrator — there is no config setting to disable or degrade this
(verified 2026-07-09: `workflow_mode` is not a valid config key — see
[Configuration: AgentConfig Structure](05_agent_08_01_configuration-loading-agent-config.md#agentconfig-structure)).
If the file is missing, a `RuntimeError` is raised with actionable guidance.

**Expected path:** `config/workflows/default.json`

**Remediation:** Deploy the workflow definition to the expected path. There is no config
toggle to skip this check — a config file that previously set `workflow_mode = "disabled"`
or `"auto"` will now fail to load entirely (`ConfigLoadError`, since `workflow_mode` is a
rejected key), rather than reaching the workflow check at all.

The preflight check (`StartupOrchestrator._check_workflow_definition()` in
`agent/startup.py`, wrapping `check_workflow_definition()` in `agent/repl_health.py`) runs
before `Orchestrator.__init__()` and produces a clear error message rather than a cryptic
`WorkflowLoadError` that may not include the expected file path. `Orchestrator.__init__()`
itself also unconditionally raises `RuntimeError` if `WorkflowLoader().load()` fails for any
other reason once past the preflight check.

**Note:** This validation always runs once at agent boot — it is not a config setting and
cannot be changed via `/reload`. Any fix requires deploying the workflow definition file and
restarting the agent.

---

## MCP Server Reload and Restart Semantics

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
Context state:
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
Turns: 5 | Tool calls: 12 | Errors: 1
LLM: retries=0, reconnects=0, HB timeouts=0, partials=0, parse_errors=0
Cache hits: 3 | Compress: 1 | Semantic cache hits: 0
Input tokens: 2,048 | Output tokens: 512
Latency (mean/max): llm=1.2s/2.1s, tools=0.3s/0.8s
```

- **Partial completions:** LLM responses interrupted mid-stream are recorded; check `session_diagnostics` (`kind=partial_completion`) for details. For the canonical partial-completion model → [05_agent_03 §Partial-Completion Model](05_agent_03_01_turn-processing-flow-overview.md)
- **HB timeouts:** SSE heartbeat timeouts (possible LLM overload)
- **Cache hits:** tool result cache hits
- **Approval pending:** `Approval: PENDING — use /approve or /reject` line appears only when `ctx.workflow.approval_pending=True`. Shown when a workflow task is waiting for `/approve` or `/reject`.

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_10_01_operations-and-observability-startup-and-health.md`
- `05_agent_10_02_operations-and-observability-audit-and-otel.md`
- `05_agent_10_03_operations-and-observability-workflow-observability.md`
- `05_agent_10_05_operations-and-observability-monitoring.md`
- `05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`

## Keywords

workflow startup validation
MCP server reload
/context
/stats
partial completion
troubleshooting
