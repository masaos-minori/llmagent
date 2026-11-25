"""tests/mcp_servers/test_execution_context.py

Contract tests for mcp_servers/execution_context.py: the typed context, the
header cross-check, and the preview-capability injection seam.
"""

from __future__ import annotations

import dataclasses

import pytest
from mcp_servers.execution_context import (
    ExecutionContext,
    ExecutionContextError,
    build_execution_context,
    configure_tool_preview_capabilities,
)

_CAPABLE_ENTRY = {"name": "write_file", "preview_capability": "dry_run"}
_INCAPABLE_ENTRY = {"name": "read_text_file", "preview_capability": "none"}


@pytest.fixture(autouse=True)
def _reset_preview_capabilities() -> None:
    """Each test declares its own seam state; an empty iterable resets it."""
    configure_tool_preview_capabilities(())


def _build(args: dict, header_mode: str = "") -> ExecutionContext:
    return build_execution_context(
        "write_file",
        args,
        session_id="sess-1",
        request_id="req-1",
        idempotency_key=" key-1 ",
        header_mode=header_mode,
    )


class TestExecutionContextShape:
    def test_fields_and_stripped_key(self) -> None:
        ctx = ExecutionContext(
            request_id="req-1",
            session_id="sess-1",
            idempotency_key="  key-1  ",
            execution_mode="applied",
        )
        assert ctx.idempotency_key == "key-1"
        assert (ctx.request_id, ctx.session_id, ctx.execution_mode) == (
            "req-1",
            "sess-1",
            "applied",
        )

    def test_stays_frozen(self) -> None:
        ctx = ExecutionContext("req-1", "sess-1", "key-1", "applied")
        with pytest.raises(dataclasses.FrozenInstanceError):
            ctx.execution_mode = "preview"  # type: ignore[misc] — frozen dataclass field write; the runtime FrozenInstanceError guard blocks it, which this assertion verifies.


class TestBuilderWithHeader:
    def test_agreeing_header_is_accepted(self) -> None:
        configure_tool_preview_capabilities((_CAPABLE_ENTRY,))
        ctx = _build({"dry_run": True}, header_mode="preview")
        assert ctx.execution_mode == "preview"

    def test_empty_header_accepts_the_resolved_mode(self) -> None:
        configure_tool_preview_capabilities((_CAPABLE_ENTRY,))
        ctx = _build({"dry_run": True})
        assert ctx.execution_mode == "preview"

    def test_disagreeing_header_raises(self) -> None:
        configure_tool_preview_capabilities((_CAPABLE_ENTRY,))
        with pytest.raises(ExecutionContextError) as excinfo:
            _build({"dry_run": True}, header_mode="applied")
        assert "write_file" in str(excinfo.value)
        assert "disagrees" in str(excinfo.value)

    def test_unknown_header_raises(self) -> None:
        with pytest.raises(ExecutionContextError) as excinfo:
            _build({}, header_mode="no_op")
        assert "outside" in str(excinfo.value)

    def test_error_text_does_not_echo_argument_values(self) -> None:
        configure_tool_preview_capabilities((_CAPABLE_ENTRY,))
        with pytest.raises(ExecutionContextError) as excinfo:
            _build({"dry_run": True, "path": "secret-value"}, header_mode="applied")
        assert "secret-value" not in str(excinfo.value)


class TestResolverThroughTheBuilder:
    def test_non_bool_dry_run_on_capable_tool_raises_the_context_error(self) -> None:
        configure_tool_preview_capabilities((_CAPABLE_ENTRY,))
        with pytest.raises(ExecutionContextError):
            _build({"dry_run": "true"})

    def test_unconfigured_map_resolves_applied(self) -> None:
        ctx = _build({"dry_run": True})
        assert ctx.execution_mode == "applied"

    def test_configure_skips_entries_without_a_name(self) -> None:
        configure_tool_preview_capabilities(
            ({"preview_capability": "dry_run"}, _CAPABLE_ENTRY, _INCAPABLE_ENTRY)
        )
        assert _build({"dry_run": True}).execution_mode == "preview"
        assert _build({"dry_run": False}).execution_mode == "applied"

    def test_empty_iterable_resets_the_set(self) -> None:
        configure_tool_preview_capabilities((_CAPABLE_ENTRY,))
        configure_tool_preview_capabilities(())
        assert _build({"dry_run": True}).execution_mode == "applied"


class TestProgrammaticCall:
    def test_empty_ids_and_resolved_mode(self) -> None:
        configure_tool_preview_capabilities((_CAPABLE_ENTRY,))
        ctx = ExecutionContext.for_programmatic_call("write_file", {"dry_run": True})
        assert ctx.request_id == ""
        assert ctx.session_id == ""
        assert ctx.execution_mode == "preview"

    def test_key_is_stripped(self) -> None:
        ctx = ExecutionContext.for_programmatic_call(
            "read_text_file", {}, idempotency_key=" key-2 "
        )
        assert ctx.idempotency_key == "key-2"
        assert ctx.execution_mode == "applied"
