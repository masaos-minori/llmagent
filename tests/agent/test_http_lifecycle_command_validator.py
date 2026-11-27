"""tests/agent/test_http_lifecycle_command_validator.py

Unit tests for CommandValidator and related error classes.

cliplc006 REQ-004: trusted-directory confinement is the default. The basename
allowlist is reachable only through the explicit ``LLMAGENT_COMMAND_MODE=permissive``
opt-in, and ``validate`` returns the resolved path together with its file identity.
"""

from __future__ import annotations

import fnmatch
import os
import shutil
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from agent import http_lifecycle_command_validator as cv_module
from agent.http_lifecycle_command_validator import (
    _DEFAULT_ALLOWED_ENV_VARS,
    CommandValidator,
)
from agent.http_lifecycle_errors import HttpStartupError, StartupFailure

pytestmark = pytest.mark.contract

_TEST_SERVER_KEY = "test_server"

# REQ-006 fixed runtime set: the only variables a child inherits from the parent
# process. Per-server tokens and declared names come from the launch spec (row 2).
_FIXED_RUNTIME_PATTERNS = frozenset(
    {
        "PATH",
        "HOME",
        "USER",
        "LOGNAME",
        "SHELL",
        "TMPDIR",
        "TMP",
        "TEMP",
        "LANG",
        "LC_*",
        "LLMAGENT_CONFIG_DIR",
        "LLMAGENT_SUDACHI_DICT",
    }
)


class _OsStatShim:
    """Delegate every ``os`` attribute, but report a fixed uid for chosen paths.

    Ownership is asserted without ``chown``: the validator's own ``os.stat`` calls
    return a stat-shaped object whose ``st_uid`` is the one under test, while
    ``st_mode``, ``st_dev`` and ``st_ino`` stay the real ones.
    """

    def __init__(self, uids: dict[str, int]) -> None:
        self._uids = {os.path.realpath(path): uid for path, uid in uids.items()}

    def __getattr__(self, name: str) -> object:
        return getattr(os, name)

    def stat(self, path: object, *args: object, **kwargs: object) -> object:
        real = os.stat(path, *args, **kwargs)  # type: ignore[arg-type]
        uid = self._uids.get(os.path.realpath(str(path)))
        if uid is None:
            return real
        return SimpleNamespace(
            st_mode=real.st_mode,
            st_uid=uid,
            st_gid=real.st_gid,
            st_dev=real.st_dev,
            st_ino=real.st_ino,
            st_size=real.st_size,
            st_mtime=real.st_mtime,
        )


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
        # REQ-002 (AC-1): the rendered form carries the stable code and no absolute path.
        assert str(error) == "my_server: general: Test failure"


class TestCommandValidatorValidatePermissive:
    """Tests for CommandValidator.validate() under the explicit permissive opt-in.

    These are the basename-allowlist cases the opt-in restores; each unpacks the
    (path, identity) pair validate returns.
    """

    @pytest.fixture(autouse=True)
    def _permissive_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LLMAGENT_STRICT_COMMAND", raising=False)
        monkeypatch.delenv("LLMAGENT_BINARY_DIR", raising=False)
        monkeypatch.setenv("LLMAGENT_COMMAND_MODE", "permissive")

    def test_allowed_command_python(self):
        validator = CommandValidator()
        result, identity = validator.validate(_TEST_SERVER_KEY, "python3")
        assert result is not None
        assert os.path.isabs(result)
        assert os.path.isfile(result)
        assert isinstance(identity, tuple)

    def test_allowed_command_node(self):
        validator = CommandValidator()
        if shutil.which("node"):
            result, _ = validator.validate(_TEST_SERVER_KEY, "node")
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
        result, _ = custom_validator.validate(_TEST_SERVER_KEY, "python3")
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
                        result, _ = custom_validator.validate(_TEST_SERVER_KEY, name)
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
                        result, _ = validator.validate(_TEST_SERVER_KEY, name)
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
        result, _ = validator.validate(_TEST_SERVER_KEY, "python3")
        assert os.path.isabs(result)

    def test_validate_realpath_resolves_symlinks(self):
        """validate() returns realpath, not the original which() path."""
        validator = CommandValidator()
        result, _ = validator.validate(_TEST_SERVER_KEY, "python3")
        # The result should be the resolved realpath
        assert result == os.path.realpath(result)


