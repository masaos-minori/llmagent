"""scripts/agent/services/mcp_health.py

MCP service health checks — LLM and embed health plus Security Posture gating: collect_server_postures()
probes every usable MCP server's /health once, classifies each result as an Availability, Safety, or
Integrity failure, and hands the fully green gates to Tool Discovery. Each gate also carries the body
parsed through the shared health contract, and classify_capabilities() reads that report for the server's
catalog required_capability: required loss is a FATAL finding, optional loss is a warning (REQ-005).
"""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from http import HTTPStatus
from urllib.parse import urlparse

import httpx
from shared.logger import Logger
from shared.mcp_config import TransportType, get_effective_health_timeout
from shared.mcp_health_contract import (
    CAPABILITY_STATE_OK,
    HealthReport,
    parse_health_body,
)
from shared.security.result_dto import (
    REASON_CHECK_SET_MISMATCH,
    REASON_CONFIG_INVALID,
    REASON_CONTRACT_VERSION_MISMATCH,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_FINGERPRINT_MISMATCH,
    REASON_POSTURE_MISSING,
    REASON_SERVER_KEY_MISMATCH,
)
from shared.tool_catalog import load_tool_catalog, required_capability_for

from agent.context import AgentContext
from agent.http_lifecycle_health_checker import HealthChecker
from agent.output_tags import OutputTag
from agent.services.posture_validator import parse_posture
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
    timeout_sec: float | None = None,
) -> McpHealthProbeResult:
    """Probe /health and return a structured McpHealthProbeResult.

    `timeout_sec` is the server's effective `health_timeout` (REQ-001); when omitted the request
    keeps the client's own timeout, which is the per-server value the `/mcp status` path builds.
    Never raises. On network failure returns reachable=False with status_code=None.
    On JSON parse failure falls back to restart_recommended=False, operator_action_required=False.
    """
    kwargs: dict[str, object] = {}
    if timeout_sec is not None:
        kwargs["timeout"] = timeout_sec
    if headers:
        kwargs["headers"] = headers
    try:
        resp = await http.get(f"{base_url}/health", **kwargs)
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


class ServerFailureClass(StrEnum):
    """Kind of MCP server failure. Availability is reachability; Safety and Integrity are posture."""

    AVAILABILITY = "availability"
    SAFETY = "safety"
    INTEGRITY = "integrity"


@dataclass(frozen=True)
class PostureGate:
    """One server's permission to serve tools, decided from the posture it published.

    Fields:
        server_key:       Config key of the probed server.
        required:         Config flag deciding error versus warning for an Availability failure; a Safety or Integrity failure is an error whatever it says. Classification source: `registry/component_mandatoriness.yaml` (validated against config at startup).
        reachable:        An HTTP response was received.
        posture_accepted: The published posture satisfied the shared contract.
        ready:            The posture's own ready flag; False when the posture was rejected.
        validated:        The posture's own validated flag; False when the posture was rejected.
        reason_code:      Shared reason vocabulary entry explaining a non-green gate.
        parse_failed:     The server answered, but not with a body the Agent could read.
        report:           The body parsed through the shared health contract (seq 01); None when
                          the body was unreadable or violated the contract. Readiness proof for
                          REQ-005 comes from this, not from the status code.
        failure_class:    None when the gate is green.
    """

    server_key: str
    required: bool
    reachable: bool
    posture_accepted: bool
    ready: bool
    validated: bool
    reason_code: str
    parse_failed: bool = False
    report: HealthReport | None = None
    failure_class: ServerFailureClass | None = None


_INTEGRITY_REASON_CODES = frozenset(
    {
        REASON_POSTURE_MISSING,
        REASON_CONTRACT_VERSION_MISMATCH,
        REASON_CHECK_SET_MISMATCH,
        REASON_FINGERPRINT_MISMATCH,
        REASON_SERVER_KEY_MISMATCH,
        REASON_CONFIG_INVALID,
    }
)

_POSTURE_LABEL_PREFIX = "mcp:"

_SAFETY_INTEGRITY_CLASSES = frozenset(
    {ServerFailureClass.SAFETY, ServerFailureClass.INTEGRITY}
)


