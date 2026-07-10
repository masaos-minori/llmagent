---
title: "Reading Audit Logs"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_configuration-file-inventory.md
source:
  - 04_mcp_06_configuration-file-inventory.md
---

# Reading Audit Logs

## Reading Audit Logs

The shared audit log at `/opt/llm/logs/audit.log` contains JSON-lines records from both MCP server and agent-side audit events. Each line is a parseable JSON object.

### MCP server audit log (per-call)

Format: JSON-lines, one JSON object per line. Example:
```json
{"event":"mcp_tool_exec","source":"mcp_server","ts":1719500000.0,"session_id":"sess-abc","request_id":"req-uuid","tool":"read_text_file","target":"/tmp/f.txt","outcome":"ok","server_key":"file_read","error_type":""}
```

**Shared audit log** (`/opt/llm/logs/audit.log`): Used by web-search-mcp, file-read-mcp, file-write-mcp, rag-pipeline-mcp, cicd-mcp.

```bash
# View MCP server audit events (JSON-lines format)
tail -f /opt/llm/logs/audit.log | jq 'select(.source == "mcp_server")'
# View all audit events (MCP server + agent-side)
tail -f /opt/llm/logs/audit.log | jq .
```

**Per-server audit logs:**

```bash
# GitHub operations (ISO8601 + op + repo + user)
grep "op=create_pull_request" /opt/llm/logs/github_audit.log

# Shell executions (ISO8601 + cmd + uid + exit)
grep "exit=1" /opt/llm/logs/shell_audit.log

# File deletions (ISO8601 + op + path + user)
grep "op=delete_directory" /opt/llm/logs/delete_audit.log

# MDQ operations (MDQ-specific format)
grep "op=" /opt/llm/logs/mdq_audit.log
```

> **Note:** cicd-mcp and git-mcp do not have dedicated audit log files. They use `logging.getLogger(__name__)` only.

### Per-server log files

| Server | Log path | Notes |
|---|---|---|
| web-search-mcp | `/opt/llm/logs/web-search-mcp.log` | Dedicated app log |
| file-read-mcp | `/opt/llm/logs/file-read-mcp.log` | Dedicated app log |
| file-write-mcp | `/opt/llm/logs/file-write-mcp.log` | Dedicated app log |
| file-delete-mcp | `/opt/llm/logs/file-delete-mcp.log` | Dedicated app log |
| github-mcp | `/opt/llm/logs/github-mcp.log` | Dedicated app log |
| shell-mcp | `/opt/llm/logs/shell-mcp.log` | Dedicated app log |
| mdq-mcp | `/opt/llm/logs/mdq-mcp.log` | Dedicated app log |
| rag-pipeline-mcp | `/opt/llm/logs/rag-mcp.log` | Dedicated app log |
| cicd-mcp | No dedicated log file | Uses `logging.getLogger(__name__)` |
| git-mcp | No dedicated log file | Uses `logging.getLogger(__name__)` |

### Per-server audit log files

| Server | Audit log path | Format |
|---|---|---|
| web-search-mcp | `/opt/llm/logs/audit.log` (shared) | JSON-lines (MCP server audit) |
| file-read-mcp | `/opt/llm/logs/audit.log` (shared) | JSON-lines (MCP server audit) |
| file-write-mcp | `/opt/llm/logs/audit.log` (shared) | JSON-lines (MCP server audit) |
| file-delete-mcp | `/opt/llm/logs/delete_audit.log` | Structured (ISO8601 + op + path + user) |
| github-mcp | `/opt/llm/logs/github_audit.log` | Structured (ISO8601 + op + repo + user) |
| shell-mcp | `/opt/llm/logs/shell_audit.log` | Structured (ISO8601 + op + command + user) |
| mdq-mcp | `/opt/llm/logs/mdq_audit.log` | Structured (MDQ-specific) |
| rag-pipeline-mcp | `/opt/llm/logs/audit.log` (shared) | JSON-lines (MCP server audit) |
| cicd-mcp | `/opt/llm/logs/audit.log` (shared) | JSON-lines (MCP server audit) |
| git-mcp | Config key exists but no write code | `audit_log_path = "/opt/llm/logs/git-mcp.log"` in TOML — no audit write code in service.py; reserved for future implementation |

### Agent-side audit log (structured events)

Format: JSON-lines, e.g.:
```json
{"event":"tool_exec","task_id":"turn-123","tool":"shell_run","operation_type":"MCP","mcp_request_id":"abc-456","is_error":true,"error_type":"transport","ts":1719500000.0,"workflow_id":"","session_id":""}
```

```bash
# View raw agent-side audit events (JSON-lines format)
tail -f /opt/llm/logs/audit.log | jq .

# Filter by event type
tail -f /opt/llm/logs/audit.log | jq 'select(.event == "tool_exec")'

# Filter by error type (agent-side JSON-lines format)
grep '"error_type":"transport"' /opt/llm/logs/audit.log

# Filter by tool name
grep '"tool":"shell_run"' /opt/llm/logs/audit.log
```

---


## Related Documents

- [04_mcp_06_configuration-file-inventory.md](04_mcp_06_configuration-file-inventory.md)

## Keywords

configuration
