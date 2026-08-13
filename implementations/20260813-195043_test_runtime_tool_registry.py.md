## Goal

Update `tests/shared/test_runtime_tool_registry.py` for the `resource_scope` →
`resource_scope_kind`/`resource_scope_keys` (on `RuntimeTool`) and `resource_scope` →
`resource_scopes` (on `ToolSpec`) renames, and add coverage that
`_build_tool_spec()`/`tool_spec_for_call()` actually resolve scopes via
`resolve_resource_scopes()` against real call arguments — the specific behavior gap the
companion `runtime_tool_registry.py` source doc closes.

## Scope

In scope: `tests/shared/test_runtime_tool_registry.py` only — the one existing test
referencing `resource_scope` (`test_tool_spec_map_copies_write_serial_scope_fields`,
lines 62–76) plus new coverage for scope resolution flowing through
`tool_spec_for_call()`. Out of scope: `test_resource_scope.py` (tests
`resolve_resource_scopes()` in isolation), `test_runtime_tool.py`,
`test_tool_spec.py` — each has its own doc.

## Assumptions

- The only existing reference to the old singular field in this file is inside
  `test_tool_spec_map_copies_write_serial_scope_fields` (lines 62–76): the keyword
  argument `resource_scope="delete_file"` at line 68 and the assertion
  `assert spec.resource_scope == "delete_file"` at line 75 — confirmed by reading the
  full 250-line file plus a targeted `rg "resource_scope"` grep that returned only these
  two lines within that one test.
- `test_tool_spec_for_call_fills_call_specific_fields` (lines 78–86) currently uses a
  tool with no scope kind/keys at all (`build_runtime_tool(name="write_file",
  server_key="fs", is_write=True)`, line 79) and never asserts anything about scope —
  this is the specific gap the new dedicated scope-resolution test (below) fills, since
  this existing test's tool has an empty `resource_scope_kind` and would resolve to a
  scope determined solely by the fallback rule (`is_write=True` + no keys →
  `("global:write",)`), not by an actual resolved argument value.

## Design decisions

- **Update the existing test in place** for the rename (minimal diff, same scenario:
  "tool_spec_map copies write/serial/scope fields") — the test's *intent* is unchanged,
  only the field shape it asserts against changes.
