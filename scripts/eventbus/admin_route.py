#!/usr/bin/env python3
"""scripts/eventbus/admin_route.py — Admin topics-authorization endpoint handler."""

import dataclasses
import logging
from typing import Any

from fastapi import HTTPException, Request

from eventbus.auth import _populate_token_maps
from eventbus.route_helpers import get_config

logger = logging.getLogger(__name__)


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


def _validate_topic_authorization(value: Any) -> dict[str, list[str]]:
    """Validate a `topic_authorization` value per EventBusConfig's own rules:
    string keys, list/set values of strings.
    """
    if not isinstance(value, dict):
        raise HTTPException(
            status_code=422, detail="topic_authorization must be an object"
        )
    for topic, consumer_ids in value.items():
        if not isinstance(topic, str):
            raise HTTPException(
                status_code=422,
                detail=f"topic_authorization key must be string, got {type(topic).__name__}",
            )
        if not isinstance(consumer_ids, (list, set)):
            raise HTTPException(
                status_code=422,
                detail=f"topic_authorization value must be list/set, got {type(consumer_ids).__name__}",
            )
        for consumer_id in consumer_ids:
            if not isinstance(consumer_id, str):
                raise HTTPException(
                    status_code=422,
                    detail=f"topic_authorization consumer_id must be string, got {type(consumer_id).__name__}",
                )
    return value


async def update_topics_authorization(request: Request) -> dict[str, Any]:
    """Update `consumer_authorization`/`topic_authorization` at runtime and
    refresh the derived per-token `Principal` authorization state.

    Validates the request body fully before mutating any state, so an
    invalid request never leaves `app.state.config` partially updated.
    """
    body: dict[str, Any] = await request.json()

    new_consumer_authorization = None
    if "consumer_authorization" in body:
        new_consumer_authorization = _validate_consumer_authorization(
            body["consumer_authorization"]
        )

    new_topic_authorization = None
    if "topic_authorization" in body:
        new_topic_authorization = _validate_topic_authorization(
            body["topic_authorization"]
        )

    config = get_config(request)
    replacements: dict[str, Any] = {}
    if new_consumer_authorization is not None:
        replacements["consumer_authorization"] = new_consumer_authorization
    if new_topic_authorization is not None:
        replacements["topic_authorization"] = new_topic_authorization

    if replacements:
        # EventBusConfig is a frozen dataclass — build a replacement instance
        # rather than mutating the existing one, then swap it into app.state
        # so every other request-scoped `get_config(request)` call sees the
        # update immediately.
        config = dataclasses.replace(config, **replacements)
        request.app.state.config = config

    _populate_token_maps(config)

    logger.info("admin: topics authorization updated")
    return {"status": "ok"}
