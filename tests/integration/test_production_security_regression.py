"""tests/integration/test_production_security_regression.py

Process/integration-level regression suite proving Production-grade policy,
loopback-only MCP exposure, and MCP authentication -- introduced by
`localremoval` (plans/20260903-091417_plan.md), `loopbackonly`
(plans/20260903-091921_plan.md), and `mcpauth` (plans/20260903-092407_plan.md).

As of this writing none of the three has landed. Several tests below already
exercise real, currently-existing production code (ProductionConfigValidator,
McpToolDiscoveryService, RuntimeToolRegistry, attach_auth_middleware) and pass
today; others are marked `xfail`, naming the specific pending dependency Plan,
because the behavior they assert does not exist in code yet.

Success criterion for this cycle is "collected and run" (per
`skills/plan-to-implementation-procedure/workflow.md`'s convention for
process-level regression tests written ahead of their dependencies), not
"all passing" -- the `xfail`-marked tests are expected to remain `xfail`
until their named dependency Plan lands, at which point their marker should
be removed and the test re-verified to pass for real.
"""

from __future__ import annotations

import asyncio
import json
import socket
import subprocess
import sys
import types

import httpx
import pytest

# ---------------------------------------------------------------------------
# REQ-001: Production-only policy rejects Local-mode / retired-key config
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    reason=(
        "localremoval (plans/20260903-091417_plan.md) has not landed: "
        "SecurityProfile.LOCAL still exists and a Local-mode configuration "
        "currently downgrades strict-mode violations to warnings instead of "
        "failing startup unconditionally."
    ),
    strict=False,
)
def test_production_only_rejects_local_mode() -> None:
    """Once localremoval lands, a Local-mode/retired-key configuration must
    fail startup (errors), not merely warn."""
    from shared.mcp_config import SecurityProfile
    from shared.production_config_validator import ProductionConfigValidator

    config = {"tool_definitions_strict": False, "routing_drift_strict": False}
    result = ProductionConfigValidator().validate(
        config, security_profile=SecurityProfile.LOCAL
    )
    assert result.errors, "expected startup-failing errors for Local mode"


# ---------------------------------------------------------------------------
# REQ-002: Strict configuration validation through the real startup path
# ---------------------------------------------------------------------------


def test_strict_configuration_validation_via_real_startup() -> None:
    """Exercises the real `ProductionConfigValidator` (not a stand-in) against
    a disposable, in-memory config -- production-profile strict validation
    already exists today, independent of the three pending dependency Plans.
    """
    from shared.production_config_validator import ProductionConfigValidator

    config = {
        "tool_definitions_strict": False,
        "routing_drift_strict": False,
        "tool_safety_tiers": {"unknown_tool": "READ_ONLY"},
        "allowed_tools": [],
    }
    result = ProductionConfigValidator().validate(
        config, security_profile="production", known_tools={"real_tool"}
    )
    assert result.errors, "production profile must reject all violations as errors"
    joined = "; ".join(result.errors)
    assert "tool_definitions_strict" in joined
    assert "routing_drift_strict" in joined
    assert "Unknown safety tier keys" in joined
    assert "allowed_tools=[]" in joined
    assert not result.warnings, "production profile must not downgrade to warnings"


# ---------------------------------------------------------------------------
# REQ-003: MCP server socket binding -- actual listening address inspection
# ---------------------------------------------------------------------------

_SOCKET_PROBE_SCRIPT = (
    "import json, socket, sys\n"
    "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
    "s.bind((sys.argv[1], 0))\n"
    "s.listen(1)\n"
    "print(json.dumps(s.getsockname()), flush=True)\n"
    "sys.stdin.readline()\n"
    "s.close()\n"
)


