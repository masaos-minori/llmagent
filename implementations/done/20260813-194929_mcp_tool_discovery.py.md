## Goal

Make `McpToolDiscoveryService` require and validate all 4 schema-2.0 fields
(`is_write`, `requires_serial`, `resource_scope_kind`, `resource_scope_keys`)
on every discovered tool entry, rejecting (excluding from the built registry)
any tool whose declaration is incomplete or invalid — replacing the current
behavior where absence of these fields is not an error and an incomplete tool
is silently registered via `build_runtime_tool()`'s defaulting.

## Scope

In scope:
- `McpToolDiscoveryService._validate_and_normalize_entry()` (confirmed
  current location: `scripts/agent/services/mcp_tool_discovery.py:204-259`).
- `McpToolDiscoveryService._dedupe_and_build()` (confirmed current location:
  `scripts/agent/services/mcp_tool_discovery.py:261-305`).
- The module's use of a shared contract validator (a dependency, not written
  here — see Assumptions) to perform the actual field-completeness/type/
  scope-key checks.
- The module's existing severity scheme (WARNING vs. FATAL via
  `_is_fatal_severity()`) as the reporting mechanism for rejected entries.

Out of scope:
- `scripts/shared/resource_scope.py` and its `validate_tool_schema_v2()` (or
  equivalently named) contract validator — a dependency of this change, owned
  by a different implementation cycle per the plan's Phase 1.
- `scripts/agent/tool_runner.py`, `scripts/agent/tool_scheduler.py` (consume
  `RuntimeToolRegistry`/`ToolSpec` downstream of this file; not touched
  here).
