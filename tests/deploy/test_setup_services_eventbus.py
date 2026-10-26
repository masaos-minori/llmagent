"""tests/deploy/test_setup_services_eventbus.py

Integration tests for the EventBus readiness gate in deploy/setup_services.sh
(REQ-004): a crashed, unreachable, or genuinely-unavailable EventBus must abort
the script, while a healthy start (including a capacity-only 503) is reported
READY. The script runs from a tmp_path sandbox copy; all /opt/llm paths are
redirected via the DEPLOY_* / WORKFLOW_JSON / EVENTBUS_HEALTH_URL overrides and
LLMAGENT_CONFIG_DIR, so no production path is written to.
"""

import http.server
import json
import os
import pathlib
import re
import shutil
import signal
import socket
import sqlite3
import subprocess
import threading
import time

from db.schema_sql import WORKFLOW_SCHEMA_VERSION, build_eventbus_schema_sql

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

_TOKEN = "test-eventbus-token-0123456789"

_HEALTH_CAPACITY_ONLY = {
    "status": "degraded",
    "db": "ok",
    "dlq_task": "running",
    "degraded_reasons": ["lock_wait_high", "subscribers_at_capacity"],
}
_HEALTH_DB_UNAVAILABLE = {
    "status": "degraded",
    "db": "unavailable",
    "dlq_task": "running",
    "degraded_reasons": ["db_unavailable"],
}


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = int(sock.getsockname()[1])
    sock.close()
    return port


def _start_canned(body: dict[str, object], code: int) -> http.server.HTTPServer:
    """Serve a fixed JSON body on an ephemeral port (mock LLM / canned /health)."""
    payload = json.dumps(body).encode()

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args: object) -> None:
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _make_sandbox(tmp_path: pathlib.Path, eventbus_port: int) -> pathlib.Path:
    """Sandbox tree whose REPO_ROOT the copied setup_services.sh will resolve to."""
    sb = tmp_path
    for sub in ("deploy", "config/workflows", "db", "logs", "storage", "deadletter"):
        (sb / sub).mkdir(parents=True)
    shutil.copyfile(
        _REPO_ROOT / "deploy" / "setup_services.sh", sb / "deploy" / "setup_services.sh"
    )
    shutil.copyfile(
        _REPO_ROOT / "deploy" / "load_env.sh", sb / "deploy" / "load_env.sh"
    )
    shutil.copyfile(
        _REPO_ROOT / "config" / "workflows" / "default.json",
        sb / "config" / "workflows" / "default.json",
    )
    return sb


def _write_configs(
    sb: pathlib.Path, eventbus_port: int, llm_embed_port: int, llm_url_port: int
) -> None:
    (sb / "config" / "agent.toml").write_text(
        f'embed_url = "http://127.0.0.1:{llm_embed_port}"\n'
        f'llm_url = "http://127.0.0.1:{llm_url_port}"\n',
        encoding="utf-8",
    )
    text = (_REPO_ROOT / "config" / "eventbus.toml").read_text(encoding="utf-8")
    text = text.replace("port = 8015", f"port = {eventbus_port}")
    text = text.replace('"/opt/llm/db', f'"{sb}/db')
    text = text.replace('"/opt/llm/storage', f'"{sb}/storage')
    text = text.replace('"/opt/llm/deadletter', f'"{sb}/deadletter')
    (sb / "config" / "eventbus.toml").write_text(text, encoding="utf-8")


def _seed_workflow_db(sb: pathlib.Path) -> None:
    conn = sqlite3.connect(sb / "db" / "workflow.sqlite")
    conn.executescript(
        """
        CREATE TABLE tasks (id INTEGER PRIMARY KEY);
        CREATE TABLE attempts (id INTEGER PRIMARY KEY);
        CREATE TABLE processed_events (id INTEGER PRIMARY KEY);
        CREATE TABLE artifacts (id INTEGER PRIMARY KEY);
        CREATE TABLE workflow_schema_version (version TEXT, applied_at TEXT);
        """
    )
    conn.execute(
        "INSERT INTO workflow_schema_version (version, applied_at) VALUES (?, ?)",
        (WORKFLOW_SCHEMA_VERSION, "2026-10-26 00:00:00"),
    )
    conn.commit()
    conn.close()


def _seed_eventbus_db(sb: pathlib.Path, *, malformed: bool) -> None:
    conn = sqlite3.connect(sb / "db" / "eventbus.sqlite")
    conn.executescript(build_eventbus_schema_sql())
    if malformed:
        # Unrepairable by the IF NOT EXISTS DDL re-apply (Doc 03/09 pattern).
        conn.execute("ALTER TABLE events ADD COLUMN malformed_extra TEXT")
    conn.commit()
    conn.close()


