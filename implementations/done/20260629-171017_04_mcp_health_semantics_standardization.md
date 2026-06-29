# Implementation: MCP /health response field consistency standardization

## Goal

Define and enforce consistent semantics for MCP `/health` response fields (`status`, `ready`, `dependencies`) across all servers, fix the mdq health endpoint schema mismatch, and align watchdog documentation with implementation.

## Scope

- **In-Scope**:
  - Canonical health semantics definition (status values, ready semantics, HTTP status code rules)
  - Fix `mcp/mdq/server.py` health() referencing stale `sections` schema instead of `documents/chunks`
  - Audit all 11 MCP server health() implementations for conformance
  - Document watchdog behavior (HTTP status only, not body fields) in both docs and code comments
  - Clarify that dependency values like `"not configured"` and `"not_set"` do degrade status
  - Add missing health tests: file-read, file-write, file-delete, rag-pipeline, mdq servers
  - Update `docs/04_mcp_02_protocol_and_transport.md` and `docs/04_mcp_06_configuration_and_operations.md`
- **Out-of-Scope**:
  - Replacing health endpoints with a new API design
  - Adding external monitoring integrations (Prometheus, Grafana, etc.)
  - Changing watchdog from HTTP-status-only to body-field inspection

## Assumptions

- The canonical semantics are: `status="ok"` + `ready=true` + HTTP 200 for healthy; `status="degraded"` + `ready=false` + HTTP 503 for any dependency failure.
- `status="unhealthy"` (mentioned in requirement) is NOT currently used by any server and should NOT be introduced without explicit design decision; plan treats it as a future extension.
- Dependency states `"not configured"`, `"not_set"`, `"check failed"` all constitute degraded (not silently healthy), consistent with current shell/git/github/cicd/rag implementations.
- `mcp_status.py` (`/mcp` command) uses HTTP status code only for `McpAvailability.OK` vs `McpAvailability.HTTP_ERROR` — this is correct and requires no change; only needs documentation.

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | `mdq/server.py` health() checks `sections` table but service.py uses `documents/chunks` schema after migration — health check will report stale/wrong schema results | Fix health() to check `documents`, `chunks`, `chunks_fts` tables and triggers (`chunks_ai`, `chunks_ad`, `chunks_au`) |
| UNK-02 | Whether `status="unhealthy"` should be introduced for a third tier (e.g. server process unresponsive vs. dependency missing) | Clarify in docs as reserved/future; current implementation uses only `"ok"`/`"degraded"` |
| UNK-03 | `rag-pipeline-mcp` returns `"not configured"` for `embed_url` — does this intentionally mean the server starts but is non-functional? | Document explicitly: embed_url is required for functionality; degraded means all tool calls will fail |

## Implementation

### Target file: `scripts/mcp/mdq/server.py` (health() function)

#### Procedure

Update health() to check `documents`, `chunks`, `chunks_fts` tables instead of `sections`, `sections_fts`.

#### Method

Direct file edit — replace all schema references in the health() function.

#### Details

**Replace lines 317-354 (health dependency checks):**
```python
if "documents" not in tables:
    deps["db_schema"] = "missing documents table"
elif "chunks" not in tables:
    deps["db_schema"] = "missing chunks table"
elif "chunks_fts" not in tables:
    deps["db_schema"] = "missing chunks_fts FTS5 table"
else:
    expected_triggers = {"chunks_ai", "chunks_ad", "chunks_au"}
    existing_triggers = set()
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'chunks_%'"
        ).fetchall()
        for row in rows:
            existing_triggers.add(row[0])
    except Exception:
        pass
    if expected_triggers - existing_triggers:
        deps["db_schema"] = "missing chunks triggers"

    try:
        stale_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM chunks_fts WHERE chunks_fts = 'delete' LIMIT 1"
        ).fetchone()[0]
        deps["chunks_deleted"] = stale_count if stale_count else None
    except Exception:
        pass

    try:
        chunk_count = conn.execute("SELECT COUNT(*) as cnt FROM chunks").fetchone()[0]
        path_count = conn.execute(
            "SELECT COUNT(DISTINCT source_path) as cnt FROM chunks"
        ).fetchone()[0]
        fts_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM chunks_fts WHERE chunks_fts != 'delete'"
        ).fetchone()[0]
        deps["chunks"] = chunk_count
        deps["documents"] = path_count
        deps["fts_entries"] = fts_count

        row = conn.execute("SELECT MAX(mtime_ns) as mt FROM documents").fetchone()
        if row and row[0]:
            deps["latest_chunk_mtime"] = row[0]
    except Exception:
        pass
```

