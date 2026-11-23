"""Shared fixtures for integration tests."""

from __future__ import annotations

import asyncio
import json
import socket
import sqlite3
import sys
import threading
import time
from collections.abc import AsyncGenerator, Callable, Generator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import pytest
from shared.mcp_dedup import DedupStore, DedupStoreConfig, open_dedup_store


@pytest.fixture
def http_retry_delays(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Skip the real HTTP retry backoff and return the delays it asked for.

    The transport sleeps 1 s and then 2 s between attempts. The replacement still
    yields to the event loop once, so code that relies on ``asyncio.sleep`` to
    yield keeps working.
    """
    real_sleep = asyncio.sleep
    delays: list[float] = []

    async def _record_sleep(delay: float, result: object = None) -> object:
        delays.append(delay)
        return await real_sleep(0, result)

    monkeypatch.setattr("shared.http_transport.asyncio.sleep", _record_sleep)
    return delays


@pytest.fixture
async def stdio_echo_server():
    """Minimal stdio MCP server that echoes requests with ID field."""
    script = (
        "import sys, json\n"
        "for line in sys.stdin:\n"
        "    req = json.loads(line)\n"
        "    resp = {'id': req['id'], 'result': f'echo:{req[\"name\"]}', 'is_error': False, 'truncated': False, 'total_bytes': 0}\n"
        "    sys.stdout.write(json.dumps(resp) + '\\n')\n"
        "    sys.stdout.flush()\n"
    )
    proc = await asyncio.create_subprocess_exec(
        "python",
        "-c",
        script,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )
    yield proc
    if proc.returncode is None:
        proc.terminate()
        await proc.wait()


@pytest.fixture
def tmp_sqlite_db(tmp_path: Path) -> str:
    """Temp SQLite DB with workflow schema initialized."""
    from db.config import DbConfig
    from db.create_schema import create_workflow_schema

    db_path = str(tmp_path / "workflow.sqlite")
    create_workflow_schema(
        DbConfig(
            rag_db_path=str(tmp_path / "rag.sqlite"),
            session_db_path=str(tmp_path / "session.sqlite"),
            workflow_db_path=db_path,
        )
    )
    return db_path


def make_llm_stream(tokens: list[str], error: Exception | None = None):
    """Return an async generator that yields token deltas and optionally raises."""

    async def _stream(*args: Any, **kwargs: Any):
        for t in tokens:
            yield {"type": "content_block_delta", "delta": {"text": t}}
        if error is not None:
            raise error

    return _stream


def hold_write_lock(db_path: str, duration_sec: float) -> threading.Thread:
    """Start a thread that holds a SQLite EXCLUSIVE lock for duration_sec seconds."""

    def _lock() -> None:
        conn = sqlite3.connect(db_path, timeout=0)
        conn.execute("PRAGMA locking_mode = EXCLUSIVE")
        conn.execute("BEGIN EXCLUSIVE")
        time.sleep(duration_sec)
        conn.close()

    t = threading.Thread(target=_lock, daemon=True)
    t.start()
    return t


@pytest.fixture
async def hanging_stdio_process():
    """Subprocess that reads one line from stdin, then sleeps forever.

    Used to test bounded-timeout reads against a wedged MCP server
    subprocess (see tests/integration/test_mcp_transport_crash.py).
    """
    script = "import sys, time\nsys.stdin.readline()\ntime.sleep(3600)\n"
    proc = await asyncio.create_subprocess_exec(
        "python",
        "-c",
        script,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )
    yield proc
    if proc.returncode is None:
        proc.kill()
        await proc.wait()


def _has_table(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


_VEC_SO = "/opt/llm/sqlite-vec/vec0.so"
_MEMORIES_VEC_DDL = "CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec"


def apply_session_schema(
    conn: sqlite3.Connection, schema: str | None = None, dims: int = 4
) -> None:
    """Create the session schema on a raw connection, with or without sqlite-vec.

    When the extension file exists it is loaded so the full schema (including the
    ``memories_vec`` vec0 table) is created. Otherwise the schema is created up to,
    and excluding, the ``memories_vec`` statement: recovery tests do not depend on
    the vec table, and CI has no extension installed.
    """
    from db.schema_sql import build_session_schema_sql

    script = build_session_schema_sql(dims) if schema is None else schema
    if Path(_VEC_SO).exists():
        conn.enable_load_extension(True)
        conn.load_extension(_VEC_SO)
        conn.enable_load_extension(False)
    else:
        script = script.split(_MEMORIES_VEC_DDL)[0]
    conn.executescript(script)


@pytest.fixture
def corrupt_wal_db(tmp_path: Path) -> str:
    """A WAL-mode session-schema SQLite DB, byte-truncated to fail
    PRAGMA integrity_check while still opening successfully via
    sqlite3.connect() (header intact, b-tree pages corrupted).

    Used by tests/integration/test_session_recovery.py.
    """
    db_path = str(tmp_path / "corrupt.sqlite")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    apply_session_schema(conn)
    if _has_table(conn, "sessions"):
        conn.execute("INSERT INTO sessions (session_id) VALUES (1)")
    conn.commit()
    conn.close()

    # Byte-level truncation: corrupts b-tree pages while preserving the
    # SQLite header (first 16 bytes), so sqlite3.connect() still succeeds
    # but PRAGMA integrity_check fails. Offset confirmed empirically
    # during implementation (see plan UNK-02 resolution).
    size = Path(db_path).stat().st_size
    with open(db_path, "r+b") as f:
        f.seek(size // 2)
        f.truncate()

    return db_path


# ── Cross-layer harness (used by the two-layer verification tests, rows 02/03) ──

_SCRIPTS_DIR = str(Path(__file__).resolve().parents[2] / "scripts")

_TEST_SERVER_NAME = "test-mcp"
_TEST_CONTROL_TOKEN = "cross-process-control-token"
# Fixed test values. The config shared_call_store builds is the contract between the
# two processes: the store identity reopen gate refuses a reopen whose config
# fingerprint differs from the one written at first initialization, so tests must use
# the returned config unchanged. A long lease keeps live-lease classification stable
# between test time and read time; an expired lease is seeded deterministically with a
# past now_epoch, so no test depends on wall-clock drift.
_TEST_LEASE_SECONDS = 300
_TEST_MAX_ATTEMPTS = 3
# Short busy timeout so lock contention surfaces as the typed DedupStoreError, as
# tests/shared/test_mcp_dedup_identity.py asserts.
_SHORT_BUSY_TIMEOUT_MS = 200
_READINESS_TIMEOUT_SEC = 10.0
_CHILD_CONTROL_TIMEOUT_SEC = 5.0


def fingerprint_payload(config: DedupStoreConfig) -> str:
    """JSON of the fingerprint fields, the only fields the reopen gate compares (D-5)."""
    return json.dumps(
        {
            "db_path": config.db_path,
            "retention_days": config.retention_days,
            "pending_timeout_minutes": config.pending_timeout_minutes,
            "lease_seconds": config.lease_seconds,
            "max_attempts": config.max_attempts,
        }
    )


@dataclass(frozen=True)
class SharedCallStore:
    """One tmp_path dedup store: path, the validated config, and the Agent-side handle.

    Both sides of the process boundary open this same file under the config unchanged;
    the child cannot inherit the parent's handle, only the config.
    """

    path: str
    config: DedupStoreConfig
    handle: DedupStore

    def payload(self) -> str:
        """JSON of the fingerprint fields, the only fields the reopen gate compares (D-5).

        Tests pass this to a child unchanged; a child that changes any field is refused
        by the identity gate, which is what the matrix tests assert.
        """
        return fingerprint_payload(self.config)


@dataclass(frozen=True)
class ControlApiProcess:
    """A live control-API subprocess: loopback port, control token, shared store."""

    port: int
    token: str
    store: SharedCallStore

    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"


@pytest.fixture
def shared_call_store(tmp_path: Path) -> Generator[SharedCallStore]:
    """Initialize a store under tmp_path and yield the path, config, and handle.

    The fixture performs the first initialization; the control-API subprocess opens
    the same file second, which classifies as healthy under the identical config.
    """
    config = DedupStoreConfig(
        db_path=str(tmp_path / "dedup.sqlite"),
        lease_seconds=_TEST_LEASE_SECONDS,
        max_attempts=_TEST_MAX_ATTEMPTS,
    )
    handle = open_dedup_store(config, busy_timeout_ms=_SHORT_BUSY_TIMEOUT_MS)
    try:
        yield SharedCallStore(path=str(config.db_path), config=config, handle=handle)
    finally:
        handle.close()


def _free_loopback_port() -> int:
    """Bind port 0 and read the assigned port.

    Same pattern as tests/integration/test_production_security_regression.py:279-283.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


# The child is a fresh interpreter: the tests/conftest.py sys.path shim does not reach
# it, so the fixture passes scripts/ as PYTHONPATH and starts sys.executable (the venv
# interpreter, which has fastapi/httpx/uvicorn; the plain-"python" pattern in the
# existing fixtures runs stdlib-only children).
# argv: port, config JSON, token, server name, evidence file, tool name. A "none" config
# and an empty tool name are the closed variants a test can request; a named tool gets the
# test reconciler, which answers from the trace file the recorded call left.
_CONTROL_API_CHILD_SCRIPT = """
import json, sys
from fastapi import FastAPI
import uvicorn
from mcp_servers import control_api
from shared.mcp_dedup import DedupStoreConfig

port, config_json, token, server_name, evidence_file, tool_name = (
    int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
)
config = None if config_json == "none" else DedupStoreConfig(**json.loads(config_json))
if tool_name:
    from shared.mcp_call_state_contract import ReconcileEvidence

    class TestReconciler:
        # Answers from the trace the recorded call left, never by re-executing.
        def reconcile(self, tool, key, snapshot):
            try:
                trace = open(evidence_file).read().strip()
            except OSError:
                trace = ""
            if not trace:
                return ReconcileEvidence(outcome="no_evidence", digest="none")
            return ReconcileEvidence(outcome="evidence_found", digest=trace)

    control_api.register_reconciler(tool_name, TestReconciler())

app = FastAPI()
control_api.configure_control(token, config, server_name)
control_api.attach_control_api(app)
uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
"""


async def _wait_for_control_api(
    proc: asyncio.subprocess.Process, port: int, token: str
) -> None:
    """Wait for the control path to answer on the port, with a bounded timeout.

    Any HTTP answer proves the child serves the control stack: the probe key is
    valid but has no row, so the ready state is 404 unknown_key (or 503 when the
    store did not open).
    """
    deadline = time.monotonic() + _READINESS_TIMEOUT_SEC
    while time.monotonic() < deadline:
        if proc.returncode is not None:
            stderr = await proc.stderr.read() if proc.stderr else b""
            raise RuntimeError(
                f"control API child exited with {proc.returncode}: "
                f"{stderr.decode(errors='replace')}"
            )
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                response = await client.get(
                    f"http://127.0.0.1:{port}/v1/call_state/readiness",
                    headers={"Authorization": f"Bearer {token}"},
                )
            if response.status_code in (200, 404, 503):
                return
        except httpx.TransportError:
            pass  # the child is still starting
        await asyncio.sleep(0.1)
    raise RuntimeError(f"control API did not answer on port {port} within timeout")


class ControlApiLauncher:
    """Starts control-API children on the shared store, one per test configuration.

    `control_api_subprocess` is the default configuration; the matrix and crash tests ask
    for the closed variants the control code itself defines: no store configured, or a
    test reconciler that answers from recorded evidence. Same child script either way, so
    the boundary under test is the real control stack in a fresh process.
    """

    def __init__(
        self,
        store: SharedCallStore,
        build_env: Callable[[Mapping[str, str] | None], dict[str, str]],
    ) -> None:
        self._store = store
        self._build_env = build_env
        self._procs: list[asyncio.subprocess.Process] = []

    async def start(
        self,
        *,
        config_json: str | None = None,
        evidence_file: str = "",
        tool_name: str = "",
        token: str = _TEST_CONTROL_TOKEN,
    ) -> ControlApiProcess:
        """Start one control-API child and wait for it to answer on its port."""
        port = _free_loopback_port()
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-c",
            _CONTROL_API_CHILD_SCRIPT,
            str(port),
            config_json or self._store.payload(),
            token,
            _TEST_SERVER_NAME,
            evidence_file,
            tool_name,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._build_env({"PYTHONPATH": _SCRIPTS_DIR}),
        )
        self._procs.append(proc)
        await _wait_for_control_api(proc, port, token)
        return ControlApiProcess(port=port, token=token, store=self._store)

    async def stop(self) -> None:
        """Kill every child this test started, with a bounded cleanup."""
        for proc in self._procs:
            if proc.returncode is None:
                proc.kill()
            await asyncio.wait_for(proc.wait(), _CHILD_CONTROL_TIMEOUT_SEC)


