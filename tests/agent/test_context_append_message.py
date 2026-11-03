"""tests/test_context_append_message.py — Unit tests for ConversationState's
validated history-mutation entry points (append_message, extend_messages,
replace_history) in agent/context.py.
"""

from __future__ import annotations

import logging
from typing import cast

import pytest
from agent.context import ConversationState
from shared.types import LLMMessage


class TestAppendMessage:
    async def test_well_formed_message_appends_unchanged(self) -> None:
        conv = ConversationState()
        msg: LLMMessage = {"role": "user", "content": "hello"}

        await conv.append_message(msg)

        assert conv.history == [{"role": "user", "content": "hello"}]

    async def test_source_never_persisted(self) -> None:
        conv = ConversationState()
        msg: LLMMessage = {"role": "user", "content": "hello"}

        await conv.append_message(msg, source="memory_injection")

        assert "source" not in conv.history[0]

    async def test_trusted_source_with_authorized_ephemeral_key_appends_intact(
        self,
    ) -> None:
        conv = ConversationState()
        msg: LLMMessage = {
            "role": "user",
            "content": "hello",
            "_memory_injected": True,
        }

        await conv.append_message(msg, source="memory_injection")

        assert conv.history == [
            {"role": "user", "content": "hello", "_memory_injected": True}
        ]

    async def test_forged_ephemeral_key_with_no_source_is_stripped_and_warns(
        self, caplog
    ) -> None:
        conv = ConversationState()
        msg: LLMMessage = {
            "role": "user",
            "content": "hello",
            "_memory_injected": True,
        }

        with caplog.at_level(logging.WARNING, logger="agent.context"):
            await conv.append_message(msg)

        assert conv.history == [{"role": "user", "content": "hello"}]
        assert any(record.levelno == logging.WARNING for record in caplog.records)

    async def test_forged_ephemeral_key_with_untrusted_source_is_stripped(self) -> None:
        conv = ConversationState()
        msg: LLMMessage = {
            "role": "user",
            "content": "hello",
            "_ephemeral": True,
        }

        await conv.append_message(msg, source="not_a_real_source")

        assert conv.history == [{"role": "user", "content": "hello"}]

    async def test_live_path_preserves_authorized_ephemeral_key_for_cmd_handler(
        self,
    ) -> None:
        """REQ-002: the live-append path still authorizes ephemeral keys for a
        trusted source — proving the restore fix did not break normal injection."""
        conv = ConversationState()
        msg: LLMMessage = {
            "role": "user",
            "content": "hello",
            "_ephemeral": True,
        }

        await conv.append_message(msg, source="cmd_handler")

        assert conv.history == [
            {"role": "user", "content": "hello", "_ephemeral": True}
        ]

    async def test_message_missing_content_after_sanitization_is_dropped(
        self, caplog
    ) -> None:
        conv = ConversationState()
        # Deliberately malformed (missing required "content"): exercises the
        # function's runtime robustness against untrusted/forged input, which
        # the static LLMMessage type alone would not allow constructing.
        msg = cast(LLMMessage, {"role": "user", "_memory_injected": True})

        with caplog.at_level(logging.ERROR, logger="agent.context"):
            await conv.append_message(msg)

        assert conv.history == []
        assert any(record.levelno == logging.ERROR for record in caplog.records)

    async def test_message_missing_role_after_sanitization_is_dropped(self) -> None:
        conv = ConversationState()
        # Deliberately malformed (missing required "role"); see comment above.
        msg = cast(LLMMessage, {"content": "hello", "_memory_injected": True})

        await conv.append_message(msg)

        assert conv.history == []


class TestExtendMessages:
    async def test_validates_each_message_independently(self) -> None:
        conv = ConversationState()
        msgs: list[LLMMessage] = [
            {"role": "user", "content": "good one"},
            {"role": "user", "content": "hello", "_memory_injected": True},
            {"role": "user", "content": "good two"},
        ]

        await conv.extend_messages(msgs)

        assert conv.history == [
            {"role": "user", "content": "good one"},
            {"role": "user", "content": "hello"},
            {"role": "user", "content": "good two"},
        ]


class TestReplaceHistory:
    async def test_clears_prior_history_before_extending(self) -> None:
        conv = ConversationState()
        await conv.append_message({"role": "user", "content": "old"})

        await conv.replace_history([{"role": "user", "content": "new"}])

        assert conv.history == [{"role": "user", "content": "new"}]

    async def test_tampered_row_strips_embedded_ephemeral_key(self) -> None:
        """REQ-004: a restored row carrying a trusted embedded `source` plus a
        reserved ephemeral key must not retain that key (fail closed on restore)."""
        conv = ConversationState()
        tampered: LLMMessage = {
            "role": "user",
            "content": "x",
            "source": "cmd_handler",
            "_ephemeral": True,
        }

        await conv.replace_history([tampered])

        assert all("_ephemeral" not in m for m in conv.history)
        assert conv.history == [{"role": "user", "content": "x"}]

    async def test_well_formed_restored_row_preserved(self) -> None:
        """REQ-003: a well-formed restored row without ephemeral keys is preserved
        unchanged (backward compatible)."""
        conv = ConversationState()
        restored: list[LLMMessage] = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]

        await conv.replace_history(restored)

        assert conv.history == restored