def _is_fatal_gate(gate: PostureGate) -> bool:
    """Decide whether one non-green gate blocks startup.

    A Safety or Integrity posture failure blocks startup whatever `required` says: ADR-004 Group 2
    item 6 and INV-09/INV-10 permit partial availability only for an availability failure of a
    component classified non-mandatory. `required` therefore decides the fate of an Availability
    failure alone; the mandatory/non-mandatory classification itself comes from the machine-readable
    registry `registry/component_mandatoriness.yaml` (ADR-004 Group 3 item 13: criteria in ADR-004,
    classification in the registry, derived table in `agent_08_04`).
    """
    return gate.required or gate.failure_class in _SAFETY_INTEGRITY_CLASSES


def classify_server_failure(gate: PostureGate) -> ServerFailureClass | None:
    """Return the failure kind of one gate, or None when the gate is green.

    Fixed order, first match wins: an unreachable probe or an unreadable body is Availability; a
    rejected posture is Integrity when its reason says the contract was not satisfied and Availability
    otherwise; an accepted posture that was not validated is Safety; an accepted, validated posture that
    is not ready is Availability. An unclassified rejection is a failure, never a pass.
    """
    if not gate.reachable or gate.parse_failed:
        return ServerFailureClass.AVAILABILITY
    if not gate.posture_accepted:
        if gate.reason_code in _INTEGRITY_REASON_CODES:
            return ServerFailureClass.INTEGRITY
        return ServerFailureClass.AVAILABILITY
    if not gate.validated:
        return ServerFailureClass.SAFETY
    if not gate.ready:
        return ServerFailureClass.AVAILABILITY
    return None


def _decide(gate: PostureGate) -> PostureGate:
    """Attach the failure class a gate carries, computed by the single classification rule."""
    return replace(gate, failure_class=classify_server_failure(gate))


@dataclass(frozen=True)
class CapabilityFinding:
    """What one gate's parsed report proves about its capabilities.

    Fields:
        required_capability: The catalog identifier the gate is measured against; None when the
                             server declares none, which puts the decision on the legacy `ready` flag.
        required_proven:     True when the report proves that capability `ok`; a legacy body, or a
                             server with no declared capability, is read through its `ready` flag (D-6).
        degraded_optional:   Every other capability reported `degraded` or `unavailable`, sorted.
                             This is the map Tool Discovery hands to the registry (seq 09).
    """

    required_capability: str | None
    required_proven: bool
    degraded_optional: tuple[str, ...]


def classify_capabilities(
    gate: PostureGate, required_capability: str | None
) -> CapabilityFinding:
    """Classify one gate's report for its required capability and its optional losses.

    The readiness decision is the shared predicate's (`HealthChecker.is_ready`), not a copy of it.
    A gate with no parsed report proves nothing, so its required capability is not proven.
    """
    report = gate.report
    if report is None:
        return CapabilityFinding(required_capability, False, ())
    degraded = tuple(
        sorted(
            name
            for name, state in report.capabilities.items()
            if name != required_capability and state.state != CAPABILITY_STATE_OK
        )
    )
    return CapabilityFinding(
        required_capability,
        HealthChecker.is_ready(report, required_capability),
        degraded,
    )


def _parse_report(body: Mapping[str, object]) -> HealthReport | None:
    """Parse a body through the shared contract; a contract-violating body yields no report."""
    try:
        return parse_health_body(body)
    except ValueError:
        # Not proof, and not a parse failure the gate already reports: the gate keeps its own
        # reason code and the classification reads it as unproven.
        return None


def _load_catalog_for_gates() -> Mapping[str, object] | None:
    """Load the catalog once for the gate loop.

    An unreadable catalog resolves to None with a warning here, so gates are read through the
    legacy `ready` fallback (D-6). The fail-closed FATAL for a missing catalog stays at tool
    discovery, which is the enforcement point for REQ-005.
    """
    try:
        return load_tool_catalog()
    except (OSError, tomllib.TOMLDecodeError) as exc:
        logger.warning("Posture gate: tool catalog unavailable: %s", exc)
        return None


