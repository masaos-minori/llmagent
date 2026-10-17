"""tests/agent/test_http_lifecycle_command_validator.py

Unit tests for CommandValidator and related error classes.
"""

from __future__ import annotations

import logging
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
            stderr_full="password=secret123\napi_key=abc123",
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
        """Bounded interpreter match: real variants pass, 'python3evil' is rejected."""
        custom_validator = CommandValidator(
            allowed_commands=frozenset({"python3"}),
        )
        fixtures_dir = Path("/tmp/validator_fixtures")
        fixtures_dir.mkdir(exist_ok=True)
        try:
            for name in ["python3", "python3.11", "python3.12"]:
                fixture = fixtures_dir / name
                try:
                    fixture.write_text("")
                    with patch.object(shutil, "which", return_value=str(fixture)):
                        result = custom_validator.validate(_TEST_SERVER_KEY, name)
                        assert os.path.isabs(result)
                        assert os.path.isfile(result)
                finally:
                    fixture.unlink(missing_ok=True)
            # Crafted basename that merely starts with 'python3' must be rejected.
            evil = fixtures_dir / "python3evil"
            try:
                evil.write_text("")
                with patch.object(shutil, "which", return_value=str(evil)):
                    with pytest.raises(HttpStartupError) as exc_info:
                        custom_validator.validate(_TEST_SERVER_KEY, "python3evil")
                assert "not in the allowed commands list" in str(exc_info.value)
            finally:
                evil.unlink(missing_ok=True)
        finally:
            try:
                fixtures_dir.rmdir()
            except OSError:
                pass

    def test_python3_evil_rejected(self):
        """Crafted basename 'python3evil' (starts with python3) raises HttpStartupError."""
        custom_validator = CommandValidator(
            allowed_commands=frozenset({"python3"}),
        )
        fixtures_dir = Path("/tmp/validator_fixtures")
        fixtures_dir.mkdir(exist_ok=True)
        try:
            evil = fixtures_dir / "python3evil"
            try:
                evil.write_text("")
                with patch.object(shutil, "which", return_value=str(evil)):
                    with pytest.raises(HttpStartupError) as exc_info:
                        custom_validator.validate(_TEST_SERVER_KEY, "python3evil")
                assert "not in the allowed commands list" in str(exc_info.value)
            finally:
                evil.unlink(missing_ok=True)
        finally:
            try:
                fixtures_dir.rmdir()
            except OSError:
                pass

    def test_interpreter_variants_accepted(self):
        """Real interpreter basenames python3/.11/.12 validate to an absolute path."""
        validator = CommandValidator()
        fixtures_dir = Path("/tmp/validator_fixtures")
        fixtures_dir.mkdir(exist_ok=True)
        try:
            for name in ["python3", "python3.11", "python3.12"]:
                fixture = fixtures_dir / name
                try:
                    fixture.write_text("")
                    with patch.object(shutil, "which", return_value=str(fixture)):
                        result = validator.validate(_TEST_SERVER_KEY, name)
                        assert os.path.isabs(result)
                        assert os.path.isfile(result)
                finally:
                    fixture.unlink(missing_ok=True)
        finally:
            try:
                fixtures_dir.rmdir()
            except OSError:
                pass

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


class TestCommandValidatorFilterEnv:
    """Tests for CommandValidator.filter_env() (default-deny allowlist)."""

    _FAKE_SECRET = "fake-parent-secret-value"

    def test_inherited_denylist_keys_stripped_when_cfg_env_empty(self):
        with patch.dict(
            os.environ,
            {
                "LD_PRELOAD": "/x",
                "LD_LIBRARY_PATH": "/y",
                "PYTHONPATH": "/z",
                "PATH": "/usr/bin",
            },
            clear=False,
        ):
            result = CommandValidator().filter_env({})
        assert result is not None
        assert result["PATH"] == "/usr/bin"
        assert "LD_PRELOAD" not in result
        assert "LD_LIBRARY_PATH" not in result
        assert "PYTHONPATH" not in result

    def test_unlisted_parent_vars_are_not_inherited(self):
        with patch.dict(
            os.environ,
            {"FAKE_PARENT_SECRET": self._FAKE_SECRET, "BENIGN_A": "a", "BENIGN_B": "b"},
            clear=False,
        ):
            result = CommandValidator().filter_env({})
        assert result is not None
        assert "FAKE_PARENT_SECRET" not in result
        assert "BENIGN_A" not in result
        assert "BENIGN_B" not in result
        assert self._FAKE_SECRET not in result.values()

    def test_allowlisted_parent_vars_are_inherited(self):
        with patch.dict(
            os.environ,
            {"PATH": "/usr/bin", "HOME": "/home/tester", "MCP_SHELL_AUTH_TOKEN": "tok"},
            clear=False,
        ):
            result = CommandValidator().filter_env({})
        assert result is not None
        assert result["PATH"] == "/usr/bin"
        assert result["HOME"] == "/home/tester"
        assert result["MCP_SHELL_AUTH_TOKEN"] == "tok"

    def test_denylisted_key_in_server_env_is_blocked(self):
        with patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=False):
            result = CommandValidator().filter_env({"PYTHONPATH": "/z"})
        assert result is not None
        assert "PYTHONPATH" not in result

    def test_config_non_protected_var_merges_and_protected_override_logged(
        self, caplog
    ):
        with patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=False):
            with caplog.at_level(logging.WARNING):
                result = CommandValidator().filter_env(
                    {"MY_NEW_VAR": "value", "HOME": "hacked"}
                )
        assert result is not None
        assert result["MY_NEW_VAR"] == "value"
        assert result["HOME"] != "hacked"
        assert "HOME" in caplog.text
        assert "hacked" not in caplog.text

    def test_none_passthrough(self):
        assert CommandValidator().filter_env(None) is None


