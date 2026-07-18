# Implementation procedure: `scripts/agent/services/mcp_tool_discovery.py` (schema_version tolerance)

Source plan: `plans/20260717-131019_plan.md` ("Add MCP tool schema versioning and validation tests"),
Implementation step 3.

**Relationship to existing docs for this file**: two prior docs already design this not-yet-implemented
file — `implementations/20260717-203830_mcp_tool_discovery.py.md` (requirement 03's base design: fetch,
normalize, dedupe, build `ToolRegistry`) and `implementations/20260717-224511_mcp_tool_discovery.py.md`
(requirement 09's extension: absorbs drift/tool-definitions-startup checks from `repl_health.py`, unified
severity). Neither mentions `schema_version` anywhere (confirmed via grep of both files — zero hits).
**Flagged explicitly, not silently skipped**: this is a genuine additive gap, not a false-positive filename
match — this doc specifies the third, `schema_version`-tolerance layer on the same not-yet-implemented
file. Confirmed via `ls scripts/agent/services/mcp_tool_discovery.py` that the file does not exist in real
source yet — all three docs (203830, 224511, this one) must be implemented together, in the order they
were designed, against the same eventual file.

## Goal

Extend the planned `McpToolDiscoveryService._validate_and_normalize_entry()` (per the base doc's Procedure
step 7) and the per-server fetch/parse step so that: (a) an optional top-level `schema_version` key on the
`/v1/tools` response body is read if present but its **absence is not an error** ("Agent tolerates
schema_version absence during migration", per the plan's Goal and Assumption 3), and (b) confirms the
per-tool optional-field validation the base doc already specifies (`status`/`is_write`/`requires_serial`/
`resource_scope`, type-checked only when present) is the same set this plan's test suite (step 4) exercises
— no new validation rule is introduced beyond what requirement 03's doc already designed; this doc's only
production-facing addition is the `schema_version` read-and-tolerate step.

## Scope

**In scope**
- The per-server fetch/parse step in `McpToolDiscoveryService` (base doc's Procedure, the `_fetch_server_tools`
  method that parses each `/v1/tools` JSON body): read `response_body.get("schema_version")` (may be
  `None`/absent) and store it for optional logging; never treat its absence as a validation failure or
  `StartupCheckOutcome`.
- Confirm (not re-design) that `_validate_and_normalize_entry()`'s existing optional-field handling for
  `status`/`is_write`/`requires_serial`/`resource_scope` (base doc Procedure step 4/6, already specified)
  is what this plan's Scope refers to — no changes needed there.

**Out of scope**
- Any change to the unified severity scheme, drift detection, or `_check_tool_definitions` absorption —
  fully specified by `implementations/20260717-224511_mcp_tool_discovery.py.md`, untouched by this doc.
- Making `schema_version` required or branching validation logic by its value (e.g. `"2.0"` vs `"1.0"`
  rules) — explicitly out of scope per the plan's own Out-of-scope section.

## Assumptions

1. **The response body shape** each server now returns (per
   `implementations/20260718-084001_mcp_servers_server.py.md` and
   `implementations/20260718-084035_mcp_server_schema_version_rollout.md`) is
   `{"schema_version": "1.0", "tools": [...]}` — the base doc's own fetch step already reads
   `response_body["tools"]` (or equivalent); this doc's addition is reading the sibling
   `schema_version` key from the same parsed JSON dict, not a new HTTP call or new parsing pass.
2. Since `MCP_TOOL_SCHEMA_VERSION` is currently `"1.0"` everywhere (single shared constant, no server
   emits a different value), there is nothing to branch on yet; the tolerate-if-absent behavior is the
   only behavior this plan requires today, and is trivially satisfiable by simply not asserting on the
   key's presence — no `if/else` branch on schema_version's *value* is needed, only on the key's
   presence/absence (which itself requires no branch either, since `dict.get("schema_version")` already
   returns `None` gracefully when absent — the "tolerance" is structural, not code that needs special
   exception handling).
3. No log line is strictly required by the plan's acceptance criteria ("Agent tolerates its absence") —
   the plan's Design section mentions optionally logging it "for logging/future-compatibility branching."
   This doc treats that as a nice-to-have, not a hard requirement: a single `logger.debug()` call is
   sufficient if added, at implementer's discretion, since it has no test-observable behavior difference
   either way.

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py` (not yet created in real source — implement this doc's
addition together with `implementations/20260717-203830_mcp_tool_discovery.py.md` and
`implementations/20260717-224511_mcp_tool_discovery.py.md` as one combined file, applying all three docs'
specifications in the same implementation pass).

### Procedure

1. In the per-server fetch/parse step (base doc's `_fetch_server_tools`, which parses the JSON response
   body into `entries`/`tools`), after successfully parsing the top-level JSON object, additionally read:
   `schema_version = response_body.get("schema_version")` — a plain, optional string, `None` if absent.
   Do not raise, warn, or emit any `StartupCheckOutcome` if it is `None`.
2. No change to the return shape of `_fetch_server_tools` is required unless the implementer chooses to
   surface `schema_version` for optional debug logging — if added, log at `DEBUG` level only
   (`logger.debug("server_key=%s schema_version=%s", server_key, schema_version)`), never at `WARNING`/
   `ERROR` for a missing value.
3. Confirm (via a quick re-read of `implementations/20260717-203830_mcp_tool_discovery.py.md`'s Procedure
   step 4, lines 133-136 per that doc) that `_validate_and_normalize_entry()` already validates
   `status`/`is_write`/`requires_serial`/`resource_scope` "type-checked only if present" — this is the
   exact rule the plan's Scope describes; no edit needed to that method for this doc's purposes.

### Method

No new class/protocol. This is a small addition (one `.get()` call, optionally one debug log line) inside
the already-planned `McpToolDiscoveryService` from the two prior docs — implemented in the same file, same
class, same method as those docs specify.

### Details

Pseudocode addition only (no production code):

```
class McpToolDiscoveryService:
    # ... existing methods from the base (203830) and drift-extension (224511) docs ...

    async def _fetch_server_tools(self, server_key: str, server_url: str) -> ...: ...
        # existing fetch/parse logic (base doc) ...
        # response_body = resp.json()
        # schema_version = response_body.get("schema_version")  # None if absent — tolerated, not an error
        # logger.debug("mcp_tool_discovery: server_key=%s schema_version=%s", server_key, schema_version)
        # tools = response_body.get("tools", [])
        # ... continue with existing per-tool validation loop (base doc's _validate_and_normalize_entry) ...
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/agent/services/mcp_tool_discovery.py && uv run ruff check scripts/agent/services/mcp_tool_discovery.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/services/mcp_tool_discovery.py` | 0 errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Security | `uv run bandit -r scripts/agent/services/mcp_tool_discovery.py -c pyproject.toml` | 0 high/medium |
| Missing-schema_version tolerance | `uv run pytest tests/test_mcp_tool_discovery.py -v -k schema_version` | a response lacking `schema_version` is accepted without any `StartupCheckOutcome`/warning/error (see `implementations/20260718-084145_test_mcp_tool_discovery.py.md`) |
| Full discovery-service suite | `uv run pytest tests/test_mcp_tool_discovery.py -v` | all pass, including base-doc (203830) and drift-extension-doc (224511) cases, unaffected by this addition |
