# Implementation: Document firejail sandbox default in configuration_and_operations.md

Steps covered: Plan 20260626-091916 — Step 3-2

---

## Goal

Document the `sandbox_backend="firejail"` production default and the startup health checks in `docs/04_mcp_06_configuration_and_operations.md`.

---

## Scope

- **In scope**: `docs/04_mcp_06_configuration_and_operations.md` — add sandbox configuration section
- **Out of scope**: runtime code changes

---

## Implementation

### Target file
`docs/04_mcp_06_configuration_and_operations.md`

### Procedure
1. Find the shell MCP server configuration section.
2. Add or update sandbox backend documentation:
   ```
   ### Sandbox Backend (shell MCP server)

   The shell MCP server executes commands in a sandbox. The production default is `firejail`.

   ```toml
   # config/shell_mcp_server.toml
   sandbox_backend = "firejail"  # production default
   # sandbox_backend = "none"    # development only, WARNING: unsandboxed
   ```

   **Startup health checks**:
   - If `sandbox_backend != "firejail"`: WARNING at startup.
   - If `sandbox_backend = "firejail"` but firejail binary is missing: ERROR at startup.

   Install firejail: `apt-get install firejail` (Debian/Ubuntu) or equivalent.
   ```

### Method
Documentation-only change.

---

## Validation plan

- Pre-commit: `pre-commit run --all-files` — markdown lint must pass.
- Confirm: `grep -n "firejail\|sandbox_backend" docs/04_mcp_06_configuration_and_operations.md` shows the section.
