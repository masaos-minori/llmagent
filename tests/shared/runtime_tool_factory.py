"""tests/shared/runtime_tool_factory.py
Shared test-only builder for RuntimeTool fixtures.

Single home for the permissive defaults that tests used to spell per call site.
Production code must import only `build_runtime_tool`; the import-linter
contract in `.importlinter` enforces this boundary at lint time.

`build_runtime_tool` itself has no defaults for the required field set, so the
fixture defaults for the policy fields live only here. Every fixture default is
the most conservative closed-set value for its dimension: no default lowers risk.
"""

from __future__ import annotations

from typing import Any

from shared.runtime_tool import RuntimeTool, build_runtime_tool
from shared.tool_metadata import TOOL_FIELD_SET_VERSION


def build_fixture_runtime_tool(
    name: str, server_key: str, **kwargs: Any
) -> RuntimeTool:
    """Build a RuntimeTool fixture with the required fields filled conservatively.

    Faithful to the pre-strict `build_runtime_tool` behavior:
        - `is_write` defaults to `False` when omitted or `None`.
        - `requires_serial` replicates the legacy derivation `_or_default(
          requires_serial, is_write is None)`: `True` when `is_write` was omitted,
          `False` when it was supplied, unless explicitly passed.
        - `resource_scope_kind` defaults to `""` (the legacy signature default).
        - `resource_scope_keys` defaults to `{}` (empty mapping).
        - `agent_safety_tier` defaults to `"WRITE_DANGEROUS"` (legacy most-conservative default).

    Policy-field defaults are the highest-risk/most-restrictive value of each
    closed set, so a fixture can never look safer than a real declaration:
        - `side_effect_class` → `"external_write"`, `retry_policy` → `"never"`,
          `reconciliation_policy` → `"external_state"`, `idempotency_required` → True,
          `preview_capability` → `"none"`, `policy_version` → `TOOL_FIELD_SET_VERSION`.

    Call sites that already passed explicit values keep them via `kwargs`.
    """
    fields: dict[str, Any] = {"name": name, "server_key": server_key}
    fields.update(kwargs)
    is_write_omitted = "is_write" not in fields or fields["is_write"] is None
    fields["is_write"] = False if is_write_omitted else fields["is_write"]
    fields.setdefault("requires_serial", is_write_omitted)
    fields.setdefault("resource_scope_kind", "")
    fields.setdefault("resource_scope_keys", {})
    fields.setdefault("agent_safety_tier", "WRITE_DANGEROUS")
    fields.setdefault("side_effect_class", "external_write")
    fields.setdefault("retry_policy", "never")
    fields.setdefault("reconciliation_policy", "external_state")
    fields.setdefault("idempotency_required", True)
    fields.setdefault("preview_capability", "none")
    fields.setdefault("policy_version", TOOL_FIELD_SET_VERSION)
    return build_runtime_tool(**fields)
