"""tests/mcp_servers/mdq/test_mdq_search_cancellation.py

Phase 1 characterization for the search connection lifecycle (REQ-004, AC-4): one dedicated
cancellable connection per search, progress-handler cancellation, the stop event on async
timeout with a bounded drain, no reuse of an interrupted connection, the bounded active-search
concurrency limit, and the repeated-timeout resource-leak check. Source:
issues/20261119-142124_mdqmcp002_mdq-search-query-boundary.md.

Fail-first state, recorded 20261128: the helper-ownership, handler, drain, interrupted-identity,
active-search-limit, and peak-concurrency assertions fail before the production change lands,
because today no progress handler is installed, the caller returns at the timeout without waiting
for the worker, there is no active-search limit, and the connection is taken from the service
accessor. The connection-per-search and leak assertions already hold today and stay as guards:
today the synchronous worker runs to completion before the caller raises, so its connection is
already closed at the raise point; the post-change contract keeps that observable state under the
bounded drain.

The handler is consulted only every `check_every` VM steps, so a short statement can finish
before the stop event is observed; the connection stand-in below represents a statement long
enough for the handler to fire by polling the handler the way SQLite does.
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
import time
from collections.abc import Callable
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp_servers.mdq import search as search_module
from mcp_servers.mdq.indexer import index_paths
from mcp_servers.mdq.mdq_models import (
    IndexPathsRequest,
    MdqServiceError,
    SearchDocsRequest,
)
from mcp_servers.mdq.mdq_service import MdqService
from shared.tool_transport_invoker import DEFAULT_PER_SERVER_CONCURRENCY

from tests.mcp_servers.mdq._startup import make_startup

POLL_INTERVAL_SEC = 0.01
QUERY = "CancellationProbe"


class RecordingConnection(sqlite3.Connection):
    """Stand-in for a SQLite connection that records the cancellation contract.

    A statement long enough for the progress handler to be consulted is represented by polling
    the handler, as SQLite does every `check_every` VM steps; a handler that signals stop is
    reported as the same `sqlite3.OperationalError` SQLite raises. A connection with no handler
    delegates to the real connection, which is the behavior pinned today.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.scope: CancellationScope | None = None
        self.polls = 1
        self.ignore_handler = False
        self.handler: Callable[[], int | None] | None = None
        self.interrupted = False
        self.closed = False

    def set_progress_handler(
        self,
        handler: Callable[[], int | None] | None,
        check_every: int,
    ) -> None:
        self.handler = handler
        super().set_progress_handler(handler, check_every)

    def execute(self, sql: str, parameters: object = ()) -> sqlite3.Cursor:
        for _ in range(self.polls):
            if self.handler is not None and self.handler() and not self.ignore_handler:
                self.interrupted = True
                raise sqlite3.OperationalError("interrupted")
            if self.polls > 1:
                time.sleep(POLL_INTERVAL_SEC)
        return super().execute(sql, parameters)

    def close(self) -> None:
        self.closed = True
        if self.scope is not None and self.scope.measures_peak:
            self.scope.left()
        super().close()


class CancellationScope:
    """Recording scope for one test: the connections it opened and their peak in-flight count."""

    def __init__(self, *, measures_peak: bool = False) -> None:
        self.connections: list[RecordingConnection] = []
        self.polls = 1
        self.ignore_handler = False
        self.measures_peak = measures_peak
        self.active = 0
        self.peak_active = 0

    def record_open(self, conn: RecordingConnection) -> None:
        conn.scope = self
        conn.polls = self.polls
        conn.ignore_handler = self.ignore_handler
        self.connections.append(conn)
        if self.measures_peak:
            self.entered()

    def entered(self) -> None:
        self.active += 1
        self.peak_active = max(self.peak_active, self.active)

    def left(self) -> None:
        self.active -= 1


@pytest.fixture
def scope(monkeypatch: pytest.MonkeyPatch) -> CancellationScope:
    """Patch `sqlite3.connect` so every connection the search path opens is recorded."""
    recorded = CancellationScope()

    def factory(*args, **kwargs) -> RecordingConnection:
        conn = RecordingConnection(*args, **kwargs)
        recorded.record_open(conn)
        return conn

    monkeypatch.setattr(sqlite3, "connect", factory)
    return recorded


@pytest.fixture
def service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> MdqService:
    """MdqService with a temp DB path, tmp_path in allowed_dirs, one row indexed, and a
    timeout shorter than the stand-in's simulated long statement.
    """
    fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
    try:
        svc = MdqService(make_startup(db))
        svc._allowed_dirs = [str(tmp_path)]
        monkeypatch.setattr(svc, "search_timeout_sec", 0.05)
        (tmp_path / "doc.md").write_text(
            f"# Title\n\n{QUERY} content.", encoding="utf-8"
        )
        asyncio.run(index_paths(svc, IndexPathsRequest(paths=[str(tmp_path)])))
        return svc
    finally:
        os.close(fd)


def _search(service: MdqService) -> object:
    """Run one search through the tool path with the fixture's short timeout."""
    return asyncio.run(
        search_module.search_docs(service, SearchDocsRequest(query=QUERY))
    )


def _search_connection(scope: CancellationScope) -> RecordingConnection:
    """The connection the last search opened."""
    return scope.connections[-1]


