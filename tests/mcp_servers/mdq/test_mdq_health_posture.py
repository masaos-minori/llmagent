"""tests/mcp_servers/mdq/test_mdq_health_posture.py

Security Posture HTTP bind gate for scripts/mcp_servers/mdq/mdq_server.py (REQ-004, AC-004).

The posture is built once at module import from the already loaded config, so the gate is
startup-only and no later /health probe re-validates it (ADR-003 Static Availability).
tests/conftest.py sets MCP_MDQ_AUTH_TOKEN to a non-empty dummy value, so the shipped posture
carries every check as OK and stays validated.
"""

from __future__ import annotations

import logging

import pytest
from mcp_servers.mdq import mdq_server
from mcp_servers.mdq.mdq_security_validation import build_mdq_posture


def _let_the_module_log(monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-enable propagation so caplog sees the dedicated logger shared.logger disables."""
    monkeypatch.setattr(logging.getLogger(mdq_server.__name__), "propagate", True)


class TestBindGate:
    """AC-004: mdq-mcp does not bind HTTP when the posture is not validated."""

    def test_validated_posture_does_not_block_bind(self) -> None:
        mdq_server._enforce_posture_gate()

    def test_gate_refuses_bind_and_logs_reason_codes(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        posture = build_mdq_posture(
            mdq_cfg={},
            db_file_present=False,
            schema_error=("db_file", "database not found"),
            schema_checked=True,
            index_stats=None,
        )
        monkeypatch.setattr(mdq_server, "_security_posture", posture)
        _let_the_module_log(monkeypatch)

        assert posture.validated is False
        failed = {
            f"{check.check_id}:{check.reason_code}"
            for check in posture.checks
            if check.status.value == "failed"
        }
        assert failed, "expected the failing inputs to produce a FAILED check"

        with pytest.raises(SystemExit) as excinfo:
            mdq_server._enforce_posture_gate()

        assert excinfo.value.code == 1
        gate_lines = [
            record.getMessage()
            for record in caplog.records
            if "refusing to bind" in record.getMessage()
        ]
        assert gate_lines, "the gate did not log a refusal"
        for expected in failed:
            assert expected in gate_lines[0]