class TestCommandValidatorAllowedBinaryDir:
    """AC-06 (permissive branch): accept a regular file directly inside an allowed,
    non-writable binary directory; reject the four reject cases."""

    _BIN_BASENAME = "mcp_shell"

    @pytest.fixture(autouse=True)
    def _permissive_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LLMAGENT_STRICT_COMMAND", raising=False)
        monkeypatch.setenv("LLMAGENT_COMMAND_MODE", "permissive")

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
            result, _ = CommandValidator().validate(
                _TEST_SERVER_KEY, self._BIN_BASENAME
            )
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
        result, _ = CommandValidator().validate(_TEST_SERVER_KEY, "python3")
        assert os.path.isabs(result)


class TestCommandValidatorEnvAllowlist:
    """REQ-006: the inherited allowlist is the fixed runtime set, with no token
    pattern and no GITHUB_TOKEN. The per-server environment is built by
    http_lifecycle_launch_spec.build_child_env, not by the validator."""

    @pytest.mark.parametrize("pattern", sorted(_FIXED_RUNTIME_PATTERNS))
    def test_fixed_runtime_set_is_admitted(self, pattern):
        assert pattern in _DEFAULT_ALLOWED_ENV_VARS

    def test_allowlist_is_exactly_the_fixed_runtime_set(self):
        assert set(_DEFAULT_ALLOWED_ENV_VARS) == _FIXED_RUNTIME_PATTERNS

    @pytest.mark.parametrize(
        "name",
        [
            "MCP_OTHER_AUTH_TOKEN",
            "MCP_OTHER_CONTROL_TOKEN",
            "MCP_GITHUB_AUTH_TOKEN",
            "MCP_GITHUB_CONTROL_TOKEN",
            "GITHUB_TOKEN",
        ],
    )
    def test_credential_names_are_not_admitted(self, name):
        assert not any(
            fnmatch.fnmatch(name, pattern) for pattern in _DEFAULT_ALLOWED_ENV_VARS
        )

    @pytest.mark.parametrize(
        ("name", "admitted"),
        [
            ("PATH", True),
            ("HOME", True),
            ("LC_ALL", True),
            ("LC_CTYPE", True),
            ("LLMAGENT_CONFIG_DIR", True),
            ("LLMAGENT_SUDACHI_DICT", True),
            ("LLMAGENT_BINARY_DIR", False),
            ("LLMAGENT_COMMAND_MODE", False),
            ("AWS_SECRET_ACCESS_KEY", False),
            ("https_proxy", False),
            ("UV_INDEX_URL", False),
        ],
    )
    def test_parent_variables_are_admitted_or_dropped(self, name, admitted):
        assert (
            any(fnmatch.fnmatch(name, pattern) for pattern in _DEFAULT_ALLOWED_ENV_VARS)
            is admitted
        )


