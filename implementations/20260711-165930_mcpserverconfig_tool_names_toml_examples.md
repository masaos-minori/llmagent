# Docs: tool_names TOML Examples in MCPServerConfig Field Reference

## Goal

Add concrete TOML examples for the three distinct `tool_names` states (omitted,
explicit empty list, populated) directly in the field reference doc, and state plainly
that routing is identical in all three cases — `tool_names` is validation-only metadata,
never a routing input.

## Scope

**In scope:**
- `docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md`: add 3 TOML example
  blocks plus one clarifying sentence, near the existing `tool_names` field description
  (currently around line 29).

**Out of scope:**
- No code changes.
- No change to `validate_routing_against_config()`'s `if not cfg.tool_names: continue`
  skip logic (already correct; documented, not modified).
- The cross-reference target for these examples from `docs/04_mcp_03_01_dispatch-and-routing.md`
  is a separate doc phase (see sibling doc
  `dispatch_and_routing_tool_names_and_duplicate_detection_notes`).

## Assumptions

- The field reference doc already states the core facts (`tool_names` not a routing
  input, validation-only, empty = no validation) correctly at/around line 29, but lacks
  concrete multi-case TOML examples — confirmed by direct read in the plan.
- `McpServerConfig`'s `tool_names` field defaults to `[]` when omitted from TOML, making
  "omitted" and "explicit `tool_names = []`" behaviorally and semantically identical for
  `validate_routing_against_config()`'s truthiness check.

## Implementation

### Target file

`docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md`

### Procedure

1. Locate the existing `tool_names` field description (around line 29).
2. Immediately above or below the existing prose, insert one clarifying sentence stating
   that routing is identical in all three cases (omitted / empty / populated) — only
   whether config-vs-registry drift validation runs for this server differs.
3. Insert three TOML example blocks, each under a `[mcp_servers.<key>]` section using
   distinct example server keys (e.g. `example_a`, `example_b`, `example_c`) so the three
   cases do not collide with any real server key already documented elsewhere in the file:
   - Case 1 — key omitted entirely (no `tool_names` line).
   - Case 2 — key explicitly set to `tool_names = []`.
   - Case 3 — key populated with a small representative list of tool names (e.g.
     `["read_text_file", "list_directory"]`).
4. Add a one-line comment above each example block stating what that example demonstrates
   and, for cases 1 and 2, noting they are equivalent in effect.

### Method

Direct Markdown edit: insert a short prose sentence followed by three fenced ```toml
code blocks, placed adjacent to the existing `tool_names` field row/description so a
reader scanning that field sees the examples immediately.

### Details

- Sentence to add (verbatim, per the plan's Design section): "Routing is identical in
  all three cases — `tool_names` never determines which server a tool routes to; only
  whether config-vs-registry drift validation runs for this server."
- Example content (per the plan's Design section):
  ```toml
  # Omitted — identical to tool_names = [] (both skip config-vs-registry validation for this server)
  [mcp_servers.example_a]
  cmd = ["..."]

  # Explicit empty — same effect as omitting the key entirely
  [mcp_servers.example_b]
  cmd = ["..."]
  tool_names = []

  # Populated — validated against the registry at startup; mismatches are drift, not routing changes
  [mcp_servers.example_c]
  cmd = ["..."]
  tool_names = ["read_text_file", "list_directory"]
  ```
- Keep existing field-reference prose/table structure in the file otherwise unchanged.
- English only, per `rules/coding.md` conventions applied to docs as well.

## Validation plan

Filtered to checks relevant to this doc:

| Check | Tool | Target |
|---|---|---|
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
| Docs (MCP-specific) | `uv run check-mcp-docs` | Passes (no new inconsistency introduced) |
| Manual | Visual review of rendered Markdown | 3 example blocks render correctly, distinguishable, and consistent with the field's existing description |
