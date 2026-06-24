# Implementation: Unified MCP Failure Diagnosis Section

## Goal

Add a unified "MCP Failure Diagnosis" decision flow section to `04_mcp_06` that cross-links all existing failure-related sections. Add a brief reference in `04_mcp_03`.

## Scope

**In:**
- `docs/04_mcp_06_configuration_and_operations.md` — add "MCP Failure Diagnosis" decision flow
- `docs/04_mcp_03_routing_lifecycle_and_execution.md` — add brief reference to ops diagnosis flow

**Out:** No code changes.

## Assumptions

1. Individual detail sections already exist in `04_mcp_06` (transport errors, tool errors, health states, watchdog).
2. The new section is a navigation/decision layer — references existing sections rather than duplicating.
3. End-to-end tracing example from plan req 19 (`04_mcp_02` correlation keys) complements this section.

## Implementation

### Target file

`docs/04_mcp_06_configuration_and_operations.md`, `docs/04_mcp_03_routing_lifecycle_and_execution.md`

### Procedure

1. Read `docs/04_mcp_06_configuration_and_operations.md` TOC/headings to identify existing section names and anchors.
2. Add "MCP Failure Diagnosis" section referencing existing sections.
3. Read `docs/04_mcp_03_routing_lifecycle_and_execution.md` and add reference.

### Method

`grep -n "^##" docs/04_mcp_06_configuration_and_operations.md` to find TOC → Edit patches.

### Details

**Decision flow for `04_mcp_06` (new section "MCP Failure Diagnosis"):**

```markdown
## MCP Failure Diagnosis

Use this flow to trace a failed or unexpected MCP tool call:

```
1. Was the request delivered to the server?
   NO → Transport failure. See §Transport Errors.
   YES → continue

2. Did the tool return an error response?
   YES → Tool-level error. See §Tool-Level Error Handling.
   NO (timeout or silent fail) → continue

3. Has server health status changed?
   YES → See §Health States. Check health transition timestamp.
   NO → continue

4. Has the watchdog taken action (restart / circuit-break)?
   YES → See §Watchdog Configuration.
   NO → Check serialization. See §Serialization Behavior.
```

For correlation across layers, see §End-to-End Tool Call Tracing.

**Restart-worthy:** health transition to `failed` + repeated tool errors within threshold
**Not restart-worthy:** single tool error, one-time timeout, serialization delay
```

**Reference in `04_mcp_03`:**
```
MCP 障害の診断手順については `04_mcp_06` §MCP Failure Diagnosis を参照。
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Diagnosis section added | `grep -n "Failure Diagnosis\|MCP.*Diagnosis" docs/04_mcp_06_configuration_and_operations.md` | found |
| Reference in 04_mcp_03 | `grep -n "Failure Diagnosis" docs/04_mcp_03_routing_lifecycle_and_execution.md` | found |
| No code changes | `git diff scripts/` | empty |
