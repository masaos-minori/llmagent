# Implementation: docs/04_mcp_06_configuration_and_operations.md — watchdog behavior section

## Goal

Add a dedicated "Watchdog Behavior" section documenting local vs production defaults, what
happens when watchdog is disabled, and where to check the current state.

## Scope

- `docs/04_mcp_06_configuration_and_operations.md` only (doc-only change).

## Assumptions

1. The doc already references `mcp_watchdog_interval` and `mcp_watchdog_max_restarts` in tables.
2. A new section should expand on the behavior and cross-reference the `/mcp status` output.

## Implementation

### Target file

`docs/04_mcp_06_configuration_and_operations.md`

### Procedure

Read existing content, then add a "Watchdog Behavior" section after the existing watchdog
config entries, covering:
- LOCAL vs PRODUCTION default
- Disabled state consequences
- Where to verify state at runtime (/mcp status, startup logs)

## Validation plan

| Check | Action | Target |
|---|---|---|
| File readable | Read file | No error |
| Section present | Grep for "Watchdog Behavior" | Found |
