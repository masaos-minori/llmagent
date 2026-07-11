# Implementation Doc: Document Shared `McpServerHealthRegistry` Wiring

## Goal

Document that `ToolExecutor` and the watchdog share the same
`McpServerHealthRegistry` instance, and explain why this shared wiring is
required for dispatch-gating consistency — closing a documentation gap, no
code change.

## Scope

**In scope:**
- `docs/04_mcp_03_03_transport-and-health.md`: add one paragraph after the
  existing `McpServerHealthRegistry` section.

**Out of scope:**
- Any code change to `agent/factory.py`, `ToolExecutor`, or the watchdog —
  this documents existing, already-correct behavior only.

## Assumptions

- `agent/factory.py::_build_tool_executor()` (lines 209-228) creates exactly
  one `McpServerHealthRegistry()` instance (line 221), calls
  `tools.set_health_registry(registry)` on the `ToolExecutor`, and returns
  the same `registry` object, which becomes `AppServices.health_registry`
  (plan Assumption 1, confirmed by direct read).
- `_watchdog_check_http()` in `repl_health.py` reads/writes
  `ctx.services_required.health_registry`, the identical object — this is
  the "shared wiring" this doc update makes explicit.
- No code change is needed for this part; this is a docs-only clarification
  of already-correct, existing behavior.

## Implementation

### Target file

`docs/04_mcp_03_03_transport-and-health.md`

### Procedure

1. Locate the existing section that describes `McpServerHealthRegistry` in
   this doc.
2. Insert one new paragraph immediately after that section (do not rewrite
   existing content).
3. Cross-check the paragraph's claims against `agent/factory.py`'s
   `_build_tool_executor()` at documentation-write time to ensure line
   numbers / method names cited are still accurate (they may drift from the
   plan's line 209-228 reference over time).

### Method

Not applicable (documentation-only; no code signatures to define beyond
referencing existing ones: `_build_tool_executor()`, `set_health_registry()`,
`AppServices.health_registry`, `is_unavailable()`).

### Details

New paragraph content (adapt wording to match the doc's existing tone/style,
but preserve all factual claims):

- The registry is created once, in `agent/factory.py::_build_tool_executor()`.
- The same object is injected into `ToolExecutor` via `set_health_registry()`.
- The same object is stored as `AppServices.health_registry`.
- `ToolExecutor`'s transport-failure recording and the watchdog's probe
  recording both mutate this one shared object.
- Consequence: dispatch gating (`is_unavailable()`) sees both sources'
  effects immediately, with no synchronization lag.
- Warning: replacing or rebuilding the registry object anywhere (e.g. a
  future refactor that constructs a second `McpServerHealthRegistry()`)
  would desynchronize the two consumers and silently break dispatch-gating
  consistency — call this out explicitly as a constraint for future changes.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Docs consistency | `uv run python tools/check_docs_consistency.py` | Passes |
| Docs consistency (MCP-specific) | `uv run check-mcp-docs` | Passes |
| Manual | Re-read `agent/factory.py::_build_tool_executor()` at write time to confirm line numbers/method names in the new paragraph are still accurate | Matches current source |
