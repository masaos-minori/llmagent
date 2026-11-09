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
        """REQ-006: the pattern inventory is 14 (8 secmask001 patterns + six diagmask001
        shapes); no stray bare-token pattern slipped in."""
        from agent.secrets_masker import SECRET_PATTERNS

        assert len(SECRET_PATTERNS) == 14


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


class TestExtendedShapeMasking:
    """diagmask001 REQ-003/REQ-005: the extended pattern inventory masks the new
    shapes with no part of the secret left, keeps the empty-value exemption, and
    stays idempotent. Red until the extended SECRET_PATTERNS land (Plan Phase 1).
    """

    @pytest.mark.parametrize(
        "input_text,value",
        [
            ("authorization=xyz", "xyz"),
            ("credential=xyz", "xyz"),
            ("private_key=xyz", "xyz"),
            ("bearer=xyz", "xyz"),
            ("authorization: xyz", "xyz"),
            ("credential: abc", "abc"),
            ("private_key: abc", "abc"),
            ('{"authorization": "xyz"}', "xyz"),
            ('{"credential": "xyz"}', "xyz"),
            ('{"private_key": "xyz"}', "xyz"),
            # Composite quoted-JSON keys: not masked by the 8-pattern inventory
            # today, but refused by the old diagnostic guard (REQ-002).
            ('{"access_token": "xyz"}', "xyz"),
            ('{"auth_token": "xyz"}', "xyz"),
            ('{"client_secret": "xyz"}', "xyz"),
        ],
    )
    def test_new_key_names_masked(self, input_text: str, value: str) -> None:
        """New key names mask in the =, : and quoted-JSON forms."""
        result = _mask_secrets(input_text)
        assert value not in result
        assert "***MASKED***" in result

    def test_arrow_separator(self) -> None:
        """REQ-003: the `=>` separator masks the value."""
        assert _mask_secrets("api_key => topsecretxyz") == "api_key => ***MASKED***"

    def test_bare_jwt_masked(self) -> None:
        """A three-segment eyJ token in prose is fully masked; a shorter eyJ
        word stays unchanged."""
        token = "eyJhbGciOiJIUzI1NiJ9.c2VjcmV0cGF5bG9hZA.qS3pR8xYvZ0aB1cD2eF3gH4i"
        result = _mask_secrets(f"the token is {token}")
        assert "eyJ" not in result
        assert result == "the token is ***MASKED***"
        assert _mask_secrets("retry eyJabc counter") == "retry eyJabc counter"

    def test_url_credential_masked(self) -> None:
        """Only the password segment of a scheme://user:password@host URL is
        masked; a plain URL without userinfo is unchanged."""
        result = _mask_secrets("postgres://admin:s3cr3tpw@db:5432/x")
        assert "s3cr3tpw" not in result
        assert result == "postgres://admin:***MASKED***@db:5432/x"
        plain = "https://example.com/api/items"
        assert _mask_secrets(plain) == plain

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("x=https://LONECRED@h/p", "x=https://***MASKED***@h/p"),
            (
                "raw=https://RAWJWTTOKENEXAMPLEABC123@svc.io/x",
                "raw=https://***MASKED***@svc.io/x",
            ),
            ("redis://:pw@host:6379/0", "redis://***MASKED***@host:6379/0"),
        ],
    )
    def test_bare_password_url_masked(self, raw: str, expected: str) -> None:
        """A bare-password userinfo (scheme://token@host) is masked like the
        colon form (secmask002 REQ-001)."""
        result = _mask_secrets(raw)
        assert result == expected

    def test_username_only_userinfo_is_masked(self) -> None:
        """Accepted over-mask: username-only userinfo is masked too, matching
        _redact_remote_url in mcp_servers/git/repository_state.py."""
        assert (
            _mask_secrets("ssh://git@github.com/o/r.git")
            == "ssh://***MASKED***@github.com/o/r.git"
        )

    @pytest.mark.parametrize(
        "text",
        [
            "https://example.com/api/items",
            "https://example.com:8080/a?e=a@b.co",
            "mail a@b.com",
            "a_b@domain.org",
        ],
    )
    def test_userinfo_negative_cases(self, text: str) -> None:
        """Plain URLs (host:port, query with @) and bare emails are unchanged
        (secmask002 REQ-003)."""
        assert _mask_secrets(text) == text

    def test_scheme_preserved_with_authorization_key(self) -> None:
        """The extended authorization key names must not mask the scheme keyword
        the pre-existing Authorization pattern already handles (secmask001 AC-4)."""
        assert (
            _mask_secrets("Authorization: Bearer abc123")
            == "Authorization: Bearer ***MASKED***"
        )

    def test_empty_json_value_not_masked(self) -> None:
        """UNK-01 exemption: an empty quoted-JSON value is returned unchanged."""
        assert _mask_secrets('{"token": ""}') == '{"token": ""}'
        assert _mask_secrets('{"password": ""}') == '{"password": ""}'

    def test_extended_idempotence(self) -> None:
        """AC-5: applying the masker twice equals applying it once for every new
        shape."""
        samples = [
            "api_key => topsecretxyz",
            "the token is eyJhbGciOiJIUzI1NiJ9.c2VjcmV0cGF5bG9hZA.qS3pR8xYvZ0aB1cD2eF3gH4i",
            "postgres://admin:s3cr3tpw@db:5432/x",
            "https://LONECRED@h/p",
            '{"credential": "hunter2"}',
            "authorization: abcdefghijkl",
            '{"private_key": "abc"}',
        ]
        for sample in samples:
            once = _mask_secrets(sample)
            assert _mask_secrets(once) == once

    def test_large_input_terminates(self) -> None:
        """Plan Risks 4: a 10 000-char mixed payload completes and stays
        idempotent."""
        chunk = (
            "token=abcdefghij api_key => xyz123 credential: abcdefgh "
            '{"note": "postgres://u:p@h/x"} '
        )
        payload = (chunk * 300)[:10000]
        assert len(payload) == 10000
        result = _mask_secrets(payload)
        assert isinstance(result, str)
        assert _mask_secrets(result) == result
