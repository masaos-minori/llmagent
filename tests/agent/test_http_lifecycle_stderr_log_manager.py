"""Tests for scripts/agent/http_lifecycle_stderr_log_manager.py."""

import os
import subprocess
import tempfile
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from agent.http_lifecycle_errors import HttpStartupError
from agent.http_lifecycle_stderr_log_manager import (
    _DEFAULT_MAX_LOG_FILES,
    _DEFAULT_MAX_LOG_SIZE_BYTES,
    _DEFAULT_STDERR_TAIL_BYTES,
    StderrLogManager,
)

pytestmark = pytest.mark.contract


class TestReadTail:
    def test_read_tail_missing_server_key(self):
        mgr = StderrLogManager()
        result = mgr.read_tail("nonexistent")
        assert result == b""

    def test_read_tail_small_file(self):
        mgr = StderrLogManager(stderr_tail_bytes=1024)
        content = b"hello world"
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            f.flush()
            mgr._log_paths["server1"] = f.name
        try:
            result = mgr.read_tail("server1")
            assert result == content
        finally:
            os.unlink(f.name)

    def test_read_tail_large_file(self):
        mgr = StderrLogManager(stderr_tail_bytes=10)
        content = b"x" * 100 + b"TAILING"
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            f.flush()
            mgr._log_paths["server1"] = f.name
        try:
            result = mgr.read_tail("server1")
            expected = content[-10:]
            assert result == expected
        finally:
            os.unlink(f.name)

    def test_read_tail_os_error_returns_empty(self):
        mgr = StderrLogManager()
        mgr._log_paths["server1"] = "/nonexistent/path/stderr.log"
        result = mgr.read_tail("server1")
        assert result == b""


class TestStderrLogManagerInit:
    def test_default_tail_bytes(self):
        mgr = StderrLogManager()
        assert mgr._stderr_tail_bytes == _DEFAULT_STDERR_TAIL_BYTES

    def test_custom_tail_bytes(self):
        mgr = StderrLogManager(stderr_tail_bytes=1024)
        assert mgr._stderr_tail_bytes == 1024

    def test_none_uses_default(self):
        mgr = StderrLogManager(stderr_tail_bytes=None)
        assert mgr._stderr_tail_bytes == _DEFAULT_STDERR_TAIL_BYTES

    def test_empty_dict_state(self):
        mgr = StderrLogManager()
        assert mgr._log_paths == {}
        assert mgr._generations == {}

    def test_defaults_mirror_config_model_defaults(self):
        """The plain-value defaults must stay aligned with the config model defaults."""
        from shared.mcp_config import McpServerConfig, TransportType

        cfg = McpServerConfig(transport=TransportType.HTTP, url="http://localhost")
        mgr = StderrLogManager()
        assert mgr._max_log_size_bytes == _DEFAULT_MAX_LOG_SIZE_BYTES
        assert mgr._max_log_size_bytes == int(cfg.max_stderr_log_size_mb * 1024 * 1024)
        assert mgr._max_log_files == _DEFAULT_MAX_LOG_FILES
        assert mgr._max_log_files == cfg.max_stderr_log_files


class TestOpenLog:
    def test_open_log_creates_directory_and_returns_handle(self):
        mgr = StderrLogManager()
        cfg = MagicMock()
        with tempfile.TemporaryDirectory():
            # Patch the log dir creation to use temp directory
            with (
                patch("os.makedirs") as mock_makedirs,
                patch("os.open", return_value=3) as mock_open,
                patch("os.fdopen", return_value=MagicMock(spec=BytesIO)) as mock_fdopen,
            ):
                result = mgr.open_log("server1", cfg)
                assert result is not None
                mock_makedirs.assert_called_once()
                mock_open.assert_called_once()
                mock_fdopen.assert_called_once_with(3, "ab")

    def test_open_log_retains_no_handle(self):
        mgr = StderrLogManager()
        cfg = MagicMock()
        mock_fh = MagicMock(spec=BytesIO)
        with (
            patch("os.makedirs"),
            patch("os.open", return_value=3),
            patch("os.fdopen", return_value=mock_fh),
        ):
            result = mgr.open_log("server1", cfg)
            assert result is mock_fh
            assert not hasattr(mgr, "_log_files")

    def test_open_log_stores_path(self):
        mgr = StderrLogManager()
        cfg = MagicMock()
        with (
            patch("os.makedirs"),
            patch("os.open", return_value=3),
            patch("os.fdopen", return_value=MagicMock(spec=BytesIO)),
        ):
            mgr.open_log("server1", cfg)
            assert "server1" in mgr._log_paths

    def test_open_log_raises_on_os_error(self):
        mgr = StderrLogManager()
        cfg = MagicMock()
        with patch("os.makedirs", side_effect=OSError("Permission denied")):
            with pytest.raises(Exception):
                mgr.open_log("server1", cfg)

    def test_open_log_creates_file_with_mode_0600(self):
        """REQ-006 (AC-3): the log file is created 0o600, not the umask default."""
        mgr = StderrLogManager()
        cfg = MagicMock()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("tempfile.gettempdir", return_value=tmp):
                handle = mgr.open_log("server1", cfg)
                try:
                    mode = os.stat(handle.name).st_mode & 0o777
                    assert mode == 0o600
                finally:
                    handle.close()


