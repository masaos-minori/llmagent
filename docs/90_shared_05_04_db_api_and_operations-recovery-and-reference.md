---
title: "DB API and Operations - Recovery and Reference"
category: shared
tags:
  - shared
  - db
  - corruption-recovery
  - error-handling
  - verification
  - ai-reference
related:
  - 90_shared_00_document-guide.md
  - 90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
  - 90_shared_05_02_db_api_and_operations-protocol-and-backend.md
  - 90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md
source:
  - 90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
---

# DB API and Operations

- Schema → [90_shared_04_01_db_architecture_and_schema-overview-and-config.md](90_shared_04_01_db_architecture_and_schema-overview-and-config.md)

## 9. Corruption Recovery

```python
from db.recovery import recover_corruption
from db.models import RecoveryResult

result = recover_corruption(
    backup_path="/opt/llm/db/backup/rag.sqlite",
    target="rag",
    dry_run=False,
)
```

`target` は `"rag"`(デフォルト)または `"session"` のみを想定している。実装は
`target == "rag"` かどうかの二択でパス表示用の `db_path` を決定するため、`"workflow"` や
`"eventbus"` を渡した場合は表示上 `session_db_path` にフォールバックする一方、実際に開く
DB接続は `SQLiteHelper(target)` に渡した文字列(`"workflow"`/`"eventbus"`)で解決される。
両者が食い違うため、`target` には `"rag"`/`"session"` 以外を渡さないこと
(Explicit in code — `db/recovery.py::recover_corruption`)。

### `RecoveryResult`

```python
@dataclass(frozen=True)
class RecoveryResult:
    success: bool
    action: str      # "vacuum" | "vacuum_failed" | "restored" | "no_backup" | "error"
    detail: str | None = None
    dry_run: bool = False
```

---

## 10. エラーハンドリング

| エラー | 挙動 |
|---|---|
| `sqlite3.OperationalError`(busy/locked） | `PRAGMA busy_timeout` による自動待機(デフォルト30秒） |
| `sqlite3.IntegrityError` | 呼び出し元に伝播する;upsertパスでは発生しない |
| sqlite-vec ロードエラー | `sqlite3.OperationalError` → 接続失敗 |
| スキーマDDL失敗 | `executescript()` から例外が再スローされる |
| 整合性チェック失敗 | エラーをログ記録 + バックアップからの復元を試行 |
| `prune_old_memories` の失敗 | STRICT: 例外が伝播する;BEST_EFFORT: `MaintenanceResult(success=False)` を返す |
| `commit()` エラー | WARNINGをログ記録 + `sqlite3.OperationalError` を再スロー |
| `close()` エラー | WARNINGをログ記録するのみ;例外は発生させない |

---

## 11. DB再作成手順

スキーマ変更にはDBの再作成が必要 — マイグレーション機能は存在しない。

**手順1: アーカイブ** — `rotate_all_dbs()` を実行し、本番用3DBすべてをアーカイブする:

```bash
uv run python -c "from db.rotation import rotate_all_dbs; rotate_all_dbs()"
```

**手順2: 削除** — DBファイルを手動で削除する:

```bash
rm /opt/llm/db/rag.sqlite /opt/llm/db/session.sqlite /opt/llm/db/workflow.sqlite
```

DBパスは `agent.toml` の `rag_db_path`、`session_db_path`、`workflow_db_path`、`eventbus_db_path`
キーから解決される(`db/config.py::DbConfig`)。`create_schema()` は `eventbus.sqlite` も再作成対象
なので、削除する場合は `/opt/llm/db/eventbus.sqlite` も対象に含めること
(Explicit in code — `db/create_schema.py`)。

**手順3: 再作成** — `create_schema()` を実行し空のDBを初期化する:

```bash
uv run python -c "from db.create_schema import create_schema; create_schema()"
```

**重要な注意事項:**
- 再作成されたDBは空である — 既存レコードは自動的に移行されない。
- `create_schema()` は `create_rag_schema()` → `create_session_schema()` → `create_workflow_schema()` →
  `create_eventbus_schema()` を無条件に順次呼び出す4関数のラッパーである。各スキーマDDLは
  `IF NOT EXISTS` で保護されているため、既存ファイルに対して再実行しても冪等
  (Explicit in code — `db/create_schema.py`)。「`eventbus.sqlite` が未存在の場合のみ初期化する」という
  条件分岐は実装には存在しない。
- 1つのDBのみ再作成が必要な場合は個別の関数を使う: `create_rag_schema()`、`create_session_schema()`、
  `create_workflow_schema()`、`create_eventbus_schema()`。

---

## 12. 検証計画

```bash
# Schema initialization
uv run pytest tests/test_create_schema.py

# DB maintenance
uv run pytest tests/test_db_maintenance.py

# Type check
uv run mypy scripts/db/

# Full integration: create DB → check all tables exist
python -c "from db.create_schema import create_schema; create_schema()"
sqlite3 /opt/llm/db/rag.sqlite ".tables"
sqlite3 /opt/llm/db/session.sqlite ".tables"
```

---

## 13. AIリファレンスガイド

| 質問 | 回答 |
|---|---|
| DB接続を開く方法 | `with SQLiteHelper("rag").open(row_factory=True) as db:` |
| アトミックに書き込む方法 | `open(write_mode=True)` コンテキスト内で `with db.begin_immediate():` |
| `target="workflow"` は何に接続するか | `workflow.sqlite` — タスク追跡DB |
| 埋め込みBLOBを検証する方法 | `db.store` の `validate_embedding_blob(blob)` |
| 古いセッションをパージする方法 | `purge_old_sessions(db, RetentionConfig(...))` — `MaintenanceResult` を返す;`.success` を確認 |
| 破損から復旧する方法 | `recover_corruption(backup_path=..., target="rag")` |
| `prune_old_memories` は例外を捕捉するか | **STRICT**(デフォルト）: 伝播する;**BEST_EFFORT**: 捕捉され `MaintenanceResult` に格納される |
| BEST_EFFORTモードの使い方 | `vacuum_db`、`purge_old_sessions`、`prune_old_memories` に `mode=MaintenanceMode.BEST_EFFORT` を渡す |
| RAG整合性を確認する方法 | `check_rag_consistency(db)` → `is_consistent(report)` + `summarize_issues(report)` |

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md`
- `90_shared_05_02_db_api_and_operations-protocol-and-backend.md`
- `90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md`

## Keywords

corruption recovery
error handling
DB recreation procedure
verification plan
ai reference guide
