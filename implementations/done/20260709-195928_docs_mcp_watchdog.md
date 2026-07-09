# Implementation: docs — watchdog recommendations expansion

## Goal

Expand `mcp_watchdog_interval` guidance with operational impact analysis and ensure `/mcp status` watchdog display is documented correctly.

## Scope

- `docs/04_mcp_06_configuration_and_operations.md`
- `docs/05_agent_10_operations-and-observability.md`

## Assumptions

1. Phase 1 verification of `mcp_status.py` is complete.
2. Watchdog interval is configurable via `mcp_watchdog_interval` in `agent.toml`.

## Implementation

### Target files

1. `docs/04_mcp_06_configuration_and_operations.md`
2. `docs/05_agent_10_operations-and-observability.md`

### Procedure

1. In `04_mcp_06_configuration_and_operations.md`: expand the `mcp_watchdog_interval` field description with:
   - Recommended values for production vs local
   - Operational impact of setting too high/low
   - How to verify with `/mcp status`
2. In `05_agent_10_operations-and-observability.md`: ensure `/mcp status` watchdog display is documented accurately based on `mcp_status.py` verification.

### Details

- Keep content concise; cross-reference between the two docs.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Watchdog docs expanded | `rg "watchdog" docs/04_mcp_06_configuration_and_operations.md` | 3+ matches |
| /mcp status display accurate | Manual review | Matches mcp_status.py behavior |
