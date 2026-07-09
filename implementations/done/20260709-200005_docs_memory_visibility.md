# Implementation: docs — memory visibility documentation

## Goal

Update memory status documentation to reflect the new mode labels and improved visibility.

## Scope

- `docs/05_agent_10_operations-and-observability.md`
- `docs/05_agent_12_memory.md`

## Assumptions

1. Phase 1 and Phase 2 changes are complete.
2. The new mode labels are:
   - "Memory layer disabled"
   - "Memory enabled, embedding disabled (FTS-only)"
   - "Degraded mode (circuit open, FTS fallback)"
   - "Hybrid mode (semantic + FTS)"

## Implementation

### Target files

1. `docs/05_agent_10_operations-and-observability.md`
2. `docs/05_agent_12_memory.md`

### Procedure

1. In `05_agent_10_operations-and-observability.md`: update `/memory status` output documentation to include the mode labels.
2. In `05_agent_12_memory.md`: add section explaining each memory mode and what it means for retrieval behavior.

### Details

- Cross-reference between the two docs.
- Include a table of modes and their implications.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Memory modes documented | `rg "FTS-only\|Degraded mode" docs/` | 2+ matches |