class TestCommandValidatorAllowedBinaryDir:
    """AC-06: accept a regular file directly inside an allowed, non-writable
    binary directory; reject the four reject cases."""

    _BIN_BASENAME = "mcp_shell"

    def _make_allowed_dir(self, tmp_path: Path, *, writable: bool) -> Path:
        d = tmp_path / "bin"
        d.mkdir()
        (d / self._BIN_BASENAME).write_text("#!/bin/sh\n")
        os.chmod(d, 0o777 if writable else 0o755)
        return d

    def _patch_which(self, target: Path):
        return patch.object(shutil, "which", return_value=str(target))

    def test_accept_regular_file_in_allowed_dir(self, tmp_path, monkeypatch):
        d = self._make_allowed_dir(tmp_path, writable=False)
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(d.resolve()))
        target = d / self._BIN_BASENAME
        with self._patch_which(target):
            result = CommandValidator().validate(_TEST_SERVER_KEY, self._BIN_BASENAME)
        assert os.path.isabs(result)
        assert os.path.realpath(result) == os.path.realpath(str(target))

    def test_reject_symlink_in_allowed_dir_pointing_elsewhere(
        self,
        tmp_path,
        monkeypatch,
    ):
        d = tmp_path / "bin"
        d.mkdir()
        # Target file lives OUTSIDE the allowed dir.
        outside = tmp_path / "outside" / "target"
        outside.parent.mkdir()
        outside.write_text("")
        link = d / self._BIN_BASENAME
        try:
            link.symlink_to(outside)
        except OSError:
            pytest.skip("Cannot create symlinks")
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(d.resolve()))
        with self._patch_which(link):
            with pytest.raises(HttpStartupError) as exc_info:
                CommandValidator().validate(_TEST_SERVER_KEY, self._BIN_BASENAME)
        assert "not in the allowed commands list" in str(exc_info.value)

    def test_reject_file_in_writable_dir(self, tmp_path, monkeypatch):
        d = self._make_allowed_dir(tmp_path, writable=True)
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(d.resolve()))
        target = d / self._BIN_BASENAME
        with self._patch_which(target):
            with pytest.raises(HttpStartupError) as exc_info:
                CommandValidator().validate(_TEST_SERVER_KEY, self._BIN_BASENAME)
        assert "not in the allowed commands list" in str(exc_info.value)

    def test_reject_non_regular_file_in_allowed_dir(self, tmp_path, monkeypatch):
        d = tmp_path / "bin"
        d.mkdir()
        # A subdirectory (non-regular file) directly inside the allowed dir.
        sub = d / self._BIN_BASENAME
        sub.mkdir()
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(d.resolve()))
        with self._patch_which(sub):
            with pytest.raises(HttpStartupError) as exc_info:
                CommandValidator().validate(_TEST_SERVER_KEY, self._BIN_BASENAME)
        assert "is not a regular file" in str(exc_info.value)

    def test_reject_outside_allowlist_and_dir(self, tmp_path, monkeypatch):
        # File outside the allowed dir, basename not in the allowlist.
        other = tmp_path / "other"
        other.mkdir()
        target = other / self._BIN_BASENAME
        target.write_text("")
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str((tmp_path / "bin").resolve()))
        with self._patch_which(target):
            with pytest.raises(HttpStartupError) as exc_info:
                CommandValidator().validate(_TEST_SERVER_KEY, self._BIN_BASENAME)
        assert "not in the allowed commands list" in str(exc_info.value)

    def test_existing_allowlist_still_passes(self, tmp_path, monkeypatch):
        # python3 passes via the unchanged allowlist branch even when the
        # allowed binary dir points at an unrelated empty directory.
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str((tmp_path / "bin").resolve()))
        result = CommandValidator().validate(_TEST_SERVER_KEY, "python3")
        assert os.path.isabs(result)


