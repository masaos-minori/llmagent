---
title: "Reading Audit Logs"
area: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# Reading Audit Logs

The shared audit log at `/opt/llm/logs/audit.log` records both MCP server and agent-side audit events in JSON-lines format. Each line is a parsable JSON object.

## MCP Server Audit Logs (Per Call)

Format: JSON-lines, one JSON object per line. Example:
```json
{"event":"mcp_tool_exec","source":"mcp_server","ts":1719500000.0,"session_id":"sess-abc","request_id":"req-uuid","tool":"read_text_file","target":"/tmp/f.txt","outcome":"ok","server_key":"file_read","error_type":""}
```

**Shared Audit Log** (`/opt/llm/logs/audit.log`): Used by `web-search-mcp`, `github-mcp`, `shell-mcp`, `git-mcp`, `cicd-mcp`, and `mdq-mcp`.

```bash
# View MCP server audit events (JSON-lines format)
tail -f /opt/llm/logs/audit.log | jq 'select(.source == "mcp_server")'
# View all audit events (MCP server + agent-side)
tail -f /opt/llm/logs/audit.log | jq .
```

**Server-specific Audit Logs:**

```bash
# GitHub operations (ISO8601 + op + repo + user)
grep "op=create_pull_request" /opt/llm/logs/github_audit.log

# Shell executions (ISO8601 + cmd + uid + exit)
grep "exit=1" /opt/llm/logs/shell_audit.log

# File deletions (ISO8601 + op + path + user)
grep "op=delete_directory" /opt/llm/logs/delete_audit.log

# MDQ operations (JSON-lines format, shared audit log only; no dedicated file)
grep '"event":"mcp_tool_exec"' /opt/llm/logs/audit.log
```

> **Note:** `cicd-mcp`, `git-mcp`, and `mdq-mcp` use the shared audit log only (no dedicated audit log files). They record via `_audit_log()` to the shared audit log (`/opt/llm/logs/audit.log`) in JSON-lines format.

## Server-specific Log Files

| Server | Log Path | Notes |
|---|---|---|
| web-search-mcp | `/opt/llm/logs/web-search-mcp.log` | Dedicated application log |
| file-read-mcp | `/opt/llm/logs/file-read-mcp.log` | Dedicated application log |
| file-write-mcp | `/opt/llm/logs/file-write-mcp.log` | Dedicated application log |
| file-delete-mcp | `/opt/llm/logs/file-delete-mcp.log` | Dedicated application log |
| github-mcp | `/opt/llm/logs/github-mcp.log` | Dedicated application log |
| shell-mcp | `/opt/llm/logs/shell-mcp.log` | Dedicated application log |
| mdq-mcp | `/opt/llm/logs/mdq-mcp.log` | Dedicated application log |
| rag-pipeline-mcp | `/opt/llm/logs/rag-mcp.log` | Dedicated application log |
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
| web-search-mcp | `/opt/llm/logs/audit.log` (shared) | JSON-lines (MCP server audit) |
| file-read-mcp | None | No audit functionality implemented |
| file-write-mcp | None | No audit functionality implemented |
| file-delete-mcp | `/opt/llm/logs/delete_audit.log` | Structured (ISO8601 + op + path + user) |
| github-mcp | `/opt/llm/logs/github_audit.log` | Structured (ISO8601 + op + repo + user). Also used with shared audit log |
| shell-mcp | `/opt/llm/logs/shell_audit.log` | Structured (ISO8601 + op + command + user). Also used with shared audit log |
| mdq-mcp | `/opt/llm/logs/audit.log` (shared) | JSON-lines (`_audit_log()`) |
| rag-pipeline-mcp | None | No audit functionality implemented |
| cicd-mcp | `/opt/llm/logs/audit.log` (shared) | JSON-lines (`_audit_log()`) |
| git-mcp | `/opt/llm/logs/audit.log` (shared) | JSON-lines (`_audit_log()`). `audit_log_path` setting is reserved but unimplemented |

**Note (2026-07-13):** It was confirmed that `audit_log_path` for `mdq-mcp` and `git-mcp` are dead settings that are never referenced in implementation; they were removed from both servers' configuration files (`config/mdq_mcp_server.toml`, `config/git_mcp_server.toml`). MDQ audit events are actually recorded via `MdqService`/`server.py`'s `_audit_log()` to the shared audit log (`/opt/llm/logs/audit.log`) in JSON-lines format. (Explicit in code)

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

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)
- `00_security_01_architecture-and-trust-boundaries.md` — System security architecture / Trust boundaries / Threat modeling / AuthN/AuthZ / Auditing / Local vs Production / Fail-open/Fail-closed / Prompt injection responsibility boundaries

## Keywords

configuration
