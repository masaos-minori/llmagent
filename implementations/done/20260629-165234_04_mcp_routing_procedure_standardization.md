# Implementation: MCP tool/server addition procedure standardization

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
- **Out-of-Scope**:
  - Changing the routing model itself
  - Removing GitHub prefix routing
  - Changing `shared/tool_constants.py`, `shared/tool_registry.py`, or `shared/route_resolver.py` logic
  - Adding or removing frozensets from production code

## Assumptions

- The four-layer routing priority (discovery map > registry > config > static fallback) is correct and stable.
- `_populate_default_registry()` in `tool_registry.py` is the authoritative place that maps frozensets to server keys — no change needed.
- `_fallback_route()` in `route_resolver.py` contains `github_` prefix matching; this is intentional and remains supported.
- `config/tools_definitions.toml` is the LLM schema file (not `config/agent.toml tool_definitions`); both are relevant but serve different purposes.
- `tool_safety_tiers` is configured in `config/agent.toml` and applies per tool name.

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | Plan claimed `tests/test_route_resolver.py` does not exist, but it actually exists (278 lines). | Update doc references — the test file is valid and should be kept in the validation commands. |
| UNK-02 | `config/tools_definitions.toml` vs `config/agent.toml tool_definitions` distinction | Confirmed: `config/tools_definitions.toml` is the OpenAI function-calling schema file; `agent.toml tool_definitions` is the runtime reference. Both are relevant. |
| UNK-03 | Whether `github_` prefix tools require a frozenset entry or rely solely on prefix matching | Confirmed: GitHub prefix tools route via `_fallback_route()` static fallback (layer 4); no frozenset entry needed unless they should also appear in `get_all_mcp_tool_names()`. |

## Implementation

### Target file: `docs/04_mcp_03_routing_lifecycle_and_execution.md`

#### Change 1: Fix Japanese routing source of truth table (line ~101)

**Issue**: Line 101 says "起動時に自動構築" (auto-constructed at startup) for `shared/tool_registry.py`, which is misleading — the registry is populated from `tool_constants.py` frozensets at import time.

**Method**: Direct file edit — clarify the ownership relationship.

**Details**: Replace line 101:
```markdown
| `shared/tool_registry.py` | **Priority 2** | ツール→サーバー逆引き; `tool_constants.py` frozensetからimport時に自動構築 |
```

#### Change 2: Add Required/Optional labels to "Adding a new tool" section

**Method**: Direct file edit — add [Required]/[Optional] labels and add `tool_safety_tiers` step.

**Details**: Replace lines 136-142:
```markdown
### Adding a new tool

| Step | Action | Required? |
|---|---|---|
| 1 | Add the tool name to the appropriate frozenset in `shared/tool_constants.py` | **[Required]** |
| 2 | Registry auto-populates from these frozensets at import time — no manual registry edit needed | (automatic) |
| 3 | Implement `dispatch()` handler in the owning MCP server (`mcp/<name>/server.py`) | **[Required]** |
| 4 | Expose tool in `/v1/tools` endpoint (return tool definition with `server_key` field) | **[Recommended]** — enables priority-1 discovery routing |
| 5 | Add LLM schema to `config/tools_definitions.toml` (OpenAI function-calling format) | **[Required]** — if tool should be visible to LLM |
| 6 | Add `tool_safety_tiers` entry in `config/agent.toml` for the new tool | **[Required]** — all tools must have a declared safety tier |
| 7 | Add tool name to `tool_names` in `config/mcp_servers.toml` for the owning server | **[Optional]** — enables startup drift validation only; routing does not require it |

**GitHub prefix exception**: Tools whose names start with `github_` route to the `github` server key via prefix matching in `_fallback_route()`. No entry in `tool_constants.py` is needed for these tools unless they should also appear in `get_all_mcp_tool_names()`.
```

#### Change 3: Add validation commands after "Adding a new tool" section

**Method**: Direct file edit — add a "Verification" subsection.

**Details**: Add after line 142:
```markdown
### Verification

After completing registration:

```bash
uv run pytest tests/test_tool_constants.py tests/test_route_resolver.py -v
```

Expected: all routing tests pass. If `tool_definitions_strict = true`, restart the agent and confirm startup logs show `"Routing: N/N tools mapped"` with no unmapped warnings.
```

### Target file: `docs/04_mcp_06_configuration_and_operations.md`

#### Change 1: Replace "New Tool Registration Procedure" with canonical 7-step procedure

**Method**: Direct file edit — replace lines 642-671.

