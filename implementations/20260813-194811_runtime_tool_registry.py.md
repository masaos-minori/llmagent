## Goal

Update `RuntimeToolRegistry._build_tool_spec()` to call the new
`resolve_resource_scopes(tool, args)` (from the new `scripts/shared/resource_scope.py`)
instead of copying a static `tool.resource_scope` string, and populate `ToolSpec`'s new
plural `resource_scopes` field with the result — making per-call scope resolution live
in this registry rather than baked in at discovery time.

## Scope

In scope: `scripts/shared/runtime_tool_registry.py::_build_tool_spec()` only (the sole
method in this file referencing `resource_scope`), plus its module-level import list.
Out of scope: `resolve_resource_scopes()`'s own implementation (`resource_scope.py` doc),
the `RuntimeTool`/`ToolSpec` field renames themselves (`runtime_tool.py`/`tool_spec.py`
docs — this doc assumes those renames already landed), and every other method in this
file (`resolve`, `get`, `all_tools`, `llm_tool_definitions`, `tool_spec_map`,
`tool_spec_for_call`, `is_side_effect`, `classify_operation_type`, `apply_policy`,
`diagnostics`), none of which reference `resource_scope` and are therefore untouched.

## Assumptions

- By the time this change lands, `RuntimeTool` already has `resource_scope_kind`/
  `resource_scope_keys` (per the `runtime_tool.py` doc) and `ToolSpec` already has
  `resource_scopes` (per the `tool_spec.py` doc) — this doc's change is purely the
  glue between those two already-updated shapes via the new resolver function.
- `tool_spec_map()` (lines 145–154), which calls `_build_tool_spec("", name, tool)` with
  no `args`, will resolve scopes against an empty `{}` args mapping — for any tool whose
  `resource_scope_keys` require an actual argument value, this produces `()` (or
  `("global:write",)` for a write tool per the fallback rule), which is an accepted,
  documented behavior change: `tool_spec_map()`'s own docstring (lines 146–149) already
  states it is "for shape/config inspection, not for representing an actual call," so an
  empty-args resolution is consistent with its existing documented purpose.
- `resolve_resource_scopes` will be imported as a plain function from
  `shared.resource_scope`, not wrapped — this file has no existing precedent for
  wrapping imported leaf-module functions.

## Design decisions

- **Resolution happens per-call, not once at registration.** `_build_tool_spec()` is
  called both from `tool_spec_map()` (no real args) and `tool_spec_for_call()` (real
  call args, line 164) — moving from a static copied field to a call-time
  `resolve_resource_scopes(tool, args)` invocation is exactly what makes
  `tool_spec_for_call()`'s previously-`args`-ignoring behavior (it only forwarded `args`
  into `ToolSpec.args`, never into scope computation) now scope-aware, closing the gap
  the plan's Design section identifies.
- **Static method stays static.** `_build_tool_spec()` is already `@staticmethod`
  (line 128) and takes `tool: RuntimeTool` explicitly rather than reading from
  `self._tools` — no change to that shape; `resolve_resource_scopes()` is called with the
  same `tool` and `args` it already has in scope, no new parameter threading needed.
- **Import added at module level, not inline.** `from shared.resource_scope import
  resolve_resource_scopes` is added alongside the existing `from shared.runtime_tool
  import ...` / `from shared.tool_spec import ToolSpec` imports (lines 39–40) — both are
  `shared/`-internal imports, so no `shared-is-leaf` concern (that contract restricts
  imports *out of* `shared`, not imports *within* `shared`).

## Alternatives considered

Having `RuntimeToolRegistry.__init__` pre-resolve and cache scopes per tool at
registration time (avoiding a `resolve_resource_scopes()` call on every `_build_tool_spec()`
invocation). Rejected: scopes are inherently call-argument-dependent (e.g. `write_file`'s
scope depends on which `path` argument a specific call uses), so a registration-time
cache would be wrong for any tool with non-empty `resource_scope_keys` — only the
per-call resolution in `_build_tool_spec()` is correct.

## Implementation

### Target file: `scripts/shared/runtime_tool_registry.py`

### Procedure

1. Add `from shared.resource_scope import resolve_resource_scopes` to the import block
   (currently lines 39–40: `from shared.runtime_tool import AgentSafetyTier, RuntimeTool`
   / `from shared.tool_spec import ToolSpec`), placed alphabetically after those two
   existing `shared.*` imports.
2. In `_build_tool_spec()` (lines 128–143), replace the line
   `resource_scope=tool.resource_scope,` (currently line 140) with
   `resource_scopes=resolve_resource_scopes(tool, args or {}),` — passing `args or {}`
   (not bare `args`) since `args` is typed `dict[str, Any] | None = None` (line 133) and
   `resolve_resource_scopes()` expects a `Mapping[str, Any]`, never `None`.
