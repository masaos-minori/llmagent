"""scripts/mcp_servers/execution_context.py — Typed execution context for MCP calls.

The context carries the logical-call identity the dispatcher needs: the request
and session ids, the idempotency key, and the execution mode resolved from the
validated arguments plus the tool's declared preview capability.

The mode is resolved here, never read from the header: the header is a
cross-check, so a disagreement between the caller's claim and the resolver's
answer is an error rather than a silent override.

The preview-capability map is injected once at the bootstrap seam next to the
retry-policy map; an unconfigured map resolves every call to ``applied``, the
safe direction. This module imports nothing from ``mcp_servers.server`` or
``mcp_servers.dispatch``: both import it, so there is no cycle.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from shared.execution_mode import ExecutionMode, resolve_execution_mode

# Header values a caller may claim. "no_op" is a dispatcher outcome, never an
# input-derived claim, so it is not accepted here.
_HEADER_MODES: frozenset[str] = frozenset({"preview", "applied"})

_preview_capable_tools: set[str] = set()


class ExecutionContextError(ValueError):
    """Raised when a claimed header mode disagrees with the resolved mode."""


@dataclass(frozen=True)
class ExecutionContext:
    """Immutable per-call context handed to the dispatcher."""

    request_id: str
    session_id: str
    idempotency_key: str = field(default="")
    execution_mode: ExecutionMode = "applied"

    def __post_init__(self) -> None:
        # The key is stored stripped so a padded value from a header or a tool
        # argument compares identically to the same key without padding.
        object.__setattr__(self, "idempotency_key", self.idempotency_key.strip())

    @classmethod
    def for_programmatic_call(
        cls, tool: str, args: Mapping[str, object], idempotency_key: str = ""
    ) -> ExecutionContext:
        """Build a context for a programmatic call with no HTTP request identity."""
        mode = resolve_execution_mode(tool, args, tool in _preview_capable_tools)
        return cls(
            request_id="",
            session_id="",
            idempotency_key=idempotency_key,
            execution_mode=mode,
        )


def configure_tool_preview_capabilities(
    entries: Iterable[Mapping[str, object]],
) -> None:
    """Inject this process's declared preview capability (bootstrap seam).

    Only entries with a name and ``preview_capability == "dry_run"`` are
    recorded. The set is replaced wholesale on each call, so a test can reset it
    with an empty iterable.
    """
    global _preview_capable_tools
    _preview_capable_tools = {
        str(entry["name"])
        for entry in entries
        if entry.get("name") and entry.get("preview_capability") == "dry_run"
    }


def build_execution_context(
    tool: str,
    args: Mapping[str, object],
    session_id: str,
    request_id: str,
    idempotency_key: str,
    header_mode: str,
) -> ExecutionContext:
    """Resolve the mode and cross-check it against the claimed header mode.

    An empty ``header_mode`` means the caller claimed nothing and the resolved
    mode stands. A claim outside the input-derived modes, or one that differs
    from the resolved mode, is rejected. Argument values are never echoed into
    the error text: the message names the tool and the disagreement only.

    Raises:
        ExecutionContextError: the claim is unknown or disagrees with the
            resolver, or the resolver rejected a malformed ``dry_run``.
    """
    try:
        mode = resolve_execution_mode(tool, args, tool in _preview_capable_tools)
    except ValueError as exc:
        raise ExecutionContextError(str(exc)) from exc

    if not header_mode:
        return ExecutionContext(
            request_id=request_id,
            session_id=session_id,
            idempotency_key=idempotency_key,
            execution_mode=mode,
        )
    if header_mode not in _HEADER_MODES:
        raise ExecutionContextError(
            f"tool {tool}: X-Execution-Mode claim is outside the input-derived modes"
        )
    if header_mode != mode:
        raise ExecutionContextError(
            f"tool {tool}: X-Execution-Mode claim disagrees with the resolved mode"
        )
    return ExecutionContext(
        request_id=request_id,
        session_id=session_id,
        idempotency_key=idempotency_key,
        execution_mode=mode,
    )
