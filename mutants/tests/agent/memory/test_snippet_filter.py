"""tests/test_snippet_filter.py — Unit tests for agent/memory/snippet_filter.py."""

from __future__ import annotations

from agent.memory.snippet_filter import (
    filter_pii,
    truncate_snippet,
)


class TestFilterPii:
    def test_no_pii_returns_unmodified(self) -> None:
        result = filter_pii("Hello world, this is a normal message.")
        assert result.text == "Hello world, this is a normal message."
        assert result.was_filtered is False

    def test_email_redaction(self) -> None:
        result = filter_pii("Contact user@example.com for details.")
        assert "[REDACTED_EMAIL]" in result.text
        assert result.was_filtered is True

    def test_phone_number_redaction(self) -> None:
        result = filter_pii("Call me at 555-123-4567.")
        assert "[REDACTED_PHONE]" in result.text
        assert result.was_filtered is True

    def test_credit_card_redaction(self) -> None:
        result = filter_pii("Card number: 4111-1111-1111-1111.")
        assert "[REDACTED_CREDIT_CARD]" in result.text
        assert result.was_filtered is True

    def test_ssn_redaction(self) -> None:
        result = filter_pii("SSN: 123-45-6789.")
        assert "[REDACTED_SSN]" in result.text
        assert result.was_filtered is True

    def test_api_key_redaction(self) -> None:
        result = filter_pii("Key: abcdefghijklmnopqrstuvwxyz0123456789+/ABCD==")
        assert "[REDACTED_API_KEY]" in result.text
        assert result.was_filtered is True

    def test_ip_address_redaction(self) -> None:
        result = filter_pii("Server at 192.168.1.1.")
        assert "[REDACTED_IP_ADDRESS]" in result.text
        assert result.was_filtered is True

    def test_multiple_pii_types_all_redacted(self) -> None:
        result = filter_pii("Email: test@test.com, Phone: 555-123-4567.")
        assert "[REDACTED_EMAIL]" in result.text
        assert "[REDACTED_PHONE]" in result.text
        assert result.was_filtered is True

    def test_short_string_not_flagged_as_api_key(self) -> None:
        result = filter_pii("short key: abcdefghij")
        assert result.was_filtered is False

    def test_partial_redaction_preserves_context(self) -> None:
        result = filter_pii("Send to admin@corp.com and user@example.org.")
        assert result.was_filtered is True
        assert "[REDACTED_EMAIL]" in result.text
        # Both emails should be redacted
        assert result.text.count("[REDACTED_EMAIL]") == 2

    def test_text_with_newlines_and_special_chars(self) -> None:
        result = filter_pii("Line1\nLine2: secret@email.com\nLine3")
        assert "[REDACTED_EMAIL]" in result.text
        assert result.was_filtered is True

    def test_empty_string(self) -> None:
        result = filter_pii("")
        assert result.text == ""
        assert result.was_filtered is False

    def test_text_only_numbers_no_match(self) -> None:
        result = filter_pii("Just numbers: 12345678")
        assert result.was_filtered is False

    def test_phone_with_dots_instead_of_hyphens(self) -> None:
        result = filter_pii("Phone: 555.123.4567.")
        assert "[REDACTED_PHONE]" in result.text
        assert result.was_filtered is True

    def test_credit_card_with_spaces_instead_of_dashes(self) -> None:
        result = filter_pii("Card: 4111 1111 1111 1111.")
        assert "[REDACTED_CREDIT_CARD]" in result.text
        assert result.was_filtered is True

    def test_ssn_without_hyphens_not_matched(self) -> None:
        result = filter_pii("SSN-like: 123456789")
        assert result.was_filtered is False

    def test_ip_v4_like_pattern_redacted(self) -> None:
        result = filter_pii("IP: 10.0.0.1")
        assert "[REDACTED_IP_ADDRESS]" in result.text
        assert result.was_filtered is True

    def test_text_containing_replacement_strings_still_works(self) -> None:
        result = filter_pii("Text has REDACTED_EMAIL in it already.")
        assert result.was_filtered is False

    def test_api_key_with_equals_padding(self) -> None:
        result = filter_pii(
            "Token: ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx=="
        )
        assert "[REDACTED_API_KEY]" in result.text
        assert result.was_filtered is True

    def test_api_key_without_equals_padding(self) -> None:
        result = filter_pii(
            "Token: ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxy"
        )
        assert "[REDACTED_API_KEY]" in result.text
        assert result.was_filtered is True


class TestTruncateSnippet:
    def test_no_truncation_when_within_limit(self) -> None:
        result = truncate_snippet("Short text", max_length=500)
        assert result.text == "Short text"
        assert result.was_truncated is False
        assert result.original_length == 10

    def test_truncation_at_exact_boundary(self) -> None:
        text = "a" * 500
        result = truncate_snippet(text, max_length=500)
        assert result.text == text
        assert result.was_truncated is False
        assert result.original_length == 500

    def test_truncation_exceeding_limit(self) -> None:
        text = "a" * 600
        result = truncate_snippet(text, max_length=500)
        assert result.was_truncated is True
        assert result.original_length == 600
        assert "...[truncated]" in result.text
        assert len(result.text) < len(text)

    def test_truncation_with_custom_max_length(self) -> None:
        text = "a" * 100
        result = truncate_snippet(text, max_length=50)
        assert result.was_truncated is True
        assert len(result.text) == 50 + len("...[truncated]")

    def test_empty_string_no_truncation(self) -> None:
        result = truncate_snippet("", max_length=500)
        assert result.text == ""
        assert result.was_truncated is False

    def test_truncation_preserves_prefix_metadata(self) -> None:
        text = "[Semantic memory] " + "a" * 500
        result = truncate_snippet(text, max_length=500)
        assert result.was_truncated is True
        assert result.text.startswith("[Semantic memory]")
        assert "...[truncated]" in result.text

    def test_unicode_content_truncates_by_characters(self) -> None:
        text = "\u3042\u3044\u3046\u304a\u304b" * 100  # 500 chars
        result = truncate_snippet(text, max_length=500)
        assert result.was_truncated is False

        text_longer = "\u3042\u3044\u3046\u304a\u304b" * 101  # 505 chars
        result_longer = truncate_snippet(text_longer, max_length=500)
        assert result_longer.was_truncated is True
        assert result_longer.original_length == 505