class TestRotateLog:
    def test_rotate_log_no_path_registered(self):
        mgr = StderrLogManager()
        result = mgr.rotate_log("nonexistent", 1024)
        assert result is False

    def test_rotate_log_below_threshold(self):
        mgr = StderrLogManager()
        size = 100
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"x" * size)
            f.flush()
            mgr._log_paths["server1"] = f.name
        try:
            result = mgr.rotate_log("server1", 1024)
            assert result is False
            # File should not be renamed
            assert os.path.exists(f.name)
        finally:
            os.unlink(f.name)

    def test_rotate_log_above_threshold(self):
        mgr = StderrLogManager()
        size = 1024
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"x" * size)
            f.flush()
            mgr._log_paths["server1"] = f.name
        try:
            result = mgr.rotate_log("server1", 512)
            assert result is True
            # Copy-and-truncate: the active path is never renamed, so the writer fd and
            # read_tail() keep pointing at the same file; the content moves to generation 1.
            assert os.path.exists(f.name)
            assert os.path.getsize(f.name) == 0
            rotated = f"{f.name}.1"
            assert os.path.exists(rotated)
            with open(rotated, "rb") as rf:
                assert rf.read() == b"x" * size
        finally:
            if os.path.exists(f"{f.name}.1"):
                os.unlink(f"{f.name}.1")
            os.unlink(f.name)

    def test_rotate_log_os_error_returns_false(self):
        mgr = StderrLogManager()
        mgr._log_paths["server1"] = "/nonexistent/path/stderr.log"
        result = mgr.rotate_log("server1", 1024)
        assert result is False


class TestGetLogPath:
    def test_get_log_path_missing_server_key(self):
        mgr = StderrLogManager()
        assert mgr.get_log_path("nonexistent") is None

    def test_get_log_path_returns_tracked_path(self):
        mgr = StderrLogManager()
        mgr._log_paths["server1"] = "/tmp/server1.stderr.log"
        assert mgr.get_log_path("server1") == "/tmp/server1.stderr.log"


class TestRetentionAndWriterCompatibility:
    def test_purge_removes_oldest_generations(self):
        mgr = StderrLogManager(max_log_files=2)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stderr.log")
            with open(path, "wb") as f:
                f.write(b"x" * 1024)
            mgr._log_paths["server1"] = path
            for generation in (1, 2, 3):
                with open(f"{path}.{generation}", "wb") as f:
                    f.write(b"g")
            removed = mgr.purge_generations("server1")
            assert removed == 1
            assert not os.path.exists(f"{path}.1")
            assert os.path.exists(f"{path}.2")
            assert os.path.exists(f"{path}.3")

    def test_purge_no_path_registered(self):
        mgr = StderrLogManager()
        assert mgr.purge_generations("nonexistent") == 0

    def test_rotate_uses_configured_default_limit(self):
        mgr = StderrLogManager(max_log_size_bytes=512)
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"x" * 600)
            f.flush()
            mgr._log_paths["server1"] = f.name
        try:
            assert mgr.rotate_log("server1") is True
            assert os.path.exists(f"{f.name}.1")
        finally:
            if os.path.exists(f"{f.name}.1"):
                os.unlink(f"{f.name}.1")
            os.unlink(f.name)

    def test_rotate_purges_beyond_max_files(self):
        mgr = StderrLogManager(max_log_size_bytes=100, max_log_files=2)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stderr.log")
            mgr._log_paths["server1"] = path
            # Build generations 1, 2, 3 through real rotations.
            for generation in (1, 2, 3):
                with open(path, "wb") as f:
                    f.write(b"x" * 200)
                assert mgr.rotate_log("server1") is True
                assert os.path.exists(f"{path}.{generation}")
            # The third rotation purged generation 1.
            assert not os.path.exists(f"{path}.1")
            assert os.path.exists(f"{path}.2")
            assert os.path.exists(f"{path}.3")

    def test_rotate_truncation_keeps_writer_fd_usable(self):
        """REQ-006 (AC-3): copy-and-truncate keeps the writer fd on the same path."""
        mgr = StderrLogManager(max_log_size_bytes=100)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stderr.log")
            with open(path, "wb") as f:
                f.write(b"x" * 200)
            mgr._log_paths["server1"] = path
            writer = open(path, "ab")
            try:
                assert mgr.rotate_log("server1") is True
                writer.write(b"after")
                writer.flush()
                # The writer still sees the active path, and read_tail() returns only
                # the post-rotation content.
                assert mgr.read_tail("server1") == b"after"
            finally:
                writer.close()

    @pytest.mark.integration
    def test_writer_fd_survives_rotation_with_real_subprocess(self):
        """REQ-006 (AC-3): a real writer fd keeps writing to the active path after rotation."""
        mgr = StderrLogManager(max_log_size_bytes=100)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stderr.log")
            with open(path, "wb") as f:
                f.write(b"x" * 200)
            mgr._log_paths["server1"] = path
            # The child writes only after the parent signals, so the write is guaranteed
            # to land on the truncated active file rather than the rotated copy.
            writer = open(path, "ab")
            proc = subprocess.Popen(
                [
                    "python3",
                    "-c",
                    "import sys; sys.stdin.readline(); sys.stdout.write('from_writer')",
                ],
                stdin=subprocess.PIPE,
                stdout=writer,
                text=True,
            )
            try:
                assert mgr.rotate_log("server1") is True
                proc.stdin.write("go\n")
                proc.stdin.flush()
                proc.wait(timeout=10)
                assert mgr.read_tail("server1") == b"from_writer"
            finally:
                writer.close()