class TestCommandValidatorStrictConfinement:
    """REQ-004: strict confinement is the default, with no variable set."""

    @pytest.fixture(autouse=True)
    def _strict_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LLMAGENT_STRICT_COMMAND", raising=False)
        monkeypatch.delenv("LLMAGENT_COMMAND_MODE", raising=False)

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
        target.chmod(0o755)
        return target

    def _patch_which(self, target: Path):
        return patch.object(shutil, "which", return_value=str(target))

    def test_rejects_allowlisted_name_outside_trusted_dir(self, tmp_path, monkeypatch):
        trusted = self._trusted_dir(tmp_path)
        target = self._outside_file(tmp_path, "node")
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(trusted.resolve()))
        with self._patch_which(target):
            with pytest.raises(HttpStartupError) as exc_info:
                CommandValidator().validate(_TEST_SERVER_KEY, "node")
        assert _TEST_SERVER_KEY in str(exc_info.value)
        # The rendered message shows the logical identifier, not the absolute path.
        assert target.name in str(exc_info.value)
        assert "/" not in str(exc_info.value).split(": ", 1)[1]
        assert "outside the trusted binary directory" in str(exc_info.value)

    def test_accepts_non_allowlisted_name_inside_trusted_dir(
        self, tmp_path, monkeypatch
    ):
        trusted = self._trusted_dir(tmp_path)
        target = trusted / "mcp_shell"
        target.write_text("#!/bin/sh\n")
        target.chmod(0o755)
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(trusted.resolve()))
        with self._patch_which(target):
            result, _ = CommandValidator().validate(_TEST_SERVER_KEY, "mcp_shell")
        assert os.path.realpath(result) == os.path.realpath(str(target))

    def test_rejects_symlink_escape(self, tmp_path, monkeypatch):
        trusted = self._trusted_dir(tmp_path)
        outside = self._outside_file(tmp_path, "real_node")
        link = trusted / "node"
        try:
            link.symlink_to(outside)
        except OSError:
            pytest.skip("Cannot create symlinks")
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(trusted.resolve()))
        with self._patch_which(link):
            with pytest.raises(HttpStartupError) as exc_info:
                CommandValidator().validate(_TEST_SERVER_KEY, "node")
        assert "outside the trusted binary directory" in str(exc_info.value)

    def test_trusted_dir_falls_back_to_default_when_unset(self, tmp_path, monkeypatch):
        target = self._outside_file(tmp_path, "node")
        monkeypatch.delenv("LLMAGENT_BINARY_DIR", raising=False)
        with self._patch_which(target):
            with pytest.raises(HttpStartupError) as exc_info:
                CommandValidator().validate(_TEST_SERVER_KEY, "node")
        # The default trusted directory is rendered as its logical identifier.
        assert "bin" in str(exc_info.value)
        assert "/opt/llm/bin" not in str(exc_info.value)


class TestCommandValidatorPermissiveOptIn:
    """REQ-004: only the literal value ``permissive`` restores the basename allowlist."""

    _BIN_BASENAME = "mcp_shell"

    @pytest.fixture(autouse=True)
    def _clean_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LLMAGENT_STRICT_COMMAND", raising=False)
        monkeypatch.delenv("LLMAGENT_COMMAND_MODE", raising=False)

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
        target.chmod(0o755)
        return target

    def _patch_which(self, target: Path):
        return patch.object(shutil, "which", return_value=str(target))

    def test_permissive_value_restores_basename_allowlist(self, tmp_path, monkeypatch):
        trusted = self._trusted_dir(tmp_path)
        target = self._outside_file(tmp_path, "node")
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(trusted.resolve()))
        monkeypatch.setenv("LLMAGENT_COMMAND_MODE", "permissive")
        with self._patch_which(target):
            result, _ = CommandValidator().validate(_TEST_SERVER_KEY, "node")
        assert os.path.realpath(result) == os.path.realpath(str(target))

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "0",
            "false",
            "FALSE",
            "off",
            "no",
            " No ",
            "1",
            "yes",
            "true",
            "enabled",
            "PERMISSIVE",
            " permissive",
            "permissive ",
        ],
    )
    def test_other_values_keep_strict_default(self, tmp_path, monkeypatch, value):
        trusted = self._trusted_dir(tmp_path)
        target = self._outside_file(tmp_path, "node")
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(trusted.resolve()))
        monkeypatch.setenv("LLMAGENT_COMMAND_MODE", value)
        with self._patch_which(target):
            with pytest.raises(HttpStartupError) as exc_info:
                CommandValidator().validate(_TEST_SERVER_KEY, "node")
        assert "outside the trusted binary directory" in str(exc_info.value)

    def test_unset_variable_is_strict(self, tmp_path, monkeypatch):
        trusted = self._trusted_dir(tmp_path)
        target = self._outside_file(tmp_path, "node")
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(trusted.resolve()))
        with self._patch_which(target):
            with pytest.raises(HttpStartupError) as exc_info:
                CommandValidator().validate(_TEST_SERVER_KEY, "node")
        assert "outside the trusted binary directory" in str(exc_info.value)

    def test_legacy_strict_variable_has_no_effect(self, tmp_path, monkeypatch):
        # The removed opt-in switch must not resurrect permissive behavior.
        trusted = self._trusted_dir(tmp_path)
        target = self._outside_file(tmp_path, "node")
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(trusted.resolve()))
        monkeypatch.setenv("LLMAGENT_STRICT_COMMAND", "0")
        with self._patch_which(target):
            with pytest.raises(HttpStartupError) as exc_info:
                CommandValidator().validate(_TEST_SERVER_KEY, "node")
        assert "outside the trusted binary directory" in str(exc_info.value)


