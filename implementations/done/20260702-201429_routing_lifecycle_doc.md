# Implementation Procedure: docs/04_mcp_03_routing_lifecycle_and_execution.md

## Goal

Update the drift-validation table and add a prose note distinguishing the two startup checks in the routing lifecycle document.

## Scope

**In**:
- Update `validate_routing_against_live()` row in drift-validation table: change "Not yet wired (future)" → "Startup (`check_routing_drift_live()` in `repl_health.py`)"
- Add/prose note below the table distinguishing the two startup checks

**Out**:
- No changes to any other files

## Assumptions

1. The drift-validation table exists in the document and has a row for `validate_routing_against_live()`.
2. A prose note about startup validation semantics should be added below the existing table.

## Implementation

### Target file

`docs/04_mcp_03_routing_lifecycle_and_execution.md`

### Procedure

1. Find the drift-validation table in the document and update the `validate_routing_against_live()` row:

Change:
```
| `validate_routing_against_live()` | Config → Live (agent.toml vs server) | Not yet wired (future) |
```

To:
```
| `validate_routing_against_live()` | Config → Live (agent.toml vs server) | Startup (`check_routing_drift_live()` in `repl_health.py`) |
```

2. Add a prose note below the table:

```markdown
**Startup validation semantics** — Two distinct startup checks run in `_check_services()`:

- `_check_tool_definitions` / `check_tool_definitions_startup`: compares configured `tool_definitions` (from `agent.toml`) against live `/v1/tools`. Detects LLM-visible tool schema drift. Controlled by `tool_definitions_strict`.

- `check_routing_drift_live`: compares live `/v1/tools` ownership (`server_key`) against `ToolRegistry`. Detects routing ownership drift. Always warning-only.
```

### Method

- Locate the drift-validation table using a search for "Drift validation" or "validate_routing_against_live".
- Update the row text in place — no structural changes to the table.
- Add the prose note as a blockquote or bold paragraph below the table, following the existing document style.

### Details

- The note should clarify that these are two separate checks with different purposes:
  - Tool definition drift (schema-level, configurable strict mode)
  - Routing ownership drift (ownership-level, always warning-only)
- Use the same formatting as other notes in the document (bold prefix + dash-separated items).

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Document review | Manual | Table row updated correctly, prose note added below table |
