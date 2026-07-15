"""Unit tests for tool_executor helper functions.

This file contains tests for:
- tool_hash_key: generates consistent hash keys for (tool name, args) pairs
- is_side_effect: identifies tools with side effects
"""

from shared.tool_executor_helpers import (
    format_transport_error,
    is_side_effect,
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


def test_is_side_effect_unknown_tool() -> None:
    """Test that unknown tools default to non-side-effect."""
    # Unknown tools should return False
    assert is_side_effect("unknown_tool") is False


def test_is_side_effect_git_write_tools() -> None:
    """Test that Git write tools are correctly identified as side effect tools."""
    from shared.tool_constants import GIT_WRITE_TOOLS

    for tool_name in GIT_WRITE_TOOLS:
        assert is_side_effect(tool_name) is True


def test_is_side_effect_github_write_tools() -> None:
    """Test that GitHub write tools are correctly identified as side effect tools."""
    from shared.tool_constants import GITHUB_WRITE_TOOLS

    for tool_name in GITHUB_WRITE_TOOLS:
        assert is_side_effect(tool_name) is True


def test_is_side_effect_github_dangerous_tools() -> None:
    """Test that GitHub dangerous tools are correctly identified as side effect tools."""
    from shared.tool_constants import GITHUB_DANGEROUS_TOOLS

    for tool_name in GITHUB_DANGEROUS_TOOLS:
        assert is_side_effect(tool_name) is True


def test_is_side_effect_cicd_write_tools() -> None:
    """Test that CI/CD write tools are correctly identified as side effect tools."""
    from shared.tool_constants import CICD_WRITE_TOOLS

    for tool_name in CICD_WRITE_TOOLS:
        assert is_side_effect(tool_name) is True


def test_is_side_effect_rag_write_tools() -> None:
    """Test that RAG write tools are correctly identified as side effect tools."""
    from shared.tool_constants import RAG_WRITE_TOOLS

    for tool_name in RAG_WRITE_TOOLS:
        assert is_side_effect(tool_name) is True


def test_is_side_effect_mdq_write_tools() -> None:
    """Test that MDQ write/admin tools are correctly identified as side effect tools."""
    from shared.tool_constants import MDQ_WRITE_TOOLS

    for tool_name in MDQ_WRITE_TOOLS:
        assert is_side_effect(tool_name) is True


def test_is_side_effect_non_side_effect_tools() -> None:
    """Test that non-side-effect tools are correctly identified."""
    # Test various read-only tools
    read_only_tools = [
        "read_file",
        "list_files",
        "search_files",
        "get_metadata",
        "search_docs",
        "rag_run_pipeline",
        "get_workflow_status",
    ]
    for tool_name in read_only_tools:
        assert is_side_effect(tool_name) is False


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
