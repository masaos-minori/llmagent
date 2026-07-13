---
title: "DB API and Operations - Maintenance and Rotation"
category: shared
tags:
  - shared
  - db
  - maintenance
  - rotation
  - rag-consistency
related:
  - 90_shared_00_document-guide.md
  - 90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
  - 90_shared_05_02_db_api_and_operations-protocol-and-backend.md
  - 90_shared_05_04_db_api_and_operations-recovery-and-reference.md
source:
  - 90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
---

# DB API and Operations

- スキーマ → [90_shared_04_01_db_architecture_and_schema-overview-and-config.md](90_shared_04_01_db_architecture_and_schema-overview-and-config.md)

## 7. メンテナンス関数 (`db/maintenance.py`)

すべての関数は `SQLiteHelper` インスタンスを受け取り、低レベルの操作をそのインスタンスに委譲する。

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `checkpoint_wal(db, mode=None)` | `-> WalCheckpointCounts` | WAL のフラッシュ; デフォルトモードは `agent.toml::sqlite_wal_checkpoint_mode` から取得 (デフォルト `TRUNCATE`) |
| `vacuum_db(db, mode=STRICT)` | `-> MaintenanceResult` | `db.vacuum()` に委譲する; トランザクション外で呼び出すこと |
| `purge_old_sessions(db, cfg=None, mode=STRICT)` | `-> MaintenanceResult` | 経過日数ベース + 件数ベースのセッションパージ; 内部でコミットする |
| `prune_old_memories(db, older_than_days, mode=STRICT)` | `-> MaintenanceResult` | `SQLiteMemoryDeleteStore` 経由で古いメモリを削除 |

`checkpoint_wal` の `mode` に不正な文字列(`PASSIVE`/`FULL`/`RESTART`/`TRUNCATE` 以外)を渡すと、
`SQLiteHelper.checkpoint()` 側の `_CHECKPOINT_MODES` チェックで `ValueError` を送出する
(Explicit in code — `db/helper.py`)。

### `MaintenanceMode` と `MaintenanceResult`

```python
class MaintenanceMode(StrEnum):
    STRICT = "strict"        # Exceptions propagate (default; preserves existing behavior)
    BEST_EFFORT = "best_effort"  # Exceptions caught, logged, returned in MaintenanceResult

@dataclass(frozen=True)
class MaintenanceResult:
    success: bool
    action: str              # "vacuum" | "vacuum_failed" | "purge" | "purge_failed" | "prune" | "prune_failed"
    mode: MaintenanceMode
    detail: str | None = None  # Exception message on failure
    data: dict | None = None   # e.g. {"age_deleted": N, "count_deleted": N} or {"deleted": N}
```

**モードの意味:**
- `STRICT` (デフォルト): mode 導入前のコードと挙動は変わらない — 例外はそのまま伝播する; 成功時は `MaintenanceResult(success=True)` が返される
- `BEST_EFFORT`: 例外は捕捉され、ERROR としてログに記録され、`MaintenanceResult(success=False, detail=str(exc))` として返される; 呼び出し側は必ず `result.success` を確認すること

```python
from db.maintenance import MaintenanceMode, MaintenanceResult, vacuum_db

# STRICT mode (default) — raises on error
result = vacuum_db(db)
assert result.success

# BEST_EFFORT mode — caller checks result
result = vacuum_db(db, mode=MaintenanceMode.BEST_EFFORT)
if not result.success:
    logger.error("vacuum failed: %s", result.detail)
```

### `RetentionConfig`

```python
@dataclass(frozen=True)
class RetentionConfig:
    max_sessions: int = 100   # max sessions to retain
    max_age_days: int = 90    # purge sessions older than N days (0 = disabled)
```

`RetentionConfig.from_config()` は `agent.toml::sqlite_retention_max_sessions` /
`sqlite_retention_max_age_days` を読み込む。

### `purge_old_sessions` の挙動

1. `max_age_days > 0` の場合: N日より古いセッションを削除する (`age_deleted`)
2. 残り件数が `max_sessions` を超える場合: 最も古い超過分のセッションを削除する (`count_deleted`)
3. `messages` に `ON DELETE CASCADE` が設定されていることを前提とする
4. 最後に `db.conn.commit()` を呼ぶ
5. `MaintenanceResult(success=True, data={"age_deleted": N, "count_deleted": N})` を返す

### `prune_old_memories` の挙動

1. `older_than_days` より古い `memory_id` を収集する
2. `memories`、`memories_fts`、`memories_vec` から削除する
3. `db.commit()` を呼ぶ
4. `MaintenanceResult(success=True, data={"deleted": N})` を返す
5. STRICT モードで失敗した場合: 例外が伝播する; BEST_EFFORT モードの場合: `success=False` を返す

---

## 7a. DB ローテーション (`db/rotation.py`)

```python
from db.rotation import rotate_session_db, rotate_workflow_db, rotate_all_dbs, rotate_db

# Archive only session DB
session_dest = rotate_session_db()

# Archive rag + session DBs
rag_dest, session_dest = rotate_db()

# Archive all three DBs
rag_dest, session_dest, workflow_dest = rotate_all_dbs()
```

