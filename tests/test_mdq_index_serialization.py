"""tests/test_mdq_index_serialization.py

Proof that MdqService._index_lock serializes overlapping index/refresh
operations — index_paths and refresh_index must not run concurrently.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp_servers.mdq.mdq_models import RefreshIndexRequest
from mcp_servers.mdq.mdq_service import MdqService


@pytest.fixture
def service(tmp_path: Path) -> MdqService:
    """MdqService with a temp DB path and tmp_path in allowed_dirs."""
    fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
    try:
        svc = MdqService(db_path=db)
        svc._allowed_dirs = [str(tmp_path)]
        return svc
    finally:
        import os  # noqa: PLC0415

        os.close(fd)


@pytest.fixture
def md_file(tmp_path: Path) -> Path:
    """A temporary Markdown file."""
    f = tmp_path / "test.md"
    f.write_text("# Title\n\nContent here.", encoding="utf-8")
    return f


def test_concurrent_refresh_calls_are_serialized(
    service: MdqService, md_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two overlapping refresh_index calls must not interleave their critical sections."""
    order: list[str] = []

    async def tracked_refresh() -> str:
        result: str = await service.refresh_index(
            RefreshIndexRequest(paths=[str(md_file.parent)])
        )
        return result

    # Record start/end only inside the section actually protected by
    # _index_lock (the call into _refresh_paths), and force a scheduling
    # yield there — if the lock did not serialize the two calls, the second
    # call's "start" would be recorded before the first call's "end".
    import mcp_servers.mdq.mdq_service as service_module

    original_refresh_paths = service_module._refresh_paths

    async def slow_refresh_paths(svc: MdqService, req: RefreshIndexRequest) -> object:
        order.append("start")
        try:
            await asyncio.sleep(0.05)
            return await original_refresh_paths(svc, req)
        finally:
            order.append("end")

    monkeypatch.setattr(service_module, "_refresh_paths", slow_refresh_paths)

    async def _run_both() -> None:
        await asyncio.gather(tracked_refresh(), tracked_refresh())

    asyncio.run(_run_both())

    assert order == ["start", "end", "start", "end"]
