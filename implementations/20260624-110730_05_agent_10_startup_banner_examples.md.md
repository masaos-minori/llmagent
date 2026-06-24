# Implementation: Refresh Startup-Banner /context /stats Examples

## Goal

Update startup-banner, `/context`, and `/stats` output examples in `05_agent_10` to reflect current format. Verify consistency in `05_agent_15` and `05_agent_17`.

## Scope

**In:**
- `docs/05_agent_10_operations_and_deployment.md` — update examples
- `docs/05_agent_15_performance_and_tuning.md` — verify `/context` token example
- `docs/05_agent_17_troubleshooting_and_diagnostics.md` — verify `/stats` diagnostic example

**Out:** No changes to output format.

## Assumptions

1. Current startup banner shows: version, model, session_id, active MCP servers, tool count.
2. `/context` shows: token usage, context window limit, compression threshold.
3. `/stats` shows: uptime, turn count, partial completions, DLQ depth, MCP server health, approval pending.
4. Existing examples may be missing `approval_pending` field (added in recent commit 9559444).

## Implementation

### Target file

`docs/05_agent_10_operations_and_deployment.md`, `docs/05_agent_15_performance_and_tuning.md`, `docs/05_agent_17_troubleshooting_and_diagnostics.md`

### Procedure

1. Read startup banner from repl.py:
   ```bash
   grep -n "banner\|startup.*print\|print.*version\|print.*model" agent/repl.py | head -20
   ```
2. Read `/context` output from cmd_context.py:
   ```bash
   grep -rn "def.*context\|write_table\|token.*usage" agent/commands/cmd_context.py | head -20
   ```
3. Read `/stats` output from cmd_stats.py or cmd_config.py:
   ```bash
   grep -rn "def.*stats\|approval_pending\|write_table" agent/commands/ --include="*.py" | head -20
   ```
4. Update examples in `05_agent_10` to match current output.
5. Verify `05_agent_15` and `05_agent_17` examples are consistent.

### Method

Bash grep to confirm format → Read docs → Edit patches.

### Details

**Updated startup-banner example:**

```
[LLMAgent v0.9.0] model=claude-sonnet-4-6 session=abc12345
  MCP servers: file_read(ok) shell_exec(ok) rag_pipeline(ok)
  Tools: 12 active, 0 disabled
  Approval: 0 pending
  Type /help for commands
```

**Updated `/context` example:**

```
Context: 4,231 / 200,000 tokens (2.1%)
  Compression threshold: 80% (160,000 tokens)
  Auto-compress: enabled
  Compress at: ~160,000 tokens
```

**Updated `/stats` example:**

```
Uptime: 1h 23m | Turns: 47 | Partial: 0
  DLQ depth: 0 | MCP: 3 ok / 0 degraded
  Approval pending: 0 | Workflows: 2 active
  Memory items: 12 | Cache hits: 34%
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| approval_pending in /stats example | `grep -n "approval_pending\|Approval pending" docs/05_agent_10_operations_and_deployment.md` | found |
| /context token example | `grep -n "tokens.*200\|200,000" docs/05_agent_10_operations_and_deployment.md` | found |
| No code changes | `git diff agent/` | empty |
