#!/usr/bin/env python3
"""scripts/mcp_servers/control_api.py — Agent-only call-state control plane.

Serves GET /v1/call_state/{key} and POST /v1/call_state/{key}/reconcile from the
dedup ledger, authenticated with the control Bearer token (mcpdl004 REQ-001/REQ-002).
The control middleware is registered after the tool-auth middleware, so it is
outermost: control paths are answered here and never reach tool auth. This module
opens its own store handle from the validated `[dedup]` config and never imports
`mcp_servers.server` or `mcp_servers.dispatch`.
"""

import dataclasses
import hmac
import logging
import re
import uuid
from collections.abc import Callable
from typing import Any, Protocol

from fastapi import Request
from fastapi.responses import JSONResponse
from shared.logger import attach_redaction_filter, register_secret
from shared.mcp_call_state_contract import (
    CONTROL_ERROR_CODES,
    RECONCILE_OUTCOMES,
    ReconcileEvidence,
    Reconciler,
    agent_state_for,
)
from shared.mcp_dedup import (
    CallStateView,
    DedupLeaseConflict,
    DedupStore,
    DedupStoreConfig,
    open_dedup_store,
)

from mcp_servers.models import CallStateResponse, ReconcileResponse

logger = logging.getLogger(__name__)
attach_redaction_filter(logger)

CONTROL_PATH_PREFIX = "/v1/call_state/"
_RECONCILE_SUFFIX = "/reconcile"

# Control keys are opaque ids; the pattern is the same one the ledger accepts, so a
# key that cannot be a ledger key is refused before any lookup (422).
_KEY_RE = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")

# Module state written by configure_control and read at request time. The store is
# only opened when both a control token and a validated dedup config exist.
_control_token = ""
_control_server = ""
_control_store: DedupStore | None = None
_reconcilers: dict[str, Reconciler] = {}


def configure_control(
    token: str, dedup_config: DedupStoreConfig | None, server_name: str
) -> None:
    """Store the control-plane state for this server.

    An empty token closes the control paths and logs one warning naming the server
    only: the server still starts, because tool paths keep their own token.
    """
    global _control_token, _control_server, _control_store
    _control_token = token
    _control_server = server_name
    _control_store = None
    if not token:
        logger.warning(
            f"control token empty: control paths closed for server={server_name}"
        )
        return
    register_secret(token)
    if dedup_config is None:
        logger.warning(
            f"control api not configured: no dedup config for server={server_name}"
        )
        return
    _control_store = open_dedup_store(dedup_config)


def register_reconciler(tool_name: str, reconciler: Reconciler) -> None:
    """Registration seam for per-tool reconcilers (mcpdl004 REQ-004)."""
    _reconcilers[tool_name] = reconciler


def clear_reconcilers() -> None:
    """Drop the reconciler registry; used by fixtures between tests."""
    _reconcilers.clear()


class _ControlApp(Protocol):
    """Minimal app surface the control middleware needs.

    Mirrors `server._FastAPIApp` rather than importing it: the control module must
    not depend on `server.py` (row 09), and the protocol keeps the graph acyclic.
    """

    def middleware(self, middleware_type: str) -> Callable[[Callable], Callable]:
        """Attach a middleware function to the FastAPI application."""
        ...


def attach_control_api(app: _ControlApp) -> None:
    """Register the control middleware on a FastAPI app.

    Called from `attach_auth_middleware` after the tool-auth middleware, so this one
    runs first and control paths never reach tool auth. Tool paths are untouched.
    """

    @app.middleware("http")
    async def _control_middleware(request: Request, call_next):  # noqa: ANN001,ANN202 — FastAPI middleware protocol
        """Authenticate control paths with the control Bearer token and serve them."""
        path = request.url.path
        if not path.startswith(CONTROL_PATH_PREFIX):
            return await call_next(request)
        req_id = str(uuid.uuid4())
        request.state.request_id = req_id
        if not _control_authorized(request):
            return _respond(401, {"error": "Unauthorized"}, req_id)
        remainder = path[len(CONTROL_PATH_PREFIX) :]
        reconcile = remainder.endswith(_RECONCILE_SUFFIX)
        key = remainder[: -len(_RECONCILE_SUFFIX)] if reconcile else remainder
        if not _KEY_RE.fullmatch(key):
            return _respond(422, _error_payload(key, "invalid_key"), req_id)
        store = _control_store
        if store is None:
            return _respond(503, _error_payload(key, "store_unavailable"), req_id)
        if (request.method, reconcile) == ("POST", True):
            status, body = build_reconcile(store, key)
        elif (request.method, reconcile) == ("GET", False):
            status, body = build_call_state(store, key)
        else:
            # No method code exists in the closed vocabulary, so the fixed error shape
            # reports the request as not a valid control reference.
            return _respond(405, _error_payload(key, "invalid_key"), req_id)
        return _respond(status, body, req_id)


