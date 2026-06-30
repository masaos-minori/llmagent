# Implementation: MCP tool and server addition procedure — Documentation consistency fix

## Goal

Establish a single, internally consistent procedure for adding MCP tools and servers by correcting documentation that contradicts the actual `ToolRegistry`/`tool_constants` model and clearly labeling required vs. optional steps.

## Scope

- **In-Scope**:
  - Rewrite "Adding a new tool" section in `docs/04_mcp_03_routing_lifecycle_and_execution.md`
  - Rewrite "New Tool Registration Procedure" and "New MCP Server Addition Checklist" in `docs/04_mcp_06_configuration_and_operations.md`
  - Correct any text that states frozensets are added to `shared/tool_registry.py` (they belong in `shared/tool_constants.py`)
  - Explicitly document GitHub prefix routing (`github_*`) as an exception in the static fallback layer
  - Label each step as [Required] or [Optional] in all checklists
  - Add `tool_safety_tiers` to the new-tool procedure (currently missing)
  - Add validation commands (`uv run pytest` targets) for each procedure
  - No source code changes — documentation and developer workflow cleanup only

- **Out-of-Scope**:
  - Changing the routing model itself
  - Removing GitHub prefix routing
  - Changing `shared/tool_constants.py`, `shared/tool_registry.py`, or `shared/route_resolver.py` logic
  - Adding or removing frozensets from production code

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | `tests/test_route_resolver.py` referenced in `04_mcp_06` line 655 does not appear to exist | Resolved: The file DOES exist at `tests/test_route_resolver.py`. No change needed for this reference. |
| UNK-02 | `config/tools_definitions.toml` vs `config/agent.toml tool_definitions` distinction | Resolved: `config/tools_definitions.toml` exists and is the LLM schema file. `config/agent.toml` has a `tool_safety_tiers` section (not `tool_definitions`). |
| UNK-03 | Whether `github_` prefix tools require a frozenset entry or rely solely on prefix matching in `_fallback_route()` | Resolved: GitHub prefix routing is a layer 4 static fallback in `route_resolver.py`. Tools with `github_*` names route to the `github` server key via prefix matching — no entry in `tool_constants.py` needed unless they should also appear in `get_all_mcp_tool_names()`. |

## Code Verification: Current State

### 1. Frozenset registration is automatic via `_populate_default_registry()`

**File**: `scripts/shared/tool_registry.py` — `_populate_default_registry()` reads frozensets from `tool_constants.py` at import time. No manual registry edit needed.

### 2. GitHub prefix routing is intentional static fallback

**File**: `scripts/shared/route_resolver.py:102` — Layer 4 (Static fallback) includes `github_*` prefix matching. This is documented as a named exception.

### 3. `tool_safety_tiers` is in `config/agent.toml`, not `config/tools_definitions.toml`

**File**: `config/agent.toml:254-258` — `[tool_safety_tiers]` section exists under the `config/agent.toml` file.

### 4. `test_route_resolver.py` exists

**File**: `tests/test_route_resolver.py` — confirmed via glob search. UNK-01 resolved — no change needed.

## Implementation Steps

### Target file: `docs/04_mcp_03_routing_lifecycle_and_execution.md`

#### Procedure
Rewrite "Adding a new tool" section and routing source of truth table.

#### Method
Direct file edit — replace existing text with corrected procedure.

#### Details

**Under "Routing Source of Truth" table**: Add note:
> Priority 2 (registry) is populated automatically from `shared/tool_constants.py` frozensets at import time via `_populate_default_registry()`. No manual registry edit is needed when adding a new tool.

**Under "Tool Registry" section — "Adding a new tool" sub-procedure**: Replace with canonical 7-step procedure:

| Step | Action | Required? |
|---|---|---|
| 1 | Add tool name to the appropriate frozenset in `shared/tool_constants.py` | **Required** |
| 2 | Registry auto-populates at import time — no manual registry edit needed | (automatic) |
| 3 | Implement `dispatch()` handler in the owning MCP server (`mcp/<name>/server.py`) | **Required** |
| 4 | Expose tool in `/v1/tools` endpoint (return tool definition with `server_key` field) | Recommended — enables priority-1 discovery routing |
| 5 | Add LLM schema to `config/tools_definitions.toml` (OpenAI function-calling format) | Required if tool should be visible to LLM |
| 6 | Add `tool_safety_tiers` entry in `config/agent.toml` for the new tool | **Required** — all tools must have a declared safety tier |
| 7 | Add tool name to `tool_names` in `config/mcp_servers.toml` for the owning server | Optional — enables startup drift validation only; routing does not require it |

