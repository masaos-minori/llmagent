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

Tool membership and risk tiers: [mcp_01_tool_ownership_matrix.md](mcp_01_tool_ownership_matrix.md). Health response semantics common to all servers: [mcp_02_02](mcp_02_02_startup-modes-and-health.md). Availability metadata: [mcp_03_06_tool-runtime-availability-metadata.md](mcp_03_06_tool-runtime-availability-metadata.md). Each server is a high-risk category tool; the cross-cutting policy is [security_02_high-risk-tool-common-policy.md](../91_security/security_02_high-risk-tool-common-policy.md) (Layered protection model). Agent-side approval confirms user intent only; it is not a bypass for any check below, and none of these servers performs an approval check itself.

## file-write-mcp

**Purpose:** Write operations to the local filesystem. All tools support `dry_run=True`, which returns the diff or feasibility information and performs no write.
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/file_write_mcp_server.toml` (`allowed_dirs`, `max_write_bytes`)

- No tool requires configuration (`config_dependent: false`); availability depends on `allowed_dirs` (empty means disabled, reason `"allowed_dirs is empty"`).
- `max_write_bytes` is enforced as a UTF-8 byte count by a manual check in the service (not Pydantic constraints): `write_file` on the content, `edit_file` on the text after the edits are applied. Exceeding it raises `FileValidationError`.
- Error mapping: 403 `FileAuthorizationError`, 404 `FileNotFoundError`, 422 `FileValidationError`.
- `/health`: `dependencies.filesystem` reports a workspace root that is not a directory; HTTP 200 when ready, 503 when degraded.
- Logs: `<log_dir>/file-write-mcp.log`. Audit: Layer1 (Agent/MCP shared) `tool_exec`, Layer2 (Shared MCP) `mcp_tool_exec`, Layer3 (Dedicated) none.

### Guard and postcondition coverage

- **Common guard:** `call_tool` rejects a disabled tool first. Every tool resolves its path through `WriteFileService._resolve_safe()`, which canonicalizes with `Path.resolve()` and requires containment in `allowed_dirs`; traversal and symlink escapes raise `FileAuthorizationError`. An empty `allowed_dirs` denies every path.
- **Command-specific guard:** `edit_file` rejects a file that cannot be decoded as UTF-8 and an `old_text` not present in the file. `move_file` rejects a missing source. `create_directory` is idempotent (an existing path returns `created=false`). Dangerous-option rejection is not applicable: the tool surface is a fixed, named dispatch table with no free-form argument that reaches a shell.
- **Postcondition verification:** `write_file` and `edit_file` write atomically (a `.tmp_<name>` file plus `os.replace`; the temporary file is deleted if the write fails) and then compare the resulting file size with the requested byte count. `move_file` rejects a destination that does not exist or a source that still exists. A mismatch raises `FileValidationError` and is reported as a failure, never as success.
- **Audit:** `call_tool` records one `mcp_tool_exec` entry per call: `outcome` is `"ok"` or `"error"` from the dispatch result, and the disabled-`allowed_dirs` and argument-validation early returns record `outcome="rejected"`. `target` is the caller-supplied path truncated to 80 characters and `server_key` is `file_write`; `requested_target` and `canonical_target` are not supplied. No before/after state or approval correlation is recorded.

---

## file-delete-mcp

**Purpose:** Deletion from the local filesystem. All tools support `dry_run=True`; `delete_directory` then scans the contents (bounded file count, reported as `"<count>+ files"` past the cap) and deletes nothing.
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/file_delete_mcp_server.toml` (`allowed_dirs`)

- No tool requires configuration (`config_dependent: false`); availability depends on `allowed_dirs` (empty means disabled, reason `"allowed_dirs is empty"`).
- Error mapping: 403 `FileAuthorizationError`, 404 `FileNotFoundError`, 422 `FileValidationError`. `/health` is the same as file-write-mcp.
- Logs: `<log_dir>/file-delete-mcp.log`. Audit: Layer1 `tool_exec`, Layer2 `mcp_tool_exec` (in `file-delete-mcp.log`), Layer3 `<log_dir>/delete_audit.log` (ISO8601 UTC + op + path + user). The audit destination is fixed in code, not a configuration key.
- **Audit write failure policy:** failure to write `delete_audit.log` is logged as an error and does not raise; the deletion still returns as successful. This differs from github-mcp, where `GitHubAuditError` fails the call.

### Guard and postcondition coverage

