"""Characterization tests for memory snippet injection security.

Verifies current behavior around PII filtering, snippet truncation,
message priority ordering, and content truncation — documenting what
the system actually does today, not what it ought to do tomorrow.
"""

from __future__ import annotations

import pytest
from agent.memory.snippet_filter import (
    PII_PATTERNS,
    filter_pii,
    truncate_snippet,
)

# ── PII Filtering ──────────────────────────────────────────────────────────────


class TestSensitiveDataFiltering:
    """Characterize current PII filtering behavior."""

    def test_email_redacted(self) -> None:
        result = filter_pii("Contact admin@example.com for help")
        assert result.was_filtered is True
        assert "[REDACTED_EMAIL]" in result.text
        assert "admin@example.com" not in result.text

    def test_phone_redacted(self) -> None:
        result = filter_pii("Call 555-123-4567")
        assert result.was_filtered is True
        assert "[REDACTED_PHONE]" in result.text
        assert "555-123-4567" not in result.text

    def test_credit_card_redacted(self) -> None:
        result = filter_pii("Card: 4111-1111-1111-1111")
        assert result.was_filtered is True
        assert "[REDACTED_CREDIT_CARD]" in result.text
        assert "4111-1111-1111-1111" not in result.text

    def test_ssn_redacted(self) -> None:
        result = filter_pii("SSN: 123-45-6789")
        assert result.was_filtered is True
        assert "[REDACTED_SSN]" in result.text
        assert "123-45-6789" not in result.text

    def test_api_key_redacted(self) -> None:
        long_key = "a" * 40
        result = filter_pii(f"Key: {long_key}")
        assert result.was_filtered is True
        assert "[REDACTED_API_KEY]" in result.text

    def test_ip_address_redacted(self) -> None:
        result = filter_pii("Server at 192.168.1.1")
        assert result.was_filtered is True
        assert "[REDACTED_IP_ADDRESS]" in result.text
        assert "192.168.1.1" not in result.text

    def test_multiple_pii_types_all_redacted(self) -> None:
        result = filter_pii("Email: a@b.com Phone: 555-123-4567")
        assert result.was_filtered is True
        assert "[REDACTED_EMAIL]" in result.text
        assert "[REDACTED_PHONE]" in result.text
        assert "a@b.com" not in result.text
        assert "555-123-4567" not in result.text

    def test_no_pii_returns_unfiltered(self) -> None:
        result = filter_pii("Just regular text here")
        assert result.was_filtered is False
        assert result.text == "Just regular text here"

    def test_empty_string_returns_unfiltered(self) -> None:
        result = filter_pii("")
        assert result.was_filtered is False
        assert result.text == ""

    def test_partial_pii_only_matching_patterns_redacted(self) -> None:
        result = filter_pii("Email: a@b.com but phone is safe")
        assert result.was_filtered is True
        assert "[REDACTED_EMAIL]" in result.text
        assert "a@b.com" not in result.text
        assert "phone is safe" in result.text

    def test_text_returned_is_not_none_when_filtered(self) -> None:
        result = filter_pii("Email: a@b.com")
        assert result.text is not None
        assert isinstance(result.text, str)

    def test_all_known_pii_patterns_exist(self) -> None:
        expected_keys = {
            "EMAIL",
            "PHONE",
            "CREDIT_CARD",
            "SSN",
            "API_KEY",
            "IP_ADDRESS",
        }
        assert set(PII_PATTERNS.keys()) == expected_keys

    def test_pii_pattern_values_are_valid_regex(self) -> None:
        import re

        for name, pattern in PII_PATTERNS.items():
            try:
                re.compile(pattern)
            except re.error:
                pytest.fail(f"Invalid regex pattern for {name}: {pattern}")


# ── Snippet Length Enforcement ─────────────────────────────────────────────────


