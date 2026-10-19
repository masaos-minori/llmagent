"""tests/mcp_servers/lifespan_fixtures.py

Test-only FastAPI apps referenced by ``tests/mcp_servers/test_mcp_server_base.py``
through ``app_module`` (see implementations/20261019-092908_01 and
-092908_02). They exercise the real ``_LoopbackVerifyingServer.startup()`` override
in ``scripts/mcp_servers/server.py`` without touching production code:

- ``failing_lifespan_app`` drives the lifespan-startup-failure path (REQ-002).
- ``healthy_lifespan_app`` reaches the normal start path (REQ-003).

Both are created at import time with no runtime side effects.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def failing_lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    raise RuntimeError("simulated application startup failure")
    yield  # noqa: B011 — unreachable; forces a startup failure


failing_lifespan_app = FastAPI(lifespan=failing_lifespan)


@asynccontextmanager
async def healthy_lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    yield


healthy_lifespan_app = FastAPI(lifespan=healthy_lifespan)
