# Implementation: Add `LifecycleProtocol` identity test

## Goal

Add a test to `tests/test_tool_executor_routing.py` that asserts
`shared.tool_executor.LifecycleProtocol` and `shared.tool_lifecycle.LifecycleProtocol`
are the same object (identity, not just structural equivalence), proving the
consolidation performed in the `LifecycleProtocol` phase is a true re-export rather
than a coincidentally-identical duplicate.

## Scope

**In-Scope:**
- `tests/test_tool_executor_routing.py`: add one new test function asserting object
  identity between the two import paths.
- Confirm the existing `from shared.tool_executor import LifecycleProtocol` import
  (line 24) still resolves correctly after the consolidation phase lands (it should,
  unchanged, since the re-export preserves the name).

**Out-of-Scope:**
- `scripts/shared/tool_executor.py` / `scripts/shared/tool_lifecycle.py` — no
  production code changes in this document; consolidation is handled in a separate
  phase/document.
- `docs/04_mcp_03_03_transport-and-health.md` — handled in a separate
  phase/document.
- Any other existing test in this file — unchanged; this is a purely additive test.

## Assumptions

1. `tests/test_tool_executor_routing.py` already has
   `from shared.tool_executor import LifecycleProtocol` at line 24, per the plan's
   Scope section — this import must continue to resolve after the consolidation phase.
2. The consolidation phase (separate document,
   `20260711-171556_tool_executor_lifecycle_protocol_consolidation.md`) lands before or
   together with this test, so that `shared.tool_executor.LifecycleProtocol` is the
   re-exported object from `shared.tool_lifecycle` by the time this test runs. If the
   consolidation phase has not yet landed, this test will fail (two distinct classes,
   not identical objects) — this is the correct, intended failure mode proving the test
   is meaningful.
3. `shared.tool_lifecycle.LifecycleProtocol` is importable without circular-import
   concerns from a test module (both are `shared` layer per the import-layer contract
   in `AGENTS.md`; tests may import any layer).

## Implementation

### Target file

`tests/test_tool_executor_routing.py`

### Procedure

1. Confirm the file's existing imports; the module-level
   `from shared.tool_executor import LifecycleProtocol` (line 24) may remain as-is,
   or the new test can perform its own local imports (matching the plan's Design
   section, which favors local imports within the test function for clarity of what
   is being compared).
2. Add a new test function, e.g. `test_lifecycle_protocol_is_canonical_reexport()`,
   placed in a logical location in the file (near other `LifecycleProtocol`-related
   tests if any exist, otherwise near the top-level fixture/import-related tests).
3. Inside the test, import `LifecycleProtocol` from both `shared.tool_executor` and
   `shared.tool_lifecycle` (using distinct local aliases to avoid name collision), and
   assert they are the identical object using `is`.
4. Do not modify, reorder, or remove any existing test in the file.

### Method

```python
def test_lifecycle_protocol_is_canonical_reexport() -> None:
    from shared.tool_executor import LifecycleProtocol as ExecutorLP
    from shared.tool_lifecycle import LifecycleProtocol as CanonicalLP

    assert ExecutorLP is CanonicalLP
```

### Details

- Use `is` (object identity), not `==` or structural/shape comparison — the entire
  point of this test is to prove there is exactly one class object shared between both
  import paths, not two independently-defined-but-identically-shaped classes.
- Local imports inside the test function (rather than relying solely on the
  module-level import at line 24) make the comparison self-documenting: the test reads
  clearly as "these two import paths yield the same object" without requiring the
  reader to cross-reference the file's top-of-file imports.
- No fixture or mock needed — this is a pure import-time assertion with no I/O or
  side effects.
- Test name follows the existing snake_case `test_<subject>_<behavior>` convention
  used elsewhere in the file.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_tool_executor_routing.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/tool_executor.py` | No new errors (test file itself is covered by pre-commit's mypy run per `rules/coding.md`) |
| Tests | `uv run pytest tests/test_tool_executor_routing.py -v` | All pass, including the new `test_lifecycle_protocol_is_canonical_reexport` test |
| Manual | `PYTHONPATH=scripts uv run python -c "from shared.tool_executor import LifecycleProtocol as A; from shared.tool_lifecycle import LifecycleProtocol as B; assert A is B"` | Confirms identity independent of pytest, matching the plan's Validation plan table |
