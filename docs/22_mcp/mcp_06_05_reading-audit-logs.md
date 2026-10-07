---
title: "Reading Audit Logs"
area: mcp
tags:
  - mcp
  - configuration
related:
  - mcp_00_document-guide.md
  - mcp_06_01_configuration-file-inventory.md
source:
  - mcp_06_01_configuration-file-inventory.md
---

# Reading Audit Logs

The shared audit log at `<log_dir>/audit.log` records both MCP server and agent-side audit events in JSON-lines format. Each line is a parsable JSON object.

## MCP Server Audit Logs (Per Call)

Format: JSON-lines, one JSON object per line. Example:
```json
{"event":"mcp_tool_exec","source":"mcp_server","ts":1719500000.0,"session_id":"sess-abc","request_id":"req-uuid","tool":"read_text_file","target":"/tmp/f.txt","outcome":"ok","server_key":"file_read","error_type":""}
```

**Shared Audit Log** (`<log_dir>/audit.log`): Used by `web-search-mcp`, `github-mcp`, `shell-mcp`, `git-mcp`, `cicd-mcp`, and `mdq-mcp`.

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

> **Note:** `cicd-mcp`, `git-mcp`, and `mdq-mcp` use the shared audit log only (no dedicated audit log files). They record via `_audit_log()` to the shared audit log (`<log_dir>/audit.log`) in JSON-lines format.

## Server-specific Log Files

| Server | Log Path | Notes |
|---|---|---|
| web-search-mcp | `<log_dir>/web-search-mcp.log` | Dedicated application log |
| file-read-mcp | `<log_dir>/file-read-mcp.log` | Dedicated application log |
| file-write-mcp | `<log_dir>/file-write-mcp.log` | Dedicated application log |
| file-delete-mcp | `<log_dir>/file-delete-mcp.log` | Dedicated application log |
| github-mcp | `<log_dir>/github-mcp.log` | Dedicated application log |
| shell-mcp | `<log_dir>/shell-mcp.log` | Dedicated application log |
| mdq-mcp | `<log_dir>/mdq-mcp.log` | Dedicated application log |
| rag-pipeline-mcp | `rag-mcp.log` (in the log directory) | Dedicated application log |
| cicd-mcp | No dedicated log file | Uses `logging.getLogger(__name__)` |
| git-mcp | No dedicated log file | Uses `logging.getLogger(__name__)`. `audit_log_path` is reserved but unimplemented |

## Server-specific Audit Log Layers

| Server | Layer1: Agent/MCP Shared | Layer2: Shared MCP | Layer3: Dedicated |
|---|---|---|---|
| web-search-mcp | tool_exec | mcp_tool_exec | None |
| file-read-mcp | tool_exec | None | None |
| file-write-mcp | tool_exec | None | None |
| file-delete-mcp | tool_exec | None | delete_audit.log |
| github-mcp | tool_exec | mcp_tool_exec | github_audit.log |
| shell-mcp | tool_exec | mcp_tool_exec | shell_audit.log |
| mdq-mcp | tool_exec | mcp_tool_exec | None |
| rag-pipeline-mcp | tool_exec | None | None |
| cicd-mcp | tool_exec | mcp_tool_exec | None |
| git-mcp | tool_exec | mcp_tool_exec | None |

### Server-specific Audit Log Files

| Server | Audit Log Path | Format |
|---|---|---|
| web-search-mcp | `<log_dir>/audit.log` (shared) | JSON-lines (MCP server audit) |
| file-read-mcp | None | No audit functionality implemented |
| file-write-mcp | None | No audit functionality implemented |
| file-delete-mcp | `<log_dir>/delete_audit.log` | Structured (ISO8601 + op + path + user) |
| github-mcp | `<log_dir>/github_audit.log` | Structured (ISO8601 + op + repo + user). Also used with shared audit log |
| shell-mcp | `<log_dir>/shell_audit.log` | Structured (ISO8601 + op + command + user). Also used with shared audit log |
| mdq-mcp | `<log_dir>/audit.log` (shared) | JSON-lines (`_audit_log()`) |
| rag-pipeline-mcp | None | No audit functionality implemented |
| cicd-mcp | `<log_dir>/audit.log` (shared) | JSON-lines (`_audit_log()`) |
| git-mcp | `<log_dir>/audit.log` (shared) | JSON-lines (`_audit_log()`). `audit_log_path` setting is reserved but unimplemented |

**Note:** `mdq-mcp` and `git-mcp` have no effective `audit_log_path` setting (it is not set in `config/mdq_mcp_server.toml` or `config/git_mcp_server.toml`). MDQ audit events are actually recorded via `MdqService`/`server.py`'s `_audit_log()` to the shared audit log (`<log_dir>/audit.log`) in JSON-lines format. (Explicit in code)

### MCP Servers without Audit Logging

The following MCP servers do not write any audit logs:

| Server | Reason |
|---|---|
| file-read-mcp | No audit functionality implemented |
| file-write-mcp | No audit functionality implemented |
| rag-pipeline-mcp | No audit functionality implemented |

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

configuration
