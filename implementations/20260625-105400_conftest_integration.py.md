# tests/integration/conftest_integration.py — shared fixtures for integration tests

**Plan:** `plans/20260625-095157_plan.md` (req #71)
**Target:** `tests/integration/conftest_integration.py` (new file, or `tests/integration/conftest.py`)

## Priority: P3 (Normal)

## Fixtures to implement

### `stdio_echo_server` fixture

Minimal stdio MCP server that reads one JSON-RPC request and echoes a response:

```python
@pytest.fixture
async def stdio_echo_server():
    script = (
        "import sys, json\n"
        "for line in sys.stdin:\n"
        "    req = json.loads(line)\n"
        "    resp = {'id': req['id'], 'result': f'echo:{req[\"name\"]}', 'is_error': False}\n"
        "    sys.stdout.write(json.dumps(resp) + '\\n')\n"
        "    sys.stdout.flush()\n"
    )
    proc = await asyncio.create_subprocess_exec(
        "python", "-c", script,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )
    yield proc
    if proc.returncode is None:
        proc.terminate()
        await proc.wait()
```

### `tmp_sqlite_db` fixture

Temp SQLite DB with schema initialized:

```python
@pytest.fixture
def tmp_sqlite_db(tmp_path: Path) -> str:
    from db.workflow_schema import init_schema
    db_path = str(tmp_path / "test.sqlite")
    init_schema(db_path)
    return db_path
```

### `mock_llm_stream` fixture

Configurable async generator that yields tokens and optionally raises:

```python
def make_llm_stream(tokens, error=None):
    async def _stream(*args, **kwargs):
        for t in tokens:
            yield {"type": "content_block_delta", "delta": {"text": t}}
        if error is not None:
            raise error
    return _stream
```

### `hold_write_lock` helper

Thread-based SQLite exclusive lock holder (used in TC-B02):

```python
def hold_write_lock(db_path: str, duration_sec: float) -> threading.Thread:
    def _lock():
        conn = sqlite3.connect(db_path, timeout=0)
        conn.execute("PRAGMA locking_mode = EXCLUSIVE")
        conn.execute("BEGIN EXCLUSIVE")
        time.sleep(duration_sec)
        conn.close()
    t = threading.Thread(target=_lock, daemon=True)
    t.start()
    return t
```

## pyproject.toml change needed

Add to `[tool.pytest.ini_options]`:
```toml
asyncio_mode = "auto"
```

## requirements-dev.txt additions

```
respx
pytest-asyncio
pytest-timeout
```

## Validation

```
uv run pytest tests/integration/ -v --timeout=30
```
