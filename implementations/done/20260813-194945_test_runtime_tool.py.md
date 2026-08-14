## Goal

Update `tests/shared/test_runtime_tool.py` for the `RuntimeTool`/`build_runtime_tool()`
field split (`resource_scope: str` → `resource_scope_kind: str` +
`resource_scope_keys: tuple[str, ...]`), and add coverage for the two new fields'
default/explicit-value behavior.

## Scope

In scope: `tests/shared/test_runtime_tool.py` only — every existing test referencing
`resource_scope` (there is exactly one today) plus new test methods for
`resource_scope_kind`/`resource_scope_keys`. Out of scope: `test_tool_spec.py`,
`test_resource_scope.py`, `test_runtime_tool_registry.py` (separate docs in this set).

## Assumptions

- The only existing reference to the old field in this file is inside
  `test_construct_with_full_annotation` (currently lines 19–47): the keyword argument
  `resource_scope="delete_file"` at line 30, and the assertion
  `assert tool.resource_scope == "delete_file"` at line 44 — confirmed by reading the
  full file (100 lines read; no other occurrence of `resource_scope` appears in the
  remaining `test_safe_defaults_when_unannotated`,
  `test_requires_serial_false_when_is_write_explicitly_false`,
  `test_requires_serial_explicit_override_wins`, `test_is_frozen`,
  `test_input_schema_and_raw_definition_default_to_empty_dict_not_shared_object`,
  `test_capabilities_defaults_to_empty_tuple`, or
  `test_capabilities_stored_as_tuple_from_sequence` tests).
- New tests for `resource_scope_kind`/`resource_scope_keys` defaults should mirror the
  existing `capabilities`-defaults pattern (lines 92–100: one test for the empty-tuple
  default, one for tuple-storage-from-an-explicit-sequence) since `resource_scope_keys`
  shares the exact same `tuple[str, ...]`-with-empty-tuple-default shape as
  `capabilities`.

## Design decisions

- **Update the one existing reference in place; add two new dedicated test methods**
  rather than folding the new-field coverage into the existing
  `test_construct_with_full_annotation` test alone — matches this file's existing
  granularity where `capabilities` gets its own two dedicated tests
  (`test_capabilities_defaults_to_empty_tuple`,
  `test_capabilities_stored_as_tuple_from_sequence`) separate from the "full annotation"
  smoke test.
- **`test_construct_with_full_annotation` still exercises both new fields together as
  part of "full annotation"** (not just the dedicated tests), since that test's purpose
  is a single all-fields-populated smoke check — both new fields must appear there too
  so a future field addition to `RuntimeTool` continues to be caught by this test if
  omitted from the "full" construction.

## Alternatives considered

Removing `test_construct_with_full_annotation`'s field-by-field assertions in favor of
comparing the whole `dataclasses.asdict(tool)` dict at once. Rejected: the existing test
already uses individual `assert tool.<field> == <value>` lines throughout (lines 35–47);
changing to a whole-dict comparison would be a larger, unrelated style change beyond this
plan's narrow rename scope.

## Implementation

### Target file: `tests/shared/test_runtime_tool.py`

### Procedure

1. In `test_construct_with_full_annotation` (lines 19–47):
   - Replace the keyword argument at line 30, `resource_scope="delete_file",` with
     `resource_scope_kind="filesystem",` followed by
     `resource_scope_keys=("path",),` (using a realistic filesystem-kind example
     consistent with the tool being modeled, `delete_file`, and with the plan's
     `resource_scope_keys=["path"]` example for file-delete tools).
   - Replace the assertion at line 44,
     `assert tool.resource_scope == "delete_file"` with two assertions:
     `assert tool.resource_scope_kind == "filesystem"` and
     `assert tool.resource_scope_keys == ("path",)`.
2. Add a new test method `test_resource_scope_kind_defaults_to_empty_string` after
   `test_capabilities_stored_as_tuple_from_sequence` (currently ending at line 100):
   construct via `build_runtime_tool(name="t", server_key="s")` (no scope kwargs) and
   assert `tool.resource_scope_kind == ""`.
3. Add a new test method `test_resource_scope_keys_defaults_to_empty_tuple`: same
   construction, assert `tool.resource_scope_keys == ()`.
4. Add a new test method `test_resource_scope_keys_stored_as_tuple_from_sequence`:
   construct via `build_runtime_tool(name="t", server_key="s",
   resource_scope_keys=("path", "destination"))` and assert
   `tool.resource_scope_keys == ("path", "destination")` — mirroring
   `test_capabilities_stored_as_tuple_from_sequence`'s exact pattern (lines 96–100).

### Method

Direct `Edit` of the two lines inside the existing test (keyword arg + assertion), then
append three new test methods at the end of the `TestRuntimeTool` class using the same
one-method-per-scenario style already used throughout this file. Run
`uv run pytest tests/shared/test_runtime_tool.py -v` immediately after editing to confirm
all methods (existing + new) pass against the updated `RuntimeTool`/`build_runtime_tool()`.

### Details

- File currently 100 lines; after this change it grows to roughly 112–118 lines (one
  2-line replacement, net +1 line inside the existing test; three new ~4-line test
  methods appended).
- No import changes needed — `from shared.runtime_tool import RuntimeTool,
  build_runtime_tool` (line 10) already covers everything these new tests need.
- The `_minimal_kwargs()` helper (lines 13–15) is unaffected — it returns only
  `("t", "s")`, unrelated to the scope fields.

## Compatibility considerations

N/A — this is the test file being updated to match its subject's already-planned rename;
no separate compatibility concern beyond staying in sync with `runtime_tool.py`'s change.

## Security considerations

N/A — pure test-file update.

## Rollback considerations

Must be reverted together with `scripts/shared/runtime_tool.py`'s field-split change
(this file's sole subject); reverting one without the other leaves either a
`TypeError`/`AttributeError` (if source is reverted but test isn't) or an import-time
collection failure (if test is reverted but source isn't).

## Validation plan

- `uv run pytest tests/shared/test_runtime_tool.py -v` — all 10 test methods (7 existing
  + 3 new) pass.
- `rg -n "\.resource_scope\b|resource_scope=" tests/shared/test_runtime_tool.py` returns
  nothing (zero remaining singular-field references).

## Out of scope

`tests/shared/test_tool_spec.py`, `tests/shared/test_resource_scope.py`,
`tests/shared/test_runtime_tool_registry.py` (each has its own doc in this set).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-183049_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-194945
- Related target files: tests/shared/test_runtime_tool.py
