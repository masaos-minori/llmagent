"""tests/test_mdq_index_serialization.py

Proof that MdqService._index_lock serializes overlapping index/refresh
operations — index_paths and refresh_index must not run concurrently.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp_servers.mdq.mdq_models import (
    IndexPathsRequest,
    RefreshIndexRequest,
    SearchDocsRequest,
)
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
        text, _metadata = await service.refresh_index(
            RefreshIndexRequest(paths=[str(md_file.parent)])
        )
        return text

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


def test_concurrent_index_paths_calls_are_serialized(
    service: MdqService, md_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two overlapping index_paths calls must not interleave their critical sections."""
    order: list[str] = []

    async def tracked_index() -> str:
        text, _metadata = await service.index_paths(
            IndexPathsRequest(paths=[str(md_file.parent)])
        )
        return text

    import mcp_servers.mdq.mdq_service as service_module

    original_index_paths = service_module._index_paths

    async def slow_index_paths(svc: MdqService, req: IndexPathsRequest) -> object:
        order.append("start")
        try:
            await asyncio.sleep(0.05)
            return await original_index_paths(svc, req)
        finally:
            order.append("end")

    monkeypatch.setattr(service_module, "_index_paths", slow_index_paths)

    async def _run_both() -> None:
        await asyncio.gather(tracked_index(), tracked_index())

    asyncio.run(_run_both())

    assert order == ["start", "end", "start", "end"]


def test_index_paths_and_refresh_index_are_serialized(
    service: MdqService, md_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A mixed index_paths/refresh_index pair must not interleave, regardless of which
    side wins the race to acquire the lock first."""
    order: list[str] = []

    import mcp_servers.mdq.mdq_service as service_module

    original_index_paths = service_module._index_paths
    original_refresh_paths = service_module._refresh_paths

    async def slow_index_paths(svc: MdqService, req: IndexPathsRequest) -> object:
        order.append("start")
        try:
            await asyncio.sleep(0.05)
            return await original_index_paths(svc, req)
        finally:
            order.append("end")

    async def slow_refresh_paths(svc: MdqService, req: RefreshIndexRequest) -> object:
        order.append("start")
        try:
            await asyncio.sleep(0.05)
            return await original_refresh_paths(svc, req)
        finally:
            order.append("end")

    monkeypatch.setattr(service_module, "_index_paths", slow_index_paths)
    monkeypatch.setattr(service_module, "_refresh_paths", slow_refresh_paths)

    async def tracked_index() -> str:
        text, _metadata = await service.index_paths(
            IndexPathsRequest(paths=[str(md_file.parent)])
        )
        return text

    async def tracked_refresh() -> str:
        text, _metadata = await service.refresh_index(
            RefreshIndexRequest(paths=[str(md_file.parent)])
        )
        return text

    async def _run_both() -> None:
        await asyncio.gather(tracked_index(), tracked_refresh())

    asyncio.run(_run_both())

    # Either operation may legitimately run first; what matters is that they
    # never interleave — each "start" is immediately followed by its own "end".
    assert order.count("start") == 2
    assert order.count("end") == 2
    assert order[0] == "start"
    assert order[1] == "end"
    assert order[2] == "start"
    assert order[3] == "end"


@pytest.mark.asyncio
async def test_is_indexing_warning_visible_during_active_index(
    service: MdqService, md_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """search_docs() must surface the _is_indexing warning suffix while an
    index_paths call is still in flight."""
    import mcp_servers.mdq.mdq_service as service_module

    original_index_paths = service_module._index_paths

    async def slow_index_paths(svc: MdqService, req: IndexPathsRequest) -> object:
        await asyncio.sleep(0.05)
        return await original_index_paths(svc, req)

    monkeypatch.setattr(service_module, "_index_paths", slow_index_paths)

    task = asyncio.create_task(
        service.index_paths(IndexPathsRequest(paths=[str(md_file.parent)]))
    )
    await asyncio.sleep(0)  # let index_paths acquire the lock and set _is_indexing

    text, _metadata = await service.search_docs(SearchDocsRequest(query="Title"))

    assert "[WARNING: Index is being updated" in text

    await task