### Target file: `tests/test_mdq_health_stale.py`

#### Procedure

Update test to use new schema (`documents/chunks` instead of `sections/sections_fts`).

#### Method

Direct file edit — replace all schema references in the test.

#### Details

**Replace lines 17-54 (test DB creation):**
```python
def _create_test_db(db_path: str) -> None:
    """Create a test database with documents, chunks, and chunks_fts tables."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """CREATE TABLE documents (
            id INTEGER PRIMARY KEY,
            source_path TEXT NOT NULL,
            mtime_ns INTEGER NOT NULL
        )"""
    )
    conn.execute(
        """CREATE TABLE chunks (
            seq INTEGER PRIMARY KEY,
            doc_id TEXT NOT NULL,
            heading_path TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            content TEXT NOT NULL,
            source_path TEXT NOT NULL
        )"""
    )
    conn.execute(
        """CREATE VIRTUAL TABLE chunks_fts USING fts5(
            seq, doc_id, heading_path, ordinal, content,
            content=chunks, content_rowid=seq
        )"""
    )
    conn.execute("CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN "
                 "INSERT INTO chunks_fts(rowid, seq, doc_id, heading_path, ordinal, content) "
                 "VALUES(new.rowid, new.seq, new.doc_id, new.heading_path, new.ordinal, new.content); END")
    conn.execute("CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN "
                 "INSERT INTO chunks_fts(chunks_fts, rowid, seq, doc_id, heading_path, ordinal, content) "
                 "VALUES('delete', old.rowid, old.seq, old.doc_id, old.heading_path, old.ordinal, old.content); END")
    conn.execute("CREATE TRIGGER chunks_au AFTER UPDATE ON chunks BEGIN "
                 "INSERT INTO chunks_fts(chunks_fts, rowid, seq, doc_id, heading_path, ordinal, content) "
                 "VALUES('delete', old.rowid, old.seq, old.doc_id, old.heading_path, old.ordinal, old.content); "
                 "INSERT INTO chunks_fts(rowid, seq, doc_id, heading_path, ordinal, content) "
                 "VALUES(new.rowid, new.seq, new.doc_id, new.heading_path, new.ordinal, new.content); END")
    conn.commit()
```

**Replace `_insert_sections` function (lines 59-67):**
```python
def _insert_documents(db_path: str, rows: list[tuple[int, str, float]]) -> None:
    """Insert documents and corresponding chunks into the test database."""
    conn = sqlite3.connect(db_path)
    for seq, source_path, mtime_ns in rows:
        doc_id = f"doc-{seq}"
        conn.execute(
            "INSERT INTO documents (id, source_path, mtime_ns) VALUES (?, ?, ?)",
            (seq, source_path, mtime_ns),
        )
        conn.execute(
            "INSERT INTO chunks (seq, doc_id, heading_path, ordinal, content, source_path) VALUES (?, ?, 'h1', 1, 'content', ?)",
            (seq, doc_id, source_path),
        )
    conn.commit()
```

**Replace all `_insert_sections` calls and query references:**
- Replace `_insert_sections(db_path, ...)` with `_insert_documents(db_path, ...)`
- Replace `SELECT COUNT(DISTINCT file_path) as cnt FROM sections WHERE file_mtime < ?` with `SELECT COUNT(DISTINCT source_path) as cnt FROM chunks WHERE doc_id IN (SELECT id FROM documents WHERE mtime_ns < ?)`

### Target file: `scripts/mcp/server.py`

#### Procedure

Expand `health()` docstring with explicit rules.

#### Method

Direct file edit — update docstring.

#### Details