class TestCommandValidatorOwnershipAndMode:
    """REQ-004 (AC-2): the executable and the trusted directory must be owned by the
    Agent user or root, and the executable must not be group- or world-writable."""

    _BIN_BASENAME = "mcp_github"
    _OTHER_UID = 65534

    @pytest.fixture(autouse=True)
    def _strict_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LLMAGENT_STRICT_COMMAND", raising=False)
        monkeypatch.delenv("LLMAGENT_COMMAND_MODE", raising=False)

    def _trusted(self, tmp_path: Path) -> tuple[Path, Path]:
        d = tmp_path / "bin"
        d.mkdir()
        exe = d / self._BIN_BASENAME
        exe.write_text("#!/bin/sh\nexit 0\n")
        exe.chmod(0o755)
        os.chmod(d, 0o755)
        return d, exe

    def _patch_which(self, target: Path):
        return patch.object(shutil, "which", return_value=str(target))

    def _validate(
        self,
        monkeypatch: pytest.MonkeyPatch,
        d: Path,
        exe: Path,
        uids: dict[str, int] | None,
    ):
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(d.resolve()))
        if uids is not None:
            monkeypatch.setattr(cv_module, "os", _OsStatShim(uids))
        with self._patch_which(exe):
            return CommandValidator().validate(_TEST_SERVER_KEY, self._BIN_BASENAME)

    def test_executable_owned_by_other_uid_rejected(self, tmp_path, monkeypatch):
        d, exe = self._trusted(tmp_path)
        with pytest.raises(HttpStartupError) as exc_info:
            self._validate(monkeypatch, d, exe, {str(exe): self._OTHER_UID})
        assert _TEST_SERVER_KEY in str(exc_info.value)
        assert exe.name in str(exc_info.value)

    def test_directory_owned_by_other_uid_rejected(self, tmp_path, monkeypatch):
        d, exe = self._trusted(tmp_path)
        with pytest.raises(HttpStartupError) as exc_info:
            self._validate(monkeypatch, d, exe, {str(d): self._OTHER_UID})
        assert _TEST_SERVER_KEY in str(exc_info.value)
        assert d.name in str(exc_info.value)

    def test_executable_owned_by_agent_uid_accepted(self, tmp_path, monkeypatch):
        d, exe = self._trusted(tmp_path)
        result, _ = self._validate(monkeypatch, d, exe, {str(exe): os.geteuid()})
        assert os.path.realpath(result) == os.path.realpath(str(exe))

    def test_executable_owned_by_root_accepted(self, tmp_path, monkeypatch):
        d, exe = self._trusted(tmp_path)
        result, _ = self._validate(monkeypatch, d, exe, {str(exe): 0})
        assert os.path.realpath(result) == os.path.realpath(str(exe))

    def test_directory_owned_by_root_accepted(self, tmp_path, monkeypatch):
        d, exe = self._trusted(tmp_path)
        result, _ = self._validate(monkeypatch, d, exe, {str(d): 0})
        assert os.path.realpath(result) == os.path.realpath(str(exe))

    def test_group_writable_executable_rejected(self, tmp_path, monkeypatch):
        d, exe = self._trusted(tmp_path)
        exe.chmod(0o775)
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(d.resolve()))
        with self._patch_which(exe):
            with pytest.raises(HttpStartupError) as exc_info:
                CommandValidator().validate(_TEST_SERVER_KEY, self._BIN_BASENAME)
        assert _TEST_SERVER_KEY in str(exc_info.value)
        assert exe.name in str(exc_info.value)

    def test_world_writable_executable_rejected(self, tmp_path, monkeypatch):
        d, exe = self._trusted(tmp_path)
        exe.chmod(0o777)
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(d.resolve()))
        with self._patch_which(exe):
            with pytest.raises(HttpStartupError) as exc_info:
                CommandValidator().validate(_TEST_SERVER_KEY, self._BIN_BASENAME)
        assert _TEST_SERVER_KEY in str(exc_info.value)
        assert exe.name in str(exc_info.value)

    def test_group_writable_directory_rejected(self, tmp_path, monkeypatch):
        d, exe = self._trusted(tmp_path)
        os.chmod(d, 0o775)
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(d.resolve()))
        with self._patch_which(exe):
            with pytest.raises(HttpStartupError) as exc_info:
                CommandValidator().validate(_TEST_SERVER_KEY, self._BIN_BASENAME)
        assert _TEST_SERVER_KEY in str(exc_info.value)


