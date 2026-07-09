"""Add Policy Alignment Notes block to each of the 16 require files."""

BLOCK = """### Policy Alignment Notes

This requirement must follow the Phase 1 integration policy below.

1. **Do not create `orchestrator-mcp`.**
   - The central Orchestrator is an internal Agent component, not an MCP server.
   - Role MCP services may be added and monitored via MCP health/capability checks, but the Orchestrator itself must not be registered as an MCP server.
2. **Add internal Orchestrator APIs.**
   - REPL / command layers should call internal APIs such as `start_workflow`, `resume_workflow`, `cancel_workflow`, `get_workflow_status`, `get_workflow_artifacts`, and `retry_phase`.
3. **Use `state_manager.py` as the source of truth.**
   - Workflow / task / artifact / retry / approval state must be persisted and read through `state_manager.py`.
   - REPL, `AgentContext`, WorkerRuntime, JSONL logs, and UI code must not own canonical workflow state.
4. **Extend `workflow.sqlite`.**
   - Phase 1 must reuse and extend `workflow.sqlite` for workflow metadata, task state, artifact metadata references, retries, approvals, and events.
   - Do not introduce a separate `orchestrator.sqlite` in Phase 1.

"""

for i in range(1, 17):
    path = f"issues/20260627_{i:02d}_require.md"
    with open(path) as f:
        content = f.read()

    new_content = content.replace("### Expected Result", f"{BLOCK}### Expected Result")

    if new_content == content:
        print(f"SKIP {i:02d} — no '### Expected Result' found")
        continue

    with open(path, "w") as f:
        f.write(new_content)

    print(f"DONE {i:02d}")
