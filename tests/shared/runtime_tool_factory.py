"""tests/shared/runtime_tool_factory.py
Shared test-only builder for RuntimeTool fixtures.

Single home for the permissive defaults that tests used to spell per call site.
Production code must import only `build_runtime_tool`; the import-linter
contract in `.importlinter` enforces this boundary at lint time.
"""

from __future__ import annotations

from typing import Any

from shared.runtime_tool import RuntimeTool, build_runtime_tool


def build_fixture_runtime_tool(
    name: str, server_key: str, **kwargs: Any
) -> RuntimeTool:
    """Build a RuntimeTool fixture replicating the legacy permissive defaults.

    Faithful to the pre-strict `build_runtime_tool` behavior:
        - `is_write` defaults to `False` when omitted or `None`.
        - `requires_serial` replicates the legacy derivation `_or_default(
          requires_serial, is_write is None)`: `True` when `is_write` was omitted,
          `False` when it was supplied, unless explicitly passed.
        - `resource_scope_kind` defaults to `""` (the legacy signature default).
        - `resource_scope_keys` defaults to `()`.

    Call sites that already passed explicit values keep them via `kwargs`.
    """
    fields: dict[str, Any] = {"name": name, "server_key": server_key}
    fields.update(kwargs)
    is_write_omitted = "is_write" not in fields or fields["is_write"] is None
    fields["is_write"] = False if is_write_omitted else fields["is_write"]
    fields.setdefault("requires_serial", is_write_omitted)
    fields.setdefault("resource_scope_kind", "")
    fields.setdefault("resource_scope_keys", ())
    return build_runtime_tool(**fields)
