"""tests/test_llm_partial_completion.py
Verify partial LLM completions never enter ctx.conv.history.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock


def _make_transport_error(
    partial_text: str = "partial output", kind: str = "PREMATURE_EOF"
):
    from shared.llm_exceptions import LLMTransportError

    return LLMTransportError(
        kind=kind,  # type: ignore[arg-type]
        phase="in_stream",
        url="http://localhost/llm",
        partial_text=partial_text,
    )


def _make_ctx(history: list | None = None):
    """Minimal AgentContext mock for partial completion tests."""
    if history is None:
        history = []
    llm = SimpleNamespace(stat_partial_completions=0)
    services = SimpleNamespace(llm=llm)
    session = SimpleNamespace(session_id="test-sess-1")
    stats = SimpleNamespace(stat_turns=1, stat_partial_completions=0)

    conv = SimpleNamespace(history=history)

    return SimpleNamespace(
        session=session,
        stats=stats,
        services_required=services,
        conv=conv,
    )


def _make_diagnostic_store():
    ds = MagicMock()
    ds.save = MagicMock()
    ds.save_partial_completion = MagicMock()
    return ds


# ── history invariant ─────────────────────────────────────────────────────────


def test_partial_completion_does_not_append_to_history() -> None:
    from agent.llm_transport_errors import handle_partial_completion

    ctx = _make_ctx(history=[{"role": "user", "content": "hello"}])
    initial_len = len(ctx.conv.history)
    e = _make_transport_error(partial_text="partial output")
    handle_partial_completion(e, ctx, _make_diagnostic_store())
    assert len(ctx.conv.history) == initial_len


def test_partial_completion_empty_history_stays_empty() -> None:
    from agent.llm_transport_errors import handle_partial_completion

    ctx = _make_ctx(history=[])
    e = _make_transport_error(partial_text="partial output")
    handle_partial_completion(e, ctx, _make_diagnostic_store())
    assert ctx.conv.history == []


# ── diagnostic store ──────────────────────────────────────────────────────────


def test_partial_completion_writes_session_diagnostics() -> None:
    from agent.llm_transport_errors import handle_partial_completion

    ctx = _make_ctx()
    ds = _make_diagnostic_store()
    e = _make_transport_error(partial_text="partial output")
    handle_partial_completion(e, ctx, ds)
    assert ds.save.called
    call_args = ds.save.call_args
    assert "llm_transport_error" in call_args[0][1]


def test_partial_completion_calls_save_partial_completion() -> None:
    from agent.llm_transport_errors import handle_partial_completion

    ctx = _make_ctx()
    ds = _make_diagnostic_store()
    e = _make_transport_error(partial_text="partial output")
    handle_partial_completion(e, ctx, ds)
    ds.save_partial_completion.assert_called_once()


# ── stat counter ──────────────────────────────────────────────────────────────


def test_partial_completion_increments_stat() -> None:
    from agent.llm_transport_errors import handle_partial_completion

    ctx = _make_ctx()
    before = ctx.services_required.llm.stat_partial_completions
    e = _make_transport_error(partial_text="partial output")
    handle_partial_completion(e, ctx, _make_diagnostic_store())
    assert ctx.services_required.llm.stat_partial_completions == before + 1


# ── non-partial error ─────────────────────────────────────────────────────────


def test_non_partial_error_does_not_modify_history() -> None:
    from agent.llm_transport_errors import handle_non_partial_error

    ctx = _make_ctx(history=[{"role": "user", "content": "hello"}])
    initial_len = len(ctx.conv.history)
    e = _make_transport_error(partial_text="", kind="CONNECT_ERROR")
    handle_non_partial_error(e, ctx, _make_diagnostic_store())
    assert len(ctx.conv.history) == initial_len


def test_non_partial_error_writes_mid_turn_error() -> None:
    from agent.llm_transport_errors import handle_non_partial_error

    ctx = _make_ctx()
    ds = _make_diagnostic_store()
    e = _make_transport_error(partial_text="", kind="CONNECT_ERROR")
    handle_non_partial_error(e, ctx, ds)
    ds.save.assert_called_once()
    call_args = ds.save.call_args
    assert "mid_turn_error" in call_args[0][1]


# ── router ────────────────────────────────────────────────────────────────────


def test_handle_llm_transport_error_routes_partial() -> None:
    from agent.llm_transport_errors import handle_llm_transport_error

    ctx = _make_ctx()
    e = _make_transport_error(partial_text="some partial text")
    result = handle_llm_transport_error(e, ctx, _make_diagnostic_store())
    assert result is True
    assert ctx.services_required.llm.stat_partial_completions == 1


def test_handle_llm_transport_error_routes_non_partial() -> None:
    from agent.llm_transport_errors import handle_llm_transport_error

    ctx = _make_ctx()
    ds = _make_diagnostic_store()
    e = _make_transport_error(partial_text="", kind="CONNECT_ERROR")
    result = handle_llm_transport_error(e, ctx, ds)
    assert result is False