def _gate_from_probe(
    server_key: str,
    required: bool,
    probe: McpHealthProbeResult,
) -> PostureGate:
    """Turn one probe result into an undecided gate."""
    if not probe.reachable:
        return PostureGate(
            server_key=server_key,
            required=required,
            reachable=False,
            posture_accepted=False,
            ready=False,
            validated=False,
            reason_code=REASON_DEPENDENCY_UNREACHABLE,
        )
    if probe.parse_failed:
        # The server answered but not with a readable body: the Agent cannot read its posture.
        return PostureGate(
            server_key=server_key,
            required=required,
            reachable=True,
            posture_accepted=False,
            ready=False,
            validated=False,
            reason_code=REASON_CONFIG_INVALID,
            parse_failed=True,
        )
    verdict = parse_posture(probe.body, server_key)
    posture = verdict.posture
    return PostureGate(
        server_key=server_key,
        required=required,
        reachable=True,
        posture_accepted=verdict.accepted,
        ready=bool(posture and posture.ready),
        validated=bool(posture and posture.validated),
        reason_code=verdict.reason_code,
        report=_parse_report(probe.body),
    )


async def collect_server_postures(ctx: AgentContext) -> dict[str, PostureGate]:
    """Probe every usable HTTP MCP server once and gate it on the posture it publishes.

    Never raises: a probe failure becomes an Availability gate, because the pipeline has to see a
    server it cannot read as a failure rather than as an exception that aborts the probe loop. A
    server with startup_mode=none is documented as unusable and registers no tools, so probing it
    would turn an intentional config choice into a startup failure; it is skipped here and is absent
    from allowed_server_keys().
    """
    http = ctx.services_required.http
    gates: dict[str, PostureGate] = {}
    for server_key, cfg in ctx.cfg.mcp.mcp_servers.items():
        if cfg.transport != TransportType.HTTP or not cfg.url or cfg.is_disabled:
            continue
        probe = await _probe_mcp_health_detail(
            http,
            cfg.url,
            cfg.auth_headers(),
            timeout_sec=get_effective_health_timeout(cfg),
        )
        gates[server_key] = _decide(
            _gate_from_probe(server_key, bool(cfg.required), probe)
        )
    return gates


def allowed_server_keys(gates: Mapping[str, PostureGate]) -> set[str]:
    """Server keys whose gate is fully green, for RuntimeToolRegistry(allowed_servers=...).

    Takes the gates collect_server_postures() produced rather than a context, so no consumer re-probes
    /health: the gate a server earned at readiness is the gate its tools run under.
    """
    return {
        server_key
        for server_key, gate in gates.items()
        if gate.reachable and gate.posture_accepted and gate.ready and gate.validated
    }


def _is_fatal_capability_finding(gate: PostureGate, finding: CapabilityFinding) -> bool:
    """Whether a capability finding on an otherwise green gate blocks startup (REQ-005).

    Only the required capability of a `required=true` server blocks; an optional capability that
    is degraded or unavailable is a warning whatever the flag says, which is the partial
    availability ADR-004 permits.
    """
    return gate.required and not finding.required_proven


def _capability_warning(
    gate: PostureGate, finding: CapabilityFinding, url: str
) -> ServiceWarning:
    """Build the ServiceWarning for a capability finding: the capability names only.

    No server-supplied message or reason text reaches the Agent's message here, matching
    `_posture_warning()`.
    """
    label = f"{_POSTURE_LABEL_PREFIX}{gate.server_key}"
    if not finding.required_proven:
        message = (
            f"{label} capability failure "
            f"(required={finding.required_capability or 'ready'} not proven)"
        )
    else:
        degraded = ", ".join(finding.degraded_optional)
        message = f"{label} capability failure (degraded_optional={degraded})"
    if not _is_fatal_capability_finding(gate, finding):
        message = f"{OutputTag.NON_FATAL} {message}"
    return ServiceWarning(label=label, url=url, message=message)


def _posture_warning(gate: PostureGate, url: str) -> ServiceWarning:
    """Build the ServiceWarning for one non-green gate: key, class, and reason code only.

    A fingerprint value and a server-supplied check message never reach an Agent message or log.
    """
    failure_class = gate.failure_class
    if failure_class is None:
        raise ValueError(f"green gate has no warning: {gate.server_key}")
    label = f"{_POSTURE_LABEL_PREFIX}{gate.server_key}"
    message = f"{label} {failure_class.value} failure (reason={gate.reason_code})"
    if not _is_fatal_gate(gate):
        message = f"{OutputTag.NON_FATAL} {message}"
    return ServiceWarning(label=label, url=url, message=message)


