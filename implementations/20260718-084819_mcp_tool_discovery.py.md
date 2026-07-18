# Implementation procedure: `scripts/agent/services/mcp_tool_discovery.py` (capabilities tolerance)

Source plan: `plans/20260717-131133_plan.md` ("Define MCP tool capability naming convention",
requirement `requires/20260717_13_require.md`), Implementation step 4.

**Relationship to existing docs for this file**: three prior docs already design this not-yet-implemented
file — `implementations/20260717-203830_mcp_tool_discovery.py.md` (requirement 03's base design: fetch,
validate, normalize, dedupe, build registry), `implementations/20260717-224511_mcp_tool_discovery.py.md`
(requirement 09's extension: absorbs drift/tool-definitions-startup checks), and
`implementations/20260718-084109_mcp_tool_discovery.py.md` (a sibling plan's `schema_version`-tolerance
addition). None of the three mentions `capabilities` anywhere (confirmed via grep of all three — zero
hits). This is a genuine fourth, additive layer on the same file — flagged explicitly, not a silent skip.
All four docs (203830, 224511, 084109, this one) must be implemented together, against the same eventual
file, in the order they were designed.

## Goal

Extend the planned `McpToolDiscoveryService._validate_and_normalize_entry()` (per the base doc's Procedure
step 7) so that an optional `capabilities` key on a per-tool `/v1/tools` entry is read if present — as a
list of strings — and passed through to `build_runtime_tool()`; its **absence is not an error** and
defaults to an empty tuple, consistent with the acceptance criterion "discovery service tolerates tools
with no capabilities declared." No validation of individual capability-string shape (e.g. against the
`domain.action` convention) is added — this requirement defines the convention as documentation guidance
only (`implementations/20260718-084628_tool_capability_naming_convention.md`), not a runtime schema.

## Scope

**In scope**
- `scripts/agent/services/mcp_tool_discovery.py`'s planned `_validate_and_normalize_entry()`: add
  `capabilities` to the set of optional, type-checked-only-if-present fields (alongside the base doc's
  existing `status`/`is_write`/`requires_serial`/`resource_scope` list).
- `_dedupe_and_build()`'s `build_runtime_tool(...)` call site: pass `capabilities=entry.get("capabilities")`
  through (the factory itself resolves a `None`/absent value to `()`, per
  `implementations/20260718-084710_runtime_tool.py.md`'s Procedure step 3 — no `None`-to-`()` resolution
  needed here in the discovery service; that resolution lives in the factory).

**Out of scope**
- Any change to the unified severity scheme, drift detection, `schema_version` handling, or
  `_check_tool_definitions` absorption — fully specified by the three prior docs, untouched here.
- Requiring or validating the `domain.action` shape of any capability string — the convention doc defines
  the shape for human/documentation purposes only; no regex or enum check is added at this parsing
  boundary (mirrors the base doc's existing stance on `agent_safety_tier`: `Literal` enforced statically,
  not at runtime).
