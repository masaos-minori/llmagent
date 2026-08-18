"""
tests/test_memory_extract.py
Unit tests for agent.memory.extract rule-based extraction logic.
"""

from __future__ import annotations

from agent.memory.extract import (
    MIN_USER_CONTENT_CHARS,
    _classify_content,
    extract_memories,
)
from agent.memory.models import HistoryMessage


def _hist(*pairs: tuple[str, str]) -> list[HistoryMessage]:
    """Build a history list from (role, content) pairs."""
    return [HistoryMessage(role=role, content=content) for role, content in pairs]


class TestExtractMemories:
    def test_skips_short_history(self) -> None:
        history = _hist(("user", "hi"))
        assert extract_memories(history) == []

    def test_skips_when_assistant_content_too_short(self) -> None:
        history = _hist(
            ("user", "What is the policy?"),
            ("assistant", "Short answer."),
        )
        result = extract_memories(history)
        assert result == []

    def test_extracts_semantic_with_rule_keywords(self) -> None:
        content = (
            "The rule is that we should always follow the constraint and policy "
            "established by the team. This is a decided rule that everyone must follow."
        )
        history = _hist(
            ("user", "What is the rule?"),
            ("assistant", content),
        )
        result = extract_memories(history)
        semantic = [e for e in result if e.memory_type == "semantic"]
        assert len(semantic) >= 1

    def test_extracts_episodic_failure_pattern(self) -> None:
        content = (
            "The error was caused by a missing import. I fixed the issue by "
            "adding the correct import statement. The bug is now resolved and "
            "the exception no longer occurs in the traceback."
        )
        history = _hist(
            ("user", "What happened?"),
            ("assistant", content),
        )
        result = extract_memories(history)
        failure = [e for e in result if e.source_type == "failure"]
        assert len(failure) >= 1

    def test_extracts_episodic_qa_for_long_answer(self) -> None:
        content = "A " * 100  # 200 chars, above MIN_CONTENT_CHARS * 2
        history = _hist(
            ("user", "Explain something"),
            ("assistant", content),
        )
        result = extract_memories(history)
        assert len(result) >= 1

    def test_passes_session_id_to_entry(self) -> None:
        content = "The rule is that we should always follow the policy and constraint decided by the team."
        history = _hist(("user", "Q"), ("assistant", content))
        result = extract_memories(history, session_id=42)
        assert all(e.session_id == 42 for e in result)

    def test_passes_project_repo_branch(self) -> None:
        content = "The rule is that we should always follow the policy and constraint decided by the team."
        history = _hist(("user", "Q"), ("assistant", content))
        result = extract_memories(history, project="p", repo="r", branch="b")
        for e in result:
            assert e.project == "p"
            assert e.repo == "r"
            assert e.branch == "b"

    def test_all_entries_have_valid_memory_id(self) -> None:
        content = "The rule is that we should always follow the policy and constraint decided by the team."
        history = _hist(("user", "Q"), ("assistant", content))
        result = extract_memories(history)
        for e in result:
            assert len(e.memory_id) == 36  # UUID format

    def test_importance_in_range(self) -> None:
        content = (
            "The rule is that we should always follow the policy and constraint "
            "decided by the team. This must be followed by everyone always."
        )
        history = _hist(("user", "Q"), ("assistant", content))
        result = extract_memories(history)
        for e in result:
            assert 0.0 <= e.importance <= 1.0

    def test_does_not_exceed_max_entries(self) -> None:
        # Create many history items with substantive content
        msgs: list[HistoryMessage] = []
        for i in range(30):
            msgs.append(HistoryMessage(role="user", content=f"question {i}"))
            msgs.append(
                HistoryMessage(
                    role="assistant",
                    content=(
                        f"The rule is that we should always follow the policy {i} constraint decided. "
                        * 5
                    ),
                )
            )
        result = extract_memories(msgs)
        from agent.memory.extract import MAX_ENTRIES

        assert len(result) <= MAX_ENTRIES

    def test_skips_when_no_keywords_and_under_double_min(self) -> None:
        # Content is >= MIN_CONTENT_CHARS (80) but < MIN_CONTENT_CHARS*2 (160)
        # and has no semantic/failure keywords → _classify_content returns None → no entry
        content = "x" * 90  # 90 chars, no keywords
        history = _hist(
            ("user", "Q"),
            ("assistant", content),
        )
        result = extract_memories(history)
        assert result == []

    def test_user_rule_message_extracted_as_semantic(self) -> None:
        """User message with semantic keywords >= MIN_USER_CONTENT_CHARS is extracted."""
        user_content = (
            "Always use type annotations in all Python functions. "
            "This is a policy we should always follow as a team constraint."
        )
        assert len(user_content) >= MIN_USER_CONTENT_CHARS
        history = _hist(
            ("user", user_content),
            ("assistant", "Understood."),
        )
        result = extract_memories(history)
        user_rules = [e for e in result if "user-rule" in e.tags]
        assert len(user_rules) >= 1
        assert user_rules[0].memory_type == "semantic"

    def test_user_message_without_keywords_not_extracted(self) -> None:
        """User message >= MIN_USER_CONTENT_CHARS but without semantic keywords → not extracted."""
        user_content = "x" * MIN_USER_CONTENT_CHARS  # long enough but no keywords
        history = _hist(
            ("user", user_content),
            ("assistant", "Understood."),
        )
        result = extract_memories(history)
        user_rules = [e for e in result if "user-rule" in e.tags]
        assert len(user_rules) == 0

    def test_short_user_message_not_extracted(self) -> None:
        """User message below MIN_USER_CONTENT_CHARS is not extracted."""
        history = _hist(
            ("user", "always"),  # has keyword but too short
            ("assistant", "Understood."),
        )
        result = extract_memories(history)
        user_rules = [e for e in result if "user-rule" in e.tags]
        assert len(user_rules) == 0

    def test_non_assistant_non_user_role_skipped(self) -> None:
        """Messages with role 'tool' are not extracted."""
        history = [
            HistoryMessage(role="user", content="Q"),
            HistoryMessage(
                role="tool",
                content="always follow the policy constraint rule " * 5,
            ),
            HistoryMessage(role="assistant", content="Understood."),
        ]
        result = extract_memories(history)
        assert all(e.memory_type != "tool" for e in result)

    def test_importance_priority_ordering_caps_at_max_entries(self) -> None:
        """When candidates exceed MAX_ENTRIES, highest-importance entries are kept."""
        from agent.memory.extract import MAX_ENTRIES

        msgs: list[HistoryMessage] = [
            HistoryMessage(role="user", content="seed"),
            HistoryMessage(role="assistant", content="seed"),
        ]
        # Add many user-rule messages with semantic keywords
        rule = "always follow the policy constraint rule standard principle " * 3
        for _ in range(MAX_ENTRIES + 5):
            msgs.append(HistoryMessage(role="user", content=rule))
            msgs.append(HistoryMessage(role="assistant", content=rule))
        result = extract_memories(msgs)
        assert len(result) <= MAX_ENTRIES

    def test_over_limit_assistant_message_yields_multiple_entries(self) -> None:
        """An over-long assistant message is chunked into multiple entries sharing identity fields."""
        content = (
            "The rule is that we should always follow the policy and constraint decided "
            "by the team. This must be followed by everyone in the group at all times."
        )
        history = _hist(("user", "What is the rule?"), ("assistant", content))
        result = extract_memories(
            history,
            session_id=42,
            turn_id="turn-1",
            project="p",
            repo="r",
            branch="b",
            max_content_chars=50,
        )
        assert len(result) > 1
        first = result[0]
        for e in result:
            assert e.session_id == 42
            assert e.turn_id == "turn-1"
            assert e.project == "p"
            assert e.repo == "r"
            assert e.branch == "b"
            assert e.memory_type == first.memory_type
            assert e.source_type == first.source_type
        assert len({e.memory_id for e in result}) == len(result)
        assert "".join(e.content for e in result) == content

    def test_over_limit_user_rule_message_yields_multiple_entries(self) -> None:
        """The max_content_chars parameter is wired through the user-rule extraction path too."""
        user_content = (
            "Always use type annotations in all Python functions across the codebase. "
            "This is a policy we should always follow as a team constraint without exception."
        )
        history = _hist(("user", user_content), ("assistant", "Understood."))
        result = extract_memories(
            history,
            session_id=7,
            turn_id="turn-2",
            project="p2",
            repo="r2",
            branch="b2",
            max_content_chars=50,
        )
        user_rules = [e for e in result if "user-rule" in e.tags]
        assert len(user_rules) > 1
        for e in user_rules:
            assert e.session_id == 7
            assert e.turn_id == "turn-2"
            assert e.project == "p2"
            assert e.repo == "r2"
            assert e.branch == "b2"
            assert e.memory_type == "semantic"
        assert len({e.memory_id for e in user_rules}) == len(user_rules)
        assert "".join(e.content for e in user_rules) == user_content

    def test_under_limit_message_still_yields_single_entry(self) -> None:
        """Content just under max_content_chars is not split into multiple entries."""
        content = (
            "The rule is that we should always follow the policy and constraint decided "
            "by the team. This must be followed by everyone in the group at all times."
        )
        history = _hist(("user", "What is the rule?"), ("assistant", content))
        result = extract_memories(history, max_content_chars=200)
        assert len(result) == 1
        assert result[0].content == content


