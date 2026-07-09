# Implementation: docs — production fail-fast documentation updates

## Goal

Update 4 doc files for the `ProductionConfigValidator` changes.

## Scope

- `docs/04_mcp_05_security_and_safety_model.md`: fix `tool_definitions_strict` default (`true`→`false`), add 3 table rows
- `docs/04_mcp_06_configuration_and_operations.md`: add 2 checklist items
- `docs/05_agent_08_configuration.md`: add production-recommended-value note
- `docs/05_agent_11_extension-points.md`: add production-prohibition sentence

## Implementation

### Target files

1. `docs/04_mcp_05_security_and_safety_model.md`
2. `docs/04_mcp_06_configuration_and_operations.md`
3. `docs/05_agent_08_configuration.md`
4. `docs/05_agent_11_extension-points.md`

### Details

See plan design section for exact edits.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Manual review | `git diff docs/` | all doc edits correct |
