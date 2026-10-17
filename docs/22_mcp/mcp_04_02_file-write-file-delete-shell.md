---
title: "MCP Server Catalog: file-write-mcp / file-delete-mcp / shell-mcp"
area: mcp
tags:
  - mcp
  - server-catalog
  - file-operations
related:
  - mcp_00_document-guide.md
  - mcp_03_06_tool-runtime-availability-metadata.md
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
**Audit:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (Shared MCP): `mcp_tool_exec` / Layer3 (Dedicated): None — no dedicated audit log; the shared record is written for every call (see Guard and postcondition coverage below)

### Guard and postcondition coverage

See also: [security_02_high-risk-tool-common-policy.md](../91_security/security_02_high-risk-tool-common-policy.md) Layered protection model for the general framework this section instantiates. Agent-side approval confirms user intent only; it is not a bypass for any check below.

#### Common guard

`write_server.py::call_tool` rejects a disabled tool (reason `allowed_dirs is empty`) before anything else. Every tool then resolves its path through `WriteFileService._resolve_safe()`, which canonicalizes with `Path.resolve()` and requires containment in `allowed_dirs`; traversal and symlink escapes raise `FileAuthorizationError`. `max_write_bytes` is enforced as a UTF-8 byte count. (Explicit in code — `scripts/mcp_servers/file/write_server.py`, `scripts/mcp_servers/file/write_service.py`)

#### Command-specific guard status

`write_file` and `edit_file` reject content whose UTF-8 byte count exceeds `max_write_bytes`. `edit_file` additionally rejects a file that cannot be decoded as UTF-8 and an `old_text` that is not present in the file. `move_file` rejects a missing source. `create_directory` is idempotent: an existing path returns `created=false`. Dangerous-option rejection is not applicable — the tool surface is a fixed, named dispatch table with no free-form argument that reaches a shell. (Explicit in code — `scripts/mcp_servers/file/write_service.py`)

#### Postcondition verification

`write_file` and `edit_file` write through `_atomic_write()` (a `.tmp_<name>` file plus `os.replace`) and then `_verify_written_size()` compares the resulting file size with the requested byte count; a mismatch raises `FileValidationError`. `move_file` runs `_verify_moved()`, which rejects a destination that does not exist or a source that still exists. A write or move whose resulting state does not match is reported as a failure rather than as success. (Explicit in code — `scripts/mcp_servers/file/write_service.py`)

#### Audit

`write_server.py::call_tool` calls `_audit_log()` once per call: the dispatched call is recorded with the outcome taken from the dispatch result (`"ok"` or `"error"`), and the disabled-`allowed_dirs` and argument-validation early returns each record one entry with `outcome="rejected"`. `target` is the caller-supplied path truncated to 80 characters and `server_key` is `file_write`; this server supplies neither `requested_target` nor `canonical_target`, so the requested path appears in `target`. (Explicit in code — `scripts/mcp_servers/file/write_server.py`, `scripts/mcp_servers/audit.py`)

### Implementation Notes (file-write-mcp)

- Enforcement of `max_write_bytes` is implemented via manual check in `write_service.py::WriteFileService` rather than Pydantic field constraints: `write_file` checks `len(content.encode("utf-8"))` and `edit_file` checks the byte count of the text after the edits are applied (both raise `FileValidationError` if exceeded). (Explicit in code)
- `write_file` and `edit_file` perform atomic writes by writing to a temporary file (`.tmp_<name>`) first and then replacing it using `os.replace`. If the write fails, the temporary file is deleted before returning an error. (Explicit in code)
- After an applied write, `_verify_written_size()` compares the resulting file size with the requested byte count, and `move_file` runs `_verify_moved()`; a mismatch raises `FileValidationError` instead of reporting success. (Explicit in code)

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
**Audit:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (Shared MCP): `mcp_tool_exec` / Layer3 (Dedicated): `delete_audit.log`
**Error Codes:** 403 (FileAuthorizationError), 404 (FileNotFoundError), 422 (FileValidationError)
**Logs:** `<log_dir>/file-delete-mcp.log`

### Guard and postcondition coverage

See also: [security_02_high-risk-tool-common-policy.md](../91_security/security_02_high-risk-tool-common-policy.md) Layered protection model for the general framework this section instantiates. Agent-side approval confirms user intent only; it is not a bypass for any check below.

#### Common guard

`delete_server.py::call_tool` rejects a disabled tool (reason `allowed_dirs is empty`) before anything else. Both tools resolve their path through `DeleteFileService._resolve_safe()`, which canonicalizes with `Path.resolve()` and requires containment in `allowed_dirs`; traversal and symlink escapes raise `FileAuthorizationError`. (Explicit in code — `scripts/mcp_servers/file/delete_server.py`, `scripts/mcp_servers/file/delete_service.py`)

#### Command-specific guard status

