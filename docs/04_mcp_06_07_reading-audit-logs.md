---
title: "Reading Audit Logs"
category: mcp
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

`/opt/llm/logs/audit.log` にある共有audit logには、MCPサーバとagent側の両方のaudit eventがJSON-lines形式で記録される。各行はパース可能なJSONオブジェクトである。

## MCPサーバのaudit log（呼び出しごと）

形式: JSON-lines、1行に1個のJSONオブジェクト。例:
```json
{"event":"mcp_tool_exec","source":"mcp_server","ts":1719500000.0,"session_id":"sess-abc","request_id":"req-uuid","tool":"read_text_file","target":"/tmp/f.txt","outcome":"ok","server_key":"file_read","error_type":""}
```

**共有audit log** (`/opt/llm/logs/audit.log`): web-search-mcp、github-mcp、shell-mcp、git-mcp、cicd-mcp、mdq-mcpで使用される。

```bash
# View MCP server audit events (JSON-lines format)
tail -f /opt/llm/logs/audit.log | jq 'select(.source == "mcp_server")'
# View all audit events (MCP server + agent-side)
tail -f /opt/llm/logs/audit.log | jq .
```

**サーバ別audit log:**

```bash
# GitHub operations (ISO8601 + op + repo + user)
grep "op=create_pull_request" /opt/llm/logs/github_audit.log

# Shell executions (ISO8601 + cmd + uid + exit)
grep "exit=1" /opt/llm/logs/shell_audit.log

# File deletions (ISO8601 + op + path + user)
grep "op=delete_directory" /opt/llm/logs/delete_audit.log

# MDQ operations (JSON-lines形式、共有audit logのみ。専用ファイルなし)
grep '"event":"mcp_tool_exec"' /opt/llm/logs/audit.log
```

> **注記:** cicd-mcp、git-mcp、mdq-mcp は共有audit logのみを使用する。
> cicd-mcp/git-mcp は `logging.getLogger(__name__)` のみを使用し、
> mdq-mcp は `_audit_log()` 経由で共有audit log(`/opt/llm/logs/audit.log`)にJSON-linesで記録する。

## サーバ別ログファイル

| サーバ | ログパス | 補足 |
|---|---|---|
| web-search-mcp | `/opt/llm/logs/web-search-mcp.log` | 専用アプリログ |
| file-read-mcp | `/opt/llm/logs/file-read-mcp.log` | 専用アプリログ |
| file-write-mcp | `/opt/llm/logs/file-write-mcp.log` | 専用アプリログ |
| file-delete-mcp | `/opt/llm/logs/file-delete-mcp.log` | 専用アプリログ |
| github-mcp | `/opt/llm/logs/github-mcp.log` | 専用アプリログ |
| shell-mcp | `/opt/llm/logs/shell-mcp.log` | 専用アプリログ |
| mdq-mcp | `/opt/llm/logs/mdq-mcp.log` | 専用アプリログ |
| rag-pipeline-mcp | `/opt/llm/logs/rag-mcp.log` | 専用アプリログ |
| cicd-mcp | 専用ログファイルなし | `logging.getLogger(__name__)` を使用 |
| git-mcp | 専用ログファイルなし | `logging.getLogger(__name__)` を使用。audit_log_pathは予約済みだが未実装 |

## サーバ別Auditログレイヤー

| サーバー | Layer1: Agent/MCP共有 | Layer2: 共有MCP | Layer3: 専用 |
|---|---|---|---|
| web-search-mcp | tool_exec | mcp_tool_exec | なし |
| file-read-mcp | tool_exec | なし | なし |
| file-write-mcp | tool_exec | なし | なし |
| file-delete-mcp | tool_exec | なし | delete_audit.log |
| github-mcp | tool_exec | mcp_tool_exec | github_audit.log |
| shell-mcp | tool_exec | mcp_tool_exec | shell_audit.log |
| mdq-mcp | tool_exec | mcp_tool_exec | なし |
| rag-pipeline-mcp | tool_exec | なし | なし |
| cicd-mcp | tool_exec | mcp_tool_exec | なし |
| git-mcp | tool_exec | mcp_tool_exec | なし |

### サーバ別audit logファイル

| サーバ | Audit logパス | 形式 |
|---|---|---|
| web-search-mcp | `/opt/llm/logs/audit.log`（共有） | JSON-lines（MCPサーバaudit） |
| file-read-mcp | なし | audit機能を実装していない |
| file-write-mcp | なし | audit機能を実装していない |
| file-delete-mcp | `/opt/llm/logs/delete_audit.log` | 構造化（ISO8601 + op + path + user） |
| github-mcp | `/opt/llm/logs/github_audit.log` | 構造化（ISO8601 + op + repo + user）。共有audit logとも併用 |
| shell-mcp | `/opt/llm/logs/shell_audit.log` | 構造化（ISO8601 + op + command + user）。共有audit logとも併用 |
| mdq-mcp | `/opt/llm/logs/audit.log`（共有） | JSON-lines（`_audit_log()` 経由） |
| rag-pipeline-mcp | なし | audit機能を実装していない |
| cicd-mcp | `/opt/llm/logs/audit.log`（共有） | JSON-lines（`_audit_log()` 経由） |
| git-mcp | `/opt/llm/logs/audit.log`（共有） | JSON-lines（`_audit_log()` 経由）。`audit_log_path`設定は予約済みだが未実装 |

**注記（2026-07-13）:** mdq-mcp の `audit_log_path`、git-mcp の `audit_log_path` はいずれも実装で一切参照されないデッド設定であることを確認し、両サーバーの設定ファイル（`config/mdq_mcp_server.toml`、`config/git_mcp_server.toml`）から削除した。mdq-mcp の監査イベントは実際には `MdqService`/`server.py` の `_audit_log()` が共有audit log(`/opt/llm/logs/audit.log`)にJSON-linesで記録する。(Explicit in code)

### Audit ログを書かないMCPサーバー

以下のMCPサーバーはauditログを一切書きません:

| サーバ | 理由 |
|---|---|
| file-read-mcp | audit機能を実装していない |
| file-write-mcp | audit機能を実装していない |
| rag-pipeline-mcp | audit機能を実装していない |

### Agent側のaudit log（構造化イベント）

形式: JSON-lines、例:
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

## Keywords

configuration