**Details**: Replace the entire section (lines 642-671) with:
```markdown
## New Tool Registration Procedure

When adding a new tool to an **existing** MCP server:

| Step | Action | Required? |
|---|---|---|
| 1 | Add the tool name to the appropriate frozenset in `shared/tool_constants.py` (e.g., `READ_TOOLS`, `WRITE_TOOLS`, or create a new `<SERVER>_TOOLS` frozenset and add it to `get_all_mcp_tool_names()`) | **[Required]** |
| 2 | Registry auto-populates from these frozensets at import time — no manual registry edit needed | (automatic) |
| 3 | Implement `dispatch()` handler in the owning MCP server (`mcp/<name>/server.py`) | **[Required]** |
| 4 | Expose tool in `/v1/tools` endpoint (return tool definition with `server_key` field) | **[Recommended]** — enables priority-1 discovery routing |
| 5 | Add LLM schema to `config/tools_definitions.toml` (OpenAI function-calling format) | **[Required]** — if tool should be visible to LLM |
| 6 | Add `tool_safety_tiers` entry in `config/agent.toml` for the new tool | **[Required]** — all tools must have a declared safety tier |
| 7 | Add tool name to `tool_names` in server config (`config/mcp_servers.toml`) | **[Optional]** — enables startup drift validation only; routing does not require it |

**GitHub prefix exception**: If the tool name follows the `github_` prefix convention and the server key is `github`, no entry in `tool_constants.py` is needed — prefix matching in `_fallback_route()` handles it automatically. This exception applies only to the `github` server key; do not use prefix matching for any other server.

### Verification

After completing registration:

```bash
uv run pytest tests/test_tool_constants.py tests/test_route_resolver.py -v
```

Expected: all routing tests pass. If `tool_definitions_strict = true`, restart the agent and confirm startup logs show `"Routing: N/N tools mapped"` with no unmapped warnings.

---
```

#### Change 2: Fix "New MCP Server Addition Checklist" line 682

**Issue**: Line 682 says "If tools not in `shared/tool_constants.py` frozensets: set `tool_names` in server config" — this is logically inverted. The correct statement is: tools in `tool_constants.py` frozensets are automatically routed; config `tool_names` is optional drift validation only.

**Method**: Direct file edit — replace line 682.

**Details**: Replace line 682:
```markdown
- [ ] Tools are registered in `shared/tool_constants.py` frozensets (auto-routed at startup); config `tool_names` is optional drift validation only
```

#### Change 3: Add GitHub prefix exception to new-server checklist

**Method**: Direct file edit — add a new checklist item.

**Details**: Add after line 682:
```markdown
- [ ] If tools follow `github_` prefix convention and the server key is `github`, no entry in `tool_constants.py` is needed (prefix matching in `_fallback_route()` handles routing)
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/test_tool_constants.py` | Run existing tests to confirm no regressions from doc-only changes | `uv run pytest tests/test_tool_constants.py -v` | All tests pass |
| `tests/test_route_resolver.py` | Run existing routing tests | `uv run pytest tests/test_route_resolver.py -v` | All tests pass |
| `docs/04_mcp_03_routing_lifecycle_and_execution.md` | Manual review: search for "tool_registry.py" in context of frozenset addition | `grep -n "frozenset" docs/04_mcp_03_routing_lifecycle_and_execution.md` | No remaining text claims frozensets are added to `tool_registry.py` directly |
| `docs/04_mcp_06_configuration_and_operations.md` | Manual review: confirm Required/Optional labels are present | `grep -n "\[Required\]\|\[Optional\]" docs/04_mcp_03*.md docs/04_mcp_06*.md` | Labels present in both files |
| Both docs | Manual review: confirm GitHub prefix exception is explicitly documented | `grep -n "github_\*\|github prefix" docs/04_mcp_03_routing_lifecycle_and_execution.md docs/04_mcp_06_configuration_and_operations.md` | Both docs contain explicit GitHub prefix exception note |

## Risks & Mitigations

- **Risk**: Updated procedure introduces subtle inaccuracy about when `tool_names` config is consulted (priority 3 vs. drift-only) → **Mitigation**: Cross-check every routing statement against `route_resolver.py` source before finalizing.
- **Risk**: Removing "add frozenset to tool_registry.py" wording may confuse implementers if the registry-population relationship is not explained clearly → **Mitigation**: Include a one-sentence explanation in each procedure: "The registry is populated automatically from `tool_constants.py` frozensets at import time via `_populate_default_registry()`."
- **Risk**: GitHub prefix exception documentation might encourage misuse for non-github tools → **Mitigation**: Add explicit warning: "This exception applies only to the `github` server key; do not use prefix matching for any other server."
