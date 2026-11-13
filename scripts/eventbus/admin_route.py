#!/usr/bin/env python3
"""scripts/eventbus/admin_route.py — Admin topics-authorization endpoint handler."""

import dataclasses
import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from eventbus.audit import log_authorization_change
from eventbus.auth import (
    AuthzGeneration,
    Principal,
    Role,
    _build_principal_map,
    current_generation,
    publish_generation,
    require_role,
)
from eventbus.config import authorization_baseline_hash
from eventbus.route_helpers import get_config

logger = logging.getLogger(__name__)

router = APIRouter()


def _validate_consumer_authorization(value: Any) -> dict[str, list[str]]:
    """Validate a `consumer_authorization` value per EventBusConfig's own rules
    (`scripts/eventbus/config.py::EventBusConfig.__post_init__()`): string
    keys, list values of strings.
    """
    if not isinstance(value, dict):
        raise HTTPException(
            status_code=422, detail="consumer_authorization must be an object"
        )
    for consumer_id, topics in value.items():
        if not isinstance(consumer_id, str):
            raise HTTPException(
                status_code=422,
                detail=f"consumer_authorization key must be string, got {type(consumer_id).__name__}",
            )
        if not isinstance(topics, list):
            raise HTTPException(
                status_code=422,
                detail=f"consumer_authorization value must be list, got {type(topics).__name__}",
            )
        for topic in topics:
            if not isinstance(topic, str):
                raise HTTPException(
                    status_code=422,
                    detail=f"consumer_authorization topic must be string, got {type(topic).__name__}",
                )
    return value


def _changed_count[T](old: dict[str, T], new: dict[str, T]) -> int:
    """Count mapping entries whose values differ plus added/removed keys."""
    return sum(1 for k in set(old) | set(new) if old.get(k) != new.get(k))


def _authorization_pairs(cfg: Any) -> set[tuple[str, str]]:
    """Return the set of (consumer_id, topic) pairs a config grants."""
    pairs: set[tuple[str, str]] = set()
    for consumer_id, consumer_topics in (cfg.consumer_authorization or {}).items():
        pairs.update((consumer_id, topic) for topic in consumer_topics)
    return pairs