| Function | Signature | Description |
|---|---|---|
| `rotate_session_db(archive_dir=None)` | `-> Path` | Archive `session.sqlite` with timestamp suffix via SQLite online backup API |
| `rotate_workflow_db(archive_dir=None)` | `-> Path` | Archive `workflow.sqlite` with timestamp suffix |
| `rotate_all_dbs(archive_dir=None)` | `-> tuple[Path, Path, Path]` | Archive all three DBs; returns `(rag_dest, session_dest, workflow_dest)` |
| `rotate_db(archive_dir=None)` | `-> tuple[Path, Path]` | Archive both rag and session DBs; returns `(rag_dest, session_dest)` |

Archive directory defaults to `/opt/llm/db/archive` (from `agent.toml::sqlite_archive_dir`).

---

## 7b. RAG Consistency Checks (`db/rag_consistency.py`)

```python
from db.rag_consistency import RagConsistencyReport, check_rag_consistency, is_consistent, summarize_issues

with SQLiteHelper("rag").open() as db:
    report: RagConsistencyReport = check_rag_consistency(db)
    if not is_consistent(report):
        for issue in summarize_issues(report):
            print(issue)
```

| Function | Signature | Description |
|---|---|---|
| `check_rag_consistency(db, embed_failed=0)` | `-> RagConsistencyReport` | Read-only: chunks/FTS/vec row counts + orphan detection |
| `is_consistent(report)` | `-> bool` | True if no orphans and FTS gap = 0 |
| `summarize_issues(report)` | `-> list[str]` | Human-readable issue descriptions |

`check_rag_consistency` は `embed_failed`(呼び出し元で把握している埋め込み失敗件数; デフォルト0)を
そのまま `RagConsistencyReport.embed_failed` に格納するのみで、埋め込み失敗自体の検出は行わない
(Explicit in code — `db/rag_consistency.py`)。

### `RagConsistencyReport`

```python
@dataclass(frozen=True)
class RagConsistencyReport:
    chunks: int
    fts: int
    vec: int
    orphan_vec_count: int
    fts_gap: int              # chunks - fts; positive = missing FTS entries
    fts_orphan_count: int     # fts - chunks; positive = extra FTS entries (data loss risk)
    embed_failed: int = 0     # embedding failures during ingestion (caller-supplied, informational)
    issues: tuple[str, ...] = ()  # summarize_issues(report) の結果; check_rag_consistency が自動で埋める
    affected_chunk_ids: tuple[int, ...] | None = None      # FTSに欠落しているchunk_id (最大10件)
    affected_doc_ids: tuple[int, ...] | None = None        # 上記chunkが属するdoc_id (最大10件)
    affected_orphan_chunk_ids: tuple[int, ...] | None = None  # chunks_vecにのみ存在するchunk_id (最大10件)
    affected_orphan_urls: tuple[str, ...] | None = None    # orphan vec行の元URL (最大10件)
```

`affected_*` フィールドは診断用の識別子リストで、`fts_gap > 0` または `orphan_vec_count > 0` の場合のみ
埋められる(それ以外は `None`)。`issues` は `check_rag_consistency` が内部で `summarize_issues(report)` を
呼び出した結果を自動的に格納する — 呼び出し側が別途 `summarize_issues()` を呼ばなくても
`report.issues` から同じ内容を取得できる
(Explicit in code — `db/rag_consistency.py`)。

**`is_consistent` の判定条件(実装ベース):**

```python
fts_gap == 0 and fts_orphan_count == 0 and orphan_vec_count == 0 and vec == chunks
```

ドキュメント冒頭の「no orphans and FTS gap = 0」という要約は簡略化であり、実際には
`vec == chunks`(ベクトル件数とチャンク件数の完全一致)も条件に含まれる
(Explicit in code — `db/rag_consistency.py`)。

**Usage:**

```python
from db.rag_consistency import RagConsistencyReport, check_rag_consistency, is_consistent, summarize_issues

report: RagConsistencyReport = check_rag_consistency(db)
if not is_consistent(report):
    for issue in summarize_issues(report):
        print(issue)
```

- `fts_gap > 0` → FTS trigger missed some inserts; fix: `/db rag rebuild-fts`
- `fts_orphan_count > 0` → FTS has more entries than chunks (`[CRITICAL]`); data loss risk; fix: `/db rag rebuild-fts` immediately (Explicit in code)
- `orphan_vec_count > 0` → vec trigger failed; fix: re-ingest affected URLs with `ingester.py --force`
- `vec != chunks`(orphan以外の不一致)も `[WARNING]` として報告され、同じく `ingester.py --force` での再取込を促す (Explicit in code — `db/rag_consistency.py::summarize_issues`)
- Read-only; does not repair inconsistencies.

**Recovery flow:**
1. `PRAGMA integrity_check` on `target` DB
2. `dry_run=True` → return result without modifying DB
3. Result `"ok"` → run VACUUM; return `action="vacuum"` (or `"vacuum_failed"`)
4. Result not `"ok"` → archive corrupt file as `{stem}_corrupt_{timestamp}{suffix}`; copy `backup_path`; return `action="restored"` (or `"no_backup"` / `"error"`)

**Rotate archive format:** `{stem}_{YYYYMMDD_HHMMSS}{suffix}` in `archive_dir`
(default: `agent.toml::sqlite_archive_dir` → `/opt/llm/db/archive`).
Uses SQLite online backup API to preserve WAL integrity.

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md`
- `90_shared_05_02_db_api_and_operations-protocol-and-backend.md`
- `90_shared_05_04_db_api_and_operations-recovery-and-reference.md`

## Keywords

maintenance functions
db/maintenance.py
db rotation
RagConsistencyReport
affected_chunk_ids
embed_failed
RAG consistency checks
