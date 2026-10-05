"""Unit tests for agent.secrets_masker._mask_secrets."""

import os

import pytest
from agent.secrets_masker import _mask_secrets


class TestMaskSecrets:
    """Tests for _mask_secrets masking behavior."""

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            # Short values — the case the old code leaked
            ("token=abc", "token=***MASKED***"),
            ("secret=x", "secret=***MASKED***"),
            # Long values
            ("api_key=sk-1234567890abcdef", "api_key=***MASKED***"),
            ("GITHUB_TOKEN=ghp_abcdef123", "GITHUB_TOKEN=***MASKED***"),
            # Mixed-case keys
            ("PASSWORD=hunter2", "PASSWORD=***MASKED***"),
            ("Api_Key=abc123", "Api_Key=***MASKED***"),
            # Value with spaces (\S+ stops at whitespace — only "abc" masked)
            ("token=abc def", "token=***MASKED*** def"),
        ],
    )
    def test_masks_secret_values(self, input_text: str, expected: str) -> None:
        """Secret values are fully masked regardless of length."""
        result = _mask_secrets(input_text)
        assert result == expected

    def test_no_secret_returns_unchanged(self) -> None:
        """Text with no secrets is returned unchanged."""
        text = "hello world"
        assert _mask_secrets(text) == text

    def test_empty_string_returns_unchanged(self) -> None:
        """Empty string returns empty string."""
        assert _mask_secrets("") == ""

    def test_arbitrary_text_never_raises(self) -> None:
        """Arbitrary text never raises."""
        random_text = os.urandom(100).decode("latin-1")
        result = _mask_secrets(random_text)
        assert isinstance(result, str)

    def test_short_value_full_masking(self) -> None:
        """Short values must have NO characters of the secret value survive."""
        for short_val in ["abc", "x", "1", "a"]:
            result = _mask_secrets(f"token={short_val}")
            assert short_val not in result, f"Value '{short_val}' leaked in: {result}"
            assert "***MASKED***" in result
