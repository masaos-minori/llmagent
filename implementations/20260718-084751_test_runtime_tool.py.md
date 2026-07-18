# Implementation procedure: `tests/shared/test_runtime_tool.py` (capabilities field test cases)

Source plan: `plans/20260717-131133_plan.md` ("Define MCP tool capability naming convention",
requirement `requires/20260717_13_require.md`), Implementation step 5 (validation plan row "`RuntimeTool`
accepts optional capabilities").

**Relationship to the existing doc for this file**: `implementations/20260717-203244_test_runtime_tool.py.md`
(requirement 02's base test doc) designs `tests/shared/test_runtime_tool.py` as a wholly new file covering
the original 13-field `RuntimeTool`/`build_runtime_tool()` shape — it does not mention `capabilities`
anywhere (confirmed by re-read). This doc adds two additional test methods to the same `TestRuntimeTool`
class the base doc defines; it does not re-specify the base doc's existing test methods.

## Goal

Extend `tests/shared/test_runtime_tool.py`'s `TestRuntimeTool` class (per the base test doc) with test
coverage for the new `capabilities` field added to `RuntimeTool`/`build_runtime_tool()`
(`implementations/20260718-084710_runtime_tool.py.md`): (a) a tool built with no `capabilities` argument
defaults to `()`, and (b) a tool built with an explicit sequence of capability strings stores them,
normalized to a tuple.

## Scope

**In scope**: two new test methods appended to `tests/shared/test_runtime_tool.py`'s `TestRuntimeTool`
class.

**Out of scope**: any change to the base doc's existing 6 test methods
(`test_construct_with_full_annotation`, `test_safe_defaults_when_unannotated`,
`test_requires_serial_false_when_is_write_explicitly_false`,
`test_requires_serial_explicit_override_wins`, `test_is_frozen`,
`test_input_schema_and_raw_definition_default_to_empty_dict_not_shared_object`) — all unaffected by this
addition; `tests/shared/test_runtime_tool_registry.py` (separate file, `capabilities` is out of scope for
`RuntimeToolRegistry` per `implementations/20260718-084710_runtime_tool.py.md`'s Scope).

## Assumptions

1. Follows the same style already established by the base test doc (Assumption 1 there, confirmed against
   `tests/shared/test_tool_result_cache.py`): class-based `TestRuntimeTool`, plain `assert` statements, no
   `conftest.py` fixtures needed.
2. `capabilities` accepts any `Sequence[str]` at the factory boundary and is stored as a `tuple[str, ...]`
   on the frozen instance (per `implementations/20260718-084710_runtime_tool.py.md`'s Procedure step 3) —
   tests must confirm a `list[str]` input is normalized to a `tuple` on the resulting `RuntimeTool`
   instance, not merely stored as whatever type was passed in (this is the one behavior worth explicitly
   asserting, since it is the one piece of normalization logic this field addition introduces).
3. No test for invalid capability-string shape (e.g. a string not matching `domain.action`) is added — per
   the paired production doc's Assumption 4, no runtime validation of capability string shape exists, so a
   test asserting a rejection would fail against the intended (permissive) implementation.

## Implementation

### Target file

`tests/shared/test_runtime_tool.py` (extension of the base doc's new file — implement both docs together
against the same file).

### Procedure

1. Add `test_capabilities_default_to_empty_tuple_when_unannotated(self) -> None` to `TestRuntimeTool`,
   placed after the base doc's `test_safe_defaults_when_unannotated`.
2. Add `test_capabilities_stored_as_tuple_when_provided(self) -> None` to `TestRuntimeTool`, placed
   immediately after the previous new method.
3. No new imports needed beyond what the base doc already imports (`RuntimeTool`, `build_runtime_tool`) —
   `capabilities` is exercised purely through the existing factory/dataclass surface.

### Method

Same as the base doc: pytest class-based tests, plain `assert`, no new fixtures or helpers required beyond
the base doc's existing `_minimal_kwargs()` (used as-is, extended inline with a `capabilities=` keyword
where each new test needs it).

### Details

Test methods (pseudocode — no production code):

```
class TestRuntimeTool:
    # ... existing 6 methods per implementations/20260717-203244_test_runtime_tool.py.md ...

    def test_capabilities_default_to_empty_tuple_when_unannotated(self) -> None:
        # tool = build_runtime_tool(name="unknown_tool", server_key="srv")
        # assert tool.capabilities == ()

    def test_capabilities_stored_as_tuple_when_provided(self) -> None:
        # tool = build_runtime_tool(
        #     name="delete_file", server_key="fs",
        #     capabilities=["filesystem.delete", "filesystem.write"],  # list input
        # )
        # assert tool.capabilities == ("filesystem.delete", "filesystem.write")
        # assert isinstance(tool.capabilities, tuple)  # normalized from list, not stored as-is
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Run tests | `uv run pytest tests/shared/test_runtime_tool.py -v` | all pass, including the 2 new capabilities cases and the base doc's existing 6 |
| Lint | `uv run ruff check tests/shared/test_runtime_tool.py` | 0 errors |
| Type check | `uv run mypy tests/shared/test_runtime_tool.py` | 0 errors |
| Full suite | `uv run pytest -v` | no new failures |
| Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | ≥90% on changed lines |
