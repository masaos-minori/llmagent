"""Tests for scripts/agent/http_lifecycle_stderr_log.py."""

import os
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agent.http_lifecycle_stderr_log import StderrLogManager, _DEFAULT_STDERR_TAIL_BYTES


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
        assert mgr._log_files == {}
        assert mgr._log_paths == {}


class TestOpenLog:
    def test_open_log_creates_directory_and_returns_handle(self):
        mgr = StderrLogManager()
        cfg = MagicMock()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch the log dir creation to use temp directory
            with patch("os.makedirs") as mock_makedirs, \
                 patch("builtins.open", new_callable=lambda: MagicMock()) as mock_open:
                mock_fh = MagicMock(spec=BytesIO)
                mock_open.return_value = mock_fh
                result = mgr.open_log("server1", cfg)
                assert result is not None
                mock_makedirs.assert_called_once()
                mock_open.assert_called_once()

    def test_open_log_stores_handle(self):
        mgr = StderrLogManager()
        cfg = MagicMock()
        with patch("os.makedirs"), \
             patch("builtins.open", new_callable=lambda: MagicMock()) as mock_open:
            mock_fh = MagicMock(spec=BytesIO)
            mock_open.return_value = mock_fh
            mgr.open_log("server1", cfg)
            assert "server1" in mgr._log_files

    def test_open_log_stores_path(self):
        mgr = StderrLogManager()
        cfg = MagicMock()
        with patch("os.makedirs"), \
             patch("builtins.open", new_callable=lambda: MagicMock()) as mock_open:
            mock_fh = MagicMock(spec=BytesIO)
            mock_open.return_value = mock_fh
            mgr.open_log("server1", cfg)
            assert "server1" in mgr._log_paths

    def test_open_log_raises_on_os_error(self):
        mgr = StderrLogManager()
        cfg = MagicMock()
        with patch("os.makedirs", side_effect=OSError("Permission denied")):
            with pytest.raises(Exception):
                mgr.open_log("server1", cfg)


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
            # Original file should be gone, rotated file should exist
            assert not os.path.exists(f.name)
            assert os.path.exists(f"{f.name}.old")
        finally:
            if os.path.exists(f"{f.name}.old"):
                os.unlink(f"{f.name}.old")

    def test_rotate_log_os_error_returns_false(self):
        mgr = StderrLogManager()
        mgr._log_paths["server1"] = "/nonexistent/path/stderr.log"
        result = mgr.rotate_log("server1", 1024)
        assert result is False