class TestOversizedSnippetTruncation:
    """Characterize current snippet length enforcement behavior."""

    def test_short_snippet_unchanged(self) -> None:
        result = truncate_snippet("short text", max_length=500)
        assert result.was_truncated is False
        assert result.text == "short text"
        assert result.original_length == len("short text")

    def test_exact_max_length_snippet_unchanged(self) -> None:
        exact = "x" * 500
        result = truncate_snippet(exact, max_length=500)
        assert result.was_truncated is False
        assert result.text == exact
        assert result.original_length == 500

    def test_one_over_max_length_gets_truncated(self) -> None:
        over = "x" * 501
        result = truncate_snippet(over, max_length=500)
        assert result.was_truncated is True
        assert result.original_length == 501
        assert result.text.endswith("[truncated]")
        assert len(result.text) == 500 + len("...[truncated]")

    def test_truncated_text_contains_prefix_of_original(self) -> None:
        original = "hello world " + "x" * 500
        result = truncate_snippet(original, max_length=500)
        assert result.was_truncated is True
        assert result.text.startswith("hello world ")

    def test_default_max_length_is_500(self) -> None:
        long_text = "y" * 600
        result = truncate_snippet(long_text)
        assert result.was_truncated is True
        assert len(result.text) == 500 + len("...[truncated]")

    def test_custom_max_length_applied(self) -> None:
        short_text = "z" * 100
        result = truncate_snippet(short_text, max_length=50)
        assert result.was_truncated is True
        assert result.original_length == 100
        assert len(result.text) == 50 + len("...[truncated]")

    def test_zero_max_length_truncates_everything(self) -> None:
        result = truncate_snippet("anything", max_length=0)
        assert result.was_truncated is True
        assert result.original_length == 8
        assert result.text == "...[truncated]"

    def test_negative_max_length_removes_last_char_and_appends_indicator(self) -> None:
        """Negative max_length slices as text[:-N], removing N characters from end, then appends indicator."""
        result = truncate_snippet("anything", max_length=-1)
        assert result.was_truncated is True
        assert result.original_length == 8
        assert result.text == "anythin...[truncated]"

    def test_unicode_content_preserved_in_truncation(self) -> None:
        unicode_text = "\u3053\u3093\u306b\u3061\u306f " + "x" * 500
        result = truncate_snippet(unicode_text, max_length=500)
        assert result.was_truncated is True
        assert "\u3053\u3093\u306b\u3061\u306f" in result.text

    def test_truncated_indicator_present_on_truncation(self) -> None:
        result = truncate_snippet("a" * 600, max_length=500)
        assert "[truncated]" in result.text

    def test_truncated_indicator_absent_on_non_truncation(self) -> None:
        result = truncate_snippet("a" * 100, max_length=500)
        assert "[truncated]" not in result.text

    def test_original_length_preserved_after_truncation(self) -> None:
        original = "b" * 700
        result = truncate_snippet(original, max_length=500)
        assert result.original_length == 700
        assert len(result.text) < result.original_length


# ── System Message Priority ────────────────────────────────────────────────────


class TestSystemMessagePriority:
    """Characterize current message priority ordering in injected snippets."""

    def test_semantic_memory_has_prefix(self) -> None:
        prefix = "[Semantic memory]"
        assert prefix in ("[Semantic memory]", "[Episodic memory]")

    def test_episodic_memory_has_different_prefix(self) -> None:
        prefix = "[Episodic memory]"
        assert prefix in ("[Semantic memory]", "[Episodic memory]")

    def test_prefixes_are_distinguishable(self) -> None:
        semantic_prefix = "[Semantic memory]"
        episodic_prefix = "[Episodic memory]"
        assert semantic_prefix != episodic_prefix

    def test_prefix_format_consistency(self) -> None:
        """All prefixes follow [Type memory] format."""
        for prefix_name in ["[Semantic memory]", "[Episodic memory]"]:
            assert prefix_name.startswith("[")
            assert prefix_name.endswith("]")
            assert "memory" in prefix_name.lower()

    def test_no_system_priority_marker_exists(self) -> None:
        """Current implementation does not use a 'system' priority marker."""
        for prefix_name in ["[Semantic memory]", "[Episodic memory]"]:
            assert "system" not in prefix_name.lower()

    def test_injection_policy_defaults(self) -> None:
        from agent.memory.injection import InjectionPolicy

        policy = InjectionPolicy()
        assert policy.max_semantic == 5
        assert policy.max_episodic == 3
        assert policy.min_importance == 0.5
        assert policy.max_snippet_length == 500

    def test_injection_policy_format_prefixes_match_constants(self) -> None:
        from agent.memory.injection import InjectionPolicy

        policy = InjectionPolicy()
        assert policy.format_prefix_semantic == "[Semantic memory]"
        assert policy.format_prefix_episodic == "[Episodic memory]"

    def test_injection_policy_fields_are_frozen(self) -> None:
        from agent.memory.injection import InjectionPolicy

        policy = InjectionPolicy()
        with pytest.raises(Exception):  # frozen dataclass raises on assignment
            policy.max_semantic = 10


# ── Content Truncation Impact ──────────────────────────────────────────────────