def _control_authorized(request: Request) -> bool:
    """Return True only when the Bearer header matches a non-empty control token."""
    if not _control_token:
        return False
    presented = request.headers.get("Authorization", "")
    return hmac.compare_digest(
        presented.encode("utf-8"), f"Bearer {_control_token}".encode()
    )


def _respond(status: int, body: dict[str, Any], req_id: str) -> JSONResponse:
    """Build a response with the request id; bodies are model dumps or fixed errors."""
    return JSONResponse(body, status_code=status, headers={"X-Request-Id": req_id})


def _error_payload(key: str, code: str) -> dict[str, str]:
    """Fixed error body: the key and a stable code, nothing else."""
    return {"key": key, "error_code": code}


def build_call_state(store: DedupStore, key: str) -> tuple[int, dict[str, Any]]:
    """Project one ledger row; 404 unknown_key when the key is absent."""
    try:
        view = store.call_state_view(key)
    except Exception:  # noqa: BLE001 — a store failure must not become a 500 vector
        logger.warning(
            f"control read failed for server={_control_server} (store_unavailable)"
        )
        return 503, _error_payload(key, "store_unavailable")
    if view is None:
        return 404, _error_payload(key, "unknown_key")
    model = CallStateResponse(
        key=view.key,
        ledger_status=view.ledger_status,
        agent_state=view.agent_state,
        attempt_number=view.attempt_number,
        lease_live=view.lease_live,
        lease_expires_epoch=view.lease_expires_epoch,
        result_class=view.result_class,
        result_code=view.result_code or "",
        result_size_bytes=view.result_size_bytes,
        result_sha256=view.result_sha256 or "",
        external_ref=view.external_ref or "",
        reconciliation_required=view.reconciliation_required,
        error_code=view.error_code,
    )
    return 200, model.model_dump()


def build_reconcile(store: DedupStore, key: str) -> tuple[int, dict[str, Any]]:
    """Reconcile one call; the request carries no payload and nothing is re-executed."""
    try:
        view = store.call_state_view(key)
    except Exception:  # noqa: BLE001 — a store failure must not become a 500 vector
        logger.warning(
            f"control read failed for server={_control_server} (store_unavailable)"
        )
        return 503, _error_payload(key, "store_unavailable")
    if view is None:
        return 404, _error_payload(key, "unknown_key")
    if view.ledger_status == "completed":
        # A completed call is never re-executed or mutated by a control path.
        return 200, _reconcile_payload(
            view,
            decision="reused_completed",
            outcome="none",
            review=False,
            digest="",
        )
    if view.ledger_status != "pending":
        return 200, _reconcile_payload(
            view,
            decision="operator_review",
            outcome="none",
            review=True,
            digest="",
        )
    if view.lease_live:
        return 409, _reconcile_payload(
            view,
            decision="refused",
            outcome="none",
            review=False,
            digest="",
            code="lease_live",
        )
    if view.attempts_exhausted:
        return 409, _reconcile_payload(
            view,
            decision="refused",
            outcome="none",
            review=True,
            digest="",
            code="attempts_exhausted",
        )

    reconciler = _reconcilers.get(view.tool_name)
    if reconciler is None:
        # No per-tool reconciler: the row moves as the existing reconciliation path
        # governs, and the response reports that operator review is needed.
        return _move_and_report(
            store,
            view,
            decision="operator_review",
            code="not_reconcilable",
        )
    try:
        row = store.get_execution(key)
        if row is None:
            return 404, _error_payload(key, "unknown_key")
        evidence = reconciler.reconcile(view.tool_name, key, dict(row.snapshot))
    except Exception as exc:  # noqa: BLE001 — a reconciler must not become a 500 vector
        logger.warning(
            f"control reconcile failed for server={_control_server} "
            f"tool={view.tool_name} key={key[:12]} ({type(exc).__name__})"
        )
        return 200, _reconcile_payload(
            view,
            decision="operator_review",
            outcome="none",
            review=True,
            digest="",
            code="reconciler_failed",
        )
    if evidence.outcome not in RECONCILE_OUTCOMES:
        return 200, _reconcile_payload(
            view,
            decision="operator_review",
            outcome="none",
            review=True,
            digest="",
            code="reconciler_failed",
        )
    if evidence.outcome in ("evidence_found", "no_evidence"):
        return _move_and_report(
            store,
            view,
            decision="reconciled",
            code="none",
            evidence=evidence,
        )
    return _report_with_evidence(
        store,
        view,
        decision="operator_review",
        review=True,
        evidence=evidence,
    )