@pytest.fixture
async def control_api_launcher(
    shared_call_store: SharedCallStore,
    isolated_subprocess_env: Callable[..., dict[str, str]],
) -> AsyncGenerator[ControlApiLauncher]:
    """Factory for control-API subprocesses on the shared store.

    The environment comes from isolated_subprocess_env, so no child reaches a path under
    /opt/llm (AC-006).
    """
    launcher = ControlApiLauncher(shared_call_store, isolated_subprocess_env)
    try:
        yield launcher
    finally:
        await launcher.stop()


@pytest.fixture
async def control_api_subprocess(
    control_api_launcher: ControlApiLauncher,
) -> AsyncGenerator[ControlApiProcess]:
    """Run the real control API as a uvicorn subprocess on an ephemeral loopback port.

    Reaches the store opened by shared_call_store under the config unchanged, waits for
    readiness with a bounded timeout, and yields the port, token, and store.
    """
    yield await control_api_launcher.start()


class CrashedChild:
    """A live child process running one logical call, controlled by signals.

    The child prints one line naming each control point it reaches; the test waits for
    the point it wants, then kills the child there. Bounded reads only, mirroring
    tests/integration/test_mcp_transport_crash.py:40-65.
    """

    def __init__(self, proc: asyncio.subprocess.Process) -> None:
        self._proc = proc

    async def wait_for_point(self, name: str) -> None:
        """Block until the child signals `name` on stdout; bounded timeout."""
        if self._proc.stdout is None:
            raise RuntimeError("child has no stdout pipe")
        line = await asyncio.wait_for(
            self._proc.stdout.readline(), _CHILD_CONTROL_TIMEOUT_SEC
        )
        if not line:
            raise RuntimeError(f"child exited before signaling {name!r}")
        point = line.decode().strip()
        if point != name:
            raise RuntimeError(f"child signaled {point!r}, expected {name!r}")

    def kill(self) -> None:
        """Produce the crash at the point the test chose."""
        if self._proc.returncode is None:
            self._proc.kill()

    async def wait(self, timeout_sec: float = _CHILD_CONTROL_TIMEOUT_SEC) -> int:
        """Exit status after kill, with a bounded cleanup so cleanup cannot hang."""
        return await asyncio.wait_for(self._proc.wait(), timeout_sec)


class CrashedChildRunner:
    """Starts signal-controlled children on the isolated environment and scripts path."""

    def __init__(
        self, build_env: Callable[[Mapping[str, str] | None], dict[str, str]]
    ) -> None:
        self._build_env = build_env
        self.children: list[CrashedChild] = []

    async def start(self, script: str, argv: list[str]) -> CrashedChild:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-c",
            script,
            *argv,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._build_env({"PYTHONPATH": _SCRIPTS_DIR}),
        )
        child = CrashedChild(proc)
        self.children.append(child)
        return child


@pytest.fixture
async def crashed_child(
    isolated_subprocess_env: Callable[..., dict[str, str]],
) -> AsyncGenerator[CrashedChildRunner]:
    """Factory for short-lived children that perform one logical call each.

    Tests pass a child script and argv (the logical key and store path); every child
    is killed and reaped at cleanup unless the test already killed it at its point.
    """
    runner = CrashedChildRunner(isolated_subprocess_env)
    yield runner
    for child in runner.children:
        child.kill()
        try:
            await child.wait()
        except TimeoutError:
            pass  # a wedged child must not hang the cleanup
