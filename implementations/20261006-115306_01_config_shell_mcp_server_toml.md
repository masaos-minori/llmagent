## Goal

Set `shell_sandbox_backend = "firejail"` in `config/shell_mcp_server.toml` and rewrite its comment to require firejail, removing the misleading "none yields a WARNING at startup" claim. (REQ-002 / AC-2)

## Scope

- Change the `shell_sandbox_backend` value from `"none"` to `"firejail"`
- Rewrite the sandbox-backend comment block to state that firejail is required and must be installed
- Remove the "Development: none" line and the "WARNING at startup" claim

## Assumptions

- Option A (never permitted) is the adopted policy — the audit's raise-for-`none` stays unchanged
- firejail will be installed on target hosts as part of deployment; until then, startup with a `firejail` config raises (expected fail-fast)

## Design decisions

- Adopt Option A: `none` is never permitted in any environment, matching the existing audit behavior and `mcp_05_02`/`mcp_06_16` wording
- Keep the audit's raise-for-`none` intact — do not weaken it

## Alternatives considered

- Option B: Allow `none` in development by adding an environment branch to the security audit — rejected because it would increase the audit's already-high cyclomatic complexity (radon E/38) and must not be done silently

## Implementation

### Target file

`config/shell_mcp_server.toml`

### Procedure

1. Change `shell_sandbox_backend = "none"` to `shell_sandbox_backend = "firejail"` (line 31)
2. Rewrite the comment block (lines 27-30) to state that firejail is required and must be installed

### Method

- Edit the TOML value directly
- Rewrite the comment block to remove the "none" development path and replace it with a firejail-required statement

### Details

**Before (lines 27-31):**
```toml
# shell_sandbox_backend: "firejail" | "none"
# Production: set to "firejail" (requires firejail: apt-get install firejail).
#   Startup raises RuntimeError when backend="firejail" but firejail binary is not in PATH.
# Development: "none" — unsandboxed execution, WARNING at startup.
shell_sandbox_backend = "none"
```

**After:**
```toml
# shell_sandbox_backend: "firejail" (required — "none" is never permitted)
# Production: set to "firejail" (requires firejail: apt-get install firejail).
#   Startup raises RuntimeError when backend="firejail" but firejail binary is not in PATH.
shell_sandbox_backend = "firejail"
```

## Compatibility considerations

- Changing the default in `shell_models.py` (SEQ-02) means the code default also resolves to `"firejail"` — operators running without the config file will get the same behavior
- The deployed copy under `/opt/llm/config/` must be updated via the deploy workflow (not edited directly)

## Security considerations

- This change enforces the security policy that `none` is never permitted — it removes the contradiction between the config comment and the audit
- The audit's raise-for-`none` remains unchanged (see Reference Files: `security_audit.py`)

## Rollback considerations

- Reverting to `"none"` would restore the contradiction with the audit and the MCP documents
- If firejail is not yet installed on a host, reverting to `"none"` would allow the agent to start but without sandboxing — this should be avoided

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `config/shell_mcp_server.toml` | Integration: audit against the real checked-in config | `uv run pytest tests/agent/test_repl_health.py` | Audit passes when firejail present / raises firejail-missing when absent; no `none` value present |

## Completion criteria

- `shell_sandbox_backend = "firejail"` in the file
- Comment block states firejail is required and does not mention "none" as a valid option
- No "WARNING at startup" claim remains in the comment

## Out of scope

- Changes to firejail arguments or the sandbox implementation (`init_sandbox`, `build_argv`)
- Deployment of the `/opt/llm/config/` copy (deployment step only — no direct edit of the deployed copy)
- Installing firejail on the host

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Set `shell_sandbox_backend = "firejail"` and rewrite the sandbox comment | Completed | 20261006-174126 | 20261006-174126 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261006-174126 | 20261006-174126 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261006-174126 | 20261006-174126 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261006-174126 | 20261006-174126 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261005-102246_mcp001_shell-sandbox-none-config-contradicts-startup-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261005-222431_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-115306
- **Related target files**: config/shell_mcp_server.toml