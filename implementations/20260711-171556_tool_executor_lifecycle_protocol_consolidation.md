# Implementation: Consolidate `LifecycleProtocol` into a single canonical definition

## Goal

Remove the byte-for-byte duplicate `LifecycleProtocol` class body in
`scripts/shared/tool_executor.py` and replace it with a re-export import from
`scripts/shared/tool_lifecycle.py`, so there is exactly one canonical definition
while preserving `from shared.tool_executor import LifecycleProtocol` as a working
import path for existing consumers.

## Scope

**In-Scope:**
- `scripts/shared/tool_executor.py`: delete the inline `class LifecycleProtocol(Protocol): ...`
  definition (currently at line 42) and replace it with
  `from shared.tool_lifecycle import LifecycleProtocol` placed among the file's
  existing import statements.
- Confirm whether `Protocol` (from `typing`) is still used elsewhere in the file;
  if not, remove the now-unused `Protocol` import from the `typing` import line.

**Out-of-Scope:**
- `scripts/shared/tool_lifecycle.py` — this is already the canonical source; not modified.
- `scripts/shared/tool_transport_invoker.py` — already imports `LifecycleProtocol` from
  `shared.tool_lifecycle`; unaffected, not modified.
- `repeated_tool_error_threshold` removal — handled in a separate phase/document
  (`tool_executor.py::__init__`), not this one.
- Test additions — handled in a separate phase/document
  (`tests/test_tool_executor_routing.py`).
- `docs/04_mcp_03_03_transport-and-health.md` — handled in a separate phase/document.

## Assumptions

1. `scripts/shared/tool_lifecycle.py:10-15` and `scripts/shared/tool_executor.py:42-47`
   contain byte-for-byte identical `LifecycleProtocol` Protocol class definitions (same
   docstring, same single `ensure_ready()` method signature) — confirmed by direct read
   in the plan.
2. `scripts/shared/tool_transport_invoker.py` already imports its copy from
   `shared.tool_lifecycle`, establishing `tool_lifecycle.py` as the natural canonical
   location.
3. `LifecycleProtocol` is used in `tool_executor.py` as a type annotation in at least
   three locations: the `__init__` parameter (`lifecycle: LifecycleProtocol | None = None`,
   line 65), the instance attribute assignment (`self._lifecycle: LifecycleProtocol | None`,
   line 78), and the `set_lifecycle()` method parameter (line 119). All three must continue
   to resolve correctly after the re-export.
4. No other module defines or duplicates `LifecycleProtocol` outside these two files
   (per the plan's Assumption 1).

## Implementation

### Target file

`scripts/shared/tool_executor.py`

### Procedure

1. Locate the inline `class LifecycleProtocol(Protocol): ...` definition (around line 42),
   including its docstring and `ensure_ready()` method.
2. Delete the entire class body.
3. Add `from shared.tool_lifecycle import LifecycleProtocol` to the file's existing
   import block, grouped with the other `from shared.<module> import ...` lines
   (alphabetical/isort-compatible ordering per `rules/coding.md`'s import-order rule).
4. Add a `# noqa: F401` suppression on the new import line with an inline justification
   (e.g. `# noqa: F401 — re-exported for backward compatibility with existing
   `from shared.tool_executor import LifecycleProtocol` consumers`), since the name is
   used only via type annotations elsewhere in the file and ruff may flag it as unused
   depending on how annotations are evaluated.
5. Search the file for any other use of `Protocol` (from `typing`) outside the deleted
   class. If none remain, remove `Protocol` from the `from typing import Any, Protocol`
   line, leaving `from typing import Any`. If `Protocol` is still used elsewhere, leave
   the import unchanged.
6. Verify all three existing usages of `LifecycleProtocol` (constructor parameter,
   instance attribute annotation, `set_lifecycle()` parameter) still reference the name
   correctly — no changes needed to these call sites since the imported name is
   identical to the deleted class name.

### Method

Replace:
```python
class LifecycleProtocol(Protocol):
    """Protocol for MCP server lifecycle managers injected into ToolExecutor."""

    async def ensure_ready(self, server_key: str) -> None:
        """Ensure the MCP server identified by server_key is ready to accept calls."""
        ...
```
with an import placed in the import block (not inline where the class used to be):
```python
from shared.tool_lifecycle import LifecycleProtocol  # noqa: F401 — re-exported for backward compatibility
```

### Details

- This is a pure re-export: the imported `LifecycleProtocol`'s shape (single
  `ensure_ready(server_key: str) -> None` async method) is identical to the deleted
  class, so no structural change occurs for any consumer — type checking behavior is
  unaffected.
- Do not rename `LifecycleProtocol` on import (no `as` alias) — the public name must
  stay identical so `from shared.tool_executor import LifecycleProtocol` continues to
  resolve to the same object mypy/pyright see when imported from `tool_lifecycle`.
- Keep the import in the file's top-level import block, not adjacent to where the old
  class body was (mid-file placement would violate the existing import-grouping
  convention and isort/ruff `I` rules).
- If ruff's `--fix` would otherwise strip the import as unused (F401), the inline
  `# noqa: F401` with justification is required per `rules/coding.md`'s suppression
  governance rule — a bare `# noqa` is prohibited.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/shared/tool_executor.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/tool_executor.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Manual | `PYTHONPATH=scripts uv run python -c "from shared.tool_executor import LifecycleProtocol as A; from shared.tool_lifecycle import LifecycleProtocol as B; assert A is B"` | Confirms true consolidation (object identity) independent of pytest |
| Regression | `uv run pytest tests/test_tool_executor.py tests/test_tool_executor_order.py tests/test_tool_executor_routing.py -v` | All pass; no test constructs `LifecycleProtocol` directly in a way broken by the re-export |
