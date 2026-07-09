# Implementation: docs — local-to-production auth migration checklist

## Goal

Add structured migration checklist and troubleshooting guidance to `04_mcp_06_configuration_and_operations.md` for local-to-production auth migration.

## Scope

- `docs/04_mcp_06_configuration_and_operations.md`

## Assumptions

1. The pre-production checklist at line 836 already exists.
2. No runtime behavior changes are required.

## Implementation

### Target file

`docs/04_mcp_06_configuration_and_operations.md`

### Procedure

1. Add a "Local to production auth migration" section after the existing pre-production checklist.
2. Include these steps:
   - Switch `security_profile` from `local` to `production`
   - Set non-empty `auth_token` for all HTTP MCP servers
   - Avoid hardcoding secrets (use env/secret injection)
   - Restart the agent (not just `/reload`)
   - Verify with `/mcp status`
   - Inspect startup failures for missing/mismatched auth tokens
3. Add troubleshooting cases:
   - Empty `auth_token`
   - Missing env secret
   - Mismatched Bearer token
   - `/reload` vs full restart

### Details

- Use consistent formatting with existing pre-production checklist.
- No modifications to other docs.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Migration section present | `rg "migration" docs/04_mcp_06_configuration_and_operations.md` | 1 match |
| Troubleshooting present | `rg "troubleshooting" docs/04_mcp_06_configuration_and_operations.md` | 1 match |