3. Update the method's docstring (currently line 135: `"""Build a ToolSpec from a
   RuntimeTool."""`) to note the scope-resolution behavior, e.g.: `"""Build a ToolSpec
   from a RuntimeTool, resolving its resource scopes against *args* via
   resolve_resource_scopes()."""`.
4. No change needed to `tool_spec_map()` (lines 145–154) or `tool_spec_for_call()`
   (lines 156–164) themselves — both already call `_build_tool_spec()` with their
   respective `args` values (`{}`-implicit via the default, and the real call `args`
   respectively), so the new resolution behavior flows through automatically.
5. In the companion test file `tests/shared/test_runtime_tool_registry.py`, update
   `test_tool_spec_map_copies_write_serial_scope_fields` (currently lines 62–76, which
   constructs a tool with `resource_scope="delete_file"` at line 68 and asserts
   `spec.resource_scope == "delete_file"` at line 75) to use the new
   `resource_scope_kind`/`resource_scope_keys` construction and assert against
   `spec.resource_scopes` instead; add a new test exercising `tool_spec_for_call()` with
   a tool that has non-empty `resource_scope_keys` and args containing the matching key,
   asserting the resolved `resource_scopes` tuple reflects the actual call argument
   (this is the behavior gap this change closes — `tool_spec_for_call()`'s existing test
   at lines 78–86 uses a tool with no scope keys at all, so it does not currently
   exercise resolution).

### Method

Two-line functional change (import + one field-population line) plus one docstring
update, applied via `Edit`; no structural change to the class or method signatures.
Immediately re-run the companion test file after editing to confirm the updated
fixtures pass against the new resolver.

### Details

- Exact current line to change: line 140,
  `resource_scope=tool.resource_scope,` inside the `return ToolSpec(...)` call at
  lines 136–143.
- `args` parameter default is `None` (line 133: `args: dict[str, Any] | None = None`);
  the existing code already does `args=args or {}` for `ToolSpec.args` (line 139), so
  the new `resolve_resource_scopes(tool, args or {})` call reuses the exact same
  `args or {}` idiom already present two lines above it, keeping the two "empty args"
  fallbacks consistent within the same method.
- No change to `_build_tool_spec()`'s signature (`call_id: str, name: str, tool:
  RuntimeTool, args: dict[str, Any] | None = None`, lines 129–133) — `resolve_resource_scopes`
  needs no new parameter since `tool` and `args` are already both in scope.

## Compatibility considerations

Any caller of `_build_tool_spec()`, `tool_spec_map()`, or `tool_spec_for_call()`
receiving a `ToolSpec` and reading `.resource_scope` (singular) breaks per the
`tool_spec.py` doc's atomic-rename requirement — this doc's change is the mechanism that
makes `.resource_scopes` (plural) actually get populated with real values instead of
staying at its `()` default, so any downstream consumer expecting a single string must
be updated to iterate/index the tuple (out of scope for this doc set; e.g.
`tool_scheduler.py`).

## Security considerations

This is the point where the fail-closed `("global:write",)` fallback (implemented inside
`resolve_resource_scopes()`, not here) actually reaches a `ToolSpec` used for scheduling
— `_build_tool_spec()` must not swallow or override that fallback (e.g. must not
default `resource_scopes` to `()` on any exception from `resolve_resource_scopes()`;
no exception handling is added around this call, so any error there propagates rather
than silently producing an empty/unsafe scope).

## Rollback considerations

Revert together with the `tool_spec.py` field rename (this method's only consumer of the
new plural field) and, ideally, together with `runtime_tool.py`'s field split (this
method's only consumer of `tool.resource_scope_kind`/`resource_scope_keys` via
`resolve_resource_scopes()`); rolling back this file alone while keeping the other two
renamed would leave `_build_tool_spec()` referencing a field name (`tool.resource_scope`)
that no longer exists.

## Validation plan

- `uv run pytest tests/shared/test_runtime_tool_registry.py -v` — `tool_spec_for_call()`
  returns `resource_scopes` populated via `resolve_resource_scopes()` (per the plan's own
  Validation-plan row for this file).
- `uv run pytest tests/shared/test_resource_scope.py tests/shared/test_runtime_tool.py tests/shared/test_tool_spec.py tests/shared/test_runtime_tool_registry.py -v` —
  full cross-file regression across this doc set's shared-core changes together.
- `rg -n "\.resource_scope\b" scripts/shared/runtime_tool_registry.py` returns nothing.

## Out of scope

`resolve_resource_scopes()`'s own logic (`resource_scope.py`), the `RuntimeTool`/`ToolSpec`
field definitions themselves, every other method on `RuntimeToolRegistry` not touching
`resource_scope`, and any consumer of `ToolSpec.resource_scopes` outside `shared/` (e.g.
`scripts/agent/tool_scheduler.py`, `scripts/agent/tool_runner.py` — separate plan target
files not assigned to this doc set).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-183049_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-194811
- Related target files: scripts/shared/runtime_tool_registry.py
