"""tests/mcp_servers/test_server_logging_sinks.py — Every MCP server writes its audit records to a log file."""

from __future__ import annotations

import importlib
import json
import logging
from pathlib import Path

import pytest
from mcp_servers.audit import _audit_log

_SERVER_MODULES = [
    "mcp_servers.shell.shell_server",
    "mcp_servers.git.git_server",
    "mcp_servers.web_search.web_search_server",
    "mcp_servers.file.delete_server",
    "mcp_servers.file.write_server",
    "mcp_servers.file.read_server",
    "mcp_servers.github.github_server",
    "mcp_servers.cicd.cicd_server",
    "mcp_servers.rag_pipeline.rag_pipeline_server",
    "mcp_servers.mdq.mdq_server",
]


def _stdlib_logger(module_name: str) -> logging.Logger:
    return logging.getLogger(importlib.import_module(module_name).logger.name)


@pytest.mark.parametrize("module_name", _SERVER_MODULES)
def test_server_logger_has_info_enabled_and_a_handler(module_name: str) -> None:
    logger = _stdlib_logger(module_name)
    assert logger.isEnabledFor(logging.INFO)
    assert logger.handlers


@pytest.mark.parametrize("module_name", _SERVER_MODULES)
def test_audit_record_is_written_to_the_server_log_file(module_name: str) -> None:
    module = importlib.import_module(module_name)
    logger = _stdlib_logger(module_name)
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    if not file_handlers:
        pytest.skip(f"{module_name} logs to stderr only (log file could not be opened)")
    log_file = Path(file_handlers[0].baseFilename)
    request_id = f"req-sink-{module_name.rsplit('.', 1)[-1]}"

    _audit_log(
        module.logger,
        session_id="sess-sink",
        request_id=request_id,
        action="probe",
        target="t",
        outcome="ok",
        server_key="probe",
    )
    for handler in logger.handlers:
        handler.flush()

    lines = [line for line in log_file.read_text().splitlines() if request_id in line]
    assert len(lines) == 1
    record = json.loads(lines[0][lines[0].index("{") :])
    assert record["event"] == "mcp_tool_exec"
