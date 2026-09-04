"""tests/agent/test_http_lifecycle_command_validator.py

Unit tests for CommandValidator and related error classes.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from agent.http_lifecycle_command_validator import CommandValidator
from agent.http_lifecycle_errors import HttpStartupError, StartupFailure

_TEST_SERVER_KEY = "test_server"


class TestStartupFailure:
    """Tests for the StartupFailure dataclass."""

    def test_creation(self):
        failure = StartupFailure(
            server_key="my_server",
            reason="Command not found",
            stderr_full="",
        )
        assert failure.server_key == "my_server"
        assert failure.reason == "Command not found"
        assert failure.stderr_full == ""

    def test_with_stderr_content(self):
        failure = StartupFailure(
            server_key="my_server",
            reason="Startup failed",
            stderr_full="error: connection refused\nwarning: retrying",
        )
        assert failure.stderr_full == "error: connection refused\nwarning: retrying"

    def test_large_stderr_truncated_in_error_message(self):
        large_stderr = "x" * 100_000
        failure = StartupFailure(
            server_key="my_server",
            reason="Startup failed",
            stderr_full=large_stderr,
        )
        error = HttpStartupError(failure)
        msg = str(error)
        # Only last 65536 chars should appear in the message
        assert len(msg) < len(large_stderr) + 100  # Allow some overhead for formatting

    def test_masked_secrets_in_stderr(self):
        failure = StartupFailure(
            server_key="my_server",
            reason="Auth failed",
            stderr_full='password=secret123\napi_key=abc123',
        )
        error = HttpStartupError(failure)
        msg = str(error)
        assert "MASKED" in msg
        assert "secret123" not in msg
        assert "abc123" not in msg

    def test_no_stderr_tail_when_empty(self):
        failure = StartupFailure(
            server_key="my_server",
            reason="Simple error",
            stderr_full="",
        )
        error = HttpStartupError(failure)
        msg = str(error)
        assert "(stderr_tail:" not in msg

    def test_exception_chain(self):
        failure = StartupFailure(
            server_key="my_server",
            reason="Test failure",
            stderr_full="",
        )
        error = HttpStartupError(failure)
        assert isinstance(error, RuntimeError)
        assert error.failure is failure  # type: ignore[attr-defined]
        assert str(error) == "my_server: Test failure"


class TestCommandValidatorValidate:
    """Tests for CommandValidator.validate()."""

    def test_allowed_command_python(self):
        validator = CommandValidator()
        result = validator.validate(_TEST_SERVER_KEY, "python3")
        assert result is not None
        assert os.path.isabs(result)
        assert os.path.isfile(result)

    def test_allowed_command_node(self):
        validator = CommandValidator()
        if shutil.which("node"):
            result = validator.validate(_TEST_SERVER_KEY, "node")
            assert result is not None
            assert os.path.isabs(result)
        else:
            pytest.skip("node not available in PATH")

    def test_disallowed_command_raises(self):
        custom_validator = CommandValidator(
            allowed_commands=frozenset({"python3"}),
        )
        with pytest.raises(HttpStartupError) as exc_info:
            custom_validator.validate(_TEST_SERVER_KEY, "npm")
        assert "not in the allowed commands list" in str(exc_info.value)

    def test_command_not_in_path_raises(self):
        validator = CommandValidator()
        with pytest.raises(HttpStartupError) as exc_info:
            validator.validate(_TEST_SERVER_KEY, "nonexistent_cmd_xyz_12345")
        assert "not found in PATH" in str(exc_info.value)

    def test_symlink_resolved_to_non_file_raises(self):
        """Test that symlink-resolved path that is not a regular file is rejected."""
        # Create a temporary directory (not a file) and make a symlink point to it
        temp_dir = Path("/tmp/test_validator_symlink_target")
        temp_dir.mkdir(exist_ok=True)
        try:
            symlink_path = Path("/tmp/test_validator_symlink")
            symlink_path.symlink_to(temp_dir)
            try:
                custom_validator = CommandValidator(
                    allowed_commands=frozenset({"symlink_test"}),
                )
                # Patch shutil.which to return our symlink
                with patch.object(shutil, "which", return_value=str(symlink_path)):
                    with pytest.raises(HttpStartupError) as exc_info:
                        custom_validator.validate(_TEST_SERVER_KEY, "symlink_test")
                    assert "is not a regular file" in str(exc_info.value)
            finally:
                symlink_path.unlink(missing_ok=True)
        except OSError:
            pytest.skip("Cannot create symlinks in /tmp")
        finally:
            try:
                temp_dir.rmdir()
            except OSError:
                pass

    def test_custom_allowed_commands(self):
        custom_validator = CommandValidator(
            allowed_commands=frozenset({"custom_cmd", "python3"}),
        )
        result = custom_validator.validate(_TEST_SERVER_KEY, "python3")
        assert result is not None
        assert os.path.isabs(result)

    def test_python3_prefix_allows_python3x(self):
        """Commands starting with 'python3' are allowed even if not in allowlist."""
        # python3.x variants should be allowed
        custom_validator = CommandValidator(
            allowed_commands=frozenset({"python3"}),
        )
        # Find a python3.x binary
        for name in ["python3.13", "python3.12", "python3.11", "python3"]:
            if shutil.which(name):
                result = custom_validator.validate(_TEST_SERVER_KEY, name)
                assert result is not None
                break
        else:
            pytest.skip("No python3.x binary found")

    def test_validate_returns_absolute_path(self):
        validator = CommandValidator()
        result = validator.validate(_TEST_SERVER_KEY, "python3")
        assert os.path.isabs(result)

    def test_validate_realpath_resolves_symlinks(self):
        """validate() returns realpath, not the original which() path."""
        validator = CommandValidator()
        result = validator.validate(_TEST_SERVER_KEY, "python3")
        # The result should be the resolved realpath
        assert result == os.path.realpath(result)