- Any real MCP server's `TOOL_LIST` gaining a populated `capabilities` entry — out of scope for this
  requirement entirely (per the plan's own Out-of-scope section).

## Assumptions

1. **The optional-field validation pattern to extend already exists** (per
   `implementations/20260717-203830_mcp_tool_discovery.py.md`'s Procedure step 7): `status`/`is_write`/
   `requires_serial`/`resource_scope` are "type-checked only if present" inside
   `_validate_and_normalize_entry()`. `capabilities` slots into the same pattern as a fifth optional field:
   if the key is present, it must be a list (JSON array); if present but not a list (e.g. a bare string or
   a number), that is a per-tool schema warning (`StartupCheckOutcome` with `StartupCheckStatus.WARNING`),
   matching the base doc's existing severity choice for malformed optional fields (schema errors are
   per-tool warnings, not fatal, per that doc's Procedure step 7).
2. **Element-level type checking is shallow, not deep**: this doc validates that `capabilities`, if
   present, is a list; it does not additionally require every element to be a `str` (the base doc's
   existing optional-field checks are similarly shallow — e.g. `is_write` is checked to be a `bool`, not
   cross-validated against anything else). If a non-string element reaches `build_runtime_tool()`, the
   factory's `tuple(capabilities)` normalization (per the paired `runtime_tool.py` doc) will simply include
   it as-is — no additional guard is added here, consistent with this requirement's stated scope (defining
   the convention, not enforcing it broadly).
3. **No new HTTP round-trip or top-level response-shape change** — `capabilities` is read from the same
   already-parsed per-tool `entry` dict `_validate_and_normalize_entry()` already receives; no change to
   `_fetch_server_tools()`'s top-level `{"tools": [...]}` shape check is needed (that top-level shape is
   unrelated to per-tool optional fields).

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py` (not yet created in real source — implement this doc's
addition together with `implementations/20260717-203830_mcp_tool_discovery.py.md`,
`implementations/20260717-224511_mcp_tool_discovery.py.md`, and
`implementations/20260718-084109_mcp_tool_discovery.py.md` as one combined file).

### Procedure

1. In `_validate_and_normalize_entry()` (base doc's Procedure step 7, rule (e) "optional `status`/
   `is_write`/`requires_serial`/`resource_scope` type-checked only if present"), extend rule (e) to also
   cover: `capabilities`, if present, must be a `list` — on failure, return `(None,
   StartupCheckOutcome(source="mcp_tool_discovery", status=StartupCheckStatus.WARNING, message=f"tool
   {name!r} on server {server_key!r}: capabilities must be a list"))`, matching the existing message-format
   convention for this method's other optional-field failures.
2. In `_dedupe_and_build()`'s `build_runtime_tool(...)` call (base doc's Procedure step 8), add one keyword
   argument to the existing call: `capabilities=entry.get("capabilities")` — no local `or ()` fallback
   needed at this call site, since `build_runtime_tool()`'s own `None`-to-`()` resolution already handles
   the absent case (per `implementations/20260718-084710_runtime_tool.py.md`'s factory Details).
3. Update the module docstring (base doc's Procedure step 1) with one additional sentence: "an optional
   `capabilities` list per tool entry is read and normalized into `RuntimeTool.capabilities`; its absence
   is tolerated and defaults to an empty tuple — this requirement does not validate individual capability
   string shape against the `domain.action` convention documented in
   `docs/04_mcp_08_tool_capability_naming_convention.md`."

### Method

No new class/protocol. A small, additive extension to one existing validation branch and one existing
factory call — implemented in the same file, same class, same methods as the three prior docs specify.

### Details

Pseudocode addition only (no production code):

```
class McpToolDiscoveryService:
    # ... existing methods from the base (203830), drift-extension (224511), and
    #     schema_version-tolerance (084109) docs ...

    def _validate_and_normalize_entry(
        self, server_key: str, server_url: str, entry: object
    ) -> tuple[dict[str, object] | None, StartupCheckOutcome | None]: ...
        # ... existing checks: dict, name, description, inputSchema/input_schema ...
        # ... existing optional-field checks: status, is_write, requires_serial, resource_scope ...
        # capabilities = entry.get("capabilities")
        # if capabilities is not None and not isinstance(capabilities, list):
        #     return None, StartupCheckOutcome(
        #         source="mcp_tool_discovery", status=StartupCheckStatus.WARNING,
        #         message=f"tool {entry.get('name')!r} on server {server_key!r}: capabilities must be a list",
        #     )
        # return entry, None  # unchanged otherwise

    def _dedupe_and_build(
        self, entries: list[tuple[str, str, dict[str, object]]]
    ) -> tuple[RuntimeToolRegistry, list[StartupCheckOutcome]]: ...
        # ... existing grouping/dedup logic ...
        # tool = build_runtime_tool(
        #     name=..., server_key=..., server_url=..., description=..., input_schema=...,
        #     raw_definition=entry, status=entry.get("status", "active"),
        #     is_write=entry.get("is_write"), requires_serial=entry.get("requires_serial"),
        #     capabilities=entry.get("capabilities"),  # None -> () inside the factory
        # )
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/agent/services/mcp_tool_discovery.py && uv run ruff check scripts/agent/services/mcp_tool_discovery.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/services/mcp_tool_discovery.py` | 0 errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations — agent layer may import shared |
| Security | `uv run bandit -r scripts/agent/services/mcp_tool_discovery.py -c pyproject.toml` | 0 high/medium |
| Missing-capabilities tolerance | `uv run pytest tests/test_mcp_tool_discovery.py -v -k capabilit` | a `/v1/tools` entry without `capabilities` parses without error, `RuntimeTool.capabilities == ()` (see paired test doc `implementations/20260718-084859_test_mcp_tool_discovery.py.md`) |
| Malformed-capabilities warning | same command as above | a non-list `capabilities` value produces a `WARNING`-severity `StartupCheckOutcome`, not a fatal error, and excludes only that tool |
| Full discovery-service suite | `uv run pytest tests/test_mcp_tool_discovery.py -v` | all pass, including base/drift/schema_version cases, unaffected by this addition |
| Constraint | `ast-grep --pattern 'except: $$$' --lang python scripts/agent/services/mcp_tool_discovery.py` | no bare except |