- **Add a new, separate test for real scope-resolution-through-call-args**, rather than
  overloading the updated `test_tool_spec_map_copies_write_serial_scope_fields`, because
  `tool_spec_map()` deliberately calls `_build_tool_spec()` with no real args (per that
  method's own docstring, "for shape/config inspection, not for representing an actual
  call") — so asserting a *resolved-from-args* scope belongs on a `tool_spec_for_call()`
  test instead, extending `test_tool_spec_for_call_fills_call_specific_fields`'s sibling
  set rather than repurposing the `tool_spec_map` test.
- **Also add a `tool_spec_map()`-with-scoped-tool case** verifying it resolves against
  empty args (i.e. a write tool with real `resource_scope_keys` yields
  `("global:write",)` via `tool_spec_map()` specifically, since no real args are ever
  supplied there) — this locks in the documented, accepted behavior noted as an
  assumption in the source doc, preventing a future change from silently changing
  `tool_spec_map()`'s empty-args resolution semantics without a failing test.

## Alternatives considered

Testing scope resolution only in `test_resource_scope.py` and treating
`test_runtime_tool_registry.py`'s coverage as pure pass-through/no-new-test-needed.
Rejected: the plan's own Validation-plan row for `runtime_tool_registry.py` explicitly
states "`tool_spec_for_call()` returns `resource_scopes` populated via
`resolve_resource_scopes()`" as the expected outcome for *this* file's test — an
integration-level assertion here that scope resolution actually flows through the real
call path is necessary in addition to `resolve_resource_scopes()`'s own isolated unit
tests, since a wiring mistake (e.g. forgetting to pass `args` through) would not be
caught by `test_resource_scope.py` alone.

## Implementation

### Target file: `tests/shared/test_runtime_tool_registry.py`

### Procedure

1. In `test_tool_spec_map_copies_write_serial_scope_fields` (lines 62–76):
   - Replace the keyword argument at line 68, `resource_scope="delete_file",` with
     `resource_scope_kind="filesystem",` followed by
     `resource_scope_keys=("path",),`.
   - Replace the assertion at line 75, `assert spec.resource_scope == "delete_file"`
     with `assert spec.resource_scopes == ("global:write",)` — since `tool_spec_map()`
     calls `_build_tool_spec()` with no real args (confirmed: `tool_spec_map()`,
     lines 145–154, calls `_build_tool_spec("", name, tool)` with the `args` parameter
     omitted, defaulting to `None` → `{}`), a write tool with unresolvable
     `resource_scope_keys` against empty args hits the fail-closed fallback rather than
     resolving `"filesystem:delete_file"` literally — rename the test slightly if needed
     (e.g. to `test_tool_spec_map_copies_write_serial_scope_fields_and_falls_back_to_global_write_scope`)
     or add a one-line comment explaining why the assertion is `("global:write",)` and
     not a literal `"filesystem:..."` string, to avoid this reading like a mistake to a
     future reader.
2. Add a new test method `test_tool_spec_for_call_resolves_scope_from_call_args` after
   `test_tool_spec_for_call_fills_call_specific_fields` (currently ending at line 86):
   construct a tool via `build_runtime_tool(name="write_file", server_key="fs",
   is_write=True, resource_scope_kind="filesystem", resource_scope_keys=("path",))`;
   call `reg.tool_spec_for_call(call_id="call-1", name="write_file", args={"path":
   "/data/a.txt"})`; assert `spec.resource_scopes == ("filesystem:/data/a.txt",)` —
   this is the concrete regression test for the plan's stated expected outcome for this
   file.
3. Add a new test method `test_tool_spec_for_call_falls_back_to_global_write_when_scope_key_missing`:
   same tool as above, but call `tool_spec_for_call(call_id="call-2", name="write_file",
   args={})` (the declared `path` key absent); assert
   `spec.resource_scopes == ("global:write",)`.

### Method

Direct `Edit` of the two lines inside the existing test (keyword arg + assertion, plus
an optional rename/comment for clarity), then append two new test methods immediately
after the existing `tool_spec_for_call` test, keeping all `tool_spec_for_call`-related
tests grouped together in the class body. Run
`uv run pytest tests/shared/test_runtime_tool_registry.py -v` after editing.

### Details

- Exact current lines: 68 (`resource_scope="delete_file",` inside the
  `build_runtime_tool(...)` call spanning lines 63–69) and 75
  (`assert spec.resource_scope == "delete_file"`), inside
  `test_tool_spec_map_copies_write_serial_scope_fields` (def at line 62).
- No import changes needed — `from shared.runtime_tool import RuntimeTool,
  build_runtime_tool` (line 10), `from shared.runtime_tool_registry import
  RuntimeToolRegistry` (line 11), `from shared.tool_spec import ToolSpec` (line 12)
  already cover everything these updated/new tests need; no direct import of
  `resolve_resource_scopes` is needed in this file since these tests exercise it only
  indirectly through `RuntimeToolRegistry`'s methods (unlike `test_resource_scope.py`,
  which imports and calls it directly).
- The `_registry_with(*tools)` helper (lines 15–16) is reused unchanged for all new
  tests.

## Compatibility considerations

Must land in the same commit as the `runtime_tool.py`, `tool_spec.py`, and
`runtime_tool_registry.py` source changes (all four rename together per the plan's Risk
mitigation) — this test file cannot pass in isolation against an un-renamed source tree.

## Security considerations

The new `test_tool_spec_for_call_falls_back_to_global_write_when_scope_key_missing` test
is a direct regression guard for the fail-closed behavior actually reaching real call
handling (not just `resolve_resource_scopes()` in isolation) — do not remove it without
an explicit separate decision, since it is the integration-level check that a future
refactor of `_build_tool_spec()`'s `args or {}` handling doesn't accidentally swallow the
fallback.

## Rollback considerations

Revert together with `scripts/shared/runtime_tool.py`, `scripts/shared/tool_spec.py`, and
`scripts/shared/runtime_tool_registry.py` — this test file depends on all three renamed
shapes simultaneously.

## Validation plan

- `uv run pytest tests/shared/test_runtime_tool_registry.py -v` — all existing tests
  (updated) plus the two new tests pass; matches the plan's own Validation-plan row
  ("`tool_spec_for_call()` returns `resource_scopes` populated via
  `resolve_resource_scopes()`").
- `rg -n "\.resource_scope\b|resource_scope=" tests/shared/test_runtime_tool_registry.py`
  returns nothing.
- `uv run pytest tests/shared/ -v` — full `tests/shared/` regression once all 8 files in
  this doc set are implemented together.

## Out of scope

`test_resource_scope.py`'s isolated `resolve_resource_scopes()` unit tests,
`test_runtime_tool.py`, `test_tool_spec.py` (each has its own doc), and any
`tests/agent/` test file consuming `ToolSpec.resource_scopes` downstream (separate plan
target files, not assigned to this doc set).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-183049_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-195043
- Related target files: tests/shared/test_runtime_tool_registry.py