def _move_and_report(
    store: DedupStore,
    view: CallStateView,
    decision: str,
    code: str,
    evidence: ReconcileEvidence | None = None,
) -> tuple[int, dict[str, Any]]:
    """Move a stale pending row through the existing reconciliation path and report it."""
    try:
        moved = store.reconcile_execution(view.key)
    except DedupLeaseConflict:
        # Lost the race to another owner, or the row is no longer a stale pending row.
        return 409, _reconcile_payload(
            view,
            decision="refused",
            outcome="none",
            review=False,
            digest="",
            code=code,
        )
    if evidence is not None:
        _append_evidence(store, view.key, evidence)
    state = agent_state_for(moved.status, False)
    moved_view = dataclasses.replace(
        view,
        ledger_status=moved.status,
        lease_live=False,
        lease_expires_epoch=None,
        agent_state=state,
        reconciliation_required=state == "reconciliation_required",
        error_code=code,
    )
    return 200, _reconcile_payload(
        moved_view,
        decision=decision,
        outcome=_outcome(evidence),
        review=True,
        digest=_digest(evidence),
        code=code,
    )


def _report_with_evidence(
    store: DedupStore,
    view: CallStateView,
    decision: str,
    review: bool,
    evidence: ReconcileEvidence,
) -> tuple[int, dict[str, Any]]:
    """Report an outcome that leaves the row unchanged, with its evidence digest."""
    _append_evidence(store, view.key, evidence)
    return 200, _reconcile_payload(
        view,
        decision=decision,
        outcome=_outcome(evidence),
        review=review,
        digest=_digest(evidence),
    )


def _append_evidence(store: DedupStore, key: str, evidence: ReconcileEvidence) -> None:
    """Record the decision and digest in the attempt history; never the payload."""
    try:
        store.append_reconcile_evidence(key, evidence.outcome, evidence.digest)
    except Exception as exc:  # noqa: BLE001 — a history write must not become a 500 vector
        logger.warning(
            f"control evidence not recorded for server={_control_server} key={key[:12]} "
            f"({type(exc).__name__})"
        )


def _outcome(evidence: ReconcileEvidence | None) -> str:
    """Reported outcome: the reconciler's own, or none when none ran."""
    return evidence.outcome if evidence is not None else "none"


def _digest(evidence: ReconcileEvidence | None) -> str:
    """Non-sensitive digest of the evidence, empty when there is none."""
    return evidence.digest if evidence is not None else ""


def _reconcile_payload(
    view: CallStateView,
    decision: str,
    outcome: str,
    review: bool,
    digest: str,
    code: str = "none",
) -> dict[str, Any]:
    """Validate the response through the model so the boundary stays closed."""
    model = ReconcileResponse(
        key=view.key,
        decision=decision,
        outcome=outcome,
        ledger_status=view.ledger_status,
        agent_state=view.agent_state,
        operator_review=review,
        evidence_digest=digest,
        error_code=code if code in CONTROL_ERROR_CODES else "none",
    )
    return model.model_dump()
