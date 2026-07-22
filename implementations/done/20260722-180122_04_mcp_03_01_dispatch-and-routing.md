## Goal

Clarify that DAG scheduling uses metadata from configured LLM tool definitions (config/agent.toml), not from RuntimeToolRegistry.

## Scope

- Update `docs/04_mcp_03_01_dispatch-and-routing.md` — clarify DAG scheduling data source

## Assumptions

1. DAG scheduling uses metadata from `config/agent.toml` tool definitions, not from RuntimeToolRegistry (confirmed by existing plans referencing `tool_definitions` as the source)
2. The distinction between runtime routing metadata and DAG scheduling metadata is accurate

## Design decisions

- Add a dedicated "Data source for DAG scheduling" subsection under the DAGスケジューリング section
- Clearly separate the two data sources: RuntimeToolRegistry (routing + LLM visibility) vs config/agent.toml (DAG scheduling)
- List the specific metadata fields used by the scheduler

## Alternatives considered

- Adding inline notes within existing sections instead of creating a new subsection
- Creating a separate appendix for data source mapping

## Implementation

### Target file

- `docs/04_mcp_03_01_dispatch-and-routing.md`

### Procedure

#### Step 1: Locate insertion point

1. Open `docs/04_mcp_03_01_dispatch-and-routing.md`
2. Find the DAGスケジューリング section
3. Identify where the data source clarification should be inserted

#### Step 2: Add data source clarification subsection

Insert the following markdown after the DAGスケジューリング section:

```markdown
## Data source for DAG scheduling

The DAG scheduler does NOT read from `RuntimeToolRegistry`. Instead, it reads metadata from the configured LLM tool definitions in `config/agent.toml`.

### Fields used by the DAG scheduler

The following metadata fields are read from `config/agent.toml` tool definitions:

- `requires_serial`: Controls whether the tool requires serialized execution
- `resource_scope`: Determines which resources the tool can access during DAG execution
- `is_write`: Indicates whether the tool performs write operations
- Side-effect status: Determines if the tool is considered a side effect
- Shell-specific serial behavior: Controls how the tool behaves in shell contexts

### Key distinction

- **RuntimeToolRegistry**: Controls routing + LLM visibility (what tools appear in `/v1/tools`)
- **config/agent.toml**: Controls DAG scheduling metadata (how tools execute in the DAG)

These two data sources are independent. Updating `/v1/tools` metadata alone does not change DAG scheduling behavior. Both `/v1/tools` and `config/agent.toml` must be updated independently when changing tool metadata.
```

#### Step 3: Cross-reference the metadata document

If there's a cross-reference to the tool-runtime-availability-metadata.md document, ensure it points to the updated content.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The new section complements existing DAG scheduling documentation without conflicting

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the added section if the data source descriptions are incorrect

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `shared/tool_executor_helpers.py` | Read-only verification | grep for is_side_effect() | Data source confirmed |
| `docs/04_mcp_03_01_dispatch-and-routing.md` | Documentation consistency check | Manual review | Section added correctly |

## Out of scope

- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-124113_require.md
- Source plan: plans/20260722-144242_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-180122
- Related target files: docs/04_mcp_03_01_dispatch-and-routing.md
