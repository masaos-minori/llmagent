"""scripts/agent/services/mcp_health.py

MCP service health checks."""

from __future__ import annotations

from http import HTTPStatus
from urllib.parse import urlparse

import httpx
from shared.logger import Logger

from agent.context import AgentContext
from agent.output_tags import OutputTag
from agent.shared.health_models import (
    HealthCheckResult,
    McpHealthProbeResult,
    ServiceWarning,
)

logger = Logger(__name__, "/opt/llm/logs/agent.log")


async def _probe_mcp_health_detail(
    http: httpx.AsyncClient,
    base_url: str,
    headers: dict[str, str] | None = None,
) -> McpHealthProbeResult:
    """Probe /health and return a structured McpHealthProbeResult.

    Never raises. On network failure returns reachable=False with status_code=None.
    On JSON parse failure falls back to restart_recommended=False, operator_action_required=False.
    """
    try:
        if headers:
            resp = await http.get(f"{base_url}/health", timeout=5.0, headers=headers)
        else:
            resp = await http.get(f"{base_url}/health", timeout=5.0)
    except (httpx.HTTPError, OSError, TimeoutError):
        return McpHealthProbeResult(
            reachable=False,
            status_code=None,
            restart_recommended=False,
            operator_action_required=False,
            body={},
        )
    try:
        body: dict[str, object] = resp.json()  # noqa: S603 — MCP server response body structure varies
    except Exception as exc:  # noqa: BLE001 — health check must not fail on body parse errors
        return McpHealthProbeResult(
            reachable=True,
            status_code=resp.status_code,
            restart_recommended=False,
            operator_action_required=False,
            body={},
            parse_failed=True,
            parse_error=f"{exc} (raw={resp.text[:200]!r})",
        )
    restart_recommended: bool = bool(body.get("restart_recommended", False))
    operator_action_required: bool = bool(body.get("operator_action_required", False))
    return McpHealthProbeResult(
        reachable=True,
        status_code=resp.status_code,
        restart_recommended=restart_recommended,
        operator_action_required=operator_action_required,
        body=body,
    )


async def check_service_health(ctx: AgentContext) -> HealthCheckResult:
    """Probe LLM and Embed service health at startup.

    The LLM is a required service: its failure is reported as a fatal error. The
    embed-llm is optional: the agent runs in degraded mode without it, so its
    failure is a non-fatal warning. Derives each /health URL by stripping the path
    from the endpoint URL.
    """
    if ctx.services_required.http is None:
        raise RuntimeError("http service not initialized")
    # (label, url, required): required-service failures are fatal; optional ones degrade.
    checks: list[tuple[str, str, bool]] = [
        ("llm", ctx.cfg.llm.llm_url, True),
        ("embed-llm", ctx.cfg.rag.embed_url, False),
    ]
    warnings: list[ServiceWarning] = []
    errors: list[ServiceWarning] = []
    for label, url, required in checks:
        if not url:
            continue
        parsed = urlparse(url)
        health_url = f"{parsed.scheme}://{parsed.netloc}/health"
        failure: str | None = None
        try:
            resp = await ctx.services_required.http.get(health_url, timeout=2.0)
            if resp.status_code != HTTPStatus.OK:
                failure = f"{label} health check returned HTTP {resp.status_code}"
        except (httpx.HTTPError, OSError) as exc:
            reason = f"unreachable at {health_url}: {exc}"
            failure = f"{OutputTag.NON_FATAL} {label} {reason}"
        if failure is not None:
            entry = ServiceWarning(label=label, url=health_url, message=failure)
            if required:
                errors.append(entry)
            else:
                logger.warning("%s", failure)
                warnings.append(entry)
    return HealthCheckResult(warnings=warnings, errors=errors)


async def check_readiness(ctx: AgentContext) -> HealthCheckResult:
    """Probe required services at startup; raise RuntimeError on required-service failure.

    Only required services (currently the LLM) block startup. Optional services
    (currently embed-llm) degrade: their failures surface as non-fatal warnings
    instead of raising.
    """
    result = await check_service_health(ctx)
    if result.errors:
        error_msgs = [f"{w.label}: {w.message}" for w in result.errors]
        msg = (
            "Startup readiness check failed (required services unavailable): "
            + "; ".join(error_msgs)
        )
        logger.error(msg)
        raise RuntimeError(msg)
    return result