`delete_file` rejects a path that is not an existing file. `delete_directory` rejects a path that is not a directory and rejects a non-empty directory when `recursive=false`. Both tools reject a target that is itself one of the `allowed_dirs` roots through `_check_not_deleting_allowed_root()`, on the recursive and the non-recursive path alike; the guard runs after the `dry_run` early return, so a `dry_run` call is not subject to it. Dangerous-option rejection is not applicable — the tool surface is a fixed, named dispatch table with no free-form argument that reaches a shell. (Explicit in code — `scripts/mcp_servers/file/delete_service.py`)

#### Postcondition verification

`delete_file` and `delete_directory` run `_verify_deleted()` after the deletion, which raises `FileValidationError` when the target still exists. A delete whose target survives is reported as a failure and is not written to the dedicated deletion audit log. (Explicit in code — `scripts/mcp_servers/file/delete_service.py`)

#### Audit

`delete_server.py::call_tool` calls `_audit_log()` once per call: the dispatched call is recorded with the outcome taken from the dispatch result (`"ok"` or `"error"`), and the disabled-`allowed_dirs` and argument-validation early returns each record one entry with `outcome="rejected"`. `target` is the caller-supplied path truncated to 80 characters and `server_key` is `file_delete`; this server supplies neither `requested_target` nor `canonical_target`, so the requested path appears in `target`. The dedicated `delete_audit.log` entry is written by the service only after post-delete verification passes. (Explicit in code — `scripts/mcp_servers/file/delete_server.py`, `scripts/mcp_servers/file/delete_service.py`)

### Implementation Notes

- `audit_log_path` is not a configuration key of `config/file_delete_mcp_server.toml`: `FileDeleteConfig` does not load it, and `delete_service.py::build_service` fixes the audit log destination in code. (Explicit in code)
- Even if writing to the audit log fails, no exception is raised; instead, an error is logged and the deletion process itself returns as successful (unlike github-mcp's `GitHubAuditError`, failure to write the audit log does not block the deletion operation in file-delete-mcp). (Explicit in code)
- `delete_file` and `delete_directory` reject deletion with a `FileAuthorizationError` if the target matches any root directory defined in `allowed_dirs`, on both the recursive and the non-recursive path (it does not prevent deleting individual files/subdirectories within allowed directories). (Explicit in code)
- A deletion whose target still exists after the operation raises `FileValidationError` from `_verify_deleted()`, and no entry is written to `delete_audit.log` in that case. (Explicit in code)
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
> **Enforcement:** `shell_sandbox_backend = "none"` is rejected by shell-mcp itself. `init_sandbox()` raises `RuntimeError` when the service is built, and the startup Security Posture check `server.sandbox_backend` reports `failed`, so the posture does not validate and shell-mcp refuses to bind its HTTP port. The Agent reads the same posture from `/health` and aborts startup. Set `shell_sandbox_backend = "firejail"` or disable `shell-mcp`.
>
> > **Note**: Enforcement lives in shell-mcp's own startup validation (`scripts/mcp_servers/shell/shell_service_static_helpers.py::validate_shell_security()` plus the posture gate in `scripts/mcp_servers/shell/shell_server.py`), not in a separate Agent-side audit. A shell-mcp process started independently of the Agent startup path still refuses to bind when its posture fails. See [ADR-004](../10_adr/adr_02_004_environment-failure-handling-policy.md).

### Guard and postcondition coverage

See also: [security_02_high-risk-tool-common-policy.md](../91_security/security_02_high-risk-tool-common-policy.md) Layered protection model for the general framework this section instantiates. Agent-side approval confirms user intent only; it is not a bypass for any check below.

#### Common guard

`shell_server.py::call_tool` rejects a disabled tool (reason `command_allowlist is empty`) before anything else. The service rejects a command whose base name is not in `command_allowlist` and a `cwd` outside `shell_cwd_allowed_dirs`; the sandbox backend, the `RLIMIT_*` limits, and the `env_allowlist`/`env_denylist` filtering are fixed when the service is built. (Explicit in code — `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/shell/shell_service_static_helpers.py`)

#### Command-specific guard status

Not applicable as a complete layer: `shell_run` takes a free-form command string, so dangerous-option rejection cannot be exhaustive for an allowed command. The checks that do run before execution are the `command_allowlist` base-name match, the `max_timeout_sec` limit, and the registered `shell_run` argument validator. (Explicit in code — `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/tool_validators.py`)

#### Postcondition verification

Not applicable: an arbitrary allowed command has no expected resulting state to compare against. The result checks that do run are exit-code classification, timeout enforcement, and output truncation reporting against `max_output_kb`. (Explicit in code — `scripts/mcp_servers/shell/shell_service.py`)

#### Audit

`shell_server.py::call_tool` writes one shared `mcp_tool_exec` record per dispatched call, with `target` set to the command truncated to 80 characters and `outcome` taken from the dispatch result; a disabled-tool rejection returns before the audit call and writes no record. The service writes the dedicated `shell_audit.log` entry. (Explicit in code — `scripts/mcp_servers/shell/shell_server.py`)

---

## Keywords

- mcp
- server-catalog
- file-write-mcp
- file-delete-mcp
- shell-mcp
