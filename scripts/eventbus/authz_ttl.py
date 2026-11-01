#!/usr/bin/env python3
"""scripts/eventbus/authz_ttl.py — TTL expiry sweep for authorization generations.

EBAUTHGEN001 REQ-005: pairs granted with ttl_seconds carry expiry entries in the
generation snapshot. This module detects expired pairs with an injectable clock
and removes them as one atomic generation update through the same
build-first-then-publish path the admin endpoint uses, auditing each removal.
"""

import asyncio
import dataclasses
import logging
import time
from collections.abc import Callable
from typing import Any

from eventbus.audit import log_privileged_action
from eventbus.auth import (
    AuthzGeneration,
    _build_principal_map,
    current_generation,
    publish_generation,
)
from eventbus.config import authorization_baseline_hash
from eventbus.route_helpers import app_get_config

logger = logging.getLogger(__name__)


def _expired_entries(
    generation: AuthzGeneration, now: float
) -> frozenset[tuple[str, str, float]]:
    """Return the generation's expiry entries whose deadline has passed."""
    return frozenset(entry for entry in generation.expiries if entry[2] <= now)


def _removal_config(config: Any, expired_pairs: set[tuple[str, str]]) -> Any:
    """Build the post-removal EventBusConfig, dropping expired pairs from both
    authorization mappings and any mapping entry left empty."""
    consumer_authorization = {
        consumer_id: [
            topic for topic in topics if (consumer_id, topic) not in expired_pairs
        ]
        for consumer_id, topics in (config.consumer_authorization or {}).items()
    }
    consumer_authorization = {
        consumer_id: topics
        for consumer_id, topics in consumer_authorization.items()
        if topics
    }
    topic_authorization = {
        topic: {
            consumer_id
            for consumer_id in consumer_ids
            if (consumer_id, topic) not in expired_pairs
        }
        for topic, consumer_ids in (config.topic_authorization or {}).items()
    }
    topic_authorization = {
        topic: consumer_ids
        for topic, consumer_ids in topic_authorization.items()
        if consumer_ids
    }
    return dataclasses.replace(
        config,
        consumer_authorization=consumer_authorization,
        topic_authorization=topic_authorization,
    )


def sweep_expired_authorizations(
    app: Any, clock: Callable[[], float] = time.time
) -> AuthzGeneration | None:
    """Run one expiry cycle; return the published removal generation, or None.

    Compare-and-swap: the cycle captures the in-force generation first, builds
    the complete removal generation, and re-checks that no concurrent admin
    update bumped the generation before publishing. A bump aborts the cycle
    (retry on the next interval); a failed principal build aborts it too —
    the previous generation stays in force and nothing is published.
    """
    gen = current_generation()
    if gen is None or not gen.expiries:
        return None
    expired = _expired_entries(gen, clock())
    if not expired:
        return None

    expired_pairs = {(consumer_id, topic) for consumer_id, topic, _ in expired}
    new_config = _removal_config(gen.config, expired_pairs)
    new_principals = _build_principal_map(new_config)

    if current_generation() is not gen:
        logger.info(
            "authz_sweep: generation bumped by a concurrent update; aborting cycle"
        )
        return None

    new_gen = AuthzGeneration(
        generation=gen.generation + 1,
        config=new_config,
        principals=new_principals,
        effective_at=clock(),
        baseline_hash=authorization_baseline_hash(new_config),
        expiries=frozenset(entry for entry in gen.expiries if entry not in expired),
    )
    app.state.config = new_gen.config
    publish_generation(new_gen)

    old_consumer_pairs = {
        (consumer_id, topic)
        for consumer_id, topics in (gen.config.consumer_authorization or {}).items()
        for topic in topics
    }
    old_topic_pairs = {
        (consumer_id, topic)
        for topic, consumer_ids in (gen.config.topic_authorization or {}).items()
        for consumer_id in consumer_ids
    }
    counts: dict[str, int] = {}
    removed_consumer = len(expired_pairs & old_consumer_pairs)
    if removed_consumer:
        counts["consumer_authorization"] = removed_consumer
    removed_topic = len(expired_pairs & old_topic_pairs)
    if removed_topic:
        counts["topic_authorization"] = removed_topic

    detail_parts = [f"{name}:{count}" for name, count in counts.items()]
    detail_parts.append("persistent:false")
    detail_parts.append(f"gen:{gen.generation}->{new_gen.generation}")
    log_privileged_action(
        consumer_id="system",
        request_id="",
        route="/ttl_sweep",
        target="ttl_expiry",
        detail=";".join(detail_parts),
        actor="",
        previous_generation=gen.generation,
        new_generation=new_gen.generation,
    )
    logger.info(
        "authz_sweep: removed %d expired grant(s); generation %d->%d",
        len(expired_pairs),
        gen.generation,
        new_gen.generation,
    )
    return new_gen


async def authz_sweep_loop(app: Any, clock: Callable[[], float] = time.time) -> None:
    """Periodically sweep expired authorization grants (mirrors _dlq_loop).

    A per-cycle OSError/ValueError is logged and never crashes the lifespan
    task; cancellation at shutdown propagates like the DLQ loop's.
    """
    interval = 60.0
    while True:
        try:
            cfg = app_get_config(app)
            interval = cfg.authz_sweep_interval_seconds
            sweep_expired_authorizations(app, clock)
        except asyncio.CancelledError:
            raise
        except (OSError, ValueError) as exc:
            logger.warning("authz_sweep: cycle failed: %s", exc)
        await asyncio.sleep(interval)
