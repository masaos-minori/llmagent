# Docs: tool_names Clarification + Duplicate-Detection Location Note in dispatch-and-routing.md

## Goal

In the dispatch-and-routing doc, cross-reference the new `tool_names` TOML examples
(added to the MCPServerConfig field reference) alongside the existing
omitted/empty/populated behavior description, and add a one-sentence note stating
*where* duplicate live ownership is actually detected and reported today, so a reader is
not left wondering whether this plan introduced new detection logic.

## Scope

**In scope:**
- `docs/04_mcp_03_01_dispatch-and-routing.md`: two additions near the existing
  routing-source-of-truth content (currently around lines 93-116):
  1. A cross-reference sentence pointing to the 3 TOML examples in
     `docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md`.
  2. A one-sentence note naming the exact duplicate-live-ownership detection location.

**Out of scope:**
- No code changes. Duplicate-ownership detection itself
  (`shared/route_resolver.py::build_discovery_map()`,
  `agent/repl_health.py::check_routing_drift_vs_live()`) is already implemented and
  already tested (`test_duplicate_live_ownership_detected`) — this phase only documents
  its existence and location, it does not add a second detection path.
- The TOML examples themselves live in the sibling doc
  `mcpserverconfig_tool_names_toml_examples` (target file
  `docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md`).

## Assumptions

- `docs/04_mcp_03_01_dispatch-and-routing.md` lines 93-116 already state the core facts
  correctly (`tool_names` not a routing input, validation-only, empty = no validation)
  but do not yet cross-reference concrete examples nor state the duplicate-detection
  location — confirmed by direct read in the plan.
- `shared/route_resolver.py::build_discovery_map()` (lines 23-52) already detects
  cross-server duplicate live ownership and returns `duplicates: dict[str, list[str]]`
  with all claiming server keys; `agent/repl_health.py::check_routing_drift_vs_live()`
  (lines 388-404) already consumes this and looks up the registry owner via
  `get_server_for_tool()`. Both confirmed by direct read in the plan; no code change
  needed here.

## Implementation

### Target file

`docs/04_mcp_03_01_dispatch-and-routing.md`

### Procedure

1. Locate the existing routing-source-of-truth / `tool_names` behavior content (around
   lines 93-116).
2. Add a cross-reference sentence directing the reader to the concrete
   omitted/empty/populated TOML examples now present in
   `docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md`.
3. In the same vicinity (or immediately adjacent, wherever routing-source-of-truth /
   duplicate-detection topics are already discussed), add one sentence naming exactly
   where duplicate live ownership is detected and surfaced.
4. Re-read the surrounding paragraphs before inserting, to ensure the new sentences slot
   in without duplicating or contradicting existing wording.

### Method

Direct Markdown edit: insert 1-2 sentences of prose into the existing section; no new
headings or structural changes required unless the existing section has no natural
insertion point, in which case add a short new paragraph immediately following the
existing `tool_names` discussion.

### Details

- Duplicate-detection sentence to add (verbatim, per the plan's Design section):
  "Duplicate live ownership (the same tool name reported by two or more servers'
  `/v1/tools` responses) is detected in `shared/route_resolver.py::build_discovery_map()`
  and surfaced as a `ServiceWarning` by
  `agent/repl_health.py::check_routing_drift_vs_live()` — not by the registry's own
  per-server validation, which cannot see other servers' live responses."
- Cross-reference sentence should name the target doc file explicitly (e.g. "See
  `docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md` for concrete
  omitted/empty/populated `tool_names` examples.") so the link is unambiguous even in
  plain-text Markdown without hyperlink rendering.
- English only, per `rules/coding.md` conventions applied to docs as well.
- Do not alter any other existing content in the 93-116 line range beyond these
  insertions.

## Validation plan

Filtered to checks relevant to this doc:

| Check | Tool | Target |
|---|---|---|
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
| Docs (MCP-specific) | `uv run check-mcp-docs` | Passes — in particular the "routing authority language consistency" check, since this doc touches routing-source-of-truth wording |
| Manual | `grep -n "build_discovery_map\|check_routing_drift_vs_live" docs/04_mcp_03_01_dispatch-and-routing.md` | Confirms the duplicate-detection location sentence was added |
