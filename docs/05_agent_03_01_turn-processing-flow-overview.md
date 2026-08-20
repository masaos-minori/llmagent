# Agent Turn Processing Flow - Overview

- Runtime Architecture $\rightarrow$ [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## Purpose

To document the exact sequence of operations in a single conversation turn, including state transitions, error handling paths, and behavior during partial completion.

## Design Intent

Execution via the workflow engine is mandatory. Failure to load workflow definitions is detected at startup as a `RuntimeError`, and there are no fallback paths for direct execution. This design ensures all side-effecting operations are traceable and that approval states persist across process boundaries.

## Responsibility Boundary

### Single Turn Processing Flow

``` text
User input (line)
   │
   ├─ line.startswith("/")
   │    └─ CommandRegistry.dispatch(line)     — Slash command, no LLM call
   │
   └─ Orchestrator.handle_turn(line)
        │  (If workflow.approval_pending is set, block here and return an error prompting /approve or /reject)
        │  (Also block here if any background task type is temporarily paused via _bg_pause_state)
        │
        ① Turn Start Processing
        │    → Generate current_turn_id
        │    → Issue audit log: turn_start
        │    → Start WorkflowEngine.run(task, plan_fn, execute_fn, verify_fn)
        │         (plan_fn does nothing; turn start processing is already completed here)
        │
        ② Memory Injection and Mode Classification          [Within WorkflowEngine's execute stage]
        │    → MemoryInjectionService.on_user_prompt() retrieves relevant memories
        │    → Inject memory snippets as "system" role messages
        │    → classify_and_inject_mode(): Classifies query into MDQ/RAG and injects hints as "_ephemeral" system messages
        │
        ③ User Message Addition
         │    → Sync system prompt
         │    → Add user message to history
         │    → AgentSession.save("user", content)
         │
        ④ History Compression
         │    → HistoryManager.compress(history)
         │    → If character/token limit exceeded, replace oldest turns with LLM summary
         │
        ⑤ LLM Turn Processing
         │    → LLMTurnRunner.run(llm_url)
         │         ├─ LLMClient.stream(url, history, tool_defs)
         │         │    → SSE streaming $\rightarrow$ on_token callback $\rightarrow$ CLIView.write_token()
         │         │    $\rightarrow$ Collect content_parts + tool_calls_map
         │         │
         │         └─ Tool Loop (internal, up to max_tool_turns=5):
         │              $\rightarrow$ execute_all_tool_calls()
         │                   $\rightarrow$ Execute in parallel unless side-effecting tools exist
         │                   $\rightarrow$ ToolExecutor.execute(tool_name, args)
         │                   $\rightarrow$ Add tool results to history as "tool" role
         │                        (Denied tool calls are added via extend_messages())
         │              $\rightarrow$ Re-send history to LLM
         │              $\rightarrow$ ToolLoopGuard: Guards against duplication/cycles/retries/consecutive errors
         │
        ⑥ Turn End Processing                    [Within WorkflowEngine's verify stage]
             $\rightarrow$ Issue audit log: turn_end (elapsed ms, token count, reconnection count, etc.)
             $\rightarrow$ Set current_turn_id = None
```

### Implementation note: Always goes through the workflow engine

`Orchestrator.__init__` calls `WorkflowLoader().load()`; if it fails, it raises a `RuntimeError` and orchestration construction itself fails. Therefore, when `handle_turn()` is called, the workflow definition is non-None and mandatory, with no fallback path for direct execution. The steps ①–⑥ above are executed as callbacks in the `plan`/`execute`/`verify` stages of `WorkflowEngine.run()`. The `plan_fn` is intentionally a no-op because turn start processing is already completed before this stage. For details on stage composition, see [05_agent_03_03_turn-processing-flow-workflow-engine.md](05_agent_03_03_turn-processing-flow-workflow-engine.md).

### Background Task Failure Threshold Notification and Pausing

The session title generation task scheduled on the first turn manages consecutive failure counts upon completion.

- When the consecutive failure threshold is reached, `_notify_bg_failure_threshold()` is called exactly once.
- `_notify_bg_failure_threshold()` guarantees notification to the user. If an exception occurs, it falls back to `logger.critical()` and does not propagate the exception.
- If the constructor opt-in parameter `pause_on_critical_failure` is `True`, the corresponding task type is marked as paused when the threshold is reached. This is per-task-type control, not a global pause flag.
- `handle_turn()` returns early and notifies the user if any entry in `_bg_pause_state` is `True` immediately after the `approval_pending` guard.
- The paused state is held only in process memory and persists until the process restarts.
- Since `pause_on_critical_failure` defaults to `False`, existing callers are unaffected unless they explicitly opt-in.

## Key Constraints

### Memory Injection

- Triggered in step ② if `AgentConfig.use_memory_layer=True`.
- `/undo` removes these injected messages and mode classification hints.
- Memory injection is added via `append_message(msg, source="memory_injection")` with validation.

### MDQ/RAG Mode Classification

- `classify_and_inject_mode()` runs in the same `execute` stage as memory injection, before user message addition.
- If `ctx.cfg.mdq_rag_mode` is anything other than `"auto"`, that setting is prioritized; otherwise, it uses keyword heuristics to determine MDQ vs RAG.
- Even if identified as MDQ mode, if an MCP server with the `search_docs` tool is unavailable, it falls back to RAG.
- A hint string is added as a `"system"` role message with `_ephemeral: true` based on the classification result.

### System Prompt Sync

- `Orchestrator._sync_system_prompt()` is called in step ③, before user message addition.
- If `ctx.conv.history[0]` is already in the `"system"` role, its `content` is overwritten.
- New system messages are validated before insertion.

### History Compression

- Triggered every turn in step ④ (does nothing if below threshold).
- Selects the oldest turns based on importance scores.
- The most recent `history_protect_turns` pair of turns is protected from compression.
- On success: displays a compression notification.
- If LLM call fails while exceeding character limits: discards messages starting from the lowest importance.

## Operational Notes

- Notification and pause mechanisms when background task failure thresholds are reached are opt-in (disabled by default).
- Partial content is separated from regular conversation history so as not to pollute subsequent LLM context.

## Known Limitations

- Notification and pause mechanisms when background task failure thresholds are reached are opt-in (disabled by default). The paused state persists until process restart.

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_03_02_turn-processing-flow-llm-tool-loop.md`
- `05_agent_03_03_turn-processing-flow-workflow-engine.md`
- `05_agent_04_01_state-and-persistence-state-model.md`
- `05_agent_06_01_tool-execution-and-approval-execution.md`

## Keywords

one-turn processing flow
memory injection detail
mdq/rag mode classification
system prompt sync detail
validated history append/insert
validated tool result/denied-message append
workflow engine mandatory execution path
history compression detail