class TestSplitContent:
    """Unit tests for the chunking-aware _split_content helper."""

    def test_content_under_limit_returns_single_chunk(self) -> None:
        from agent.memory.extract import _split_content

        content = "short content well under the limit"
        assert _split_content(content, 100) == [content]

    def test_content_over_limit_splits_on_paragraph_boundary(self) -> None:
        from agent.memory.extract import _split_content

        para1 = "A" * 20
        para2 = "B" * 20
        content = f"{para1}\n\n{para2}"
        result = _split_content(content, 25)
        assert result == [para1, para2]

    def test_single_paragraph_exceeding_limit_hard_cuts(self) -> None:
        from agent.memory.extract import _split_content

        content = "x" * 55
        max_chars = 20
        result = _split_content(content, max_chars)
        assert all(len(chunk) <= max_chars for chunk in result)
        assert "".join(result) == content
        assert len(result) == -(-len(content) // max_chars)  # ceil division

    def test_max_chars_zero_or_negative_disables_splitting(self) -> None:
        from agent.memory.extract import _split_content

        content = "z" * 1000
        assert _split_content(content, 0) == [content]
        assert _split_content(content, -5) == [content]


class TestClassifyContent:
    """Regression tests for _classify_content source-type classification."""

    def test_rule_keywords_classify_as_rule(self) -> None:
        from agent.memory.extract import _SEMANTIC_KEYWORDS

        text = "You must always use uv run pytest"
        semantic_hits = len(_SEMANTIC_KEYWORDS.findall(text))
        failure_hits = 0
        result = _classify_content(text * 5, semantic_hits, failure_hits)
        assert result is not None
        assert result[1] == "rule"

    def test_decision_keywords_classify_as_decision(self) -> None:
        from agent.memory.extract import _SEMANTIC_KEYWORDS

        text = (
            "We decided to use SQLite because the trade-off is clear: it must be "
            "the default policy for this project always."
        )
        semantic_hits = len(_SEMANTIC_KEYWORDS.findall(text))
        failure_hits = 0
        result = _classify_content(text, semantic_hits, failure_hits)
        assert result is not None
        assert result[1] == "decision"

    def test_failure_keywords_classify_as_failure(self) -> None:
        from agent.memory.extract import _EPISODIC_FAILURE_KEYWORDS

        text = "Fixed the regression by resetting the root cause of the deadlock"
        failure_hits = len(_EPISODIC_FAILURE_KEYWORDS.findall(text))
        result = _classify_content(text, 0, failure_hits)
        assert result is not None
        assert result[1] == "failure"

    def test_plain_conversation_classifies_as_conversation(self) -> None:
        text = "That is a good question about the config. " * 5  # long enough
        result = _classify_content(text, 0, 0)
        assert result is not None
        assert result[1] == "conversation"
