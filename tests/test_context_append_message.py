"""tests/test_context_append_message.py — Unit tests for ConversationState's
validated history-mutation entry points (append_message, extend_messages,
replace_history) in agent/context.py.
"""

from __future__ import annotations

import logging
from typing import cast

from agent.context import ConversationState
from shared.types import LLMMessage


class TestAppendMessage:
    def test_well_formed_message_appends_unchanged(self) -> None:
        conv = ConversationState()
        msg: LLMMessage = {"role": "user", "content": "hello"}

        conv.append_message(msg)

        assert conv.history == [{"role": "user", "content": "hello"}]

    def test_source_never_persisted(self) -> None:
        conv = ConversationState()
        msg: LLMMessage = {"role": "user", "content": "hello"}

        conv.append_message(msg, source="memory_injection")

        assert "source" not in conv.history[0]

    def test_trusted_source_with_authorized_ephemeral_key_appends_intact(
        self,
    ) -> None:
        conv = ConversationState()
        msg: LLMMessage = {
            "role": "user",
            "content": "hello",
            "_memory_injected": True,
        }

        conv.append_message(msg, source="memory_injection")

        assert conv.history == [
            {"role": "user", "content": "hello", "_memory_injected": True}
        ]

    def test_forged_ephemeral_key_with_no_source_is_stripped_and_warns(
        self, caplog
    ) -> None:
        conv = ConversationState()
        msg: LLMMessage = {
            "role": "user",
            "content": "hello",
            "_memory_injected": True,
        }

        with caplog.at_level(logging.WARNING, logger="agent.context"):
            conv.append_message(msg)

        assert conv.history == [{"role": "user", "content": "hello"}]
        assert any(record.levelno == logging.WARNING for record in caplog.records)

    def test_forged_ephemeral_key_with_untrusted_source_is_stripped(self) -> None:
        conv = ConversationState()
        msg: LLMMessage = {
            "role": "user",
            "content": "hello",
            "_ephemeral": True,
        }

        conv.append_message(msg, source="not_a_real_source")

        assert conv.history == [{"role": "user", "content": "hello"}]

    def test_message_missing_content_after_sanitization_is_dropped(
        self, caplog
    ) -> None:
        conv = ConversationState()
        # Deliberately malformed (missing required "content"): exercises the
        # function's runtime robustness against untrusted/forged input, which
        # the static LLMMessage type alone would not allow constructing.
        msg = cast(LLMMessage, {"role": "user", "_memory_injected": True})

        with caplog.at_level(logging.ERROR, logger="agent.context"):
            conv.append_message(msg)

        assert conv.history == []
        assert any(record.levelno == logging.ERROR for record in caplog.records)

    def test_message_missing_role_after_sanitization_is_dropped(self) -> None:
        conv = ConversationState()
        # Deliberately malformed (missing required "role"); see comment above.
        msg = cast(LLMMessage, {"content": "hello", "_memory_injected": True})

        conv.append_message(msg)

        assert conv.history == []


class TestExtendMessages:
    def test_validates_each_message_independently(self) -> None:
        conv = ConversationState()
        msgs: list[LLMMessage] = [
            {"role": "user", "content": "good one"},
            {"role": "user", "content": "hello", "_memory_injected": True},
            {"role": "user", "content": "good two"},
        ]

        conv.extend_messages(msgs)

        assert conv.history == [
            {"role": "user", "content": "good one"},
            {"role": "user", "content": "hello"},
            {"role": "user", "content": "good two"},
        ]


class TestReplaceHistory:
    def test_clears_prior_history_before_extending(self) -> None:
        conv = ConversationState()
        conv.append_message({"role": "user", "content": "old"})

        conv.replace_history([{"role": "user", "content": "new"}])

        assert conv.history == [{"role": "user", "content": "new"}]
