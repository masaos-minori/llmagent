"""Unit tests for tool_executor helper functions.

This file contains tests for:
- tool_call_key: generates consistent hash keys for (tool name, args) pairs
- is_side_effect: identifies tools with side effects
"""

import hashlib
from typing import Any

import orjson
from shared.tool_executor import is_side_effect, tool_call_key


def test_tool_call_key_consistency() -> None:
    """Test that tool_call_key generates consistent hash keys for identical inputs."""
    # Test basic case
    key1 = tool_call_key("read_file", {"path": "/tmp/test.txt"})
    key2 = tool_call_key("read_file", {"path": "/tmp/test.txt"})
    assert key1 == key2
    
    # Test different tools have different keys
    key3 = tool_call_key("write_file", {"path": "/tmp/test.txt"})
    assert key1 != key3
    
    # Test different args have different keys
    key4 = tool_call_key("read_file", {"path": "/tmp/other.txt"})
    assert key1 != key4
    
    # Test order independence (sorted args)
    key5 = tool_call_key("read_file", {"path": "/tmp/test.txt", "mode": "r"})
    key6 = tool_call_key("read_file", {"mode": "r", "path": "/tmp/test.txt"})
    assert key5 == key6


def test_tool_call_key_hash_format() -> None:
    """Test that tool_call_key returns correct hash format."""
    key = tool_call_key("test_tool", {"arg": "value"})
    # Should be a valid hex string (32 characters for MD5)
    assert len(key) == 32
    assert all(c in '0123456789abcdef' for c in key)


def test_is_side_effect_write_tools() -> None:
    """Test that write tools are correctly identified as side effect tools."""
    # Test various write tools from WRITE_TOOLS constant
    from shared.tool_constants import WRITE_TOOLS
    for tool_name in WRITE_TOOLS:
        assert is_side_effect(tool_name) is True


def test_is_side_effect_delete_tools() -> None:
    """Test that delete tools are correctly identified as side effect tools."""
    # Test various delete tools from DELETE_TOOLS constant
    from shared.tool_constants import DELETE_TOOLS
    for tool_name in DELETE_TOOLS:
        assert is_side_effect(tool_name) is True


def test_is_side_effect_shell_tools() -> None:
    """Test that shell tools are correctly identified as side effect tools."""
    assert is_side_effect("shell_run") is True


def test_is_side_effect_non_side_effect_tools() -> None:
    """Test that non-side-effect tools are correctly identified."""
    # Test various read-only tools
    read_only_tools = ["read_file", "list_files", "search_files", "get_metadata"]
    for tool_name in read_only_tools:
        assert is_side_effect(tool_name) is False


def test_is_side_effect_unknown_tool() -> None:
    """Test that unknown tools default to non-side-effect."""
    # Unknown tools should return False
    assert is_side_effect("unknown_tool") is False


def test_tool_call_key_with_complex_args() -> None:
    """Test tool_call_key with complex arguments."""
    args1 = {
        "path": "/tmp/test.txt",
        "content": "hello world",
        "metadata": {"author": "test", "version": 1},
        "options": ["a", "b", "c"]
    }
    args2 = {
        "content": "hello world",
        "path": "/tmp/test.txt", 
        "options": ["a", "b", "c"],
        "metadata": {"author": "test", "version": 1}
    }
    
    key1 = tool_call_key("write_file", args1)
    key2 = tool_call_key("write_file", args2)
    assert key1 == key2


def test_tool_call_key_empty_args() -> None:
    """Test tool_call_key with empty arguments."""
    key1 = tool_call_key("read_file", {})
    key2 = tool_call_key("read_file", {})
    assert key1 == key2