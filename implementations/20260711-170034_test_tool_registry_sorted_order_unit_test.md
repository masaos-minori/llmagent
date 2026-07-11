# Implementation Procedure: get_tool_names() sorted-order unit test (tests/test_tool_registry.py)

## Goal

Add a direct unit test proving that `ToolRegistry.get_tool_names()` enforces sorted-order output
itself — independent of caller/registration order — so the guarantee added in Phase 1
(`scripts/shared/tool_registry.py`) is locked in by a regression test rather than only inferred from
the default registry's already-sorted registration behavior.

## Scope

**In-Scope:**
- `tests/test_tool_registry.py`: add one new unit test, `test_get_tool_names_returns_sorted_order`
  (or equivalently named), that registers tools to a fresh `ToolRegistry()` in deliberately
  *non*-sorted order and asserts `get_tool_names()` returns them sorted.

**Out-of-Scope:**
- `tests/test_tool_registry_counts.py` — covered by a separate doc (per-server snapshot tests)
- Any change to `ToolRegistry`, `ToolDefinition`, or `_reset_registry_for_testing` / `get_registry`
- Existing test classes in this file (`TestValidateRoutingDriftRegistry` etc.) — unchanged

## Assumptions

- This test targets the plain `ToolRegistry` class directly (not the global singleton via
  `get_registry()`), matching this file's existing pattern of constructing `ToolRegistry()` instances
  directly for unit-level tests (see `TestValidateRoutingDriftRegistry` tests, which build fresh
  `ToolRegistry()` instances rather than using the singleton).
- `ToolDefinition` requires only `name` and `server_key` for registration (per its dataclass
  definition — `description` and `input_schema` default to `""` / `{}`).
- This test depends on Phase 1's change (`get_tool_names()` returning `sorted(...)`) already being
  applied; if run before Phase 1, this test is expected to fail, which is the intended regression
  check.

## Implementation

### Target file

`tests/test_tool_registry.py`

### Procedure

1. Add a new top-level test function (or a method in a small new test class, matching whichever style
   keeps it near related tests — this file already mixes bare functions are not present; existing
   tests are class-based, so prefer adding it as a method in a new small class, e.g.
   `TestGetToolNamesOrdering`, for consistency with the rest of the file).
2. In the test body:
   - Construct a fresh `registry = ToolRegistry()`.
   - Register three `ToolDefinition` instances under the same `server_key` (e.g. `"s1"`) in
     deliberately non-alphabetical order: `"zebra"`, `"apple"`, `"mango"`.
   - Assert `registry.get_tool_names("s1") == ["apple", "mango", "zebra"]`.
3. No fixture or mock needed — `ToolDefinition` and `ToolRegistry` are already imported at the top of
   this file (lines 14-19).

### Method

Single, self-contained unit test function/method — no I/O, no singleton registry, no reset needed
(uses a locally constructed `ToolRegistry()` instance, so `_reset_registry_for_testing()` is not
required for this specific test).

### Details

Illustrative structure (signature/pseudocode only — do not write this code in this design step):

```python
class TestGetToolNamesOrdering:
    def test_get_tool_names_returns_sorted_order(self) -> None:
        registry = ToolRegistry()
        registry.register(ToolDefinition(name="zebra", server_key="s1"))
        registry.register(ToolDefinition(name="apple", server_key="s1"))
        registry.register(ToolDefinition(name="mango", server_key="s1"))
        assert registry.get_tool_names("s1") == ["apple", "mango", "zebra"]
```

Notes for the implementer:
- The deliberate non-sorted registration order is the point of the test: it proves the guarantee is
  enforced by `get_tool_names()` itself, not merely inherited from a caller that happens to insert in
  sorted order (directly targeting the plan's concern about undocumented, accidental ordering).
- Do not use the global singleton (`get_registry()`) for this test — a fresh `ToolRegistry()` avoids
  any interaction with the default registry's own (already-sorted) registration order and isolates the
  guarantee under test.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_tool_registry.py` | 0 errors |
| Tests | `uv run pytest tests/test_tool_registry.py -v` | All pass, including the new sorted-order test |
| Regression | `uv run pytest tests/test_routing_duplicate_ownership.py tests/test_startup_routing_drift.py tests/test_github_tool_registry.py tests/test_mdq_routing.py -q` | No new failures |
