# Implementation: Add safe-by-default production config templates

Steps covered: Plan 20260626-091918 — All steps (config files + docs)

---

## Goal

Update `config/*.toml` files to have safe production defaults: fail-closed allowlists, firejail sandbox, required fields commented-out with clear instructions, and optional dangerous settings disabled by default.

---

## Scope

- **In scope**:
  - `config/cicd_mcp_server.toml`: `workflow_allowlist = []` with fail-closed comment
  - `config/shell_mcp_server.toml`: `sandbox_backend = "firejail"` with install note
  - `config/github_mcp_server.toml`: `allowed_workflows` removal or fail-closed comment
  - `config/common.toml`: any dangerous defaults (e.g., `debug = false`, `log_level = "WARNING"`)
  - Docs: `docs/04_mcp_06_configuration_and_operations.md` — "Production Configuration Checklist"
- **Out of scope**: runtime code changes

---

## Assumptions

- Config files exist and have editable settings.
- "Safe by default" means: minimum permissions granted, no anonymous access, sandboxing enabled, logging at WARNING+.

---

## Implementation

### Target files
- `config/cicd_mcp_server.toml`
- `config/shell_mcp_server.toml`
- `config/github_mcp_server.toml`
- `config/common.toml`
- `docs/04_mcp_06_configuration_and_operations.md`

### Procedure

**cicd_mcp_server.toml**:
```toml
# Fail-closed: empty list denies all workflow triggers.
# Add allowed workflow patterns to enable triggering.
# workflow_allowlist = [
#   "my-org/my-repo/.github/workflows/deploy.yml",
# ]
workflow_allowlist = []
```

**shell_mcp_server.toml**:
```toml
# Production default: firejail. Install: apt-get install firejail
sandbox_backend = "firejail"
# sandbox_backend = "none"  # development only
```

**github_mcp_server.toml**:
If `allowed_workflows` removed: delete the field and add a comment explaining removal.
If fail-closed: add fail-closed comment (matching plan 08 outcome).

**common.toml**:
```toml
debug = false
log_level = "WARNING"  # production; use "DEBUG" for development
```

**docs/04_mcp_06_configuration_and_operations.md**:
Add "Production Configuration Checklist":
```
## Production Configuration Checklist

- [ ] `sandbox_backend = "firejail"` in `shell_mcp_server.toml`
- [ ] `workflow_allowlist` populated in `cicd_mcp_server.toml`
- [ ] `debug = false` in `common.toml`
- [ ] API keys set via environment variables (not hardcoded in config)
- [ ] `log_level = "WARNING"` or higher
```

### Method
Config + docs update. No runtime changes.

---

## Validation plan

- Pre-commit: `pre-commit run --all-files` — toml and markdown lint must pass.
- Confirm: running server with default config does NOT require manual override of dangerous defaults.
