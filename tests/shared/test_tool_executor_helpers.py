"""Unit tests for tool_executor helper functions.

This file contains tests for:
- tool_hash_key: generates consistent hash keys for (tool name, args) pairs
"""

from shared.tool_executor_helpers import (
    format_transport_error,
    tool_hash_key,
)


def test_tool_hash_key_consistency() -> None:
    """Test that tool_hash_key generates consistent hash keys for identical inputs."""
    # Test basic case
    key1 = tool_hash_key("read_file", {"path": "/tmp/test.txt"})
    key2 = tool_hash_key("read_file", {"path": "/tmp/test.txt"})
    assert key1 == key2

    # Test different tools have different keys
    key3 = tool_hash_key("write_file", {"path": "/tmp/test.txt"})
    assert key1 != key3

    # Test different args have different keys
    key4 = tool_hash_key("read_file", {"path": "/tmp/other.txt"})
    assert key1 != key4

    # Test order independence (sorted args)
    key5 = tool_hash_key("read_file", {"path": "/tmp/test.txt", "mode": "r"})
    key6 = tool_hash_key("read_file", {"mode": "r", "path": "/tmp/test.txt"})
    assert key5 == key6


def test_tool_hash_key_hash_format() -> None:
    """Test that tool_hash_key returns correct hash format."""
    key = tool_hash_key("test_tool", {"arg": "value"})
    # Should be a valid hex string (32 characters for MD5)
    assert len(key) == 32
    assert all(c in "0123456789abcdef" for c in key)


def test_format_transport_error_summary_includes_all_fields() -> None:
    """Test that TransportErrorInfo.summary includes status_code and partial fields."""
    info = format_transport_error(
        source="mcp",
        phase="call_tool",
        kind="http_error",
        url="http://x",
        status_code=503,
        retryable=True,
        partial=False,
    )
    assert "MCP" in info.summary
    assert "http_error" in info.summary
    assert "call_tool" in info.summary
    assert "503" in info.summary
    assert "retryable=True" in info.summary
    assert "partial=False" in info.summary


def test_format_transport_error_detail_is_valid_json() -> None:
    """Test that TransportErrorInfo.detail is valid JSON with all expected fields."""
    import json

    info = format_transport_error(
        source="mcp",
        phase="call_tool",
        kind="timeout",
        url="http://x",
        status_code=None,
        retryable=False,
        partial=True,
    )
    parsed = json.loads(info.detail)
    assert parsed == {
        "source": "mcp",
        "phase": "call_tool",
        "kind": "timeout",
        "status_code": None,
        "url": "http://x",
        "retryable": False,
        "partial": True,
    }


def test_tool_hash_key_with_complex_args() -> None:
    """Test tool_hash_key with complex arguments."""
    args1 = {
        "path": "/tmp/test.txt",
        "content": "hello world",
        "metadata": {"author": "test", "version": 1},
        "options": ["a", "b", "c"],
    }
    args2 = {
        "content": "hello world",
        "path": "/tmp/test.txt",
        "options": ["a", "b", "c"],
        "metadata": {"author": "test", "version": 1},
    }

    key1 = tool_hash_key("write_file", args1)
    key2 = tool_hash_key("write_file", args2)
    assert key1 == key2


def test_tool_hash_key_empty_args() -> None:
    """Test tool_hash_key with empty arguments."""
    key1 = tool_hash_key("read_file", {})
    key2 = tool_hash_key("read_file", {})
    assert key1 == key2


def test_tool_hash_key_differs_for_different_tool_names() -> None:
    """Test that tool_hash_key generates different keys for different tool names with same args."""
    key_a = tool_hash_key("tool_a", {"x": 1})
    key_b = tool_hash_key("tool_b", {"x": 1})
    assert key_a != key_b, "Different tool names must produce different hash keys"

    # Also verify with empty args
    key_c = tool_hash_key("tool_c", {})
    key_d = tool_hash_key("tool_d", {})
    assert key_c != key_d


def test_tool_hash_key_same_for_same_tool_and_args() -> None:
    """Test that tool_hash_key generates identical keys for same tool and args."""
    key1 = tool_hash_key("my_tool", {"a": 1})
    key2 = tool_hash_key("my_tool", {"a": 1})
    assert key1 == key2, "Same tool and args must produce identical hash keys"

    # Verify with complex args
    key3 = tool_hash_key("complex_tool", {"nested": {"key": "value"}})
    key4 = tool_hash_key("complex_tool", {"nested": {"key": "value"}})
    assert key3 == key4
