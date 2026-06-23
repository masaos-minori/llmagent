# Implementation: Update drift validation table in routing lifecycle doc

## Goal

Update the drift validation table in `docs/04_mcp_03_routing_lifecycle_and_execution.md` to reflect that only `validate_routing_against_config()` is actually wired to startup (via `check_routing_drift()`), while the other two functions are not yet wired.

## Scope

- **In-Scope:** Update the "Drift validation" table (lines 84-88) — change "When called" column values
- **Out-of-Scope:** Other sections of this document

## Assumptions

1. The table is at lines 84-88 (confirmed by Read).
2. Only the "When called" column values change — the function names and descriptions stay the same.
3. The drift warnings example code block after the table (lines 90-94) stays unchanged.

## Verified current state

Lines 84-88 of `docs/04_mcp_03_routing_lifecycle_and_execution.md` (confirmed by Read):

```
| Function | Compares | When called |
|---|---|---|
| `validate_routing_against_config()` | Config `tool_names` vs registry | Startup |
| `validate_routing_against_live()` | Live `/v1/tools` vs registry | Startup |
| `validate_all_routing()` | Both above combined | Startup |
```

## Implementation

**Target file:** `docs/04_mcp_03_routing_lifecycle_and_execution.md`

**Procedure:**
1. Locate the drift validation table (starts with `| Function | Compares | When called |`).
2. Replace the three table data rows with updated "When called" values.

**Method:** Single Edit operation.

**Details:**

Current:
```
| `validate_routing_against_config()` | Config `tool_names` vs registry | Startup |
| `validate_routing_against_live()` | Live `/v1/tools` vs registry | Startup |
| `validate_all_routing()` | Both above combined | Startup |
```

Replacement:
```
| `validate_routing_against_config()` | Config `tool_names` vs registry | Startup (`check_routing_drift()` in `repl_health.py`) |
| `validate_routing_against_live()` | Live `/v1/tools` vs registry | Not yet wired (future) |
| `validate_all_routing()` | Both above combined | Not yet wired (future) |
```

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| "Not yet wired" present | `grep "Not yet wired" docs/04_mcp_03_routing_lifecycle_and_execution.md` | 2 matches |
| Old "Startup" rows gone | `grep "validate_routing_against_live.*Startup" docs/04_mcp_03_routing_lifecycle_and_execution.md` | 0 matches |
