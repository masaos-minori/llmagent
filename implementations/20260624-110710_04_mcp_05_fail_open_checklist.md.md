# Implementation: Consolidated Fail-Open Review Checklist

## Goal

Add a consolidated fail-open settings table to `04_mcp_05` and a pre-production operator checklist to `04_mcp_06`.

## Scope

**In:**
- `docs/04_mcp_05_security_and_safety_model.md` — add consolidated fail-open settings table
- `docs/04_mcp_06_configuration_and_operations.md` — add pre-production fail-open checklist

**Out:** No code changes.

## Assumptions

1. Multiple MCP settings can independently be fail-open (server unreachable, tool validation failure, health check failure).
2. A consolidated table helps operators review their posture in one place.
3. The checklist should be in ops doc (06), not the security doc (05).

## Implementation

### Target file

`docs/04_mcp_05_security_and_safety_model.md`, `docs/04_mcp_06_configuration_and_operations.md`

### Procedure

1. Read `docs/04_mcp_05_security_and_safety_model.md` security model sections to identify all fail-open settings.
2. Add consolidated table at end of security model.
3. Read `docs/04_mcp_06_configuration_and_operations.md` operations sections.
4. Add pre-production checklist.

### Method

Read then Edit tool patches.

### Details

**Consolidated fail-open table for `04_mcp_05`:**

```markdown
## Fail-Open / Fail-Closed Settings Review

| Setting | Default | Fail-open behavior | Production recommendation |
|---|---|---|---|
| `tool_definitions_strict` | `true` | `false` = validation errors downgraded to WARNING | Keep `true` |
| `strict_startup_validation` | `true` | `false` = missing servers downgraded to WARNING | Keep `true` |
| `require_sandbox` (shell-mcp) | `false` | `false` = no sandbox allowed | Set `true` in production |
| `allowlist_mode` | `true` | `false` = all tools allowed by default | Keep `true` |
| Server health fail-open | n/a | watchdog can skip restart on repeated failure | Configure `max_restart_attempts` |
```

**Pre-production operator checklist for `04_mcp_06`:**

```markdown
## Pre-Production Fail-Open Checklist

Before deploying to production, verify:
- [ ] `tool_definitions_strict = true` (fatal on schema mismatch)
- [ ] `strict_startup_validation = true` (fatal on unreachable servers)
- [ ] shell-mcp: `require_sandbox = true` OR sandbox_backend != "none"
- [ ] `allowlist_mode = true` (explicit tool allowlist required)
- [ ] Health check thresholds configured (`health_check_interval`, `max_restart_attempts`)
- [ ] DLQ depth monitored (see §Monitoring)
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Fail-open table added | `grep -n "Fail-Open.*Closed\|Fail-open behavior" docs/04_mcp_05_security_and_safety_model.md` | found |
| Checklist added | `grep -n "Pre-Production\|Fail-Open Checklist" docs/04_mcp_06_configuration_and_operations.md` | found |
| No code changes | `git diff scripts/` | empty |