class TestCommandValidatorIdentityCapture:
    """REQ-003: validate returns the resolved path plus its (st_dev, st_ino) identity,
    and neither a PATH change nor a symlink retarget changes the returned path."""

    _BIN_BASENAME = "mcp_github"

    @pytest.fixture(autouse=True)
    def _strict_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LLMAGENT_STRICT_COMMAND", raising=False)
        monkeypatch.delenv("LLMAGENT_COMMAND_MODE", raising=False)

    def _trusted(self, tmp_path: Path) -> tuple[Path, Path]:
        d = tmp_path / "bin"
        d.mkdir()
        exe = d / self._BIN_BASENAME
        exe.write_text("#!/bin/sh\nexit 0\n")
        exe.chmod(0o755)
        os.chmod(d, 0o755)
        return d, exe

    def test_identity_pair_matches_the_validated_file(self, tmp_path, monkeypatch):
        d, exe = self._trusted(tmp_path)
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(d.resolve()))
        with patch.object(shutil, "which", return_value=str(exe)):
            result, identity = CommandValidator().validate(
                _TEST_SERVER_KEY, self._BIN_BASENAME
            )
        st = os.stat(result)
        assert identity == (st.st_dev, st.st_ino)

    def test_path_change_after_validation_does_not_change_the_returned_path(
        self, tmp_path, monkeypatch
    ):
        d, exe = self._trusted(tmp_path)
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(d.resolve()))
        monkeypatch.setenv("PATH", str(d))
        result, _ = CommandValidator().validate(_TEST_SERVER_KEY, self._BIN_BASENAME)

        # A second directory now shadows the same basename on PATH.
        shadow = tmp_path / "shadow"
        shadow.mkdir()
        decoy = shadow / self._BIN_BASENAME
        decoy.write_text("#!/bin/sh\nexit 1\n")
        decoy.chmod(0o755)
        monkeypatch.setenv("PATH", f"{shadow}{os.pathsep}{d}")

        assert result == os.path.realpath(str(exe))
        assert shutil.which(self._BIN_BASENAME) == str(decoy)

    def test_symlink_retarget_after_validation_does_not_change_the_returned_path(
        self, tmp_path, monkeypatch
    ):
        d = tmp_path / "bin"
        d.mkdir()
        os.chmod(d, 0o755)
        real = d / "mcp_github_real"
        real.write_text("#!/bin/sh\nexit 0\n")
        real.chmod(0o755)
        link = d / self._BIN_BASENAME
        try:
            link.symlink_to(real)
        except OSError:
            pytest.skip("Cannot create symlinks")
        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(d.resolve()))
        with patch.object(shutil, "which", return_value=str(link)):
            result, _ = CommandValidator().validate(
                _TEST_SERVER_KEY, self._BIN_BASENAME
            )

        # Retarget the symlink outside the trusted directory after validation.
        outside = tmp_path / "outside"
        outside.mkdir()
        evil = outside / "evil"
        evil.write_text("#!/bin/sh\nexit 1\n")
        evil.chmod(0o755)
        link.unlink()
        try:
            link.symlink_to(evil)
        except OSError:
            pytest.skip("Cannot create symlinks")

        assert result == os.path.realpath(str(real))
        assert os.path.realpath(str(link)) == os.path.realpath(str(evil))

    def test_swapped_file_no_longer_matches_the_captured_identity(
        self, tmp_path, monkeypatch
    ):
        d, exe = self._trusted(tmp_path)
        swap_dir = tmp_path / "swap"
        swap_dir.mkdir()
        swap = swap_dir / self._BIN_BASENAME
        swap.write_text("#!/bin/sh\nexit 1\n")
        swap.chmod(0o755)

        monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(d.resolve()))
        with patch.object(shutil, "which", return_value=str(exe)):
            result, identity = CommandValidator().validate(
                _TEST_SERVER_KEY, self._BIN_BASENAME
            )

        # Replace the file behind the validated path with a different inode.
        exe.unlink()
        os.link(str(swap), str(exe))
        st = os.stat(result)
        assert (st.st_dev, st.st_ino) != identity
