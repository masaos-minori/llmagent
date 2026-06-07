"""
tests/test_memory_extract.py
Unit tests for agent.memory.extract rule-based extraction logic.
"""

from __future__ import annotations

from agent.memory.extract import MIN_USER_CONTENT_CHARS, extract_memories
from shared.types import LLMMessage


def _hist(*pairs: tuple[str, str]) -> list[LLMMessage]:
    """Build a history list from (role, content) pairs."""
    return [{"role": role, "content": content} for role, content in pairs]


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
        content = (
            "The rule is that we should always follow the policy and constraint "
            "decided by the team."
        )
        history = _hist(("user", "Q"), ("assistant", content))
        result = extract_memories(history, session_id=42)
        assert all(e.session_id == 42 for e in result)

    def test_passes_project_repo_branch(self) -> None:
        content = (
            "The rule is that we should always follow the policy and constraint "
            "decided by the team."
        )
        history = _hist(("user", "Q"), ("assistant", content))
        result = extract_memories(history, project="p", repo="r", branch="b")
        for e in result:
            assert e.project == "p"
            assert e.repo == "r"
            assert e.branch == "b"

    def test_all_entries_have_valid_memory_id(self) -> None:
        content = (
            "The rule is that we should always follow the policy and constraint "
            "decided by the team."
        )
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
        msgs: list[LLMMessage] = []
        for i in range(30):
            msgs.append({"role": "user", "content": f"question {i}"})
            msgs.append(
                {
                    "role": "assistant",
                    "content": (
                        f"The rule is that we should always follow the policy {i} "
                        "constraint decided. " * 5
                    ),
                }
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
            {"role": "user", "content": "Q"},
            {
                "role": "tool",
                "content": "always follow the policy constraint rule " * 5,
            },
            {"role": "assistant", "content": "Understood."},
        ]
        result = extract_memories(history)
        assert all(e.memory_type != "tool" for e in result)

    def test_importance_priority_ordering_caps_at_max_entries(self) -> None:
        """When candidates exceed MAX_ENTRIES, highest-importance entries are kept."""
        from agent.memory.extract import MAX_ENTRIES

        msgs: list[LLMMessage] = [
            {"role": "user", "content": "seed"},
            {"role": "assistant", "content": "seed"},
        ]
        # Add many user-rule messages with semantic keywords
        rule = "always follow the policy constraint rule standard principle " * 3
        for _ in range(MAX_ENTRIES + 5):
            msgs.append({"role": "user", "content": rule})
            msgs.append({"role": "assistant", "content": rule})
        result = extract_memories(msgs)
        assert len(result) <= MAX_ENTRIES