class TestCommandValidatorStrictConfinement:
    """Strict mode (LLMAGENT_STRICT_COMMAND): only the trusted directory counts."""

    def _trusted_dir(self, tmp_path: Path) -> Path:
        d = tmp_path / "bin"
        d.mkdir()
        os.chmod(d, 0o755)
        return d

    def _outside_file(self, tmp_path: Path, name: str) -> Path:
        other = tmp_path / "other"
        other.mkdir()
        target = other / name
        target.write_text("#!/bin/sh\n")
        return target

    def _patch_which(self, target: Path):
        return patch.object(shutil, "which", return_value=str(target))

    def test_strict_rejects_allowlisted_name_outside_trusted_dir(
        self, tmp_path, monkeypatch
    ):
        trusted = self._trusted_dir(tmp_path)
        target = self._outside_file(tmp_path, "node")
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(trusted.resolve()))
        monkeypatch.setenv("LLMAGENT_STRICT_COMMAND", "1")
        with self._patch_which(target):
            with pytest.raises(HttpStartupError) as exc_info:
                CommandValidator().validate(_TEST_SERVER_KEY, "node")
        assert "outside the trusted binary directory" in str(exc_info.value)

    def test_strict_accepts_non_allowlisted_name_inside_trusted_dir(
        self, tmp_path, monkeypatch
    ):
        trusted = self._trusted_dir(tmp_path)
        target = trusted / "mcp_shell"
        target.write_text("#!/bin/sh\n")
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(trusted.resolve()))
        monkeypatch.setenv("LLMAGENT_STRICT_COMMAND", "1")
        with self._patch_which(target):
            result = CommandValidator().validate(_TEST_SERVER_KEY, "mcp_shell")
        assert os.path.realpath(result) == os.path.realpath(str(target))

    def test_strict_rejects_symlink_escape(self, tmp_path, monkeypatch):
        trusted = self._trusted_dir(tmp_path)
        outside = self._outside_file(tmp_path, "real_node")
        link = trusted / "node"
        try:
            link.symlink_to(outside)
        except OSError:
            pytest.skip("Cannot create symlinks")
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(trusted.resolve()))
        monkeypatch.setenv("LLMAGENT_STRICT_COMMAND", "1")
        with self._patch_which(link):
            with pytest.raises(HttpStartupError) as exc_info:
                CommandValidator().validate(_TEST_SERVER_KEY, "node")
        assert "outside the trusted binary directory" in str(exc_info.value)

    def test_strict_trusted_dir_falls_back_to_default_when_unset(
        self, tmp_path, monkeypatch
    ):
        target = self._outside_file(tmp_path, "node")
        monkeypatch.delenv("LLMAGENT_BINARY_DIR", raising=False)
        monkeypatch.setenv("LLMAGENT_STRICT_COMMAND", "1")
        with self._patch_which(target):
            with pytest.raises(HttpStartupError) as exc_info:
                CommandValidator().validate(_TEST_SERVER_KEY, "node")
        assert "/opt/llm/bin" in str(exc_info.value)

    def test_permissive_default_allows_allowlisted_name_outside_trusted_dir(
        self, tmp_path, monkeypatch
    ):
        trusted = self._trusted_dir(tmp_path)
        target = self._outside_file(tmp_path, "node")
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(trusted.resolve()))
        monkeypatch.delenv("LLMAGENT_STRICT_COMMAND", raising=False)
        with self._patch_which(target):
            result = CommandValidator().validate(_TEST_SERVER_KEY, "node")
        assert os.path.realpath(result) == os.path.realpath(str(target))

    @pytest.mark.parametrize(
        ("value", "strict"),
        [
            (None, False),
            ("", False),
            ("0", False),
            ("false", False),
            ("FALSE", False),
            ("off", False),
            ("no", False),
            (" No ", False),
            ("1", True),
            ("yes", True),
            ("true", True),
            ("enabled", True),
        ],
    )
    def test_flag_value_controls_strict_mode(
        self, tmp_path, monkeypatch, value, strict
    ):
        trusted = self._trusted_dir(tmp_path)
        target = self._outside_file(tmp_path, "node")
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(trusted.resolve()))
        if value is None:
            monkeypatch.delenv("LLMAGENT_STRICT_COMMAND", raising=False)
        else:
            monkeypatch.setenv("LLMAGENT_STRICT_COMMAND", value)
        with self._patch_which(target):
            if strict:
                with pytest.raises(HttpStartupError):
                    CommandValidator().validate(_TEST_SERVER_KEY, "node")
            else:
                result = CommandValidator().validate(_TEST_SERVER_KEY, "node")
                assert os.path.realpath(result) == os.path.realpath(str(target))