**Add to the base `health()` method docstring:**
```python
def health(self) -> JSONResponse:
    """Return server health status.

    Canonical semantics (applies to all MCP servers):

    - **status values:** `"ok"` (healthy), `"degraded"` (any dependency failure).
      `"unhealthy"` is reserved for future use (e.g., server process unresponsive).
    - **ready:** `true` when status is `"ok"`; `false` when status is `"degraded"`.
    - **HTTP status code:** 200 for healthy, 503 for degraded.
      The watchdog checks the HTTP status code only, not body fields.
    - **dependencies:** Any missing or failed dependency (e.g., "not configured",
      "not_set", "check failed") constitutes a degraded state — never silently healthy.

    When a dependency is missing:
    - `status` = `"degraded"`
    - `ready` = `false`
    - HTTP status = 503
    - `dependencies.<key>` = `"not configured"` or `"not_set"` or `"check failed"`
    """
```

### Target file: `scripts/agent/repl_health.py`

#### Procedure

Add inline comment to `probe_mcp_health()` explaining watchdog uses HTTP status code only.

#### Method

Direct file edit — add comment.

#### Details

**Add after line ~100 (after the function definition):**
```python
def probe_mcp_health(
    http: Any, server_key: str, timeout_sec: float = 5.0
) -> tuple[bool, dict[str, str]]:
    """Probe MCP server health via HTTP GET /health.

    NOTE: The watchdog checks the HTTP status code only (200 vs 503), not body fields.
    A 503 response means the server is degraded; a 200 response means it is healthy.
    Body fields like `status="degraded"` are informational and not used for health decisions.
    """
```

### Target file: `scripts/mcp/rag_pipeline/server.py`

#### Procedure

Add docstring to `health()` explaining `"not configured"` semantics.

#### Method

Direct file edit — add docstring.

#### Details

**Add to the rag-pipeline `health()` method:**
```python
def health(self) -> JSONResponse:
    """Return health status of the RAG pipeline server.

    NOTE: If `embed_url` is not configured, this endpoint returns
    `status="degraded"` with HTTP 503. This means the server is running but
    all tool calls that require embedding will fail. The server starts without
    embed_url to allow partial functionality (e.g., FTS5-only search).
    """
```

### Target file: `docs/04_mcp_02_protocol_and_transport.md`

#### Procedure

Update the mdq-mcp health table row to reflect `documents/chunks` schema.

#### Method

Direct file edit — update the table row.

#### Details

**Replace the mdq-mcp health row:**
```markdown
| mdq-mcp | `details.service: "mdq-mcp"` | `documents`, `chunks`, `chunks_fts` tables; triggers `chunks_ai/ad/au`; stale detection via `documents.mtime_ns` |
```

**Update the "Canonical /health Response Semantics" section (lines 196-220):**
Add explicit note:
```markdown
**Important:** Dependency values like `"not configured"` and `"not_set"` are degraded states, not informational. Any missing or failed dependency constitutes a degraded status with HTTP 503 — the server is not healthy until all dependencies are satisfied.
```

### Target file: `tests/test_mcp_server_health_status.py`

#### Procedure

Add tests for file-read, file-write, file-delete, rag-pipeline, mdq servers.

#### Method

New file edit — add test classes.

#### Details

