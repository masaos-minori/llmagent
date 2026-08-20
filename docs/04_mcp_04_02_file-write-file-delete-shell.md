# MCP Server Catalog: file-write-mcp / file-delete-mcp / shell-mcp

## file-write-mcp (Port 8007)

**Purpose:** Write operations to the local filesystem. All tools support `dry_run=True`.
**Startup Mode:** persistent (HTTP)
**Configuration:** `config/file_write_mcp_server.toml`

**Tools:** `write_file`, `edit_file`, `create_directory`, `move_file`

All tools do not require configuration (`config_dependent: false`).

The runtime availability (`enabled`/`disabled_reason`) of these tools depends on `allowed_dirs` (empty $\rightarrow$ disabled, reason `"allowed_dirs is empty"`). See [04_mcp_03_06_tool-runtime-availability-metadata.md](04_mcp_03_06_tool-runtime-availability-metadata.md) for details.

**Configuration Fields:** `allowed_dirs`, `max_write_bytes` (default: 1,000,000)

| Tool | Input | `dry_run` Behavior |
|---|---|---|
| `write_file` | `{path, content, dry_run?}` | Returns only diff; no writing |
| `edit_file` | `{path, edits: [{old_text, new_text}], dry_run?}` | Returns diff; no writing |
| `create_directory` | `{path, dry_run?}` | Returns directory info (exists/to be created); no creation |
| `move_file` | `{source, destination, dry_run?}` | Returns whether movement is possible |

**Health:** `{"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":bool,"dependencies":{"filesystem":"/workspace is not a directory"/"check failed: <error>"},"details":{}}` — HTTP 200 when ready, 503 when degraded.
**Configuration:** `max_write_bytes` (default 1 MB; enforced as UTF-8 byte count)
**Error Codes:** 403 (FileAuthorizationError), 404 (FileNotFoundError), 422 (FileValidationError)
**Logs:** `/opt/llm/logs/file-write-mcp.log`
**Audit:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (Shared MCP): None / Layer3 (Dedicated): None — does not write audit logs

### Implementation Notes (file-write-mcp)

- Enforcement of `max_write_bytes` is implemented via manual check in `write_service.py::WriteFileService.write_file` (`len(content.encode("utf-8")) > max_write_bytes`) rather than Pydantic field constraints (raises `FileValidationError` if exceeded). [Explicit in code]
- `write_file` performs atomic writes by writing to a temporary file (`.tmp_<name>`) first and then replacing it using `os.replace`. If the write fails, the temporary file is deleted before returning an error. [Explicit in code]

---

## file-delete-mcp (Port 8008)

**Purpose:** Deletion from the local filesystem. All tools support `dry_run=True`.
**Startup Mode:** persistent (HTTP)
**Configuration:** `config/file_delete_mcp_server.toml`

**Tools:** `delete_file`, `delete_directory`

All tools do not require configuration (`config_dependent: false`).

The runtime availability (`enabled`/`disabled_reason`) of these tools depends on `allowed_dirs` (empty $\rightarrow$ disabled, reason `"allowed_dirs is empty"`). See [04_mcp_03_06_tool-runtime-availability-metadata.md](04_mcp_03_06_tool-runtime-availability-metadata.md) for details.

**Configuration Fields:** `allowed_dirs`, `audit_log_path`

| Tool | Input | `dry_run` Behavior |
|---|---|---|
| `delete_file` | `{path, dry_run?}` | Returns file information; no deletion |
| `delete_directory` | `{path, recursive?, dry_run?}` | Scans contents (up to 1000 files); no deletion |

**Health:** `{"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":bool,"dependencies":{"filesystem":"/workspace is not a directory"/"check failed: <error>"},"details":{}}` — HTTP 200 when ready, 503 when degraded.
**Deletion Audit Log:** `/opt/llm/logs/delete_audit.log` (ISO8601 UTC + op + path + user)
**Audit:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (Shared MCP): None / Layer3 (Dedicated): `delete_audit.log`
**Error Codes:** 403 (FileAuthorizationError), 404 (FileNotFoundError), 422 (FileValidationError)
**Logs:** `/opt/llm/logs/file-delete-mcp.log`

### Implementation Notes