- **Common guard:** `call_tool` rejects a disabled tool first. Both tools resolve paths through `DeleteFileService._resolve_safe()` (canonicalization plus containment in `allowed_dirs`); traversal and symlink escapes raise `FileAuthorizationError`.
- **Command-specific guard:** `delete_file` rejects a path that is not an existing file. `delete_directory` rejects a non-directory and rejects a non-empty directory when `recursive=false`. Both reject a target that is itself an `allowed_dirs` root (`FileAuthorizationError`), on the recursive and non-recursive path alike; individual files and subdirectories inside an allowed directory remain deletable. The root guard runs after the `dry_run` early return, so a `dry_run` call is not subject to it. Dangerous-option rejection is not applicable (fixed dispatch table).
- **Postcondition verification:** after deletion `_verify_deleted()` raises `FileValidationError` if the target still exists. Such a delete is reported as a failure and is not written to `delete_audit.log`; the dedicated entry is written only after verification passes.
- **Audit:** same `mcp_tool_exec` pattern as file-write-mcp (`server_key` is `file_delete`; `target` is the caller-supplied path truncated to 80 characters; no `requested_target` or `canonical_target`).

---

## shell-mcp

**Purpose:** Execution of sandboxed shell commands within the `command_allowlist`.
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/shell_mcp_server.toml` (defaults are owned by this file and `ShellConfig`)

Security-relevant settings:

- `command_allowlist` matches the base name of `argv[0]`; empty means disabled (reason `"command_allowlist is empty"`).
- `shell_cwd_allowed_dirs`: empty means all working directories are denied.
- `env_allowlist` / `env_denylist` filter `req.env` (default-deny filter; the denylist applies when the allowlist is empty).
- A command receives a small fixed base environment plus the filtered `req.env`, never the server process environment; credential-shaped variables (`MCP_*`, token, secret and password variables) are removed even when listed in `req.env`.
- `max_timeout_sec`, `max_output_kb`, `max_memory_mb` (`RLIMIT_AS`) bound resource use; `kill_policy` / `kill_grace_sec` choose SIGTERM-then-SIGKILL or SIGKILL only for timed-out processes.
- `execution_user` runs commands as another OS user via setuid and requires `CAP_SETUID`.
- `audit_log_path` is the dedicated audit log; `shell_sandbox_backend` selects isolation (below).

**Sandbox backend:** `"firejail"` isolates the process (`--private --net=none --noroot`) and is the production setting. `"none"` applies only `RLIMIT_*` limits, with no process isolation, and is never permitted.

> **Security Note - sandboxing is on by default:** The code default and `config/shell_mcp_server.toml` are both `"firejail"`, so a default configuration requires the `firejail` binary in `PATH`; if it is missing, `init_sandbox()` raises `RuntimeError` when the service is built. With `"none"`, commands would run with the OS user and privileges of the shell-mcp process, with no container or namespace isolation. The active backend is visible as `details.sandbox_backend` in `/health`.
>
> **Enforcement:** `shell_sandbox_backend = "none"` is rejected by shell-mcp itself: the startup Security Posture check `server.sandbox_backend` reports `failed`, so the posture does not validate and shell-mcp refuses to bind its HTTP port. The Agent reads the same posture from `/health` and aborts startup. Set `shell_sandbox_backend = "firejail"` or disable `shell-mcp`. Enforcement lives in shell-mcp's own startup validation (`validate_shell_security()` in `scripts/mcp_servers/shell/shell_service_static_helpers.py`), not in a separate Agent-side audit, so a shell-mcp process started independently of the Agent still refuses to bind when its posture fails. See [ADR-004](../10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md).

- `/health`: `dependencies.shell` reports `sh` not found; `details.sandbox_backend` is `firejail` or `none`.
- Logs: `<log_dir>/shell-mcp.log`. Audit: Layer1 `tool_exec`, Layer2 `mcp_tool_exec` (in `shell-mcp.log`), Layer3 `shell_audit.log`.

### Guard and postcondition coverage

- **Common guard:** `call_tool` rejects a disabled tool first. The service rejects a command whose base name is not in `command_allowlist` and a `cwd` outside `shell_cwd_allowed_dirs`; the sandbox backend, `RLIMIT_*` limits, and env filtering are fixed when the service is built.
- **Command-specific guard:** not applicable as a complete layer. `shell_run` takes a free-form command string, so dangerous-option rejection cannot be exhaustive for an allowed command. The checks that do run are the allowlist base-name match, the `max_timeout_sec` limit, and the registered `shell_run` argument validator.
- **Postcondition verification:** not applicable. An arbitrary allowed command has no expected resulting state; exit-code classification, timeout enforcement, and output truncation reporting against `max_output_kb` are result checks only.
- **Audit:** one shared `mcp_tool_exec` record per dispatched call (`target` is the command truncated to 80 characters); a disabled-tool rejection returns before the audit call and writes no record. The service writes the dedicated `shell_audit.log` entry.

---

## Layered protection coverage

file-write-mcp, file-delete-mcp, and shell-mcp are high-risk category tools (path-authorized filesystem mutation and process execution). The five Layered protection layers stand as follows per tool.

### file-write-mcp

- **Agent approval** — Not applicable server-side. Approval is an Agent-side gate; file-write enforces only its own technical constraints (`allowed_dirs`, `max_write_bytes`).
- **Common guard** — Implemented. `allowed_dirs` fail-closed authorization with `..`-traversal and symbolic-link escape blocked by `Path.resolve()` inside `resolve_safe()`; an empty `allowed_dirs` denies every path (see Path Control). (Explicit in code — `scripts/mcp_servers/file/common.py`)
- **Command-specific guard** — Partially implemented. `max_write_bytes` is enforced via a manual byte-count check in `write_file` (raises `FileValidationError`); `edit_file` performs no byte-limit check and writes non-atomically. (Explicit in code — `scripts/mcp_servers/file/write_service.py::WriteFileService.write_file`, `edit_file`)
- **Postcondition verification** — Not implemented. `write_file` never compares the written byte length against the intended size; `move_file` reports success without verifying the source is gone and the destination exists; `edit_file` reports `applied=True` without comparing the resulting file against intent. (Code review — `scripts/mcp_servers/file/write_service.py::write_file`, `move_file`, `edit_file`)
- **Audit** — Shared `mcp_tool_exec` is not emitted: `call_tool` extracts the request context and discards it, so no audit record carries identity, operation type, or before/after state. No dedicated audit log is written either. (Code review — `scripts/mcp_servers/file/write_server.py::call_tool`)

### file-delete-mcp

- **Agent approval** — Not applicable server-side. Approval is an Agent-side gate; file-delete enforces only its own technical constraints (`allowed_dirs`).
- **Common guard** — Implemented. `allowed_dirs` fail-closed authorization with `..`-traversal and symbolic-link escape blocked by `Path.resolve()` inside `resolve_safe()`. (Explicit in code — `scripts/mcp_servers/file/common.py`)
- **Command-specific guard** — Partially implemented. The allowed-root protection runs only when `recursive=true`; a non-recursive rmdir() on an empty directory that is itself an allowed root is not rejected. (Explicit in code — `scripts/mcp_servers/file/delete_service.py::delete_directory`)
- **Postcondition verification** — Not implemented. `delete_file`/`delete_directory` return `deleted=True` without verifying the target is actually gone, and a partial `shutil.rmtree` failure is reported as success. (Code review — `scripts/mcp_servers/file/delete_service.py::delete_file`, `delete_directory`)
- **Audit** — A dedicated plain-text log (`delete_audit.log`, ISO8601 UTC + op + path + user) is written after a successful deletion, plus the Agent-side `tool_exec`. Shared `mcp_tool_exec` is not emitted. (Explicit in code — `scripts/mcp_servers/file/delete_service.py::_write_audit_log`)

### shell-mcp

- **Agent approval** — Not applicable server-side. Approval is an Agent-side gate; shell enforces only its own technical constraints (`command_allowlist`, `shell_cwd_allowed_dirs`, env filter).
- **Common guard** — Implemented. `command_allowlist`, `shell_cwd_allowed_dirs` (default-deny when empty), and a default-deny environment filter. (Explicit in code — `scripts/mcp_servers/shell/shell_service_static_helpers.py`)
- **Command-specific guard** — Partially implemented. CWD allowlist, env allowlist, `RLIMIT_*` resource limits, and firejail sandbox backend are enforced; dangerous-option rejection is not applicable because the command surface is free-form. (Explicit in code — `scripts/mcp_servers/shell/shell_service_static_helpers.py`)
- **Postcondition verification** — Not applicable. An arbitrary command has no expected resulting state; exit-code classification, timeout enforcement, and output truncation reporting are result checks rather than postcondition verification.
- **Audit** — Implemented. Every call is recorded through the shared `_audit_log()` with `server_key="shell"` (session/request id, action, target command, outcome), plus a dedicated plain-text log (`shell_audit.log`). (Explicit in code — `scripts/mcp_servers/shell/shell_server.py::call_tool`)

---

## Keywords

- mcp
- server-catalog
- file-write-mcp
- file-delete-mcp
- shell-mcp