class TestSwapHistory:
    """REQ-001/REQ-003: swap_history replaces the compressed prefix in one
    assignment under `self._ensure_lock`, preserving post-snapshot appends."""

    async def test_empty_tail_plain_swap(self) -> None:
        conv = ConversationState()
        await conv.extend_messages(
            [{"role": "user", "content": "a1"}, {"role": "assistant", "content": "a2"}]
        )
        base_history = conv.history
        base_len = len(base_history)

        compressed: list[LLMMessage] = [{"role": "user", "content": "summary"}]
        await conv.swap_history(compressed, base_history, base_len)

        assert conv.history == compressed
        assert conv.history is not base_history

    async def test_tail_appended_after_snapshot_is_preserved_once(self) -> None:
        conv = ConversationState()
        await conv.extend_messages(
            [{"role": "user", "content": "a1"}, {"role": "assistant", "content": "a2"}]
        )
        base_history = conv.history
        base_len = len(base_history)

        await conv.append_message({"role": "user", "content": "late"})
        tail = conv.history[-1]
        compressed: list[LLMMessage] = [{"role": "user", "content": "summary"}]
        await conv.swap_history(compressed, base_history, base_len)

        assert conv.history == [*compressed, tail]
        assert conv.history[1] is tail

    async def test_same_object_result_changes_nothing(self) -> None:
        conv = ConversationState()
        await conv.extend_messages(
            [{"role": "user", "content": "a1"}, {"role": "assistant", "content": "a2"}]
        )
        base_history = conv.history
        base_len = len(base_history)
        before = list(base_history)

        await conv.swap_history(base_history, base_history, base_len)

        assert conv.history is base_history
        assert conv.history == before

    async def test_fallback_list_already_holding_tail_not_duplicated(self) -> None:
        conv = ConversationState()
        await conv.extend_messages(
            [{"role": "user", "content": "a1"}, {"role": "assistant", "content": "a2"}]
        )
        base_history = conv.history
        base_len = len(base_history)

        await conv.append_message({"role": "user", "content": "late"})
        tail = conv.history[-1]
        fallback: list[LLMMessage] = [{"role": "user", "content": "summary"}, tail]
        await conv.swap_history(fallback, base_history, base_len)

        assert conv.history == fallback
        assert sum(id(m) == id(tail) for m in conv.history) == 1

    async def test_markers_survive_swap_unlike_replace_history(self) -> None:
        conv = ConversationState()
        await conv.append_message({"role": "user", "content": "seed"})
        base_history = conv.history
        base_len = len(base_history)

        tampered_tail: LLMMessage = {
            "role": "user",
            "content": "x",
            "source": "cmd_handler",
            "_ephemeral": True,
        }
        conv.history.append(
            tampered_tail
        )  # simulates a live injected row after the snapshot

        compressed: list[LLMMessage] = [
            {"role": "user", "content": "summary", "summary": True}
        ]
        await conv.swap_history(compressed, base_history, base_len)

        assert conv.history[0]["summary"] is True
        assert conv.history[1] is tampered_tail
        assert conv.history[1].get("_ephemeral") is True

    async def test_swap_holds_ensure_lock(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        conv = ConversationState()

        class _LockSpy:
            def __init__(self, inner: object) -> None:
                self.inner = inner
                self.entered = 0

            async def __aenter__(self) -> _LockSpy:
                self.entered += 1
                await self.inner.acquire()  # type: ignore[attr-defined]
                return self

            async def __aexit__(self, *exc: object) -> None:
                self.inner.release()  # type: ignore[attr-defined]

        await conv.append_message({"role": "user", "content": "seed"})
        base_history = conv.history
        base_len = len(base_history)
        spy = _LockSpy(conv._ensure_lock)
        monkeypatch.setattr(type(conv), "_ensure_lock", property(lambda self: spy))

        compressed: list[LLMMessage] = [{"role": "user", "content": "summary"}]
        await conv.swap_history(compressed, base_history, base_len)

        assert spy.entered == 1
        assert conv.history == compressed

    async def test_reassigned_live_history_tail_not_preserved(self) -> None:
        conv = ConversationState()
        await conv.extend_messages(
            [{"role": "user", "content": "a1"}, {"role": "assistant", "content": "a2"}]
        )
        base_history = conv.history
        base_len = len(base_history)

        await conv.replace_history([{"role": "user", "content": "other"}])
        compressed: list[LLMMessage] = [{"role": "user", "content": "summary"}]
        await conv.swap_history(compressed, base_history, base_len)

        assert conv.history == compressed
