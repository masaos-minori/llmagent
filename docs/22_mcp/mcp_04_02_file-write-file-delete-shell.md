---
title: "MCP Server Catalog: file-write-mcp / file-delete-mcp / shell-mcp"
area: mcp
tags:
  - mcp
  - server-catalog
  - file-operations
related:
  - mcp_00_document-guide.md
---
# MCP Server Catalog: file-write-mcp / file-delete-mcp / shell-mcp

## file-write-mcp 

**Purpose:** Write operations to the local filesystem. All tools support `dry_run=True`.
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/file_write_mcp_server.toml`

**Tools:** `write_file`, `edit_file`, `create_directory`, `move_file`

All tools do not require configuration (`config_dependent: false`).

The runtime availability (`enabled`/`disabled_reason`) of these tools depends on `allowed_dirs` (empty → disabled, reason `"allowed_dirs is empty"`). See [mcp_03_06_tool-runtime-availability-metadata.md](mcp_03_06_tool-runtime-availability-metadata.md) for details.

**Configuration Fields:** `allowed_dirs`, `max_write_bytes`

| Tool | Input | `dry_run` Behavior |
|---|---|---|
| `write_file` | `{path, content, dry_run?}` | Returns only diff; no writing |
| `edit_file` | `{path, edits: [{old_text, new_text}], dry_run?}` | Returns diff; no writing |
| `create_directory` | `{path, dry_run?}` | Returns directory info (exists/to be created); no creation |
| `move_file` | `{source, destination, dry_run?}` | Returns whether movement is possible |

**Health:** `{"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":bool,"dependencies":{"filesystem":"/workspace is not a directory"/"check failed: <error>"},"details":{}}` — HTTP 200 when ready, 503 when degraded.
**Configuration:** `max_write_bytes` (enforced as UTF-8 byte count)
**Error Codes:** 403 (FileAuthorizationError), 404 (FileNotFoundError), 422 (FileValidationError)
**Logs:** `<log_dir>/file-write-mcp.log`
**Audit:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (Shared MCP): None / Layer3 (Dedicated): None — does not write audit logs

### Implementation Notes (file-write-mcp)

- Enforcement of `max_write_bytes` is implemented via manual check in `write_service.py::WriteFileService.write_file` (`len(content.encode("utf-8")) > max_write_bytes`) rather than Pydantic field constraints (raises `FileValidationError` if exceeded). (Explicit in code)
- `write_file` performs atomic writes by writing to a temporary file (`.tmp_<name>`) first and then replacing it using `os.replace`. If the write fails, the temporary file is deleted before returning an error. (Explicit in code)

---

## file-delete-mcp 

**Purpose:** Deletion from the local filesystem. All tools support `dry_run=True`.
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/file_delete_mcp_server.toml`

**Tools:** `delete_file`, `delete_directory`

All tools do not require configuration (`config_dependent: false`).

The runtime availability (`enabled`/`disabled_reason`) of these tools depends on `allowed_dirs` (empty → disabled, reason `"allowed_dirs is empty"`). See [mcp_03_06_tool-runtime-availability-metadata.md](mcp_03_06_tool-runtime-availability-metadata.md) for details.

**Configuration Fields:** `allowed_dirs`

| Tool | Input | `dry_run` Behavior |
|---|---|---|
| `delete_file` | `{path, dry_run?}` | Returns file information; no deletion |
| `delete_directory` | `{path, recursive?, dry_run?}` | Scans contents (bounded file count); no deletion |

**Health:** `{"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":bool,"dependencies":{"filesystem":"/workspace is not a directory"/"check failed: <error>"},"details":{}}` — HTTP 200 when ready, 503 when degraded.
**Deletion Audit Log:** `<log_dir>/delete_audit.log` (ISO8601 UTC + op + path + user)
**Audit:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (Shared MCP): None / Layer3 (Dedicated): `delete_audit.log`
**Error Codes:** 403 (FileAuthorizationError), 404 (FileNotFoundError), 422 (FileValidationError)
**Logs:** `<log_dir>/file-delete-mcp.log`

### Implementation Notes

