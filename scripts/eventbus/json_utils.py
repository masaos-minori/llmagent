#!/usr/bin/env python3
"""scripts/eventbus/json_utils.py

Minimal JSON helpers for eventbus — avoids importing from shared.
"""

from __future__ import annotations

from datetime import UTC, datetime

import orjson

OPT_SORT_KEYS: int = orjson.OPT_SORT_KEYS


def dumps(obj: object, option: int | None = OPT_SORT_KEYS) -> str:
    return orjson.dumps(obj, option=option).decode()


def now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
