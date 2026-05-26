"""
Tests for rag_utils.py — pure utility functions with no external dependencies.
These serve as the reference pattern for unit tests in this project.
"""

import struct

import pytest
from hypothesis import given
from hypothesis import strategies as st
from rag_utils import floats_to_blob, normalize_unicode, validate_url

# ── normalize_unicode ────────────────────────────────────────────────────────


class TestNormalizeUnicode:
    def test_fullwidth_digits_to_ascii(self):
        assert normalize_unicode("１２３") == "123"

    def test_fullwidth_latin_to_ascii(self):
        assert normalize_unicode("ａｂｃ") == "abc"

    def test_plain_ascii_unchanged(self):
        assert normalize_unicode("hello") == "hello"

    def test_empty_string(self):
        assert normalize_unicode("") == ""

    def test_non_str_raises_type_error(self):
        with pytest.raises(TypeError):
            normalize_unicode(123)

    @given(st.text())
    def test_idempotent(self, text: str):
        # NFKC normalization applied twice must equal one application
        once = normalize_unicode(text)
        assert normalize_unicode(once) == once


# ── floats_to_blob ───────────────────────────────────────────────────────────


class TestFloatsToBlob:
    def test_round_trip_single_value(self):
        blob = floats_to_blob([1.0])
        (unpacked,) = struct.unpack("<1f", blob)
        assert unpacked == pytest.approx(1.0)

    def test_round_trip_384_dims(self):
        values = [float(i) for i in range(384)]
        blob = floats_to_blob(values)
        assert len(blob) == 384 * 4  # 4 bytes per float32
        unpacked = list(struct.unpack(f"<{384}f", blob))
        assert unpacked == pytest.approx(values)

    def test_empty_list_raises_value_error(self):
        with pytest.raises(ValueError, match="empty"):
            floats_to_blob([])

    def test_non_list_raises_type_error(self):
        with pytest.raises(TypeError):
            floats_to_blob((1.0, 2.0))

    def test_non_numeric_first_element_raises_value_error(self):
        with pytest.raises(ValueError):
            floats_to_blob(["a", "b"])


# ── validate_url ─────────────────────────────────────────────────────────────


class TestValidateUrl:
    @pytest.mark.parametrize(
        "url",
        [
            "http://example.com",
            "https://example.com/path?q=1",
            "https://sub.domain.org",
        ],
    )
    def test_valid_urls(self, url: str):
        assert validate_url(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "ftp://example.com",
            "file:///etc/passwd",
            "not-a-url",
            "",
            "http://",
        ],
    )
    def test_invalid_urls(self, url: str):
        assert validate_url(url) is False
