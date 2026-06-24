# Implementation: New MCP Server/Tool Registration Checklist

## Goal

Add a validation checklist (required vs optional artifacts) for new MCP server/tool registration to `04_mcp_03`. Add a final verification step in `04_mcp_06`.

## Scope

**In:**
- `docs/04_mcp_03_routing_lifecycle_and_execution.md` — add registration checklist table
- `docs/04_mcp_06_configuration_and_operations.md` — add final verification step

**Out:** No code changes.

## Assumptions

1. Required artifacts: `shared/tool_registry.py`, server config file, `deploy/deploy.sh`, `routing.md`.
2. Optional artifacts: `tool_names` in config, `tools_definitions.toml`, startup pytest.
3. The routing.md update is Required (document guide must reference new server).

## Implementation

### Target file

`docs/04_mcp_03_routing_lifecycle_and_execution.md`, `docs/04_mcp_06_configuration_and_operations.md`

### Procedure

1. Read the "New Tool Registration" or "Adding a Server" section in `docs/04_mcp_03_routing_lifecycle_and_execution.md`.
2. Add checklist table after the section heading.
3. Read `docs/04_mcp_06_configuration_and_operations.md` "new tool" procedure section.
4. Add final verification step.

### Method

Read then Edit tool patches.

### Details

**Checklist table for `04_mcp_03`:**

```markdown
## New Server/Tool Registration Checklist

| Artifact | Required? | Notes |
|---|---|---|
| `shared/tool_registry.py` — add tool to frozenset | **Required** | Registry source of truth |
| `config/<server>.toml` — server config file | **Required** | Server must be defined |
| `deploy/deploy.sh` — add install/copy step | **Required** (new server) | Deployment must include server |
| Update this doc (`routing.md`) | **Required** | Document guide must reference new server |
| `config/agent.toml` `tool_names` | Optional | Validation hint only (see plan 17 / routing SoT) |
| `config/tools_definitions.toml` | Optional | Strict-mode validation only |
```

**Final verification step for `04_mcp_06`:**

```markdown
### Verification

After completing registration:
```bash
uv run pytest tests/test_mcp_routing.py -v
```
Expected: all routing tests pass. If `tool_definitions_strict = true`, also run:
```bash
uv run python -m scripts.agent --dry-run 2>&1 | grep "tool.*registered"
```
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Checklist table present | `grep -n "Required.*Optional\|registration.*checklist\|Registration Checklist" docs/04_mcp_03_routing_lifecycle_and_execution.md` | found |
| Verification step present | `grep -n "test_mcp_routing\|Verification" docs/04_mcp_06_configuration_and_operations.md` | found |
| No code changes | `git diff scripts/` | empty |
