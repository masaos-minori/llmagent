# Implementation: M-4 — docs/04_mcp_05_security_and_safety_model.md reload boundary note

Source plan: `plans/20260709-100958_plan.md` (M-4, Implementation step 3).

## Goal

Make explicit that production MCP auth validation is startup-only and
`/reload` never re-runs it or applies `auth_token` changes.

## Scope

**Target**: `docs/04_mcp_05_security_and_safety_model.md`, immediately after
line 186 (the "Enforcement point" sentence).

## Assumptions

1. Lines 179-186 already document the production/local auth requirement and
   its enforcement point (`audit_security_defaults()`) but say nothing about
   `/reload` — verified by reading that section while planning M-4.

## Implementation

### Target file

`docs/04_mcp_05_security_and_safety_model.md`

### Procedure

#### Step 1: Insert the new note after line 186

Current (line 186):
```markdown
**Enforcement point:** `audit_security_defaults()` in `agent/repl_health.py` raises during startup when `security_profile == "production"` and an HTTP server has an empty `auth_token`. It also warns on `shell_sandbox_backend == "none"` and empty `tool.allowed_tools`.
```

Add immediately after (before the `**Audit API isolation:**` paragraph):
```markdown

**Reload boundary:** `/reload` never re-runs this check and never applies
`auth_token` changes to a running MCP server — token changes are always
reported as restart-required (see
[Configuration: Hot-reload eligibility](05_agent_08_configuration.md#config-file-ownership-and-hot-reload-eligibility)).
Production auth validation only ever runs at startup; there is no runtime
path that can weaken or bypass it.
```

### Method

- One paragraph insertion; no existing text modified.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Note present | `grep -n "Reload boundary" docs/04_mcp_05_security_and_safety_model.md` | 1 match |
| Anchor valid | confirm `#config-file-ownership-and-hot-reload-eligibility` matches the actual heading slug in `docs/05_agent_08_configuration.md` | matches |
| MCP docs consistency | `uv run check-mcp-docs` | pass |