def _run_setup(sb: pathlib.Path, health_url: str) -> subprocess.CompletedProcess[str]:
    env: dict[str, str] = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", str(pathlib.Path.home())),
        "DEPLOY_SCRIPTS": str(_REPO_ROOT / "scripts"),
        "DEPLOY_DB": str(sb / "db"),
        "DEPLOY_LOGS": str(sb / "logs"),
        "WORKFLOW_JSON": str(sb / "config" / "workflows" / "default.json"),
        "LLMAGENT_CONFIG_DIR": str(sb / "config"),
        "LLMAGENT_LOG_DIR": str(sb / "logs"),
        "EVENTBUS_CONFIG_PATH": str(sb / "config" / "eventbus.toml"),
        "EVENTBUS_HEALTH_URL": health_url,
        "EVENTBUS_AUTH_TOKEN": _TOKEN,
        "LLM_HEALTH_RETRIES": "15",
        "LLM_HEALTH_INTERVAL": "1",
    }
    return subprocess.run(
        ["bash", str(sb / "deploy" / "setup_services.sh")],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
        check=False,
        start_new_session=True,
    )


def _child_pid(stdout_text: str) -> int | None:
    match = re.search(r"Event Bus PID: (\d+)", stdout_text)
    return int(match.group(1)) if match else None


def _reap(result: subprocess.CompletedProcess[str]) -> None:
    """Kill the whole spawned session group so no eventbus child outlives the test."""
    pid = _child_pid(result.stdout)
    if pid is None:
        return
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(os.getpgid(pid), sig)
        except (ProcessLookupError, PermissionError):
            return
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            time.sleep(0.2)


def _alive(pid: int | None) -> bool:
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def _prepare(
    tmp_path: pathlib.Path, *, malformed: bool
) -> tuple[pathlib.Path, int, list[http.server.HTTPServer]]:
    eventbus_port = _free_port()
    embed = _start_canned({"status": "ok"}, 200)
    llm = _start_canned({"status": "ok"}, 200)
    sb = _make_sandbox(tmp_path, eventbus_port)
    _write_configs(sb, eventbus_port, embed.server_address[1], llm.server_address[1])
    _seed_workflow_db(sb)
    _seed_eventbus_db(sb, malformed=malformed)
    return sb, eventbus_port, [embed, llm]


def test_setup_services_process_exit_aborts(tmp_path: pathlib.Path) -> None:
    sb, eventbus_port, mocks = _prepare(tmp_path, malformed=True)
    try:
        result = _run_setup(sb, f"http://127.0.0.1:{eventbus_port}/health")
        assert result.returncode == 1
        assert "[FATAL] Event Bus" in result.stderr
        assert "READY (db ok, dlq_task running)" not in result.stdout
        _reap(result)
        deadline = time.monotonic() + 10.0
        while _alive(_child_pid(result.stdout)) and time.monotonic() < deadline:
            time.sleep(0.2)
        assert not _alive(_child_pid(result.stdout))
    finally:
        for server in mocks:
            server.shutdown()


def test_setup_services_connection_failure_aborts(tmp_path: pathlib.Path) -> None:
    sb, _port, mocks = _prepare(tmp_path, malformed=False)
    unreachable = _free_port()  # bound then released: nothing listens here
    try:
        result = _run_setup(sb, f"http://127.0.0.1:{unreachable}/health")
        assert result.returncode == 1
        assert "[FATAL] Event Bus" in result.stderr
        assert "000" in result.stdout  # the retried connection-failure branch
        assert "READY (db ok, dlq_task running)" not in result.stdout
        _reap(result)
        deadline = time.monotonic() + 10.0
        while _alive(_child_pid(result.stdout)) and time.monotonic() < deadline:
            time.sleep(0.2)
        assert not _alive(_child_pid(result.stdout))  # eb_gate_fail killed the child
    finally:
        for server in mocks:
            server.shutdown()


def test_setup_services_status_not_ok_aborts(tmp_path: pathlib.Path) -> None:
    sb, _port, mocks = _prepare(tmp_path, malformed=False)
    canned = _start_canned(_HEALTH_DB_UNAVAILABLE, 503)
    try:
        result = _run_setup(sb, f"http://127.0.0.1:{canned.server_address[1]}/health")
        assert result.returncode == 1
        assert "[FATAL] Event Bus" in result.stderr
        assert "readiness predicate" in result.stderr
        assert "READY (db ok, dlq_task running)" not in result.stdout
        _reap(result)
    finally:
        canned.shutdown()
        for server in mocks:
            server.shutdown()


def test_setup_services_healthy_start_passes(tmp_path: pathlib.Path) -> None:
    sb, eventbus_port, mocks = _prepare(tmp_path, malformed=False)
    canned_capacity = _start_canned(_HEALTH_CAPACITY_ONLY, 503)
    try:
        # Real app, real /health: canonical DB reaches db==ok AND dlq_task==running.
        result = _run_setup(sb, f"http://127.0.0.1:{eventbus_port}/health")
        assert result.returncode == 0
        assert "READY (db ok, dlq_task running)" in result.stdout
        _reap(result)

        # Capacity-only 503 (db==ok, dlq_task==running) must also report READY.
        result2 = _run_setup(
            sb, f"http://127.0.0.1:{canned_capacity.server_address[1]}/health"
        )
        assert result2.returncode == 0
        assert "READY (db ok, dlq_task running)" in result2.stdout
        _reap(result2)
    finally:
        canned_capacity.shutdown()
        for server in mocks:
            server.shutdown()
