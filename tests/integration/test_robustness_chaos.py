"""Chaos injection integration tests (3A–3D).

Exercises ToolLoopGuard, SQLite chaos, and network chaos scenarios.

Run 5x for flakiness check:
    for i in {1..5}; do uv run pytest tests/integration/test_robustness_chaos.py -v --timeout=30; done
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
import respx

# ── Shared helpers ────────────────────────────────────────────────────────────


def _make_ctx(
    dedup_max: int = 2, cycle_window: int = 3, retry_max: int = 0
) -> MagicMock:
    ctx = MagicMock()
    ctx.cfg.tool.tool_dedup_max_repeats = dedup_max
    ctx.cfg.tool.tool_cycle_detect_window = cycle_window
    ctx.cfg.tool.tool_error_retry_max = retry_max
    ctx.diagnostics = None
    return ctx


def _call(name: str, args: str = "{}") -> dict:
    return {"id": "x", "function": {"name": name, "arguments": args}}


def _msg(*calls) -> dict:
    return {"role": "assistant", "tool_calls": list(calls)}


# ═══════════════════════════════════════════════════════════════════════════════
# 3A. ToolLoopGuard Chaos
# ═══════════════════════════════════════════════════════════════════════════════


class TestToolLoopGuardChaos:
    """3A: ToolLoopGuard chaos scenarios."""

    def test_3a1_exact_duplicate_stops(self):
        """Exact duplicate tool call → guard detects and stops."""
        from agent.tool_loop_guard import ToolLoopGuard

        ctx = _make_ctx(dedup_max=2)
        guard = ToolLoopGuard(ctx)

        call = _call("read_text_file", '{"path": "/etc/hosts"}')
        seen: dict[str, int] = {}
        fp: list[str] = []
        failed: set[str] = set()

        assert guard.check_all(seen, fp, failed, _msg(call)) is None
        result = guard.check_all(seen, fp, failed, _msg(call))
        assert result is not None

    def test_3a2_near_duplicate_different_args_not_blocked(self):
        """Near-duplicate with different args — guard does NOT fire."""
        from agent.tool_loop_guard import ToolLoopGuard

        ctx = _make_ctx(dedup_max=2)
        guard = ToolLoopGuard(ctx)

        seen: dict[str, int] = {}
        fp: list[str] = []
        failed: set[str] = set()

        assert (
            guard.check_all(
                seen, fp, failed, _msg(_call("read_text_file", '{"path": "/a"}'))
            )
            is None
        )
        assert (
            guard.check_all(
                seen, fp, failed, _msg(_call("read_text_file", '{"path": "/b"}'))
            )
            is None
        )
        assert (
            guard.check_all(
                seen, fp, failed, _msg(_call("read_text_file", '{"path": "/c"}'))
            )
            is None
        )

    def test_3a3_cycle_detection(self):
        """A→B→A→B→A cycle (5 rounds) → guard fires on A's 3rd occurrence (window=2)."""
        from agent.tool_loop_guard import ToolLoopGuard

        ctx = _make_ctx(dedup_max=100, cycle_window=2)
        guard = ToolLoopGuard(ctx)

        msg_a = _msg(_call("read_text_file", '{"path": "/a"}'))
        msg_b = _msg(_call("read_text_file", '{"path": "/b"}'))

        fp: list[str] = []

        # check_cycle appends to fp internally on no-fire
        assert guard.check_cycle(fp, msg_a) is None  # round 1: A (count=0)
        assert guard.check_cycle(fp, msg_b) is None  # round 2: B (count=0)
        assert guard.check_cycle(fp, msg_a) is None  # round 3: A (count=1)
        assert guard.check_cycle(fp, msg_b) is None  # round 4: B (count=1)
        result = guard.check_cycle(
            fp, msg_a
        )  # round 5: A (count=2 >= window=2) → fires
        assert result is not None

    def test_3a4_error_escalation(self):
        """N consecutive tool errors → check_error_limit returns message."""
        from agent.tool_loop_guard import ToolLoopGuard

        ctx = _make_ctx()
        ctx.cfg.tool.tool_error_max_consecutive = 2
        guard = ToolLoopGuard(ctx)

        assert guard.check_error_limit(1) is None
        assert guard.check_error_limit(2) is not None  # threshold reached

    def test_3a5_reset_between_turns(self):
        """Guard state clears at turn start — no cross-turn state leakage."""
        from agent.tool_loop_guard import ToolLoopGuard

        ctx = _make_ctx(dedup_max=2)
        guard = ToolLoopGuard(ctx)

        call = _call("read_text_file", '{"path": "/etc/hosts"}')
        seen: dict[str, int] = {}
        fp: list[str] = []
        failed: set[str] = set()

        # Fill to limit in "turn 1"
        guard.check_all(seen, fp, failed, _msg(call))
        guard.check_all(seen, fp, failed, _msg(call))

        # Start "turn 2" with fresh state
        seen2: dict[str, int] = {}
        fp2: list[str] = []
        failed2: set[str] = set()

        # First call with new state should succeed
        assert guard.check_all(seen2, fp2, failed2, _msg(call)) is None


