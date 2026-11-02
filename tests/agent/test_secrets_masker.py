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

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            # REQ-002: Authorization: Bearer <token>
            (
                "Authorization: Bearer dGhpczBzZWNyZXQ=",
                "Authorization: Bearer ***MASKED***",
            ),
            # REQ-003: generic Authorization: <scheme> <token>
            (
                "Authorization: Basic YWxsb246cGFzcw==",
                "Authorization: Basic ***MASKED***",
            ),
            ("Authorization: Digest abc123def", "Authorization: Digest ***MASKED***"),
            # REQ-004: standalone Bearer <token> (no Authorization: prefix)
            ("Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig", "Bearer ***MASKED***"),
        ],
    )
    def test_bearer_header_shapes(self, input_text: str, expected: str) -> None:
        """Bearer-header and standalone bearer-token shapes are masked."""
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


class TestJsonSecretMasking:
    """REQ-004: JSON-style secret values for known key names are masked.

    Covers both `:` and `,` separators and multiple known key names while leaving
    non-secret quoted values untouched (no false positives).
    """

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            ('{"token": "abc123"}', '{"token": "***MASKED***"}'),
            ('"api_key":"xyz"', '"api_key":"***MASKED***"'),
            (
                '{"password": "pw", "name": "John"}',
                '{"password": "***MASKED***", "name": "John"}',
            ),
            ('{"secret":"s3cr3t"}', '{"secret":"***MASKED***"}'),
            (
                '{"api_key": "AKIA123", "region": "us-east-1"}',
                '{"api_key": "***MASKED***", "region": "us-east-1"}',
            ),
        ],
    )
    def test_json_secret_values_are_masked(
        self, input_text: str, expected: str
    ) -> None:
        result = _mask_secrets(input_text)
        assert result == expected
        assert "***MASKED***" in result

    @pytest.mark.parametrize(
        "key_name",
        [
            "token",
            "api_key",
            "apikey",
            "api-key",
            "password",
            "passwd",
            "pwd",
            "secret",
        ],
    )
    def test_json_known_key_names_all_masked(self, key_name: str) -> None:
        input_text = f'{{"{key_name}": "value"}}'
        result = _mask_secrets(input_text)
        assert "***MASKED***" in result
        assert "value" not in result

    def test_non_secret_stderr_sample_unchanged(self) -> None:
        """REQ-003: a plausible stderr line without a known-secret-key + quoted
        value is returned unchanged (no false positive)."""
        sample = (
            "2026-10-18 12:00:00 INFO request handled "
            "path=/api/items status=200 duration_ms=12 "
            'user="John Doe" role="assistant"'
        )
        assert _mask_secrets(sample) == sample

    def test_pattern_count_matches_inventory(self) -> None:
        """REQ-006: the pattern inventory is 8 (6 + two colon forms); no stray
        bare-token pattern slipped in."""
        from agent.secrets_masker import SECRET_PATTERNS

        assert len(SECRET_PATTERNS) == 8


class TestColonFormMasking:
    """Colon-separated `key: value` forms are masked like their `key=value` forms.

    Pins the recorded whitespace decision: quoted values are masked in full
    including whitespace; unquoted values stop at the first whitespace or newline.
    """

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            ("password: hunter2", "password: ***MASKED***"),
            ("token: abc123", "token: ***MASKED***"),
            # Key suffixes match without word boundaries, as in the = patterns
            ("access_token: abc", "access_token: ***MASKED***"),
            ("X-Api-Key: abc", "X-Api-Key: ***MASKED***"),
            # Case-insensitive, spaces around the colon
            ("PWD : s3cret", "PWD : ***MASKED***"),
        ],
    )
    def test_unquoted_colon_forms(self, input_text: str, expected: str) -> None:
        result = _mask_secrets(input_text)
        assert result == expected

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            ("api_key: 'abc def'", "api_key: ***MASKED***"),
            ('password: "two words"', "password: ***MASKED***"),
        ],
    )
    def test_quoted_colon_forms(self, input_text: str, expected: str) -> None:
        result = _mask_secrets(input_text)
        assert result == expected
        assert '"' not in result and "'" not in result

    def test_whitespace_decision_pinned(self) -> None:
        """Unquoted values stop at whitespace/newline; the next line survives."""
        assert _mask_secrets("token: abc def") == "token: ***MASKED*** def"
        masked = _mask_secrets("password: hunter2\npath=/api/items status=200")
        first, second = masked.splitlines()
        assert first == "password: ***MASKED***"
        assert second == "path=/api/items status=200"

    def test_bearer_ordering_no_partial_leak(self) -> None:
        """The Bearer pattern runs before the colon patterns; no value part survives."""
        masked = _mask_secrets("token: Bearer abc123")
        assert "abc123" not in masked
        auth = _mask_secrets("Authorization: Bearer abc123")
        assert auth.startswith("Authorization: Bearer")
        assert "abc123" not in auth

    def test_idempotence_double_application(self) -> None:
        """Applying the masker twice equals applying it once."""
        samples = [
            "token: abc123",
            "api_key: 'abc def'",
            (
                "2026-10-18 12:00:00 INFO request handled "
                "path=/api/items status=200 duration_ms=12 "
                'user="John Doe" role="assistant"'
            ),
        ]
        for sample in samples:
            once = _mask_secrets(sample)
            assert _mask_secrets(once) == once
