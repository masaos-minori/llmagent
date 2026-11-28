"""tests/mcp_servers/test_audit_redaction.py

Unit tests for the shared audit-emission contract in mcp_servers/audit.py: the
exactly-once guard, the query hash helper, and the URL redaction helper.
"""

from __future__ import annotations

import logging
from unittest.mock import patch

import mcp_servers.audit as audit_module
import orjson
import pytest
from mcp_servers.audit import (
    AuditEmission,
    hash_query_value,
    path_identifier,
    redact_url,
)


class _Sink:
    """Logger stub that records each info() message."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def info(self, message: str, *args: object, **kwargs: object) -> None:
        self.messages.append(message)

    def records(self) -> list[dict[str, object]]:
        return [orjson.loads(m) for m in self.messages]


def _emission(sink: _Sink) -> AuditEmission:
    return AuditEmission(
        sink,
        session_id="s-1",
        request_id="r-1",
        action="browser_fetch",
        server_key="web_search",
    )


class TestAuditEmission:
    def test_the_first_emit_writes_one_record_with_the_identifiers(self) -> None:
        sink = _Sink()
        emission = _emission(sink)

        wrote = emission.emit(
            target="t", outcome="ok", error_type="", detail="latency_ms=1"
        )

        assert wrote is True
        assert emission.emitted is True
        (record,) = sink.records()
        assert record["session_id"] == "s-1"
        assert record["request_id"] == "r-1"
        assert record["tool"] == "browser_fetch"
        assert record["server_key"] == "web_search"
        assert record["target"] == "t"
        assert record["outcome"] == "ok"
        assert record["detail"] == "latency_ms=1"

    def test_a_second_emit_writes_nothing_and_warns(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        sink = _Sink()
        emission = _emission(sink)
        emission.emit(target="a", outcome="ok")

        with caplog.at_level(logging.WARNING, logger=audit_module.__name__):
            wrote = emission.emit(target="b", outcome="error", error_type="x")

        assert wrote is False
        assert len(sink.messages) == 1
        assert sink.records()[0]["target"] == "a"
        assert any("second audit emission" in r.message for r in caplog.records)

    def test_a_new_emission_object_is_independent(self) -> None:
        sink = _Sink()
        _emission(sink).emit(target="a", outcome="ok")
        _emission(sink).emit(target="b", outcome="ok")

        assert len(sink.messages) == 2

    def test_not_emitted_before_the_first_emit(self) -> None:
        assert _emission(_Sink()).emitted is False


class TestHashQueryValue:
    def test_the_hash_is_16_lowercase_hex_characters(self) -> None:
        value = hash_query_value("python typing")

        assert len(value) == 16
        assert value == value.lower()
        int(value, 16)

    def test_it_is_deterministic_trimmed_and_case_insensitive(self) -> None:
        assert hash_query_value("  Python Typing ") == hash_query_value("python typing")

    def test_different_values_differ(self) -> None:
        assert hash_query_value("a") != hash_query_value("b")

    def test_the_value_is_not_recoverable_from_the_output(self) -> None:
        assert "secret" not in hash_query_value("my secret query")


class TestRedactUrl:
    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("https://Example.com/a/b", "https://example.com/a/b"),
            ("https://example.com", "https://example.com"),
            ("https://example.com/", "https://example.com"),
            ("http://example.com:8080/docs", "http://example.com/docs"),
            ("https://[2606:4700::1111]/x", "https://[2606:4700::1111]/x"),
        ],
    )
    def test_scheme_host_and_plain_path_are_kept(self, url: str, expected: str) -> None:
        assert redact_url(url) == expected

    def test_query_fragment_and_user_information_are_dropped(self) -> None:
        out = redact_url(
            "https://user:hunter2@files.example.com/report.pdf"
            "?X-Amz-Signature=abc123&token=SECRET&code=OAUTHCODE#frag-secret"
        )

        assert out == "https://files.example.com/report.pdf"
        for leaked in ("hunter2", "user", "abc123", "SECRET", "OAUTHCODE", "frag"):
            assert leaked not in out

    @pytest.mark.parametrize(
        "segment",
        [
            "4f9d8c7b6a5e4d3c2b1a0f9e8d7c6b5a",
            "abcdefabcdefabcdef",
            "AbCdEf1234567890XyZ",
            "john.doe@example.com",
            "a%20b",
            "x" * 25,
            "tok=1",
        ],
    )
    def test_token_shaped_or_unsafe_segments_are_redacted(self, segment: str) -> None:
        out = redact_url(f"https://example.com/oauth/{segment}/cb")

        assert out == "https://example.com/oauth/*/cb"
        assert segment not in out

    @pytest.mark.parametrize("segment", ["report.pdf", "v1", "a_b-c~d", "x" * 24])
    def test_short_plain_segments_are_kept(self, segment: str) -> None:
        assert redact_url(f"https://example.com/{segment}") == (
            f"https://example.com/{segment}"
        )

    def test_at_most_eight_segments_are_kept(self) -> None:
        path = "/".join(f"s{i}" for i in range(1, 12))

        out = redact_url(f"https://example.com/{path}")

        assert out == "https://example.com/s1/s2/s3/s4/s5/s6/s7/s8/..."

    @pytest.mark.parametrize(
        "url",
        ["", "not a url", "example.com/path", "https:///path", "https://[::1/x"],
    )
    def test_an_unparseable_or_incomplete_url_is_a_fixed_string(self, url: str) -> None:
        assert redact_url(url) == "invalid-url"

    def test_no_fixture_secret_survives_in_any_output(self) -> None:
        secrets = ("SECRETTOKEN", "pw123", "alice@corp.example", "sig=zzz")
        url = (
            "https://bob:pw123@host.example/users/alice@corp.example/"
            "profile?sig=zzz&access_token=SECRETTOKEN#SECRETTOKEN"
        )

        out = redact_url(url)

        for secret in secrets:
            assert secret not in out


class TestPathIdentifier:
    """REQ-006: the path-identifier helper added for MDQ. Existing servers do not call
    it, so the rest of this file is the behavior lock for their unchanged output."""

    def test_a_path_inside_an_authorized_root_is_root_relative(self) -> None:
        assert (
            path_identifier("/opt/llm/docs/report.md", ["/opt/llm/docs"]) == "report.md"
        )

    def test_the_root_itself_is_a_single_dot(self) -> None:
        assert path_identifier("/opt/llm/docs", ["/opt/llm/docs"]) == "."

    def test_a_path_outside_every_root_is_a_hash(self) -> None:
        out = path_identifier("/etc/passwd", ["/opt/llm/docs"])
        assert out == hash_query_value("/etc/passwd")
        assert len(out) == 16
        assert "passwd" not in out

    def test_the_hash_branch_uses_the_same_convention_as_the_query_hash(self) -> None:
        out = path_identifier("/opt/llm/db/mdq.sqlite", ["/opt/llm/docs"])
        assert out == hash_query_value("/opt/llm/db/mdq.sqlite")

    def test_traversal_out_of_a_root_falls_back_to_the_hash(self) -> None:
        out = path_identifier("/opt/llm/docs/../private/secret.md", ["/opt/llm/docs"])
        assert out == hash_query_value("/opt/llm/private/secret.md")
        assert "secret" not in out

    def test_no_filesystem_access_is_needed_for_the_root_relative_branch(self) -> None:
        # A path that does not exist still resolves to the root-relative form, which
        # shows the helper normalizes textually rather than touching the filesystem.
        assert path_identifier("/opt/llm/docs/nope.md", ["/opt/llm/docs"]) == "nope.md"

    def test_the_roots_are_supplied_and_no_configuration_is_read(self) -> None:
        # The helper is policy-only: the caller supplies the roots, so a caller with a
        # shrunk allowlist gets the hash branch for a path under the former root.
        out = path_identifier("/opt/llm/docs/report.md", ["/opt/llm/docs/team"])
        assert out == hash_query_value("/opt/llm/docs/report.md")

    def test_the_helper_writes_nothing_to_the_logger(self) -> None:
        sink = _Sink()
        with patch.object(audit_module, "_logger", sink):
            path_identifier("/etc/passwd", ["/opt/llm/docs"])
        assert sink.messages == []


def test_the_module_docstring_has_no_plaintext_query_preview_example() -> None:
    assert "query_preview" not in (audit_module.__doc__ or "")