**Under "Static fallback" table**: Add explicit row:
> `github_*` prefix match → `github` server key (named exception: GitHub prefix routing in `_fallback_route()`. No entry in `tool_constants.py` needed for these tools unless they should also appear in `get_all_mcp_tool_names()`.)

**Under "New Server/Tool Registration Checklist"**: Rewrite to match canonical order; add `tool_safety_tiers` row; label Required/Optional consistently; fix any reference to "adding frozensets to tool_registry.py".

### Target file: `docs/04_mcp_06_configuration_and_operations.md`

#### Procedure
Rewrite "New Tool Registration Procedure" and "New MCP Server Addition Checklist".

#### Method
Direct file edit — replace existing procedures with corrected versions.

#### Details

**Under "New Tool Registration Procedure"**: Replace current 3-step procedure with the 7-step canonical procedure (same as above). Add [Required]/[Optional] labels. Keep existing `test_route_resolver.py` reference (it exists and is valid).

**Under "New MCP Server Addition Checklist"**: Fix checklist item "If tools not in `shared/tool_constants.py` frozensets: set `tool_names` in server config" — this is logically inverted; required step is to add to `tool_constants.py`; config `tool_names` is optional drift hint.

**Add GitHub prefix exception note** to the new-server checklist as an explicit optional alternative for GitHub-namespaced tools.

#### Validation commands to add to both docs:
```bash
# Verify routing coverage
uv run pytest tests/test_tool_constants.py tests/test_tool_executor_routing.py -v
# Verify no overlapping tool names
uv run pytest tests/test_tool_constants.py::TestToolConstants::test_no_overlapping_tools -v
```

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/test_tool_constants.py` | Run existing tests to confirm no regressions from doc-only changes | `uv run pytest tests/test_tool_constants.py -v` | All tests pass |
| `tests/test_tool_executor_routing.py` | Run existing routing tests | `uv run pytest tests/test_tool_executor_routing.py -v` | All tests pass |
| `docs/04_mcp_03_routing_lifecycle_and_execution.md` | Manual review: search for "tool_registry.py" in context of frozenset addition | `grep -n "frozenset" docs/04_mcp_03_routing_lifecycle_and_execution.md` | No remaining text claims frozensets are added to `tool_registry.py` |
| `docs/04_mcp_06_configuration_and_operations.md` | Manual review: search for "test_route_resolver" | `grep -n "test_route_resolver" docs/04_mcp_06_configuration_and_operations.md` | Reference confirmed correct (file exists) |
| Both docs | Manual review: confirm GitHub prefix exception is explicitly documented | `grep -n "github_\*\|github prefix" docs/04_mcp_03_routing_lifecycle_and_execution.md docs/04_mcp_06_configuration_and_operations.md` | Both docs contain explicit GitHub prefix exception note |
| Both docs | Manual review: confirm Required/Optional labels are present | `grep -n "\[Required\]\|\[Optional\]" docs/04_mcp_03*.md docs/04_mcp_06*.md` | Labels present in both files |

## Risks & Mitigations

- **Risk**: Updated procedure introduces subtle inaccuracy about when `tool_names` config is consulted (priority 3 vs. drift-only) → **Mitigation**: Cross-check every routing statement against `route_resolver.py` source before finalizing.
- **Risk**: Removing "add frozenset to tool_registry.py" wording may confuse implementers if the registry-population relationship is not explained clearly → **Mitigation**: Include a one-sentence explanation in each procedure: "The registry is populated automatically from `tool_constants.py` frozensets at import time via `_populate_default_registry()`."
- **Risk**: GitHub prefix exception documentation might encourage misuse for non-github tools → **Mitigation**: Add explicit warning: "This exception applies only to the `github` server key; do not use prefix matching for any other server."

## Files Changed

- `docs/04_mcp_03_routing_lifecycle_and_execution.md` — rewrite "Adding a new tool" section, routing source of truth table, static fallback table
- `docs/04_mcp_06_configuration_and_operations.md` — rewrite "New Tool Registration Procedure" and "New MCP Server Addition Checklist"
