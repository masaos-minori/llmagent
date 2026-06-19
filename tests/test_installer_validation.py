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
        assert validate_server_name("my-server") == "my-server"

    def test_valid_alphanumeric_name(self):
        assert validate_server_name("server123") == "server123"

    def test_invalid_underscore_name(self):
        with pytest.raises(ValueError, match="Invalid server name"):
            validate_server_name("a_b_c")

    def test_empty_string_raises_error(self):
        with pytest.raises(ValueError, match="must not be empty"):
            validate_server_name("")

    def test_none_raises_error(self):
        with pytest.raises(ValueError, match="must not be empty"):
            validate_server_name(None)  # type: ignore

    def test_starts_with_digit_rejected(self):
        with pytest.raises(ValueError, match="Invalid server name.*1server"):
            validate_server_name("1server")

    def test_uppercase_rejected(self):
        with pytest.raises(ValueError, match="Invalid server name"):
            validate_server_name("MyServer")

    def test_special_characters_rejected(self):
        with pytest.raises(ValueError, match="Invalid server name"):
            validate_server_name("my@server")

    def test_spaces_rejected(self):
        with pytest.raises(ValueError, match="Invalid server name"):
            validate_server_name("my server")

    def test_emoji_rejected(self):
        with pytest.raises(ValueError, match="Invalid server name"):
            validate_server_name("server🚀")

    def test_hyphens_only_rejected(self):
        with pytest.raises(ValueError, match="Invalid server name"):
            validate_server_name("---")

    def test_single_letter_valid(self):
        assert validate_server_name("a") == "a"


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