- The `audit_log_path` key in `config/file_delete_mcp_server.toml` was removed on 2026-07-13 (as `FileDeleteConfig` did not originally load this key, and `delete_service.py::build_service` always hardcoded `"/opt/llm/logs/delete_audit.log"` — same reason as the removal of `audit_log_path` for git-mcp. See `# NOTE:` comments in the config file). [Explicit in code]
- Even if writing to the audit log fails, no exception is raised; instead, an error is logged and the deletion process itself returns as successful (unlike github-mcp's `GitHubAuditError`, failure to write the audit log does not block the deletion operation in file-delete-mcp). [Explicit in code]
- `delete_directory(recursive=true)` rejects deletion with a `FileAuthorizationError` if the target matches any root directory defined in `allowed_dirs` (it does not prevent deleting individual files/subdirectories within allowed directories). [Explicit in code]
- Directory scanning during `dry_run` is capped at `_DRY_RUN_MAX_FILES = 1000` and reflected in `dir_info` as `"<count>+ files"`. [Explicit in code]

---

## shell-mcp (Port 8009)

**Purpose:** Execution of sandboxed shell commands within the `command_allowlist`.
**Startup Mode:** persistent (HTTP)
**Configuration:** `config/shell_mcp_server.toml`

**Tools:** `shell_run`

| Key | Default | Description |
|---|---|---|
| `command_allowlist` | `[]` | Allowed command names (base name of `argv[0]`) |
| `shell_cwd_allowed_dirs` | `[]` | Allowed CWD paths (empty = all denied) |
| `max_timeout_sec` | `300` | Timeout limit |
| `max_output_kb` | `4096` | Output limit |
| `max_memory_mb` | `512` | Memory limit (`RLIMIT_AS`) |
| `shell_sandbox_backend` | `"none"` | `"firejail"` or `"none"` (see sandbox table below) |
| `audit_log_path` | `"/opt/llm/logs/shell_audit.log"` | Audit log |
| `default_cwd` | `"/opt/llm/storage"` | Working directory if no cwd is specified in request |
| `shell_path` | `"/opt/llm/venv/bin:/usr/bin:/bin"` | PATH environment variable for child processes |
| `env_allowlist` | `[]` | Allowed environment variable keys in `req.env` (if empty, uses `env_denylist`) |
| `env_denylist` | `["LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH"]` | Glob patterns for environment variable keys to remove from `req.env` |
| `execution_user` | `""` | OS user to run commands as via setuid (requires `CAP_SETUID`) |
| `kill_policy` | `"sigterm_then_sigkill"` | SIGTERM+SIGKILL for timed-out processes, or `"sigkill_only"` |
| `kill_grace_sec` | `2.0` | Seconds to wait after SIGTERM before switching to SIGKILL |

**Health:** If `sh` is found: `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{"sandbox_backend":"firejail"/"none"}}`; if not found: `"status":"degraded","ready":false,"dependencies":{"shell":"sh not found in PATH"/"check failed"}}` — HTTP 200 when ready, 503 when degraded.
**Logs:** `/opt/llm/logs/shell-mcp.log`
**Audit:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (Shared MCP): `mcp_tool_exec` / Layer3 (Dedicated): `shell_audit.log`

| sandbox_backend | Meaning | Use Case |
|---|---|---|
| `"none"` | No process isolation; only `RLIMIT_*` limits apply | Local development only |
| `"firejail"` | Process isolation via firejail (`--private --net=none --noroot`) | Recommended for production |

> **Security Note — Sandboxing is disabled by default:** The default value for `sandbox_backend` is `"none"`. Shell commands are executed with the OS user and privileges of the agent process — there is no container or namespace isolation. To enable sandboxing, install firejail and set `sandbox_backend = "firejail"` in `config/shell_mcp_server.toml`. You can verify the active backend via the `details.sandbox_backend` field (`"none"` or `"firejail"`) in the `/health` response.
> **Enforcement in Production:** In production mode (`security_profile = "production"` in `agent.toml`), `sandbox_backend = "none"` is not allowed. If this combination is detected, the agent will raise a `RuntimeError` at startup. In production environments, either set `sandbox_backend = "firejail"` or disable `shell-mcp`.
>
> > **Note**: `shell-mcp` itself does not perform production checks or enforcement. Enforcement in production is handled by the Agent's startup sequence (via `scripts/agent/repl_health.py::audit_security_defaults()` called from `scripts/agent/startup.py`). If `shell-mcp` is started independently of the Agent startup path, this enforcement may be bypassed.

---

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_04_01_web-search-file-read-github.md`
- `04_mcp_04_03_rag-pipeline-and-cicd.md`
- `04_mcp_04_04_mdq.md`
- `04_mcp_04_05_git.md`
- `00_security_02_high-risk-tool-common-policy.md` — 高リスクMCPツール共通ポリシー (パス/リポ許可リスト, トラバーサル防止, 承認-リスクティアマッピング)

## Keywords

mcp
server-catalog
file-write-mcp, file-delete-mcp, shell-mcp, port 8007, port 8008, port 8009