- `scripts/shared/runtime_tool.py`'s `build_runtime_tool()` signature itself
  (the field rename from `resource_scope` to `resource_scope_kind`/
  `resource_scope_keys` is a different file's change).
- Any `docs/*.md` edit.

## Assumptions

- Actual current line numbers, confirmed by direct reading of the file
  (not the plan's approximate citations): `_validate_and_normalize_entry()`
  spans lines 204-259; `_dedupe_and_build()` spans lines 261-305. The plan
  cites `_validate_and_normalize_entry()` at "204-259" (exact match) and
  `_dedupe_and_build()` at "line ~300" (approximate; its actual `def` line is
  261, with its body running to 305) — this doc uses the confirmed 261-305
  range going forward.
- Current behavior of `_validate_and_normalize_entry()` (lines 239-250):
  iterates `("status", str), ("is_write", bool), ("requires_serial", bool),
  ("resource_scope", str), ("enabled", bool)` and type-checks each `if
  field_name in entry` — presence is optional; a missing field is not an
  error. The docstring (lines 209-214) states this explicitly: "optional
  `status`/`is_write`/`requires_serial`/`resource_scope`/`enabled`/
  `capabilities` are type-checked only if present."
- Current behavior of `_dedupe_and_build()` (lines 300-301): passes
  `entry.get("is_write")` and `entry.get("requires_serial")` (both `None` on
  a fully-absent entry) straight into `build_runtime_tool()`, which — per
  this file's own docstring's description of `RuntimeTool`/
  `build_runtime_tool()` elsewhere in the codebase — silently defaults
  missing values rather than rejecting the tool.
- 14 prior-cycle docs exist for this basename under
  `implementations/done/` (dated 2026-07-17 through 2026-07-21, all
  predating this plan's 2026-08-13 generation), plus 5 more for
  `test_mcp_tool_discovery.py` under the same date range. Confirmed by grep
  that `resource_scope_kind`/`resource_scope_keys` do not exist anywhere in
  `scripts/` or `tests/` today — none of those 14+5 prior docs implemented
  this plan's 4-field requirement (the field `resource_scope` — singular,
  still present in this file's current type-check list at line 243 — is the
  pre-existing, different contract those prior cycles most likely built).
  Coincidental filename matches, not this plan's change.
- A shared contract validator (e.g. `validate_tool_schema_v2(entry: dict) ->
  list[str]`, per the plan's Phase 1 step) is assumed to exist in
  `scripts/shared/resource_scope.py` or a new `scripts/shared/
  mcp_tool_contract.py` by the time this file's change lands, exposing a
  callable this module can invoke with the already-fetched `entry` dict (no
  second HTTP round-trip, per the plan's Design section). This doc describes
  the calling convention this module needs but does not implement the
  validator itself.
- The validator's key/type contract, per the plan's Design section verbatim:
  "`resource_scope_kind`/`resource_scope_keys` validation (keys must exist in
  the tool's own `inputSchema.properties`, reusing the same entry dict
  already fetched — no second HTTP round-trip)."

## Design decisions

- Follow the plan's Design section exactly: `_validate_and_normalize_entry()`
  becomes a **hard requirement check** for `is_write`, `requires_serial`,
  `resource_scope_kind`, `resource_scope_keys` — missing any one produces a
  per-tool finding at the module's existing severity
  (`_is_fatal_severity()`-derived WARNING/FATAL), where today only a
  type-mismatch on an already-present field does. This is a strictly broader
  rejection surface than today's check, not a replacement of it — the
  existing `status`/`enabled`/`capabilities` optional-if-present checks (and
  the legacy `resource_scope: str` optional check) are left as-is;
  `resource_scope` singular is retired only once the shared field-rename
  (a different file) lands, at which point this module's field list must
  drop `("resource_scope", str)` and gain
  `("resource_scope_kind", str)`/`("resource_scope_keys", list)` as required
  checks rather than optional ones.
- The 4 new required-field checks and the `resource_scope_keys`-vs-
  `inputSchema.properties` cross-check are delegated to the shared contract
  validator (dependency), not reimplemented inline in
  `_validate_and_normalize_entry()`. This follows the plan's Design section
  ("via the new contract validator") and keeps a single source of truth for
  the schema-2.0 shape shared with `tests/mcp_servers/test_tool_schema_contract.py`
  (the same validator that checks every static `TOOL_LIST` in Phase 2 checks
  live discovery entries here too — one contract, two call sites).
- `_dedupe_and_build()` stops passing `entry.get("is_write")`/
  `entry.get("requires_serial")` (and, once the field-rename lands,
  `entry.get("resource_scope_kind")`/`entry.get("resource_scope_keys")`)
  through to `build_runtime_tool()`'s silent defaulting. Instead, an entry
  that fails the hard requirement check in
  `_validate_and_normalize_entry()` is excluded from `_dedupe_and_build()`'s
  input entirely — `_validate_and_normalize_entry()` already returns
  `(None, finding)` for a rejected entry (see `_warning_entry()` helper,
  lines 91-95), and `_fetch_server_tools()`'s existing loop (lines 193-200)
  already skips appending `None`-normalized entries to its `entries` list.
  This means **no change to `_dedupe_and_build()`'s control flow is
  needed for the exclusion itself** — the exclusion happens upstream, in
  `_validate_and_normalize_entry()`, by simply extending its existing
  hard-reject path to cover the 4 new required fields. `_dedupe_and_build()`
  only needs its `build_runtime_tool()` call-site arguments updated to match
  whatever `build_runtime_tool()`'s post-rename signature expects (a
  downstream consequence of the `runtime_tool.py` rename, tracked there, not
  a new validation branch here).
- This mirrors "the existing duplicate-tool exclusion pattern one paragraph
  above it in the same method" per the plan's Design section — but the
  actual mechanism ends up being simpler than a second exclusion branch
  inside `_dedupe_and_build()`: the entry never reaches `_dedupe_and_build()`
  at all once `_validate_and_normalize_entry()` rejects it upstream, which is
  the *cleanest* way to "exclude incomplete tools from the built registry
  instead of registering them with `build_runtime_tool()`'s silent
  defaults" — no dead entry is grouped by name only to be filtered later.
- Findings for a missing schema-2.0 field are WARNING/FATAL per
  `_is_fatal_severity()`, exactly like every other finding this module
  emits (drift, tool-definitions, malformed-capabilities) — not the
  always-FATAL treatment reserved for duplicate-tool-name findings (that
  exception is unrelated to this change and stays as-is).

## Alternatives considered

- Adding a second exclusion branch inside `_dedupe_and_build()` (checking
  `is_write is None or requires_serial is None or ...` per group before
  calling `build_runtime_tool()`, in addition to
  `_validate_and_normalize_entry()`'s check): rejected as redundant — once
  `_validate_and_normalize_entry()` hard-rejects an incomplete entry,
  `_fetch_server_tools()` never appends it to `entries`, so
  `_dedupe_and_build()` never sees it. A second check there would be
  unreachable dead code under the corrected upstream behavior, unless
  `_validate_and_normalize_entry()`'s reject path were ever bypassed — which
  it is not in this design.
- Reimplementing the 4-field requirement/key-cross-check logic inline in this
  file instead of delegating to a shared validator: rejected — the plan
  explicitly designs a shared validator reused by both
  `tests/mcp_servers/test_tool_schema_contract.py` (static `TOOL_LIST` checks)
  and this module (live discovery checks), per its Phase 1 step; duplicating
  the logic here would create two contract implementations that could drift.

## Implementation

### Target file: `scripts/agent/services/mcp_tool_discovery.py`

### Procedure

1. Import the shared contract validator (dependency; exact import path
   depends on where it lands — `scripts/shared/resource_scope.py` or a new
   `scripts/shared/mcp_tool_contract.py` per the plan's Phase 1 — added
   alongside the existing `from shared.runtime_tool import RuntimeTool,
   build_runtime_tool` import block, lines 46-49).
2. In `_validate_and_normalize_entry()` (lines 204-259), after the existing
   `input_schema` presence/type check (lines 233-237) and before the existing
   optional-field loop (lines 239-250), call the shared validator against
   `entry` (already-fetched dict, no new HTTP call) and, on any reported
   error, return `_warning_entry(...)` with the validator's message(s) —
   mirroring the existing `_warning_entry()` early-return pattern used by
   every other check in this method.
3. Update the field list at lines 239-245 to add `is_write`/`requires_serial`
   as hard-required (not `if field_name in entry`-gated) once the shared
   validator's required-field check subsumes this — in practice this means
   the shared validator's call in step 2 replaces the need for
   `is_write`/`requires_serial` to remain in the *optional* loop at all, since
   the validator already enforces their presence+type; leaving them removed
   from the optional loop (moved to "handled by the shared validator") avoids
   double-checking the same field twice with two different error messages.
4. Add `resource_scope_kind`/`resource_scope_keys` to the same validator call
   (step 2) rather than to the optional loop — these 2 fields do not exist in
   the optional loop today (only the legacy singular `resource_scope` does at
   line 243), so this is a pure addition via the validator, not a migration
   of an existing loop entry. `resource_scope` singular's own removal from
   the optional loop is tracked by the `runtime_tool.py` field-rename (a
   different file), not by this step — until that rename lands, this file
   can validate both the legacy singular field (existing optional check) and
   the new plural/kind+keys fields (new required check) side by side without
   conflict, since they are different key names.
5. Update the method's docstring (lines 207-215) to state the new hard
   requirement and reference the shared validator, replacing "optional ...
   are type-checked only if present" with language reflecting the 4 fields'
   new required status.
6. In `_dedupe_and_build()` (lines 261-305): no structural change to its
   control flow is needed for the exclusion mechanism itself (per Design
   decisions above — rejection already happens upstream). Update only the
   `build_runtime_tool(...)` call's keyword arguments (lines 292-304) to
   match whatever `build_runtime_tool()`'s signature is after the
   `runtime_tool.py` rename (a downstream, different-file dependency) —
   i.e. once that file replaces `resource_scope: str` with
   `resource_scope_kind: str` + `resource_scope_keys: tuple[str, ...]`, this
   call site must pass `resource_scope_kind=entry.get("resource_scope_kind")`
   and `resource_scope_keys=tuple(entry.get("resource_scope_keys", []) or
   [])` instead of whatever the current call passes for the singular field
   today (the current call, read in full above, does not currently pass
   `resource_scope` at all — it is absent from the current
   `build_runtime_tool()` call's keyword list entirely, lines 292-304).
7. Update the method's docstring (lines 264-269) to mention the 4-field
   contract is now guaranteed satisfied for every entry reaching this method.

### Method

In-place edits to two existing methods plus a new dependency import; no new
public methods, no change to `discover_all()`'s public signature or
`DiscoveryResult`'s shape.

### Details

`_validate_and_normalize_entry()`, illustrative shape after the change
(exact validator call signature depends on the dependency's final API):

```python
def _validate_and_normalize_entry(
    self, server_key: str, server_url: str, entry: object
) -> tuple[dict[str, object] | None, StartupCheckOutcome | None]:
    """Validate one raw /v1/tools entry.

    Rules: entry is a dict; `name` is a non-empty string; `description`
    is present and is a str (empty string allowed); `inputSchema` or
    `input_schema` is a dict; `is_write`, `requires_serial`,
    `resource_scope_kind`, `resource_scope_keys` are REQUIRED and
    validated via `validate_tool_schema_v2()` (schema-2.0 contract) —
    a missing or invalid schema-2.0 field rejects the entry with a
    per-tool WARNING/FATAL finding, it is not silently defaulted.
    Optional `status`/`enabled`/`capabilities` remain type-checked only
    if present.
    """
    if not isinstance(entry, dict):
        return _warning_entry(...)
    name = entry.get("name")
    ...
    input_schema = entry.get("inputSchema", entry.get("input_schema"))
    if not isinstance(input_schema, dict):
        return _warning_entry(...)

    schema_errors = validate_tool_schema_v2(entry)
    if schema_errors:
        return _warning_entry(
            f"{server_key}: tool {name!r} failed schema-2.0 validation: "
            f"{'; '.join(schema_errors)}"
        )

    for field_name, expected_type in (
        ("status", str),
        ("enabled", bool),
    ):
        if field_name in entry and not isinstance(entry[field_name], expected_type):
            return _warning_entry(...)
    ...
    return entry, None
```

`_dedupe_and_build()`'s `build_runtime_tool()` call site, updated argument
list only (control flow unchanged):

```python
built[name] = build_runtime_tool(
    name=name,
    server_key=server_key,
    server_url=server_url,
    description=str(entry.get("description", "")),
    input_schema=entry.get("inputSchema", entry.get("input_schema")),
    raw_definition=entry,
    status=str(entry.get("status", "active")),
    is_write=entry["is_write"],
    requires_serial=entry["requires_serial"],
    resource_scope_kind=entry["resource_scope_kind"],
    resource_scope_keys=tuple(entry["resource_scope_keys"]),
    enabled_for_llm=bool(entry.get("enabled", True)),
    capabilities=tuple(entry.get("capabilities", []) or []),
)
```
Direct-index (`entry["is_write"]`, not `entry.get("is_write")`) is
deliberate: by the time an `entry` reaches `_dedupe_and_build()`, it has
already passed the hard-requirement check in
`_validate_and_normalize_entry()`, so the keys are guaranteed present —
using `.get()` here would silently reintroduce the exact defaulting
behavior this change removes.

## Compatibility considerations

- This is a **behavior-narrowing** change: any live MCP server whose
  `/v1/tools` response omits any of the 4 schema-2.0 fields on any tool will,
  after this change, have that tool excluded from the registry (previously
  it was silently registered with defaults). This directly depends on all 4
  in-scope `TOOL_LIST` modules (`rag_pipeline_tools.py`, `mdq_tools.py`,
  `shell_tools.py`, `web_search_tools.py` — sibling docs in this batch) and
  the other 6 servers in the plan's Scope (`file/*`, `git`, `github/*`,
  `cicd`) all declaring the 4 fields, or every one of their tools becomes
  unreachable from the LLM at startup. This is the plan's own stated risk
  ("Fail-closed rejection ... could silently drop a tool from the
  LLM-visible surface in production if any single server's `TOOL_LIST`
  update has a typo or omission") and its mitigation
  (`tests/mcp_servers/test_tool_schema_contract.py`) is out of scope for
  this file but load-bearing for this file's safety.
- `entry.get("resource_scope")` (legacy singular, still optionally
  type-checked at line 243 today) is left alone by this doc's changes; its
  removal is scoped to the `runtime_tool.py`/`tool_spec.py` rename, a
  different file.
- No change to `DiscoveryResult`'s public shape (`registry`, `findings`,
  `unreachable`), so `discover_all()`'s callers (e.g. startup wiring in
  `scripts/agent/startup.py`) are unaffected by this file's change alone.

## Security considerations

- Fail-closed is strictly safer than the current fail-open (silent-default)
  behavior for scheduling metadata: an incomplete declaration can no longer
  cause a tool to be scheduled as if it were read-only/unscoped when its
  actual `is_write`/`resource_scope_kind` was simply never reported.
- The severity scheme (`_is_fatal_severity()`) already ties strict-mode/
  production-profile rejections to FATAL — under `production`, an incomplete
  schema-2.0 declaration on any server now produces a FATAL finding,
  consistent with startup-blocking behavior for other FATAL findings this
  module already emits (duplicates, drift).

## Rollback considerations

- Revert requires reverting both the new validator call in
  `_validate_and_normalize_entry()` and the `build_runtime_tool()` call-site
  argument change in `_dedupe_and_build()` together — reverting only one half
  would either (a) still reject entries via the validator but no longer pass
  the new fields through (harmless but pointless), or (b) index required
  keys with `entry[...]` before the validator guarantees their presence,
  raising `KeyError` at runtime for any incomplete entry. Both files listed
  in Procedure step 2 and step 6 must move together.
- No persisted state; a revert only affects future discovery runs.

## Validation plan

- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py tests/agent/services/test_runtime_tool_routing_integration.py -v` — per the plan's
  Validation plan row verbatim: "Round-trip preserves all 4 fields;
  incomplete tool excluded from registry, not defaulted."
- New test cases needed (added in the sibling doc for
  `test_mcp_tool_discovery.py`, not here): a fully-declared entry round-trips
  all 4 fields into the built `RuntimeTool`/registry; an entry missing any
  one of the 4 fields is excluded from `result.registry` and produces exactly
  one WARNING (local profile) or FATAL (production/strict) finding; an entry
  with `resource_scope_keys` naming a key absent from its own
  `inputSchema.properties` is likewise excluded.
- `uv run pytest tests/mcp_servers/test_tool_schema_contract.py -v` (new,
  Phase 2) indirectly validates that the shared validator this file calls
  accepts every real `TOOL_LIST` in the repo, which is a precondition for
  this file not rejecting legitimate live tools in practice.

## Out of scope

- Implementing `validate_tool_schema_v2()` itself
  (`scripts/shared/resource_scope.py` or `scripts/shared/mcp_tool_contract.py`
  — a different file's change).
- `scripts/agent/tool_runner.py`/`tool_scheduler.py`'s consumption of the
  resulting `RuntimeToolRegistry`/`ToolSpec`s.
- Migrating the legacy singular `resource_scope` optional check
  (line 243) — tracked against the `runtime_tool.py` rename.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-183049_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-194929
- Related target files: scripts/agent/services/mcp_tool_discovery.py
