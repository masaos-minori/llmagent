# Implementation Procedure: Split Audit Log Documentation by Agent-Side, Shared MCP, and Per-Server Logs

## Goal

Reconcile conflicting statements about MCP and agent audit logging by clearly separating three distinct layers: agent-side audit logs, shared MCP server audit logs, and per-server audit logs. Eliminate ambiguity about which logs exist, their formats, and cross-log correlation capabilities.

## Scope

- `docs/04_mcp_02_03_audit-logging-and-errors.md`
- `docs/04_mcp_06_07_reading-audit-logs.md`
- `docs/04_mcp_06_08_end-to-end-tool-call-tracing.md`
- Individual MCP server catalog files (`docs/04_mcp_04_*`)

**Out-of-Scope:**
- Implementing missing audit writers (Non-Goal)
- Changing audit event schema (Non-Goal)
- Removing existing per-server audit logs (Non-Goal)

## Assumptions

1. The requirement `requires/20260714_12_require.md` is the canonical specification for this task.
2. Implementation inspection has confirmed the following actual behavior:
   - **Shared MCP audit writer** (`_audit_log()` → `/opt/llm/logs/audit.log`) used by: web-search-mcp, github-mcp, shell-mcp, git-mcp, cicd-mcp, mdq-mcp
   - **Per-server audit logs only**: file-delete-mcp (`/opt/llm/logs/delete_audit.log`)
   - **Both shared + per-server**: github-mcp, shell-mcp
   - **No audit logging**: file-read-mcp, file-write-mcp, rag-pipeline-mcp
   - **MDQ does NOT have a per-server audit log** — uses shared `_audit_log()` only
   - **git-mcp's `audit_log_path` is reserved/not implemented**

## Implementation

### Target files

1. `docs/04_mcp_02_03_audit-logging-and-errors.md`
2. `docs/04_mcp_06_07_reading-audit-logs.md`
3. `docs/04_mcp_06_08_end-to-end-tool-call-tracing.md`
4. `docs/04_mcp_04_server_catalog.md` (and individual server catalog files)

### Procedure

#### Step 1: Restructure `04_mcp_02_03_audit-logging-and-errors.md`

1. **Clarify shared MCP audit log scope**: Update the note about per-server audit logs to reflect actual servers:
   ```
   注記: github-mcp、shell-mcp は共有と両方の audit ログに書き込む。file-delete-mcp のみ専用 audit ログを使用する。
   ファイル読み込み・書き込み MCP サーバーは audit ログを書かない。
   ```

2. **Update correlation field availability**: Clarify that per-server audit logs lack X-Session-Id/X-Request-Id fields:
   ```
   github-mcp、shell-mcp の専用 audit ログは ISO8601 タイムスタンプ + op=<operation> + path/repo/command を使用。
   これらは X-Session-Id や X-Request-Id の相関フィールドを持たない。ログ間の相関はエージェント側の audit ログを基準として使用する必要がある。
   ```

#### Step 2: Restructure `04_mcp_06_07_reading-audit-logs.md`

1. **Add three-layer distinction table**: Add a clear table showing which layer each server writes to:

   ```markdown
   ### サーバー別Auditログレイヤー

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
   ```

2. **Correct MDQ section**: Update L48-49 to remove reference to nonexistent per-server audit log:
   ```markdown
   # MDQ operations (JSON-lines形式、共有audit logのみ。専用ファイルなし)
   grep '"event":"mcp_tool_exec"' /opt/llm/logs/audit.log
   ```

3. **Update git-mcp entry**: Mark as reserved/not implemented:
   ```markdown
   | git-mcp | 専用ログファイルなし | `logging.getLogger(__name__)` を使用。audit_log_pathは予約済みだが未実装 |
   ```

4. **Update the note at L52**: Correct to reflect actual audit logging behavior:
   ```markdown
   > **注記:** cicd-mcp、git-mcp、mdq-mcp は共有audit logのみを使用する。
   > cicd-mcp/git-mcp は `logging.getLogger(__name__)` のみを使用し、
   > mdq-mcp は `_audit_log()` 経由で共有audit log(`/opt/llm/logs/audit.log`)にJSON-linesで記録する。
   ```

5. **Update the table at L69-82**: Correct the per-server audit log entries:
   - Remove MDQ per-server audit log row
   - Mark git-mcp as "reserved/not implemented"

#### Step 3: Update `04_mcp_06_08_end-to-end-tool-call-tracing.md`

1. **Update tracing guidance**: Note that cross-layer correlation requires matching session/request IDs, and that per-server audit logs lack these fields.

#### Step 4: Update MCP server catalog files

For each server catalog file (`docs/04_mcp_04_*`), add per-server audit log path information:

1. **github-mcp**: Note both shared and per-server audit logs
2. **shell-mcp**: Note both shared and per-server audit logs
3. **file-delete-mcp**: Note per-server-only audit log
4. **mdq-mcp**: Note shared audit log only (no per-server log)
5. **git-mcp**: Note `audit_log_path` is reserved/not implemented

### Method

- Pattern-based search followed by targeted text replacement via file edit.
- Preserve surrounding context and formatting.
- Use consistent terminology across all documents: "Layer 1: Agent/MCP shared", "Layer 2: Shared MCP", "Layer 3: Per-server".

## Validation plan

1. Verify no document says every server always writes shared JSON-lines audit records.
2. Confirm three-layer distinction is consistent across all documents.
3. Verify MDQ is documented as using shared audit log only (no per-server log).
4. Verify git-mcp is consistently marked as having `audit_log_path` reserved/not implemented.
5. Verify correlation field availability is accurate per layer.
6. Run `pre-commit run --all-files` if linting is configured.
