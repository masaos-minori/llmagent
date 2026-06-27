# MCP Inconsistencies and Known Issues

This file catalogs bugs, unimplemented features, spec conflicts, and undefined behavior
in the MCP layer discovered during documentation restructuring.

Each entry format:
- **Type:** `Implementation bug` / `Unimplemented` / `Document inconsistency` / `Undefined` / `Needs confirmation`
- **Impact scope:** Affected modules/behavior
- **Statement A / B:** Conflicting facts (when applicable)
- **Current safe interpretation:** What to assume when uncertain
- **Recommended action:** Fix or investigation needed
- **Notes for AI reference:** Guidance for AI reasoning about this issue

---



## SPEC-01: tool_definitions_strict validation behavior

**Type:** Document inconsistency — **resolved**
**Impact scope:** `04_mcp_03`, `04_mcp_06`

**Statement A (`04_mcp_03:96`):** `validate_routing_against_live()` is "Not yet wired (future)"

**Statement B (`04_mcp_06:407`):** `_check_tool_definitions` runs at agent startup and compares `tool_definitions` against live `/v1/tools`

**Resolution:** These are DIFFERENT functions with different purposes:
- `validate_routing_against_live()` (route_resolver.py): compares live `/v1/tools` against the **internal routing registry** — not yet wired at startup
- `_check_tool_definitions` (repl_health.py): compares **configured `tool_definitions`** (from `agent.toml`) against live `/v1/tools` — IS wired at startup

There is no actual contradiction. Both statements are accurate — they describe different code paths.

**Current safe interpretation:** Use `04_mcp_06 §Startup Validation Behavior` as the authoritative behavior spec for `tool_definitions_strict`. The `validate_routing_against_live()` function in `04_mcp_03` is a separate, future feature.

**Notes for AI reference:** When asked about startup validation or `tool_definitions_strict` behavior, cite `04_mcp_06 §Startup Validation Behavior`. When asked about routing drift detection, cite `04_mcp_03 §Drift validation`.

---

## MDQ-01: Unsupported Markdown syntax causes heading misclassification

**Type:** Known issue — **documented**
**Impact scope:** `mcp/mdq/parser.py`

**Statement:** The MDQ parser does not support Setext-style headings (===, --- underlines), inline tags (<del>, <ins>), HTML blocks, or MDX. Unsupported syntax is treated as plain text rather than being parsed.

**Current behavior:** Content under unsupported syntax may be included in the preceding section rather than creating a new heading section. For example, Setext-style headings are treated as plain text with no heading level.

**Mitigation:** Document Markdown compatibility scope in `mcp/mdq/parser.py` docstring and `04_mcp_04_server_catalog.md`. Users should use ATX-style headings (## Heading) for reliable parsing.

---

## MDQ-02: Hybrid search embedding integration not yet implemented

**Type:** Unimplemented — **planned**
**Impact scope:** `mcp/mdq/search.py`

**Statement:** The `mode=hybrid` search mode is defined in the schema but the actual vector embedding generation and similarity search are not yet implemented. When `use_embedding=true`, the `_search_vector()` function logs a warning and returns empty results.

**Current behavior:** Hybrid search falls back to FTS5-only results with no error. The RRF merge logic is in place but has no vector results to merge.

**Mitigation:** Document hybrid search as "planned" rather than "implemented". Users should rely on FTS5-only mode for now.

---
