"""tests/test_logger.py
Unit tests for shared.logger — Logger, _ContextFilter, _JsonFormatter.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import orjson
import pytest
from shared.logger import Logger, _ContextFilter, _JsonFormatter


class TestContextFilter:
    def test_filter_injects_fields(self) -> None:
        record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
        f = _ContextFilter()
        f.set(turn_id="abc", session_id="1")
        assert f.filter(record) is True
        assert record.turn_id == "abc"
        assert record.session_id == "1"

    def test_set_clears_none_fields(self) -> None:
        f = _ContextFilter()
        f.set(turn_id="abc", session_id=None)
        # None fields should not be stored
        assert "session_id" not in f._fields

    def test_clear_removes_all_fields(self) -> None:
        f = _ContextFilter()
        f.set(turn_id="abc")
        f.clear()
        assert f._fields == {}

    def test_filter_does_not_mutate_record_keys(self) -> None:
        record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
        f = _ContextFilter()
        f.set(extra_field="value")
        assert f.filter(record) is True
        assert hasattr(record, "extra_field")
        assert record.extra_field == "value"


class TestJsonFormatter:
    def test_format_produces_valid_json(self) -> None:
        record = logging.LogRecord("test", logging.INFO, "", 0, "hello world", (), None)
        fmt = _JsonFormatter()
        result = fmt.format(record)
        parsed = orjson.loads(result)
        assert parsed["msg"] == "hello world"
        assert parsed["level"] == "INFO"

    def test_format_includes_context_fields(self) -> None:
        record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
        record.turn_id = "turn-123"
        record.session_id = "sess-456"
        fmt = _JsonFormatter()
        result = fmt.format(record)
        parsed = orjson.loads(result)
        assert parsed["turn_id"] == "turn-123"
        assert parsed["session_id"] == "sess-456"

    def test_format_includes_exc_info(self) -> None:
        record = logging.LogRecord(
            "test",
            logging.ERROR,
            "",
            0,
            "boom",
            (),
            (ValueError, ValueError("oops"), None),
        )
        fmt = _JsonFormatter()
        result = fmt.format(record)
        parsed = orjson.loads(result)
        assert "exc" in parsed

    def test_format_omits_missing_context_fields(self) -> None:
        record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
        # No turn_id or session_id set
        fmt = _JsonFormatter()
        result = fmt.format(record)
        parsed = orjson.loads(result)
        assert "turn_id" not in parsed
        assert "session_id" not in parsed

    def test_format_includes_func_name(self) -> None:
        record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
        record.funcName = "my_function"
        fmt = _JsonFormatter()
        result = fmt.format(record)
        parsed = orjson.loads(result)
        assert parsed["func"] == "my_function"

    def test_format_level_correct(self) -> None:
        record = logging.LogRecord("test", logging.WARNING, "", 0, "msg", (), None)
        fmt = _JsonFormatter()
        result = fmt.format(record)
        parsed = orjson.loads(result)
        assert parsed["level"] == "WARNING"


class TestLoggerInit:
    def test_logger_with_valid_args(self, tmp_path: Path) -> None:
        log_file = str(tmp_path / "test.log")
        logger = Logger("test_module", log_file)
        assert logger._logger.name == "test_module"

    def test_blank_name_raises_value_error(self, tmp_path: Path) -> None:
        log_file = str(tmp_path / "test.log")
        with pytest.raises(ValueError):
            Logger("", log_file)

    def test_blank_log_file_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            Logger("test_module", "")

    def test_whitespace_name_raises_value_error(self, tmp_path: Path) -> None:
        log_file = str(tmp_path / "test.log")
        with pytest.raises(ValueError):
            Logger("   ", log_file)

    def test_whitespace_log_file_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            Logger("test_module", "   ")


class TestLoggerContext:
    def test_set_context_injects_fields(self, tmp_path: Path) -> None:
        log_file = str(tmp_path / "test.log")
        logger = Logger("ctx_test", log_file)
        logger.set_context(turn_id="t1", session_id="s1")
        # The filter should have the fields
        assert logger._filter._fields.get("turn_id") == "t1"
        assert logger._filter._fields.get("session_id") == "s1"

    def test_clear_context_removes_fields(self, tmp_path: Path) -> None:
        log_file = str(tmp_path / "test.log")
        logger = Logger("ctx_test", log_file)
        logger.set_context(turn_id="t1")
        logger.clear_context()
        assert logger._filter._fields == {}

    def test_set_context_with_none_omits_field(self, tmp_path: Path) -> None:
        log_file = str(tmp_path / "test.log")
        logger = Logger("ctx_test", log_file)
        logger.set_context(turn_id="t1", session_id=None)
        assert "session_id" not in logger._filter._fields


class TestLoggerDelegation:
    def test_info_delegates_to_underlying_logger(
        self, tmp_path: Path, capsys: Any
    ) -> None:  # type: ignore[name-defined]
        log_file = str(tmp_path / "test.log")
        logger = Logger("delegate_test", log_file)
        logger.info("test message")
        captured = capsys.readouterr()
        assert "test message" in captured.err

    def test_warning_delegates_to_underlying_logger(
        self, tmp_path: Path, capsys: Any
    ) -> None:  # type: ignore[name-defined]
        log_file = str(tmp_path / "test.log")
        logger = Logger("delegate_test", log_file)
        logger.warning("warn message")
        captured = capsys.readouterr()
        assert "warn message" in captured.err

    def test_error_delegates_to_underlying_logger(
        self, tmp_path: Path, capsys: Any
    ) -> None:  # type: ignore[name-defined]
        log_file = str(tmp_path / "test.log")
        logger = Logger("delegate_test", log_file)
        logger.error("error message")
        captured = capsys.readouterr()
        assert "error message" in captured.err

    def test_debug_delegates_to_underlying_logger(
        self, tmp_path: Path, capsys: Any
    ) -> None:  # type: ignore[name-defined]
        log_file = str(tmp_path / "test.log")
        logger = Logger("delegate_test", log_file)
        # DEBUG level is below INFO (logger.setLevel(logging.INFO)), so no output expected
        logger.debug("debug message")
        captured = capsys.readouterr()
        assert "debug message" not in captured.err


class TestLoggerStructured:
    def test_structured_log_produces_json(self, tmp_path: Path) -> None:
        log_file = str(tmp_path / "structured.log")
        logger = Logger("struct_test", log_file, structured_log=True)
        logger.info("structured message")
        # Read the log file
        content = Path(log_file).read_text(encoding="utf-8")
        parsed = orjson.loads(content.strip())
        assert parsed["msg"] == "structured message"
        assert parsed["level"] == "INFO"

    def test_structured_log_with_context(self, tmp_path: Path) -> None:
        log_file = str(tmp_path / "struct_ctx.log")
        logger = Logger("struct_ctx", log_file, structured_log=True)
        logger.set_context(turn_id="t123")
        logger.info("with context")
        content = Path(log_file).read_text(encoding="utf-8")
        parsed = orjson.loads(content.strip())
        assert parsed["turn_id"] == "t123"


class TestLoggerHandlerDuplication:
    def test_second_logger_same_name_skips_duplicate_handlers(
        self, tmp_path: Path
    ) -> None:
        log_file = str(tmp_path / "dup_test.log")
        _ = Logger("dup_logger", log_file)
        second = Logger("dup_logger", log_file)
        # Should not add duplicate handlers
        handler_count = len(second._logger.handlers)
        assert handler_count <= 2  # FileHandler + StreamHandler (max 2)
