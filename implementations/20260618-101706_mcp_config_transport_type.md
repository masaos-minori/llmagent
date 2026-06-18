# Implementation: McpServerConfig.transport type docs update (req 67)

## Goal

No code changes needed — shared/mcp_config.py already uses TransportType StrEnum.
Update two docs to match.

## Changes

### `docs/04_mcp_06_configuration_and_operations.md`
- Line 54: transport type `str` → `TransportType`; update description to mention enum variants

### `docs/06_shared_90_inconsistencies_and_known_issues.md`
- TYPE-01 entry: change status from "Needs confirmation" to RESOLVED
- Add resolution note: code already uses TransportType StrEnum, __post_init__ converts strings