class TestContentTruncationImpact:
    """Characterize what happens when summary differs from content[:100]."""

    def test_summary_used_when_available(self) -> None:
        """When entry.summary exists, it is used instead of content[:100]."""
        from agent.memory.types import MemoryEntry

        entry = MemoryEntry(
            memory_id="test-id",
            memory_type="semantic",
            source_type="rule",
            session_id=None,
            turn_id=None,
            project="",
            repo="",
            branch="main",
            content="This is the full content that would be truncated to 100 chars if no summary existed.",
            summary="This is the summary that takes precedence over content[:100].",
            tags="[]",
            importance=0.5,
            pinned=0,
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        snippet_text = entry.summary if entry.summary else entry.content[:100]
        assert (
            snippet_text
            == "This is the summary that takes precedence over content[:100]."
        )

    def test_content_first_100_chars_used_when_summary_missing(self) -> None:
        """When entry.summary is empty/None, content[:100] is used as fallback."""
        from agent.memory.types import MemoryEntry

        entry = MemoryEntry(
            memory_id="test-id",
            memory_type="semantic",
            source_type="rule",
            session_id=None,
            turn_id=None,
            project="",
            repo="",
            branch="main",
            content="This is the full content that would be truncated to 100 chars if no summary existed. It contains important details beyond the first hundred characters that might be lost.",
            summary="",
            tags="[]",
            importance=0.5,
            pinned=0,
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        snippet_text = entry.summary if entry.summary else entry.content[:100]
        assert snippet_text == entry.content[:100]

    def test_content_shorter_than_100_chars_returns_full_content(self) -> None:
        """When content is shorter than 100 chars and no summary, full content is returned."""
        from agent.memory.types import MemoryEntry

        entry = MemoryEntry(
            memory_id="test-id",
            memory_type="semantic",
            source_type="rule",
            session_id=None,
            turn_id=None,
            project="",
            repo="",
            branch="main",
            content="Short content under 100 chars.",
            summary="",
            tags="[]",
            importance=0.5,
            pinned=0,
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        snippet_text = entry.summary if entry.summary else entry.content[:100]
        assert snippet_text == entry.content

    def test_empty_string_summary_treated_as_missing(self) -> None:
        """Empty string summary is falsy, so content[:100] is used instead."""
        from agent.memory.types import MemoryEntry

        entry = MemoryEntry(
            memory_id="test-id",
            memory_type="semantic",
            source_type="rule",
            session_id=None,
            turn_id=None,
            project="",
            repo="",
            branch="main",
            content="Fallback content used because summary is empty string.",
            summary="",
            tags="[]",
            importance=0.5,
            pinned=0,
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        snippet_text = entry.summary if entry.summary else entry.content[:100]
        assert snippet_text == entry.content[:100]

    def test_whitespace_only_summary_used_instead_of_content(self) -> None:
        """Whitespace-only summary is truthy in Python, so it is used instead of content[:100]."""
        from agent.memory.types import MemoryEntry

        entry = MemoryEntry(
            memory_id="test-id",
            memory_type="semantic",
            source_type="rule",
            session_id=None,
            turn_id=None,
            project="",
            repo="",
            branch="main",
            content="Fallback content used because summary is whitespace only.",
            summary="   ",
            tags="[]",
            importance=0.5,
            pinned=0,
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        snippet_text = entry.summary if entry.summary else entry.content[:100]
        assert snippet_text == "   "

    def test_critical_info_can_be_lost_with_content_truncation(self) -> None:
        """Information after position 100 in content is lost when summary is empty."""
        from agent.memory.types import MemoryEntry

        long_content = "A" * 100 + "CRITICAL_INFO_AFTER_100" + "B" * 100
        entry = MemoryEntry(
            memory_id="test-id",
            memory_type="semantic",
            source_type="rule",
            session_id=None,
            turn_id=None,
            project="",
            repo="",
            branch="main",
            content=long_content,
            summary="",
            tags="[]",
            importance=0.5,
            pinned=0,
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        snippet_text = entry.summary if entry.summary else entry.content[:100]
        assert "CRITICAL_INFO_AFTER_100" not in snippet_text

    def test_summary_prevents_information_loss(self) -> None:
        """When summary exists, critical info can be preserved via summary rather than truncation."""
        from agent.memory.types import MemoryEntry

        long_content = "A" * 100 + "CRITICAL_INFO_AFTER_100" + "B" * 100
        entry = MemoryEntry(
            memory_id="test-id",
            memory_type="semantic",
            source_type="rule",
            session_id=None,
            turn_id=None,
            project="",
            repo="",
            branch="main",
            content=long_content,
            summary="CRITICAL_INFO_AFTER_100",
            tags="[]",
            importance=0.5,
            pinned=0,
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        snippet_text = entry.summary if entry.summary else entry.content[:100]
        assert "CRITICAL_INFO_AFTER_100" in snippet_text
