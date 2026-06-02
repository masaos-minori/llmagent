Apply the following specification changes.

## Agent REPL changes
- Remove the `/chat` and `/code` slash commands from the agent REPL.
- Change the default agent REPL prompt to `>`.
- Remove `chat_url` and `code_url` from `config/agent.toml`.
- Consolidate them into a single `llm_url` setting.
- Remove in-process RAG from the REPL pipeline flow.

## Clarify the shell execution specification and add resource limits
Implement a clear shell execution policy with resource limits.

### Implementation approach
- Define an execution policy.
- Follow the existing MCP server conventions and specifications.
- Define the execution user, `cwd`, `timeout`, `max_output_kb`, kill policy, and allowed commands.
- Split shell execution into a dedicated MCP.
- Add stdout / stderr limits and audit logging.

### Implementation targets
- `shell-mcp`
- orchestrator policy
- `shared/protocols/shell` schema
