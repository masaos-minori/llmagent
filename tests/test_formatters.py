"""
tests/test_formatters.py
Unit tests for shared/formatters.py: pure formatting utilities.
"""

from __future__ import annotations

from shared.formatters import fmt_kvlog, fmt_md_link, fmt_size, truncate


class TestTruncate:
    def test_returns_text_when_shorter_than_max(self) -> None:
        assert truncate("hello", 10) == "hello"

    def test_returns_text_when_exactly_max(self) -> None:
        assert truncate("hello", 5) == "hello"

    def test_truncates_and_appends_ellipsis(self) -> None:
        result = truncate("hello world", 5)
        assert result == "hello..."
        assert len(result) == 8

    def test_empty_string(self) -> None:
        assert truncate("", 5) == ""

    def test_zero_max_chars(self) -> None:
        result = truncate("hello", 0)
        assert result == "..."
        assert len(result) == 3


class TestFmtSize:
    def test_bytes(self) -> None:
        assert fmt_size(0) == "0 B"
        assert fmt_size(1) == "1 B"
        assert fmt_size(1023) == "1023 B"

    def test_kilobytes_at_boundary(self) -> None:
        assert fmt_size(1024) == "1 KB"

    def test_kilobytes(self) -> None:
        assert fmt_size(2048) == "2 KB"
        assert fmt_size(1536) == "1 KB"
        assert fmt_size(1024 * 1024 - 1) == "1023 KB"

    def test_megabytes_at_boundary(self) -> None:
        assert fmt_size(1024 * 1024) == "1 MB"

    def test_megabytes(self) -> None:
        assert fmt_size(5 * 1024 * 1024) == "5 MB"
        assert fmt_size(1024 * 1024 * 1024) == "1024 MB"


class TestFmtMdLink:
    def test_basic_link(self) -> None:
        assert (
            fmt_md_link("text", "https://example.com") == "[text](https://example.com)"
        )

    def test_empty_text(self) -> None:
        assert fmt_md_link("", "https://example.com") == "[](https://example.com)"

    def test_empty_url(self) -> None:
        assert fmt_md_link("text", "") == "[text]()"

    def test_special_characters(self) -> None:
        result = fmt_md_link("hello world", "https://a.com/p?q=1&r=2")
        assert result == "[hello world](https://a.com/p?q=1&r=2)"


class TestFmtKvlog:
    def test_basic(self) -> None:
        result = fmt_kvlog("search", provider="bing", n=10)
        assert result == "op=search provider=bing n=10"

    def test_omits_none_values(self) -> None:
        result = fmt_kvlog("read", path="/tmp", error=None)
        assert "error=" not in result
        assert result == "op=read path=/tmp"

    def test_all_values_none(self) -> None:
        result = fmt_kvlog("test", a=None, b=None)
        assert result == "op=test"

    def test_no_kwargs(self) -> None:
        assert fmt_kvlog("ping") == "op=ping"

    def test_bool_values(self) -> None:
        result = fmt_kvlog("check", ok=True, cached=False)
        assert result == "op=check ok=True cached=False"

    def test_int_and_str_mixed(self) -> None:
        result = fmt_kvlog("write", path="/tmp/f", size=42)
        assert "op=write" in result
        assert "path=/tmp/f" in result
        assert "size=42" in result
