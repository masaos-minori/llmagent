---
title: "DB API and Operations - Protocol and Backend"
category: shared
tags:
  - shared
  - db
  - protocol-groups
  - sqlite-backend
  - memory-store
related:
  - 90_shared_00_document-guide.md
  - 90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
  - 90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md
  - 90_shared_05_04_db_api_and_operations-recovery-and-reference.md
source:
  - 90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
---

# DB API and Operations

- スキーマ → [90_shared_04_01_db_architecture_and_schema-overview-and-config.md](90_shared_04_01_db_architecture_and_schema-overview-and-config.md)

## 3. `db/store.py` のプロトコルグループ

すべてのプロトコルは `@runtime_checkable` である — `isinstance()` チェックが機能する。

### Embedding ヘルパー

```python
from db.store import get_embedding_dims, get_embedding_bytes, validate_embedding_blob

dims = get_embedding_dims()      # reads agent.toml::embedding_dims; default 384
nbytes = get_embedding_bytes()   # dims * 4 (float32)
validate_embedding_blob(blob)    # TypeError if not bytes; ValueError if wrong size
```

### `VectorStore` プロトコル

```python
class VectorStore(Protocol):
    def vec_insert(self, chunk_id: int, embedding: bytes) -> None: ...
    def vec_search(self, embedding: bytes, k: int) -> list[tuple[int, float]]: ...
    def vec_delete(self, chunk_id: int) -> None: ...
    def vec_count(self) -> int: ...
```

- `vec_search` は `(chunk_id, distance)` のペアを返す
- `vec_delete`: 見つからない場合は no-op

### `DocumentStore` プロトコル

```python
class DocumentStore(Protocol):
    def doc_upsert(self, url, title, lang, etag, last_modified) -> int: ...
    def doc_get(self, url) -> dict | None: ...
    def doc_list(self, lang, limit) -> list[dict]: ...
    def doc_delete(self, url) -> bool: ...
    def chunk_insert(self, doc_id, index, content, normalized=None, chunk_type="", source_file="") -> int: ...
    def chunk_count(self) -> int: ...
```

- `doc_upsert`: SELECT の後に UPDATE/INSERT を行う; `doc_id` を返す
- `doc_get` は `{doc_id, url, title, lang, fetched_at, etag, last_modified}` または `None` を返す
- `doc_list` は `{doc_id, url, title, lang, fetched_at}` を `fetched_at DESC` でソートして返す
- `doc_delete`: ドキュメントを削除し、chunks にもカスケードする; 見つかった場合は `True` を返す
- `chunk_insert` は `chunks` テーブルの `chunk_index`、`chunk_type`、`source_file` カラムを使用する

### `SessionStore` プロトコル

```python
class SessionStore(Protocol):
    def session_create(self) -> int: ...
    def session_list(self, limit) -> list[dict]: ...
    def session_rename(self, session_id, title) -> None: ...
    def session_delete(self, session_id) -> None: ...
    def message_save(self, session_id, role, content, tool_calls, tool_call_id=None) -> None: ...
    def message_list(self, session_id) -> list[dict]: ...
```

- `session_list` は `{session_id, created_at, title}` を `created_at DESC` でソートして返す
- `session_delete` は messages にカスケードする (ON DELETE CASCADE)
- `message_list` は `{role, content, tool_calls, tool_call_id}` を `message_id ASC` の順で返す
- `tool_calls` は `str | None` (JSON文字列)
- `tool_call_id` は `str | None`; `tool` ロールのメッセージには常に設定され、他のロールでは NULL

---

## 4. SQLite バックエンド実装

| クラス | プロトコル | コンストラクタ | 備考 |
|---|---|---|---|
| `SQLiteVectorStore(db)` | `VectorStore` | `db: SQLiteHelper` | `vec_insert` で embedding の BLOB サイズを検証する |
| `SQLiteDocumentStore(db)` | `DocumentStore` | `db: SQLiteHelper` | `doc_upsert` は SELECT の後に UPDATE/INSERT を行う |
| `SQLiteSessionStore(db)` | `SessionStore` | `db: SQLiteHelper` | セッション一覧は `created_at DESC` で返される |
| `SQLiteMemoryDeleteStore(db)` | `MemoryDeleteStore` | `db: SQLiteHelper` | `memories`/`memories_fts`/`memories_vec` に対するアトミックな横断削除 |

### `SessionMessageRepository` と `SQLiteSessionStore` の比較

| レイヤー | 担当する責務 |
|---|---|
| `SessionMessageRepository` (agent レイヤー) | ロール検証 (`user`/`assistant`/`tool`/`system`)、strict_mode のスキップ挙動、content=None の正規化、tool_calls の JSON エンコード/デコード、セッションに依存する永続化 |
| `SQLiteSessionStore` (db アダプターレイヤー) | スキーマに整合した INSERT/LIST 操作のみで、最小限の検証しか行わない |

**ルール:** 検証・エンコードのロジックを `SQLiteSessionStore` に重複させてはならない。これは薄い DB アダプターであり、ロール検証も content の正規化も JSON エンコードも行わない。これらの関心事はすべて `SessionMessageRepository` に属する。

エージェント側の責務境界の見方については [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md) を参照。

### `MemoryDeleteStore` / `SQLiteMemoryDeleteStore`

```python
from db.store import MemoryDeleteStore, SQLiteMemoryDeleteStore, MemoryDeleteResult

store = SQLiteMemoryDeleteStore(db)
result: MemoryDeleteResult = store.delete_memories_before(older_than_days=30)
# result.deleted — count of deleted entries
```

- `memories`、`memories_fts`、`memories_vec` からアトミックに削除する
- `maintenance.py::prune_old_memories()` はこのクラスに委譲する
- `MemoryDeleteStore` はプロトコル (構造的型) であり、将来 SQLite 以外のバックエンドを選択できる余地を残すために存在する。現時点では `SQLiteMemoryDeleteStore` が唯一の実装である。

---



---

## 6. メモリ関連テーブルと操作 (`MemoryStore`)

`MemoryStore` は `agent/memory/store.py` (`db/` ではない) で定義されている。`SQLiteHelper("session")` を使用する。

主要メソッド:

| メソッド | 説明 |
|---|---|
| `add(entry, embedding=None)` | `memories` + `memories_fts` へ挿入; 必要に応じて `memories_vec` にも挿入 |
| `upsert(entry, embedding=None)` | `INSERT OR REPLACE` + FTS/vec を同期 |
| `delete(memory_id)` | 1件削除; 見つかった場合は `True` を返す |
| `search_by_type(type, limit)` | `memory_type` でフィルタ; `importance DESC, pinned DESC` の順 |
| `pin(memory_id)` / `unpin(memory_id)` | pinned フラグを切り替える |
| `clear_by_session(session_id)` | セッションに紐づく全エントリを削除 |
| `count_vec()` | `memories_vec` の行数; vec0 が読み込まれていない場合は `0` を返す |

`maintenance.py` の `prune_old_memories(db, older_than_days)` は、テーブル横断削除を
`SQLiteMemoryDeleteStore` に委譲する。

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md`
- `90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md`
- `90_shared_05_04_db_api_and_operations-recovery-and-reference.md`

## Keywords

protocol groups
db/store.py
SQLite backend implementations
MemoryStore