def _remediation(errors: list[ServiceWarning]) -> str:
    """Append the actionable line for the failure kinds present in a readiness failure."""
    parts: list[str] = []
    if any(not w.label.startswith(_POSTURE_LABEL_PREFIX) for w in errors):
        parts.append("Start the required service or fix its url.")
    if any(w.label.startswith(_POSTURE_LABEL_PREFIX) for w in errors):
        parts.append(
            "Fix the MCP server security posture (see its /health security block) "
            "or set its startup_mode to none. A `required=false` that contradicts the "
            "mandatoriness registry (`registry/component_mandatoriness.yaml`) is aborted "
            "at startup, so correct the registry classification, not the config."
        )
    if not parts:
        return ""
    return " | remediation: " + " ".join(parts)


async def check_service_health(
    ctx: AgentContext, *, gates: dict[str, PostureGate] | None = None
) -> HealthCheckResult:
    """Probe LLM and Embed service health, then every MCP server posture, at startup.

    The LLM is a required service: its failure is reported as a fatal error. The
    embed-llm is optional: the agent runs in degraded mode without it, so its
    failure is a non-fatal warning. Derives each /health URL by stripping the path
    from the endpoint URL. An MCP posture entry degrades to a warning only when the
    failure is an Availability failure of a server configured required=false; a
    Safety or Integrity posture failure lands in errors whatever that flag says.

    Pass the gates this startup run already collected (from the same
    collect_server_postures() call) to avoid probing twice; omit gates to probe
    by yourself, which is what every caller did before this argument existed.

    A gate that is green on posture is still read through its parsed report: a required server
    whose catalog required_capability is not proven `ok` lands in errors (REQ-005), while a
    degraded optional capability is a warning.
    """
    if ctx.services_required.http is None:
        raise RuntimeError("http service not initialized")
    # (label, url, required): required-service failures are fatal; optional ones degrade.
    checks: list[tuple[str, str, bool]] = [
        ("llm", ctx.cfg.llm.llm_url, True),
        ("embed-llm", ctx.cfg.memory.memory_embed_url, False),
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
    if gates is None:
        gates = await collect_server_postures(ctx)
    catalog = _load_catalog_for_gates()
    for server_key in sorted(gates):
        gate = gates[server_key]
        url = ctx.cfg.mcp.mcp_servers[server_key].url
        required_capability = (
            required_capability_for(catalog, server_key)
            if catalog is not None
            else None
        )
        finding = classify_capabilities(gate, required_capability)
        if gate.failure_class is None:
            if finding.required_proven and not finding.degraded_optional:
                continue
            entry = _capability_warning(gate, finding, url)
            if _is_fatal_capability_finding(gate, finding):
                errors.append(entry)
            else:
                logger.warning("%s", entry.message)
                warnings.append(entry)
            continue
        entry = _posture_warning(gate, url)
        if _is_fatal_gate(gate):
            errors.append(entry)
        else:
            logger.warning("%s", entry.message)
            warnings.append(entry)
    return HealthCheckResult(warnings=warnings, errors=errors)


async def check_readiness(
    ctx: AgentContext, *, gates: dict[str, PostureGate] | None = None
) -> HealthCheckResult:
    """Probe required services at startup; raise RuntimeError on required-service failure.

    Required services block startup, and so does any MCP server whose posture gate reports a
    Safety or Integrity failure, or whose catalog required_capability is not proven `ok` (REQ-005).
    Optional services degrade only on an availability failure: the
    embed-llm and an MCP server configured required=false whose gate failure is Availability
    surface as non-fatal warnings instead of raising.

    Pass the gates this startup run already collected (from the same
    collect_server_postures() call) to avoid probing twice; omit gates to probe
    by yourself.
    """
    result = await check_service_health(ctx, gates=gates)
    if result.errors:
        error_msgs = [f"{w.label}: {w.message}" for w in result.errors]
        msg = (
            "Startup readiness check failed (required services unavailable): "
            + "; ".join(error_msgs)
            + _remediation(result.errors)
        )
        logger.error(msg)
        raise RuntimeError(msg)
    return result
