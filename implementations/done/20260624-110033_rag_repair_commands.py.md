# Implementation Procedure: scripts/agent/services/rag_maintenance_service.py + cmd_db.py

## Goal

`vec-rebuild` と `reconcile-url <url>` RAG インデックス修復コマンドを追加する。

## Scope

**In:**
- `scripts/agent/services/rag_maintenance_service.py` — `rebuild_vec()`, `reconcile_url(url)` 追加
- `scripts/agent/commands/cmd_db.py` — `_db_rebuild_vec()`, `_db_reconcile_url(rest)` ハンドラ + サブコマンド登録
- `docs/03_rag_05_configuration_and_operations.md` — 修復コマンドドキュメント追加

**Out:** 分散 DB サポート

## Implementation

### rag_maintenance_service.py — rebuild_vec()

```python
def rebuild_vec(self) -> int:
    """chunks_vec を chunks から再構築する。返り値: 再挿入行数。"""
    with SQLiteHelper(cfg=self._cfg) as db:
        db.execute("DELETE FROM chunks_vec")
        rows = db.execute(
            "SELECT chunk_id, embedding FROM chunks WHERE embedding IS NOT NULL"
        ).fetchall()
        for chunk_id, emb in rows:
            db.execute(
                "INSERT INTO chunks_vec(chunk_id, embedding) VALUES(?, ?)",
                (chunk_id, emb),
            )
        return len(rows)
```

### rag_maintenance_service.py — reconcile_url()

```python
def reconcile_url(self, url: str) -> dict:
    """1 URL の FTS/vec を再構築する。"""
    with SQLiteHelper(cfg=self._cfg) as db:
        doc = db.execute(
            "SELECT doc_id FROM documents WHERE url = ?", (url,)
        ).fetchone()
        if doc is None:
            return {"found": False}
        doc_id = doc["doc_id"]
        chunk_ids = [
            r["chunk_id"]
            for r in db.execute(
                "SELECT chunk_id FROM chunks WHERE doc_id = ?", (doc_id,)
            ).fetchall()
        ]
        for cid in chunk_ids:
            db.execute("DELETE FROM chunks_vec WHERE chunk_id = ?", (cid,))
        if chunk_ids:
            placeholders = ",".join("?" * len(chunk_ids))
            db.execute(f"DELETE FROM chunks_fts WHERE chunk_id IN ({placeholders})", chunk_ids)
        for cid in chunk_ids:
            row = db.execute(
                "SELECT content, embedding FROM chunks WHERE chunk_id = ?", (cid,)
            ).fetchone()
            if row:
                db.execute(
                    "INSERT INTO chunks_fts(chunk_id, content) VALUES(?, ?)",
                    (cid, row["content"]),
                )
                if row["embedding"]:
                    db.execute(
                        "INSERT INTO chunks_vec(chunk_id, embedding) VALUES(?, ?)",
                        (cid, row["embedding"]),
                    )
        return {"found": True, "chunks": len(chunk_ids)}
```

### cmd_db.py — ハンドラとサブコマンド登録

```python
async def _db_rebuild_vec(self, rest: str) -> None:
    count = await self._rag_maintenance.rebuild_vec()
    self._out.write_success(f"Vec index rebuilt: {count} rows [RAG]")

async def _db_reconcile_url(self, rest: str) -> None:
    url = rest.strip()
    if not url:
        self._out.write_validation_error("Usage: /db reconcile-url <url>")
        return
    result = await self._rag_maintenance.reconcile_url(url)
    if not result["found"]:
        self._out.write_error(f"URL not found: {url}")
    else:
        self._out.write_success(f"Reconciled {result['chunks']} chunks for {url} [RAG]")

# サブコマンド登録:
"vec-rebuild": self._db_rebuild_vec,
"reconcile-url": self._db_reconcile_url,
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| メソッド存在 | `grep -n "rebuild_vec\|reconcile_url" scripts/agent/services/rag_maintenance_service.py` | found |
| コマンド登録 | `grep -n "vec-rebuild\|reconcile-url" scripts/agent/commands/cmd_db.py` | found |
| Tests | `uv run pytest tests/ -k "maintenance" -x -q` | all pass |