class TestConnectionPerSearch:
    def test_each_search_owns_its_own_connection_and_closes_it(
        self, service: MdqService, scope: CancellationScope
    ) -> None:
        """The connection is dedicated to one search and closed by that search."""
        opened_before = len(scope.connections)
        _search(service)
        assert len(scope.connections) == opened_before + 1
        first = _search_connection(scope)
        assert first.closed

        _search(service)
        assert len(scope.connections) == opened_before + 2
        assert _search_connection(scope) is not first

    def test_search_path_owns_its_connection_through_the_shared_helper(
        self,
        service: MdqService,
        scope: CancellationScope,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Fails first: the current path takes the connection from the service connection
        accessor, so a timed-out search can carry its connection past the caller. The search
        path must own its connection through `db.helper.SQLiteHelper` with the supplied
        `db_path`.
        """
        original_accessor = service._get_db_connection
        used: list[sqlite3.Connection] = []

        def counted() -> sqlite3.Connection:
            conn = original_accessor()
            used.append(conn)
            return conn

        monkeypatch.setattr(service, "_get_db_connection", counted)
        _search(service)

        assert used == []


class TestStopEventAndBoundedDrain:
    def test_stop_event_interrupts_the_statement_and_the_connection_is_closed(
        self, service: MdqService, scope: CancellationScope
    ) -> None:
        """Fails first: no progress handler is installed today, so a short statement finishes
        before the stop event is observed and the caller returns without the worker.
        """
        scope.polls = 30
        with pytest.raises(MdqServiceError) as exc_info:
            _search(service)

        conn = _search_connection(scope)
        assert conn.handler is not None
        assert conn.interrupted
        assert conn.closed
        # AC-4: the timeout report carries no raw query text.
        assert QUERY not in str(exc_info.value)

    def test_caller_waits_for_the_worker_inside_the_bounded_drain(
        self, service: MdqService, scope: CancellationScope
    ) -> None:
        """Fails first: the caller returns at the timeout without waiting for a worker that
        never stops, so the measured wait is the timeout rather than the drain interval.
        """
        drain = getattr(search_module, "DRAIN_INTERVAL_SEC", None)
        assert drain is not None, "the bounded drain interval must be a named constant"
        assert 0 < drain <= 10.0

        # A worker that does not stop within the interval: the handler never signals.
        scope.polls = 1200
        scope.ignore_handler = True

        # Measured inside the loop: `asyncio.run` waits for the executor thread to finish at
        # shutdown, so wrapping it here would measure the worker, not the caller's wait.
        async def measure() -> float:
            started = time.perf_counter()
            with pytest.raises(MdqServiceError):
                await search_module.search_docs(service, SearchDocsRequest(query=QUERY))
            return time.perf_counter() - started

        waited = asyncio.run(measure())

        assert drain - 0.5 <= waited <= drain + 1.0
        assert not _search_connection(scope).interrupted

    def test_interrupted_connection_is_not_reused(
        self, service: MdqService, scope: CancellationScope
    ) -> None:
        """Fails first: today the timed-out search's connection is still open when the next
        search begins, so an interrupted connection can be carried into a later call.
        """
        scope.polls = 30
        with pytest.raises(MdqServiceError):
            _search(service)

        interrupted = _search_connection(scope)
        assert interrupted.interrupted

        # The next search must not inherit the interrupted connection, so the follow-up is a
        # short statement that completes inside the timeout.
        scope.polls = 1
        _search(service)
        assert _search_connection(scope) is not interrupted
        assert interrupted.closed


class TestBoundedConcurrencyAndLeak:
    def test_search_path_exposes_the_documented_active_search_limit(
        self, service: MdqService
    ) -> None:
        """Fails first: the search path has no active-search limit today. The post-change
        module-level constant must equal the existing per-server concurrency convention.
        """
        limit = getattr(search_module, "MAX_ACTIVE_SEARCHES", None)
        assert limit is not None, (
            "the search path must enforce a module-level active-search limit"
        )
        assert limit == DEFAULT_PER_SERVER_CONCURRENCY

    def test_active_connections_never_exceed_the_limit(
        self, service: MdqService, scope: CancellationScope
    ) -> None:
        """Fails first: there is no active-search limit today, so the ten concurrent searches
        run more than the limit at once. The documented per-server limit is the existing
        convention; once the search path enforces it, the recorded peak stays within it.
        """
        scope.measures_peak = True
        scope.polls = 30

        async def run_all() -> list[object]:
            # Each long search is reported as a timeout, so the outcomes are collected rather
            # than raised; the assertion is on the recorded peak, not on the results.
            return await asyncio.gather(
                *(
                    search_module.search_docs(service, SearchDocsRequest(query=QUERY))
                    for _ in range(DEFAULT_PER_SERVER_CONCURRENCY + 2)
                ),
                return_exceptions=True,
            )

        asyncio.run(run_all())

        assert scope.peak_active <= DEFAULT_PER_SERVER_CONCURRENCY

    def test_repeated_timeouts_do_not_leak_connections(
        self, service: MdqService, scope: CancellationScope
    ) -> None:
        """Guard: already holds today because the synchronous worker completes and closes its
        connection before the caller raises; the assertion pins the same observable state under
        the post-change drain.
        """
        scope.polls = 30
        opened_before = len(scope.connections)
        for _ in range(3):
            with pytest.raises(MdqServiceError):
                _search(service)
            # A timed-out search must release its own connection before the caller returns,
            # so a leak is observable at the point it happens.
            assert _search_connection(scope).closed

        assert len(scope.connections) == opened_before + 3
