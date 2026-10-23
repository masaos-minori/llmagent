---
title: "Reading Audit Logs"
area: mcp
tags:
  - mcp
  - configuration
related:
  - mcp_00_document-guide.md
  - mcp_06_01_configuration-file-inventory.md
  - mcp_02_03_audit-logging-and-errors.md
---

# Reading Audit Logs

The shared audit log at `<log_dir>/audit.log` records both MCP server and agent-side audit events in JSON-lines format. Each line is a parsable JSON object.

## MCP Server Audit Logs (Per Call)

Format: JSON-lines, one JSON object per line. Example:
```json
{"event":"mcp_tool_exec","source":"mcp_server","ts":1719500000.0,"session_id":"sess-abc","request_id":"req-uuid","tool":"read_text_file","target":"/tmp/f.txt","outcome":"ok","server_key":"file_read","error_type":""}
```

**Shared Audit Log** (`<log_dir>/audit.log`): Used by `web-search-mcp`, `github-mcp`, `shell-mcp`, `cicd-mcp`, `mdq-mcp`, and `git-mcp`.

```bash
# View MCP server audit events (JSON-lines format)
tail -f <log_dir>/audit.log | jq 'select(.source == "mcp_server")'
# View all audit events (MCP server + agent-side)
tail -f <log_dir>/audit.log | jq .
```

**Server-specific Audit Logs:**

```bash
# GitHub operations (ISO8601 + op + repo + user)
grep "op=create_pull_request" <log_dir>/github_audit.log

# Shell executions (ISO8601 + cmd + uid + exit)
grep "exit=1" <log_dir>/shell_audit.log

# File deletions (ISO8601 + op + path + user)
grep "op=delete_directory" <log_dir>/delete_audit.log

# MDQ operations (JSON-lines format, shared audit log only; no dedicated file)
grep '"event":"mcp_tool_exec"' <log_dir>/audit.log
```

> **Note:** `cicd-mcp`, `git-mcp`, and `mdq-mcp` have no dedicated audit log files. They record via `_audit_log()` into their own application log (`<log_dir>/<server>-mcp.log`) as JSON-lines records; `<log_dir>/audit.log` is written only by the Agent. Only git-mcp emits the optional `canonical_target`, `pre_condition`, and `post_condition` fields (see `mcp_02_03_audit-logging-and-errors.md`). Outcome values are `"ok"` (operation succeeded), `"error"` (operation failed with an exception), or `"rejected"` (operation rejected by a policy guard before execution).

## Server-specific Log Files and Audit Layers

Every server writes an application log `<log_dir>/<server>-mcp.log` (rag-pipeline-mcp writes `rag-mcp.log`). Audit layers:

- Layer 1 (agent-side `tool_exec`): every server.
- Layer 2 (`mcp_tool_exec` in the server's own application log `<log_dir>/<server>-mcp.log`): all servers except file-read-mcp and rag-pipeline-mcp.
- Layer 3 (dedicated audit file): file-delete-mcp (`delete_audit.log`, `ISO8601 op= path= user=llm-agent`), github-mcp (`github_audit.log`), shell-mcp (`shell_audit.log`).
- file-write-mcp and file-delete-mcp also record the `_audit_log()` payload in their dedicated application logs.
- Dedicated audit files carry no `X-Session-Id` / `X-Request-Id`; correlate through the agent-side log.

**Note:** `mdq-mcp` and `git-mcp` have no effective `audit_log_path` setting (reserved, unimplemented); they record only to the shared audit log via `_audit_log()`.

### MCP Servers without Audit Logging

file-read-mcp and rag-pipeline-mcp write no audit logs. file-write-mcp and file-delete-mcp emit audit events through `mcp_servers.audit._audit_log()` (session ID, request ID, action, truncated target, `outcome`) on every rejected path (empty `allowed_dirs`, argument validation failure) and on the completed path. Before/after file state and approval correlation are not recorded.

### Agent-side Audit Logs (Structured Events)

Format: JSON-lines, Example:
```json
{"event":"tool_exec","task_id":"turn-123","tool":"shell_run","operation_type":"MCP","mcp_request_id":"abc-456","is_error":true,"error_type":"transport","ts":1719500000.0,"workflow_id":"","session_id":""}
```

```bash
# View raw agent-side audit events (JSON-lines format)
tail -f <log_dir>/audit.log | jq .

# Filter by event type
tail -f <log_dir>/audit.log | jq 'select(.event == "tool_exec")'

# Filter by error type (agent-side JSON-lines format)
grep '"error_type":"transport"' <log_dir>/audit.log

# Filter by tool name
grep '"tool":"shell_run"' <log_dir>/audit.log
```

---


## Keywords

- configuration