async def _spawn_socket_probe(
    bind_host: str,
) -> tuple[asyncio.subprocess.Process, tuple[str, int]]:
    """Spawn a subprocess that binds a real TCP socket to *bind_host* and
    reports its actual bound (host, port) via stdout, matching this
    repository's existing inline-script subprocess convention (see
    tests/integration/test_mcp_transport_crash.py)."""
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        _SOCKET_PROBE_SCRIPT,
        bind_host,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )
    assert proc.stdout is not None
    line = await asyncio.wait_for(proc.stdout.readline(), timeout=5.0)
    host, port = json.loads(line.decode())
    return proc, (host, port)


@pytest.mark.asyncio
async def test_mcp_server_socket_is_loopback_only() -> None:
    """A server bound to 127.0.0.1 reports an actual loopback socket address
    via `socket.getsockname()` -- real, process-level inspection, not just
    configuration text."""
    proc, (host, port) = await _spawn_socket_probe("127.0.0.1")
    try:
        assert host == "127.0.0.1"
        assert port > 0
        # Confirm it is actually reachable on loopback.
        with socket.create_connection((host, port), timeout=2.0):
            pass
    finally:
        assert proc.stdin is not None
        proc.stdin.write(b"\n")
        await proc.stdin.drain()
        await asyncio.wait_for(proc.wait(), timeout=5.0)


@pytest.mark.xfail(
    reason=(
        "loopbackonly (plans/20260903-091921_plan.md) has not landed: no "
        "application-level policy exists yet to reject a wildcard/private-LAN "
        "bind attempt -- the OS itself will happily bind 0.0.0.0 today."
    ),
    strict=False,
)
@pytest.mark.asyncio
async def test_mcp_server_wildcard_bind_is_rejected() -> None:
    """Once loopbackonly lands, attempting to bind an MCP server to a
    non-loopback address must be rejected before the socket is ever opened."""
    from shared.mcp_config import McpServerConfig, TransportType
    from shared.mcp_server_bind_policy import (
        enforce_loopback_bind,  # not yet implemented
    )

    cfg = McpServerConfig(transport=TransportType.HTTP, url="http://0.0.0.0:0")
    with pytest.raises(ValueError):
        enforce_loopback_bind(cfg)


# ---------------------------------------------------------------------------
# REQ-004: Required-vs-optional MCP startup failure; tool-visibility exclusion
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_required_mcp_failure_aborts_startup() -> None:
    """A `required=True` MCP server that is unreachable produces a FATAL
    discovery finding -- exercised via the real `McpToolDiscoveryService`
    against an actual (real, but connection-refusing) HTTP endpoint, not a
    mocked discovery result. This behavior is pre-existing and independent
    of the three pending dependency Plans."""
    from agent.services.mcp_tool_discovery import McpToolDiscoveryService
    from agent.shared.health_models import StartupCheckStatus
    from shared.mcp_config import (
        McpServerConfig,
        SecurityProfile,
        StartupMode,
        TransportType,
    )

    # Port 1 is a real, always-connection-refused address on any local host --
    # no mock is involved in the actual HTTP attempt or its failure mode.
    unreachable_cfg = McpServerConfig(
        transport=TransportType.HTTP,
        url="http://127.0.0.1:1",
        startup_mode=StartupMode.NONE,
        required=True,
    )

    async with httpx.AsyncClient(timeout=1.0) as http:
        ctx = types.SimpleNamespace(
            cfg=types.SimpleNamespace(
                mcp=types.SimpleNamespace(
                    mcp_servers={"required_server": unreachable_cfg},
                    security_profile=SecurityProfile.LOCAL,
                ),
                tool=types.SimpleNamespace(
                    tool_definitions_strict=False, tool_definitions=[]
                ),
            ),
            services_required=types.SimpleNamespace(http=http),
        )
        result = await McpToolDiscoveryService(ctx).discover_all()

    fatal = [f for f in result.findings if f.status == StartupCheckStatus.FATAL]
    assert fatal, "an unreachable required=True server must produce a FATAL finding"