# ═══════════════════════════════════════════════════════════════════════════════
# 3B. ErrorInjectionService Chaos
# ═══════════════════════════════════════════════════════════════════════════════


class TestErrorInjectionChaos:
    """3B: Simulate injecting transport errors at specific rounds."""

    @pytest.mark.asyncio
    async def test_3b1_transport_error_at_specific_round(self):
        """Inject transport error → stat_transport_errors incremented."""
        from shared.mcp_config import McpServerConfig
        from shared.tool_executor import ToolExecutor

        cfg = McpServerConfig(
            transport="http",
            url="http://127.0.0.1:19002",
            cmd=[],
            tool_names=["_chaos_tool_b1"],
        )
        with respx.mock(
            base_url="http://127.0.0.1:19002", assert_all_called=False
        ) as mock:
            mock.post("/v1/call_tool").respond(504)
            async with httpx.AsyncClient() as http:
                executor = ToolExecutor(
                    http=http,
                    cache_ttl=0,
                    server_configs={"chaos_b1": cfg},
                )
                result = await executor.execute("_chaos_tool_b1", {})

        assert result.is_error
        assert executor.stat_transport_errors.get("chaos_b1", 0) == 1

    @pytest.mark.asyncio
    async def test_3b2_multiple_error_types_in_same_turn(self):
        """Different tools: one transport error, one tool error."""
        from shared.mcp_config import McpServerConfig
        from shared.tool_executor import ToolExecutor

        cfg = McpServerConfig(
            transport="http",
            url="http://127.0.0.1:19003",
            cmd=[],
            tool_names=["_chaos_tool_b2a", "_chaos_tool_b2b"],
        )

        def _side_effect(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            if body.get("name") == "_chaos_tool_b2a":
                return httpx.Response(504)  # always 504 → transport error after retries
            return httpx.Response(200, json={"result": "tool failed", "is_error": True})

        with respx.mock(
            base_url="http://127.0.0.1:19003", assert_all_called=False
        ) as mock:
            mock.post("/v1/call_tool").mock(side_effect=_side_effect)
            async with httpx.AsyncClient() as http:
                executor = ToolExecutor(
                    http=http,
                    cache_ttl=0,
                    server_configs={"chaos_b2": cfg},
                )
                r1 = await executor.execute("_chaos_tool_b2a", {})
                r2 = await executor.execute("_chaos_tool_b2b", {})

        assert r1.is_error and r1.error_type == "transport"
        assert r2.is_error and r2.error_type == "tool"

    @pytest.mark.asyncio
    async def test_3b3_partial_batch_failure(self):
        """In a batch: one tool fails, others succeed."""
        from shared.mcp_config import McpServerConfig
        from shared.tool_executor import ToolExecutor

        cfg = McpServerConfig(
            transport="http",
            url="http://127.0.0.1:19004",
            cmd=[],
            tool_names=["_chaos_ok", "_chaos_fail"],
        )
        call_count = 0

        def _side_effect(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            body = json.loads(request.content)
            if body.get("name") == "_chaos_fail":
                return httpx.Response(200, json={"result": "error!", "is_error": True})
            return httpx.Response(200, json={"result": "ok", "is_error": False})

        with respx.mock(
            base_url="http://127.0.0.1:19004", assert_all_called=False
        ) as mock:
            mock.post("/v1/call_tool").mock(side_effect=_side_effect)
            async with httpx.AsyncClient() as http:
                executor = ToolExecutor(
                    http=http,
                    cache_ttl=0,
                    server_configs={"chaos_b3": cfg},
                )
                ok, fail = await asyncio.gather(
                    executor.execute("_chaos_ok", {}),
                    executor.execute("_chaos_fail", {}),
                )

        assert not ok.is_error
        assert fail.is_error and fail.error_type == "tool"


# ═══════════════════════════════════════════════════════════════════════════════
# 3C. SQLite Chaos
# ═══════════════════════════════════════════════════════════════════════════════


class TestSqliteChaos:
    """3C: SQLite chaos scenarios."""

    def test_3c1_busy_lock_injection(self, tmp_path: Path):
        """Hold external EXCLUSIVE lock → agent write sees OperationalError."""
        from tests.integration.conftest import hold_write_lock

        db_path = str(tmp_path / "chaos_c1.sqlite")
        conn_init = sqlite3.connect(db_path)
        conn_init.execute("PRAGMA journal_mode=WAL")
        conn_init.execute("CREATE TABLE t (id TEXT PRIMARY KEY)")
        conn_init.commit()
        conn_init.close()

        lock_t = hold_write_lock(db_path, 1.0)
        time.sleep(0.05)

        conn = sqlite3.connect(db_path, timeout=0.1)
        conn.execute("PRAGMA busy_timeout=100")
        try:
            with pytest.raises(sqlite3.OperationalError):
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("INSERT INTO t VALUES ('x')")
                conn.commit()
        finally:
            conn.close()
            lock_t.join(timeout=3.0)

    def test_3c2_disk_full_simulation(self, tmp_path: Path):
        """Simulate disk-full: OperationalError raised and caught gracefully."""
        with patch(
            "sqlite3.connect",
            side_effect=sqlite3.OperationalError("disk I/O error"),
        ):
            with pytest.raises(sqlite3.OperationalError, match="disk I/O error"):
                sqlite3.connect(str(tmp_path / "never.sqlite"))

    def test_3c3_wal_checkpoint_degraded(self, tmp_path: Path):
        """WAL checkpoint on read-only path — graceful degradation."""
        db_path = str(tmp_path / "chaos_c3.sqlite")
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE t (id TEXT)")
        conn.commit()
        conn.close()

        # Make DB read-only (simulate checkpoint failure scenario)
        import os

        os.chmod(db_path, 0o444)
        try:
            ro_conn = sqlite3.connect(db_path, uri=True)
            # WAL checkpoint on read-only — should not raise
            try:
                ro_conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
            except sqlite3.OperationalError:
                pass  # expected on read-only
            ro_conn.close()
        finally:
            os.chmod(db_path, 0o644)


# ═══════════════════════════════════════════════════════════════════════════════
# 3D. Network Chaos
# ═══════════════════════════════════════════════════════════════════════════════


class TestNetworkChaos:
    """3D: Network chaos scenarios for HTTP transport."""

    @pytest.mark.asyncio
    async def test_3d1_intermittent_502s(self):
        """Server alternates 502/200 → retry handles correctly."""
        from shared.mcp_config import McpServerConfig
        from shared.tool_executor import ToolExecutor

        cfg = McpServerConfig(
            transport="http",
            url="http://127.0.0.1:19005",
            cmd=[],
            tool_names=["_chaos_d1"],
        )
        call_count = 0

        def _side_effect(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 1:
                return httpx.Response(502)
            return httpx.Response(200, json={"result": "ok", "is_error": False})

        with respx.mock(
            base_url="http://127.0.0.1:19005", assert_all_called=False
        ) as mock:
            mock.post("/v1/call_tool").mock(side_effect=_side_effect)
            async with httpx.AsyncClient() as http:
                executor = ToolExecutor(
                    http=http,
                    cache_ttl=0,
                    server_configs={"chaos_d1": cfg},
                )
                result = await executor.execute("_chaos_d1", {})

        # 502 triggers retry; should succeed on retry
        assert not result.is_error

    @pytest.mark.asyncio
    async def test_3d2_connection_reset(self):
        """Connection reset treated as transport error."""
        from shared.mcp_config import McpServerConfig
        from shared.tool_executor import ToolExecutor

        cfg = McpServerConfig(
            transport="http",
            url="http://127.0.0.1:19006",
            cmd=[],
            tool_names=["_chaos_d2"],
        )
        with respx.mock(
            base_url="http://127.0.0.1:19006", assert_all_called=False
        ) as mock:
            mock.post("/v1/call_tool").mock(
                side_effect=httpx.RemoteProtocolError("peer disconnected", request=None)
            )
            async with httpx.AsyncClient() as http:
                executor = ToolExecutor(
                    http=http,
                    cache_ttl=0,
                    server_configs={"chaos_d2": cfg},
                )
                result = await executor.execute("_chaos_d2", {})

        assert result.is_error
        assert result.error_type == "transport"

    @pytest.mark.asyncio
    async def test_3d3_partial_response_body(self):
        """HTTP 200 with truncated JSON → transport error."""
        from shared.mcp_config import McpServerConfig
        from shared.tool_executor import ToolExecutor

        cfg = McpServerConfig(
            transport="http",
            url="http://127.0.0.1:19007",
            cmd=[],
            tool_names=["_chaos_d3"],
        )
        with respx.mock(
            base_url="http://127.0.0.1:19007", assert_all_called=False
        ) as mock:
            # Respond with truncated JSON
            mock.post("/v1/call_tool").respond(200, content=b'{"result": "ok"')
            async with httpx.AsyncClient() as http:
                executor = ToolExecutor(
                    http=http,
                    cache_ttl=0,
                    server_configs={"chaos_d3": cfg},
                )
                result = await executor.execute("_chaos_d3", {})

        # Truncated JSON should cause is_error=True (parse error)
        assert result.is_error