- `audit_log_path` is not a configuration key of `config/file_delete_mcp_server.toml`: `FileDeleteConfig` does not load it, and `delete_service.py::build_service` fixes the audit log destination in code. (Explicit in code)
- Even if writing to the audit log fails, no exception is raised; instead, an error is logged and the deletion process itself returns as successful (unlike github-mcp's `GitHubAuditError`, failure to write the audit log does not block the deletion operation in file-delete-mcp). (Explicit in code)
- `delete_directory(recursive=true)` rejects deletion with a `FileAuthorizationError` if the target matches any root directory defined in `allowed_dirs` (it does not prevent deleting individual files/subdirectories within allowed directories). (Explicit in code)
- Directory scanning during `dry_run` is capped at `_DRY_RUN_MAX_FILES` (defined in `scripts/mcp_servers/file/delete_service.py`) and reflected in `dir_info` as `"<count>+ files"`. (Explicit in code)

---

## shell-mcp 

**Purpose:** Execution of sandboxed shell commands within the `command_allowlist`.
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/shell_mcp_server.toml`

**Tools:** `shell_run`

| Key | Description |
|---|---|
| `command_allowlist` | Allowed command names (base name of `argv[0]`) |
| `shell_cwd_allowed_dirs` | Allowed CWD paths (empty = all denied) |
| `max_timeout_sec` | Timeout limit |
| `max_output_kb` | Output limit |
| `max_memory_mb` | Memory limit (`RLIMIT_AS`) |
| `shell_sandbox_backend` | `"firejail"` or `"none"` (see sandbox table below) |
| `audit_log_path` | Audit log |
| `default_cwd` | Working directory if no cwd is specified in request |
| `shell_path` | PATH environment variable for child processes |
| `env_allowlist` | Allowed environment variable keys in `req.env` (if empty, uses `env_denylist`) |
| `env_denylist` | Glob patterns for environment variable keys to remove from `req.env` |
| `execution_user` | OS user to run commands as via setuid (requires `CAP_SETUID`) |
| `kill_policy` | SIGTERM+SIGKILL for timed-out processes, or `"sigkill_only"` |
| `kill_grace_sec` | Seconds to wait after SIGTERM before switching to SIGKILL |

Current default values are defined in `config/shell_mcp_server.toml`.

**Health:** If `sh` is found: `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{"sandbox_backend":"firejail"/"none"}}`; if not found: `"status":"degraded","ready":false,"dependencies":{"shell":"sh not found in PATH"/"check failed"}}` — HTTP 200 when ready, 503 when degraded.
**Logs:** `<log_dir>/shell-mcp.log`
**Audit:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (Shared MCP): `mcp_tool_exec` / Layer3 (Dedicated): `shell_audit.log`

| sandbox_backend | Meaning | Use Case |
|---|---|---|
| `"none"` | No process isolation; only `RLIMIT_*` limits apply | Never permitted |
| `"firejail"` | Process isolation via firejail (`--private --net=none --noroot`) | Recommended for production |

> **Security Note — Sandboxing is on by default:** The code default for `shell_sandbox_backend` (`ShellConfig`) and the value in `config/shell_mcp_server.toml` are both `"firejail"`, so a default configuration requires the `firejail` binary in `PATH`; if it is missing, `init_sandbox()` raises `RuntimeError` when the service is built. With `"none"`, commands run with the OS user and privileges of the shell-mcp process, with no container or namespace isolation. You can verify the active backend via the `details.sandbox_backend` field (`"none"` or `"firejail"`) in the `/health` response. (Explicit in code — `scripts/mcp_servers/shell/shell_models.py`, `scripts/mcp_servers/shell/shell_service_static_helpers.py`)
> **Enforcement:** `shell_sandbox_backend = "none"` is rejected by the Agent startup audit (`audit_security_defaults()`), which raises `RuntimeError` regardless of environment, so an Agent-managed startup fails. Set `shell_sandbox_backend = "firejail"` or disable `shell-mcp`.
>
> > **Note**: `shell-mcp` itself does not reject `"none"` (it only validates that the `firejail` binary exists when `"firejail"` is configured). Enforcement is handled by the Agent's startup sequence (via `scripts/agent/services/security_audit.py::audit_security_defaults()` called from `scripts/agent/startup.py`). If `shell-mcp` is started independently of the Agent startup path, this enforcement may be bypassed.

---

## Keywords

- mcp
- server-catalog
- file-write-mcp
- file-delete-mcp
- shell-mcp
