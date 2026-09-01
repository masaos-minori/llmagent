"""MCP service health checks."""

from __future__ import annotations

import httpx
from http import HTTPStatus
from urllib.parse import urlparse

from agent.context import AgentContext
from agent.output_tags import OutputTag
from agent.shared.health_models import HealthCheckResult, McpHealthProbeResult, ServiceWarning
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/agent.log")


async def _probe_mcp_health_detail(
    http: httpx.AsyncClient, base_url: str
) -> McpHealthProbeResult:
    """Probe /health and return a structured McpHealthProbeResult.

    Never raises. On network failure returns reachable=False with status_code=None.
    On JSON parse failure falls back to restart_recommended=False, operator_action_required=False.
    """
    try:
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
        body: dict[str, object] = resp.json()  # noqa: S603 -- MCP server response body structure varies
    except Exception as exc:  # noqa: BLE001 -- health check must not fail on body parse errors
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
    """Probe LLM and Embed service health at startup; return warning strings on failure.

    Failure is non-fatal: the REPL continues regardless.
    Derives the /health URL by stripping the path from each endpoint URL.
    """
    if ctx.services_required.http is None:
        raise RuntimeError("http service not initialized")
    checks = [
        ("llm", ctx.cfg.llm.llm_url),
        ("embed-llm", ctx.cfg.rag.embed_url),
    ]
    warnings: list[ServiceWarning] = []
    for label, url in checks:
        if not url:
            continue
        parsed = urlparse(url)
        health_url = f"{parsed.scheme}://{parsed.netloc}/health"
        try:
            resp = await ctx.services_required.http.get(health_url, timeout=2.0)
            if resp.status_code != HTTPStatus.OK:
                msg = f"{label} health check returned HTTP {resp.status_code}"
                logger.warning(msg)
                warnings.append(
                    ServiceWarning(label=label, url=health_url, message=msg)
                )
        except (httpx.HTTPError, OSError) as e:
            msg = f"{OutputTag.NON_FATAL} {label} unreachable at {health_url}: {e}"
            logger.warning(msg)
            warnings.append(ServiceWarning(label=label, url=health_url, message=msg))
    return HealthCheckResult(warnings=warnings)


async def check_readiness(
    ctx: AgentContext, *, production_mode: bool = False
) -> HealthCheckResult:
    """Probe required services at startup; raise in production mode on failure.

    In production mode, any failed health check raises RuntimeError listing
    which services are unavailable.
    In development mode, behaves like check_service_health(): warnings only.
    """
    result = await check_service_health(ctx)
    if production_mode and result.has_issues:
        error_msgs = [f"{w.label}: {w.message}" for w in result.warnings]
        msg = (
            "Startup readiness check failed (required services unavailable): "
            + "; ".join(error_msgs)
        )
        logger.error(msg)
        raise RuntimeError(msg)
    return result
