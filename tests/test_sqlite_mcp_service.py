"""tests/test_sqlite_mcp_service.py
Unit tests for SqliteMCPService and _validate_sql.

Guards tested:
  - SELECT statements pass
  - Non-SELECT statements (INSERT/UPDATE/DELETE/DROP/PRAGMA) are rejected
  - DB name outside db_allowlist raises ValueError
  - max_rows truncation
  - Multiple statements separated by semicolon are rejected
"""

from __future__ import annotations

import sqlite3

import pytest
from mcp.sqlite.service import SqliteMCPService, _validate_sql

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_db(tmp_path):
    """Create a temp SQLite DB with a small test table."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    conn.executemany(
        "INSERT INTO items VALUES (?, ?)",
        [(i, f"item{i}") for i in range(1, 11)],
    )
    conn.commit()
    conn.close()
    return db_path


def _make_service(tmp_db: str, max_rows: int = 100) -> SqliteMCPService:
    return SqliteMCPService(
        db_allowlist=["test"],
        db_paths={"test": tmp_db},
        max_rows=max_rows,
    )


# ── _validate_sql ─────────────────────────────────────────────────────────────


class TestValidateSql:
    def test_select_passes(self) -> None:
        ok, err = _validate_sql("SELECT * FROM foo")
        assert ok
        assert err == ""

    def test_select_with_leading_comment(self) -> None:
        ok, err = _validate_sql("-- comment\nSELECT 1")
        assert ok

    def test_select_with_block_comment(self) -> None:
        ok, err = _validate_sql("/* block */ SELECT 1")
        assert ok

    def test_insert_rejected(self) -> None:
        ok, err = _validate_sql("INSERT INTO foo VALUES (1)")
        assert not ok
        assert "INSERT" in err

    def test_update_rejected(self) -> None:
        ok, err = _validate_sql("UPDATE foo SET x=1")
        assert not ok

    def test_delete_rejected(self) -> None:
        ok, err = _validate_sql("DELETE FROM foo")
        assert not ok

    def test_drop_rejected(self) -> None:
        ok, err = _validate_sql("DROP TABLE foo")
        assert not ok

    def test_pragma_rejected(self) -> None:
        ok, err = _validate_sql("PRAGMA journal_mode")
        assert not ok

    def test_multiple_statements_rejected(self) -> None:
        ok, err = _validate_sql("SELECT 1; DROP TABLE foo")
        assert not ok
        assert "Multiple" in err

    def test_empty_sql_rejected(self) -> None:
        ok, err = _validate_sql("   ")
        assert not ok
        assert "empty" in err.lower()

    def test_select_case_insensitive(self) -> None:
        ok, _ = _validate_sql("select * from foo")
        assert ok

    def test_trailing_semicolon_allowed(self) -> None:
        ok, _ = _validate_sql("SELECT 1;")
        assert ok


# ── SqliteMCPService.handle_query_sqlite ─────────────────────────────────────


class TestSqliteMCPService:
    @pytest.mark.asyncio
    async def test_select_returns_json(self, tmp_db: str) -> None:
        svc = _make_service(tmp_db)
        result = await svc.handle_query_sqlite(
            {"db": "test", "sql": "SELECT * FROM items ORDER BY id"}
        )
        import orjson  # noqa: PLC0415

        data = orjson.loads(result)
        assert data["columns"] == ["id", "name"]
        assert data["row_count"] == 10
        assert not data["truncated"]

    @pytest.mark.asyncio
    async def test_db_not_in_allowlist_raises(self, tmp_db: str) -> None:
        svc = _make_service(tmp_db)
        with pytest.raises(ValueError, match="allowlist"):
            await svc.handle_query_sqlite({"db": "forbidden", "sql": "SELECT 1"})

    @pytest.mark.asyncio
    async def test_non_select_raises(self, tmp_db: str) -> None:
        svc = _make_service(tmp_db)
        with pytest.raises(ValueError, match="Only SELECT"):
            await svc.handle_query_sqlite({"db": "test", "sql": "DROP TABLE items"})

    @pytest.mark.asyncio
    async def test_max_rows_truncates_result(self, tmp_db: str) -> None:
        svc = _make_service(tmp_db, max_rows=3)
        result = await svc.handle_query_sqlite(
            {"db": "test", "sql": "SELECT * FROM items ORDER BY id"}
        )
        import orjson  # noqa: PLC0415

        data = orjson.loads(result)
        assert data["row_count"] == 3
        assert data["truncated"] is True

    @pytest.mark.asyncio
    async def test_result_within_max_rows_not_truncated(self, tmp_db: str) -> None:
        svc = _make_service(tmp_db, max_rows=100)
        result = await svc.handle_query_sqlite(
            {"db": "test", "sql": "SELECT * FROM items WHERE id <= 5"}
        )
        import orjson  # noqa: PLC0415

        data = orjson.loads(result)
        assert data["row_count"] == 5
        assert data["truncated"] is False

    @pytest.mark.asyncio
    async def test_insert_via_dispatch_returns_error_tuple(self, tmp_db: str) -> None:
        """dispatch_tool wraps ValueError into (msg, True)."""
        from mcp.server import dispatch_tool  # noqa: PLC0415

        svc = _make_service(tmp_db)
        result, is_err = await dispatch_tool(
            svc.get_dispatch_table(),
            "query_sqlite",
            {"db": "test", "sql": "INSERT INTO items VALUES (99, 'bad')"},
        )
        assert is_err
        assert "SELECT" in result

    @pytest.mark.asyncio
    async def test_unknown_db_via_dispatch_returns_error_tuple(
        self, tmp_db: str
    ) -> None:
        from mcp.server import dispatch_tool  # noqa: PLC0415

        svc = _make_service(tmp_db)
        result, is_err = await dispatch_tool(
            svc.get_dispatch_table(),
            "query_sqlite",
            {"db": "evil", "sql": "SELECT 1"},
        )
        assert is_err
        assert "allowlist" in result