class TestForget:
    def test_forget_missing_server_key_is_noop(self):
        mgr = StderrLogManager()
        mgr.forget("nonexistent")  # must not raise
        assert mgr._log_paths == {}

    def test_forget_removes_tracked_path(self):
        mgr = StderrLogManager()
        mgr._log_paths["server1"] = "/tmp/server1.stderr.log"
        mgr.forget("server1")
        assert "server1" not in mgr._log_paths

    def test_forget_clears_generation_counter(self):
        mgr = StderrLogManager()
        mgr._generations["server1"] = 2
        mgr.forget("server1")
        assert "server1" not in mgr._generations

    def test_forget_leaves_other_entries_intact(self):
        mgr = StderrLogManager()
        mgr._log_paths["server1"] = "/tmp/server1.stderr.log"
        mgr._log_paths["server2"] = "/tmp/server2.stderr.log"
        mgr.forget("server1")
        assert mgr._log_paths == {"server2": "/tmp/server2.stderr.log"}


class TestClear:
    def test_clear_empty_is_noop(self):
        mgr = StderrLogManager()
        mgr.clear()  # must not raise
        assert mgr._log_paths == {}

    def test_clear_removes_all_entries(self):
        mgr = StderrLogManager()
        mgr._log_paths["server1"] = "/tmp/server1.stderr.log"
        mgr._log_paths["server2"] = "/tmp/server2.stderr.log"
        mgr.clear()
        assert mgr._log_paths == {}

    def test_cleanup_methods_do_not_raise_without_log_files(self):
        mgr = StderrLogManager()
        mgr.forget("server1")
        mgr.clear()
        assert mgr.rotate_log("server1", 1024) is False


class TestOpenLogServerKeyValidity:
    """REQ-005 (AC-4): open_log rejects an invalid server key before touching the filesystem."""

    # The same invalid forms as tests/shared/test_mcp_config_validation.py: traversal,
    # separators, uppercase, whitespace, control characters, and the 65-character boundary.
    _INVALID_KEYS = [
        "..",
        "a/b",
        "a.b",
        "A",
        "a b",
        "a\n",
        "a\x00",
        "a\x01",
        "a" * 65,
    ]

    def _tmp_root(self, monkeypatch, tmp_path):
        monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
        return tmp_path

    @pytest.mark.parametrize("bad_key", _INVALID_KEYS)
    def test_invalid_key_rejected_before_any_path_use(
        self, monkeypatch, tmp_path, bad_key
    ):
        root = self._tmp_root(monkeypatch, tmp_path)
        mgr = StderrLogManager()

        with pytest.raises(HttpStartupError):
            mgr.open_log(bad_key, MagicMock())

        assert not (root / "mcp_server_logs").exists()
        assert sorted(path.name for path in root.iterdir()) == []
        assert mgr.get_log_path(bad_key) is None

    def test_valid_key_log_path_is_the_validated_key(self, monkeypatch, tmp_path):
        root = self._tmp_root(monkeypatch, tmp_path)
        mgr = StderrLogManager()

        handle = mgr.open_log("github", MagicMock())
        try:
            expected = str(root / "mcp_server_logs" / "github" / "stderr.log")
            assert mgr.get_log_path("github") == expected
            assert os.path.isfile(expected)
        finally:
            handle.close()
