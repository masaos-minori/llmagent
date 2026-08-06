## Goal

Propagate the fact that `config/agent.toml`'s `tool_names` field is not used for routing or circuit-breaker state, but only for drift validation/observation, to ensure consistency across documentation files.

## Scope

- **In-Scope**:
  - Update `docs/04_mcp_01_system_overview.md` with a clarifying note regarding `tool_names`.
  - Update `docs/04_mcp_06_09_mcp-failure-diagnosis.md` with a clarifying note regarding `tool_names`.
- **Out-of-Scope**:
  - Modifying source code.
  - Modifying `docs/04_mcp_03_01_dispatch-and-routing.md`.
  - Modifying other documentation files.

## Assumptions

1. The current wording in `docs/04_mcp_03_01_dispatch-and-routing.md` is correct and serves as the authoritative phrasing.
2. Adding these notes will resolve potential reader confusion without requiring restructuring of existing sections.

## Design decisions

- Add inline notes rather than rewriting existing sections — minimizes change surface and avoids cascading rewrites.
- Use consistent wording sourced from the dispatch-and-routing doc to prevent divergence.

## Alternatives considered

- Rewrite all mentions of `tool_names` across MCP docs: rejected because it risks inconsistency and is unnecessary for a single clarification.
- Create a separate FAQ section: over-engineered; an inline note suffices.

## Compatibility considerations

- Readers who previously assumed `tool_names` affects routing or circuit-breaker behavior will see the correction.
- No API contract changes — this is purely a documentation clarification.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If the added notes cause rendering issues (e.g., due to Markdown formatting), revert to the previous version.
- If the authoritative wording in dispatch-and-routing.md changes before this edit, update accordingly.

## Implementation

### Target file

`docs/04_mcp_01_system_overview.md`

### Procedure

1. Locate the Major Components table in the document.
2. After the table, insert a clarifying note about `tool_names`.

### Method

Direct file edit using sed or manual editing.

### Details

- Find the end of the Major Components table.
- Insert prose such as:
  > Note: `tool_names` in `config/agent.toml` is used only for drift validation/observation. It does not affect routing decisions or circuit-breaker state.

### Target file

`docs/04_mcp_06_09_mcp-failure-diagnosis.md`

### Procedure

1. Locate the `McpServerHealthRegistry` section.
2. At the end of the section, insert a clarifying note about `tool_names`.

### Method

Direct file edit.

### Details

- Find the end of the McpServerHealthRegistry section.
- Insert prose such as:
  > Note: `tool_names` in `config/agent.toml` is used only for drift validation/observation. It does not affect circuit-breaker state or health checks.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_01_system_overview.md` | Manual Inspection | `grep` or `Read` | Contains clarification about `tool_names` and its relation to `RuntimeToolRegistry`. |
| `docs/04_mcp_06_09_mcp-failure-diagnosis.md` | Manual Inspection | `grep` or `Read` | Contains clarification about `tool_names` and its relation to circuit breakers. |

## Out of scope

- Source code modifications (`scripts/`).
- Changes to `docs/04_mcp_03_01_dispatch-and-routing.md`.
- Modifications to other documentation not listed above.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-121000_plan_req_propagate_tool_names.md
- Source implementation procedure: N/A
- Generated at: 20260806-192629
- Related target files: docs/04_mcp_01_system_overview.md, docs/04_mcp_06_09_mcp-failure-diagnosis.md