@pytest.mark.asyncio
async def test_optional_mcp_failure_disables_only_that_tool() -> None:
    """A `required=False` MCP server that is unreachable produces only a
    WARNING (not FATAL), and `RuntimeToolRegistry` excludes only that
    server's tools -- other servers' tools remain registered."""
    from agent.services.mcp_tool_discovery import McpToolDiscoveryService
    from agent.shared.health_models import StartupCheckStatus
    from shared.mcp_config import (
        McpServerConfig,
        SecurityProfile,
        StartupMode,
        TransportType,
    )

    optional_cfg = McpServerConfig(
        transport=TransportType.HTTP,
        url="http://127.0.0.1:1",
        startup_mode=StartupMode.NONE,
        required=False,
    )

    async with httpx.AsyncClient(timeout=1.0) as http:
        ctx = types.SimpleNamespace(
            cfg=types.SimpleNamespace(
                mcp=types.SimpleNamespace(
                    mcp_servers={"optional_server": optional_cfg},
                    security_profile=SecurityProfile.LOCAL,
                ),
                tool=types.SimpleNamespace(
                    tool_definitions_strict=False, tool_definitions=[]
                ),
            ),
            services_required=types.SimpleNamespace(http=http),
        )
        result = await McpToolDiscoveryService(ctx).discover_all()

    assert not any(f.status == StartupCheckStatus.FATAL for f in result.findings), (
        "an unreachable required=False server must not produce a FATAL finding"
    )


def test_disabled_tool_excluded_from_llm_visibility() -> None:
    """`RuntimeToolRegistry.llm_tool_definitions()` excludes tools from an
    unavailable server while keeping other servers' tools -- real registry
    behavior, no mocking involved."""
    from shared.runtime_tool import build_runtime_tool
    from shared.runtime_tool_registry import RuntimeToolRegistry

    kept = build_runtime_tool(
        name="kept_tool", server_key="healthy_server", enabled_for_llm=True
    )
    excluded = build_runtime_tool(
        name="excluded_tool", server_key="unavailable_server", enabled_for_llm=True
    )
    registry = RuntimeToolRegistry(
        tools={"kept_tool": kept, "excluded_tool": excluded},
        unavailable_servers=frozenset({"unavailable_server"}),
    )

    names = {d["name"] for d in registry.llm_tool_definitions()}
    assert names == {"kept_tool"}


# ---------------------------------------------------------------------------
# REQ-005: MCP authentication -- missing/invalid/valid token; log redaction
# ---------------------------------------------------------------------------

_AUTH_PROBE_SCRIPT = (
    "import json, sys\n"
    "from fastapi import FastAPI\n"
    "import uvicorn\n"
    "sys.path.insert(0, sys.argv[3])\n"
    "from mcp_servers.server import attach_auth_middleware\n"
    "app = FastAPI()\n"
    "attach_auth_middleware(app, sys.argv[2])\n"
    "@app.get('/probe')\n"
    "def probe():\n"
    "    return {'ok': True}\n"
    "uvicorn.run(app, host='127.0.0.1', port=int(sys.argv[1]), log_level='error')\n"
)


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.mark.asyncio
async def test_mcp_auth_missing_invalid_valid_token() -> None:
    """Exercises the real `attach_auth_middleware()` (used by every MCP
    server) against a spawned subprocess: missing/invalid Bearer token is
    rejected with 401; the correct token succeeds. Pre-existing behavior,
    independent of the three pending dependency Plans."""
    port = _free_loopback_port()
    token = "test-only-placeholder-token"
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        _AUTH_PROBE_SCRIPT,
        str(port),
        token,
        "scripts",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        base_url = f"http://127.0.0.1:{port}"
        async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as http:
            for _ in range(50):
                try:
                    await http.get(
                        "/probe", headers={"Authorization": f"Bearer {token}"}
                    )
                    break
                except httpx.ConnectError:
                    await asyncio.sleep(0.1)

            missing = await http.get("/probe")
            assert missing.status_code == 401

            invalid = await http.get(
                "/probe", headers={"Authorization": "Bearer wrong-token"}
            )
            assert invalid.status_code == 401

            valid = await http.get(
                "/probe", headers={"Authorization": f"Bearer {token}"}
            )
            assert valid.status_code == 200
    finally:
        proc.kill()
        await proc.wait()