@router.post("/admin/topics/authorization", response_model=None)
async def update_topics_authorization(
    request: Request,
    principal: Principal = Depends(require_role(Role.ADMIN)),
) -> dict[str, Any] | JSONResponse:
    """Update `consumer_authorization` at runtime and
    publish the result as a new AuthzGeneration (EBAUTHGEN001).

    Validates the request body fully before mutating any state, so an
    invalid request never leaves `app.state.config` partially updated. The
    mandatory `expected_generation` is compared against the generation in
    force BEFORE change detection: a stale value is rejected with 409 even
    for a would-be no-op (REQ-007).

    Returns ``{"status": "ok", "persistent": false, "changed": <bool>,
    "previous_generation", "new_generation", "changed_count", "effective_at",
    "baseline_hash"}``; a generation mismatch returns a 409 JSONResponse
    ``{"error": "generation_conflict", "expected_generation": n,
    "current_generation": m}``. Always runtime-only (no file write).
    """
    body: dict[str, Any] = await request.json()

    # Reject empty/no-op bodies — no keys means nothing to do
    if not body:
        raise HTTPException(
            status_code=422,
            detail="request body must contain consumer_authorization (expected_generation is mandatory)",
        )

    new_consumer_authorization = None
    if "consumer_authorization" in body:
        new_consumer_authorization = _validate_consumer_authorization(
            body["consumer_authorization"]
        )

    # expected_generation is mandatory and must be a plain integer (REQ-002)
    expected_generation = body.get("expected_generation")
    if expected_generation is None:
        raise HTTPException(status_code=422, detail="expected_generation is required")
    if not isinstance(expected_generation, int) or isinstance(
        expected_generation, bool
    ):
        raise HTTPException(
            status_code=422,
            detail=f"expected_generation must be int, got {type(expected_generation).__name__}",
        )

    current_gen = current_generation()
    if current_gen is None:
        raise HTTPException(
            status_code=503, detail="no authorization generation is published yet"
        )

    if expected_generation != current_gen.generation:
        return JSONResponse(
            status_code=409,
            content={
                "error": "generation_conflict",
                "expected_generation": expected_generation,
                "current_generation": current_gen.generation,
            },
        )

    # ttl_seconds is optional; valid only for a newly published generation (REQ-005)
    ttl_seconds: int | float | None = body.get("ttl_seconds")
    if ttl_seconds is not None:
        if not isinstance(ttl_seconds, (int, float)) or isinstance(ttl_seconds, bool):
            raise HTTPException(
                status_code=422,
                detail=f"ttl_seconds must be a number, got {type(ttl_seconds).__name__}",
            )
        if not 0 < ttl_seconds <= current_gen.config.authz_max_ttl_seconds:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"ttl_seconds must satisfy 0 < ttl_seconds <= "
                    f"authz_max_ttl_seconds ({current_gen.config.authz_max_ttl_seconds}), "
                    f"got {ttl_seconds}"
                ),
            )

    config = get_config(request)
    replacements: dict[str, Any] = {}
    if new_consumer_authorization is not None:
        replacements["consumer_authorization"] = new_consumer_authorization

    # Determine if the update is a no-op by comparing against current config
    changed = False
    counts: dict[str, int] = {}
    if new_consumer_authorization is not None:
        current = config.consumer_authorization or {}
        if new_consumer_authorization != current:
            changed = True
            counts["consumer_authorization"] = _changed_count(
                current, new_consumer_authorization
            )

    if not changed:
        logger.info("admin: topics authorization no-op; nothing published")
        return {
            "status": "ok",
            "persistent": False,
            "changed": False,
            "previous_generation": current_gen.generation,
            "new_generation": current_gen.generation,
            "changed_count": 0,
            "effective_at": current_gen.effective_at,
            "baseline_hash": current_gen.baseline_hash,
        }

    # EventBusConfig is a frozen dataclass — build a replacement instance
    # rather than mutating the existing one. Build the replacement principal
    # map and generation snapshot from it before publishing anything, so a
    # failed build leaves the previous config and principal generation fully
    # active; then swap both so every other request-scoped `get_config(request)`
    # call sees the update immediately.
    new_config = dataclasses.replace(config, **replacements)
    new_principals = _build_principal_map(new_config)
    effective_at = time.time()
    new_pairs = _authorization_pairs(new_config)
    # Expiry entries for pairs this update newly grants get effective_at + ttl;
    # pairs carried over keep their previous expiry entries (REQ-005).
    expiries: set[tuple[str, str, float]] = {
        entry for entry in current_gen.expiries if (entry[0], entry[1]) in new_pairs
    }
    if ttl_seconds is not None:
        previous_pairs = _authorization_pairs(current_gen.config)
        expiries.update(
            (consumer_id, topic, effective_at + ttl_seconds)
            for consumer_id, topic in new_pairs - previous_pairs
        )
    new_gen = AuthzGeneration(
        generation=current_gen.generation + 1,
        config=new_config,
        principals=new_principals,
        effective_at=effective_at,
        baseline_hash=authorization_baseline_hash(new_config),
        expiries=frozenset(expiries),
    )
    request.app.state.config = new_gen.config
    publish_generation(new_gen)
    new_generation_number = new_gen.generation
    baseline_hash = new_gen.baseline_hash

    logger.info("admin: topics authorization updated")

    # Emit authorization-change audit record for effective changes
    detail_parts = [f"{name}:{count}" for name, count in counts.items()]
    detail_parts.append("persistent:false")
    log_authorization_change(
        consumer_id="admin",
        request_id=request.state.request_id,
        route="/admin/topics/authorization",
        target="topics_authorization",
        detail=";".join(detail_parts),
        actor=principal.token_fingerprint,
        previous_generation=current_gen.generation,
        new_generation=new_generation_number,
    )

    return {
        "status": "ok",
        "persistent": False,
        "changed": True,
        "previous_generation": current_gen.generation,
        "new_generation": new_generation_number,
        "changed_count": sum(counts.values()),
        "effective_at": effective_at,
        "baseline_hash": baseline_hash,
    }