**Add new test classes:**
```python
class TestFileReadHealth:
    def test_healthy_when_workspace_exists(self) -> None:
        """file-read-mcp health returns ok when workspace exists."""
        from mcp.file.common import _build_health_deps

        deps = _build_health_deps("/tmp")
        assert deps["workspace"] == "/tmp"

    def test_degraded_when_workspace_missing(self, tmp_path: Path) -> None:
        """file-read-mcp health returns degraded when workspace is missing."""
        from mcp.file.common import _build_health_deps

        missing = tmp_path / "nonexistent"
        deps = _build_health_deps(str(missing))
        assert deps.get("workspace") is None


class TestFileWriteHealth:
    def test_healthy_when_workspace_exists(self, tmp_path: Path) -> None:
        """file-write-mcp health returns ok when workspace exists."""
        from mcp.file.common import _build_health_deps

        deps = _build_health_deps(str(tmp_path))
        assert deps["workspace"] == str(tmp_path)

    def test_degraded_when_workspace_missing(self, tmp_path: Path) -> None:
        """file-write-mcp health returns degraded when workspace is missing."""
        from mcp.file.common import _build_health_deps

        missing = tmp_path / "nonexistent"
        deps = _build_health_deps(str(missing))
        assert deps.get("workspace") is None


class TestFileDeleteHealth:
    def test_healthy_when_workspace_exists(self, tmp_path: Path) -> None:
        """file-delete-mcp health returns ok when workspace exists."""
        from mcp.file.common import _build_health_deps

        deps = _build_health_deps(str(tmp_path))
        assert deps["workspace"] == str(tmp_path)

    def test_degraded_when_workspace_missing(self, tmp_path: Path) -> None:
        """file-delete-mcp health returns degraded when workspace is missing."""
        from mcp.file.common import _build_health_deps

        missing = tmp_path / "nonexistent"
        deps = _build_health_deps(str(missing))
        assert deps.get("workspace") is None


class TestRagPipelineHealth:
    def test_degraded_when_embed_url_not_configured(self) -> None:
        """rag-pipeline-mcp health returns degraded when embed_url is not configured."""
        from mcp.rag_pipeline.server import RAGPipelineServer

        # Create a minimal server without embed_url
        server = RAGPipelineServer(
            embed_url=None,  # No embed URL configured
            db_path="/tmp/test_rag.db",
        )
        resp = server.health()
        assert resp.status_code == 503
        body = resp.body
        assert isinstance(body, dict)
        assert body.get("status") == "degraded"
        assert body.get("ready") is False


class TestMdqHealth:
    def test_degraded_when_db_not_found(self, tmp_path: Path) -> None:
        """mdq-mcp health returns degraded when db_file not found."""
        from mcp.mdq.server import MdqServer

        # Create a minimal server with non-existent db path
        missing_db = str(tmp_path / "nonexistent.db")
        server = MdqServer(db_path=missing_db)
        resp = server.health()
        assert resp.status_code == 503
        body = resp.body
        assert isinstance(body, dict)
        assert body.get("status") == "degraded"
        assert body.get("ready") is False
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `mcp/mdq/server.py` health() | Unit test with mock SQLite DB (documents/chunks tables) | `pytest tests/test_mdq_health_stale.py -v` | health() returns degraded when chunks table missing, ok when present |
| `mcp/shell/server.py` health() | Existing test in test_mcp_server_health_status.py | `pytest tests/test_mcp_server_health_status.py -v` | HTTP 200 when sh in PATH, 503 when not |
| `mcp/file/*.py` health() | New tests: mock os.stat to raise OSError or return dir | `pytest tests/test_mcp_server_health_status.py -v` | HTTP 503 when /workspace missing, 200 when present |
| `mcp/rag_pipeline/server.py` health() | New test: mock ConfigLoader with no embed_url | `pytest tests/test_mcp_server_health_status.py -v` | HTTP 503, status=degraded, dependencies.embed_url="not configured" |
| `agent/repl_health.py` probe_mcp_health() | Existing unit tests | `pytest tests/test_repl_health.py -v` | No regression; function still checks status_code only |
| Full suite | Regression check | `uv run pytest` | All tests pass |

## Risks & Mitigations

- **Risk**: mdq health() fix may break `tests/test_mdq_health_stale.py` if it mocks `sections` table → **Mitigation**: Update test mocks to use `documents/chunks` schema in the same PR
- **Risk**: File server health tests require mocking `os.stat()` for `/workspace` — monkeypatching may be fragile → **Mitigation**: Use `pytest.monkeypatch.setattr(os, "stat", ...)` or mock `mcp.file.common._build_health_deps` directly
- **Risk**: Introducing mdq-mcp health fix may surface that staging/CI environment does not have `/opt/llm/db/mdq.sqlite` → **Mitigation**: The `db_file not found` path already returns degraded/503 gracefully; no crash risk
- **Risk**: Doc changes conflict with a simultaneous PR editing the same doc sections → **Mitigation**: Keep doc changes minimal (mdq table row + watchdog clarification only)
