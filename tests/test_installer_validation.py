#!/usr/bin/env python3
"""tests/test_installer_validation.py
Unit tests for mcp/installer_validation.py — validate_server_name, name_to_module, name_to_class.
"""

from __future__ import annotations

import pytest

from scripts.mcp.installer_validation import (
    name_to_class,
    name_to_module,
    validate_server_name,
)


# ── validate_server_name ──


class TestValidateServerName:
    def test_valid_simple_name(self):
        result = validate_server_name("my-server")
        assert result is None

    def test_valid_alphanumeric_name(self):
        result = validate_server_name("server123")
        assert result is None

    def test_valid_underscore_name(self):
        result = validate_server_name("a_b_c")
        assert result is not None
        assert "Invalid server name" in result

    def test_empty_string_raises_error(self):
        result = validate_server_name("")
        assert result == "Server name must not be empty."

    def test_none_returns_empty_error(self):
        result = validate_server_name(None)  # type: ignore
        assert result == "Server name must not be empty."

    def test_starts_with_digit_rejected(self):
        result = validate_server_name("1server")
        assert result is not None
        assert "Invalid server name" in result
        assert "1server" in result

    def test_uppercase_rejected(self):
        result = validate_server_name("MyServer")
        assert result is not None
        assert "Invalid server name" in result

    def test_special_characters_rejected(self):
        result = validate_server_name("my@server")
        assert result is not None
        assert "Invalid server name" in result

    def test_spaces_rejected(self):
        result = validate_server_name("my server")
        assert result is not None
        assert "Invalid server name" in result

    def test_emoji_rejected(self):
        result = validate_server_name("server🚀")
        assert result is not None
        assert "Invalid server name" in result

    def test_hyphens_only_rejected(self):
        result = validate_server_name("---")
        assert result is not None

    def test_single_letter_valid(self):
        result = validate_server_name("a")
        assert result is None


# ── name_to_module ──


class TestNameToModule:
    def test_hyphens_converted_to_underscores(self):
        result = name_to_module("my-server")
        assert result == "my_server"

    def test_already_underscores_preserved(self):
        result = name_to_module("my_server")
        assert result == "my_server"

    def test_uppercase_converted_to_lowercase(self):
        result = name_to_module("MyServer")
        assert result == "myserver"

    def test_mixed_hyphens_and_underscores(self):
        result = name_to_module("my-server_name")
        assert result == "my_server_name"

    def test_digits_preserved(self):
        result = name_to_module("server123")
        assert result == "server123"

    def test_special_characters_become_underscores(self):
        result = name_to_module("my@server!")
        assert result == "my_server_"

    def test_empty_string(self):
        result = name_to_module("")
        assert result == ""


# ── name_to_class ──


class TestNameToClass:
    def test_hyphens_converted_to_pascalcase(self):
        result = name_to_class("my-server")
        assert result == "MyServer"

    def test_single_word(self):
        result = name_to_class("server")
        assert result == "Server"

    def test_uppercase_preserved_in_capitalization(self):
        result = name_to_class("myServer")
        assert result == "Myserver"

    def test_multiple_hyphens(self):
        result = name_to_class("one-two-three")
        assert result == "OneTwoThree"

    def test_underscores_as_separators(self):
        result = name_to_class("my_server_name")
        assert result == "MyServerName"

    def test_mixed_hyphens_and_underscores(self):
        result = name_to_class("my-server_name-test")
        assert result == "MyServerNameTest"

    def test_digits_preserved(self):
        result = name_to_class("server123")
        assert result == "Server123"

    def test_empty_string(self):
        result = name_to_class("")
        assert result == ""