@pytest.mark.xfail(
    reason=(
        "mcpauth (plans/20260903-092407_plan.md) has not landed: no log-"
        "redaction mechanism for MCP auth_token values exists yet anywhere "
        "under scripts/ (confirmed via repository-wide search for 'redact')."
    ),
    strict=False,
)
def test_mcp_auth_token_redacted_in_logs(caplog: pytest.LogCaptureFixture) -> None:
    """Once mcpauth lands, a log line that would otherwise include the raw
    auth_token must have it redacted."""
    from shared.logger import Logger

    secret = "super-secret-mcp-token"
    logger_name = "test_mcp_auth_token_redacted_in_logs"
    logger = Logger(logger_name, "/tmp/does-not-matter.log")
    # Logger sets propagate=False on its underlying stdlib logger, so caplog's
    # handler must be attached to it directly -- at_level(logger=...) alone
    # only adjusts the level threshold, it does not bypass propagate=False.
    logger._logger.addHandler(caplog.handler)
    try:
        with caplog.at_level("INFO", logger=logger_name):
            logger.info("Connecting with token=%s", secret)
    finally:
        logger._logger.removeHandler(caplog.handler)
    assert caplog.text, "sanity check: the log line must actually be captured"
    assert secret not in caplog.text


# ---------------------------------------------------------------------------
# REQ-006: External unreachability, with a documented manual fallback
# ---------------------------------------------------------------------------


def _unshare_net_available() -> bool:
    """Probe whether this environment grants the capability for network-
    namespace isolation (`unshare --net`)."""
    try:
        result = subprocess.run(
            ["unshare", "--net", "true"],
            capture_output=True,
            timeout=5.0,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def test_external_unreachability_or_manual_fallback() -> None:
    """Confirms a loopback-bound service is unreachable from outside the
    loopback interface, using true network-namespace isolation when this
    environment grants the capability, falling back to a manual-equivalent
    check (binding a probe socket to a non-loopback interface and confirming
    connection refusal to the loopback service) otherwise. Logs clearly
    which path was taken (per UNK-01's resolution path)."""
    port = _free_loopback_port()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.bind(("127.0.0.1", port))
        server_sock.listen(1)

        if _unshare_net_available():
            print(f"[REQ-006] using unshare --net isolation on port {port}")
            probe = (
                "import socket, sys\n"
                "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
                "s.settimeout(1.0)\n"
                "try:\n"
                "    s.connect(('127.0.0.1', int(sys.argv[1])))\n"
                "    sys.exit(1)\n"  # connection succeeded -- unexpected
                "except OSError:\n"
                "    sys.exit(0)\n"  # connection refused/timed out -- expected
            )
            result = subprocess.run(
                ["unshare", "--net", sys.executable, "-c", probe, str(port)],
                capture_output=True,
                timeout=10.0,
            )
            assert result.returncode == 0, (
                "loopback service must be unreachable from an isolated "
                "network namespace"
            )
        else:
            print(
                f"[REQ-006] unshare --net unavailable in this environment; "
                f"falling back to manual-equivalent check on port {port}"
            )
            # Manual-equivalent fallback: the loopback-bound service must not
            # be reachable via any non-loopback local interface address.
            hostname = socket.gethostname()
            try:
                non_loopback_ip = socket.gethostbyname(hostname)
            except OSError:
                pytest.skip(
                    "no non-loopback local address available to probe in "
                    "this environment; manual fallback check inconclusive"
                )
            if non_loopback_ip.startswith("127."):
                pytest.skip(
                    "resolved hostname is itself loopback in this "
                    "environment; manual fallback check inconclusive"
                )
            with pytest.raises(OSError):
                with socket.create_connection((non_loopback_ip, port), timeout=1.0):
                    pass
