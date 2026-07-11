---
title: "DB API and Operations - Module Boundaries and Helper"
category: shared
tags:
  - shared
  - db
  - sqlitehelper
  - module-boundaries
  - store-protocols
related:
  - 90_shared_00_document-guide.md
  - 90_shared_05_02_db_api_and_operations-protocol-and-backend.md
  - 90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md
  - 90_shared_05_04_db_api_and_operations-recovery-and-reference.md
source:
  - 90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
---

# DB API and Operations

- スキーマ → [90_shared_04_01_db_architecture_and_schema-overview-and-config.md](90_shared_04_01_db_architecture_and_schema-overview-and-config.md)

## 1. 目的

`SQLiteHelper` API、`db/store.py` のプロトコルグループと実装、
メモリ関連のテーブル操作、メンテナンス機能、破損時の
リカバリ、エラーハンドリング、運用上の検証計画を文書化する。

---

## 1a. DB Store モジュールの境界

DB store 層は、明確なインポート境界を持つ3つのモジュールに分割されている。

| Module | 役割 | インポート境界 |
|---|---|---|
| `db/store.py` | **公開 API サーフェス** — プロトコルとエンベディングヘルパーを re-export する | 呼び出し側はここからインポートすべき。安定した契約。 |
| `db/store_protocols.py` | **拡張ポイント** — ストレージ契約のプロトコル定義 | 実装側がこれをインポートする。呼び出し側が直接使う必要はほとんどない。 |
| `db/store_impl.py` | **SQLite 実装層** — プロトコルの具体的な実装 | プロトコル抽象化を意図的にバイパスする場合を除き、直接インポートしないこと。 |

**ルール:** 呼び出し側は常に `db.store` からインポートすること。`store_protocols.py` や `store_impl.py` からの直接インポートは推奨されず、プロトコル/実装レベルで意図的に作業する場合にのみ使用すべきである。

### DB store を拡張する方法

1. `db/store_protocols.py` に新しい Protocol クラスを追加する（例: `class NewStorageProtocol(Protocol): ...`）
2. `db/store_impl.py` でプロトコルを実装する（例: `class NewStorageImpl(NewStorageProtocol): ...`）
3. `db/store.py` から export する — 呼び出し側は内部モジュールからではなく `db.store` からインポートする

**アンチパターン:** 呼び出し側コードで `store_protocols.py` や `store_impl.py` から直接インポートしないこと。

```python
# BAD — direct import of internal module
from db.store_impl import NewStorageImpl  # breaks abstraction

# GOOD — import from public API
from db.store import NewStorageProtocol, NewStorageImpl  # stable contract
```

---

## 2. `SQLiteHelper` (`db/helper.py`)

### コンストラクタ

```python
SQLiteHelper(
    target: DbTarget | str = "rag",
    *,
    db_path: str | None = None,
    sqlite_vec_so: str = "",
    sqlite_timeout: int = 30,
    sqlite_busy_timeout_ms: int = 30000,
)
# DbTarget.RAG, DbTarget.SESSION, DbTarget.WORKFLOW, DbTarget.EVENTBUS, or string literal
# "rag" → rag.sqlite  |  "session" → session.sqlite  |  "workflow" → workflow.sqlite  |  "eventbus" → eventbus.sqlite
# Invalid target → ValueError
```

すべてのパスと設定を解決するために `build_db_config()` が `__init__()` 内で呼び出される — ただし `db_path` が明示的に渡された場合は `build_db_config()` が完全にバイパスされ、指定された `db_path`/`sqlite_vec_so`/`sqlite_timeout`/`sqlite_busy_timeout_ms` がそのまま使用される（MCP サーバーなどの呼び出し側が `agent.toml` を読み込まずに DB 設定を自己完結させられる）。

### `open()` メソッド

```python
def open(
    self,
    *,
    write_mode: bool = False,
    row_factory: bool = False,
    load_vec: bool | None = None,
) -> "SQLiteHelper"
```

チェーン用に `self` を返す。`self.conn` を設定する。

| 引数 | 効果 |
|---|---|
| `write_mode=True` | `PRAGMA foreign_keys=ON` を追加する |
| `row_factory=True` | `conn.row_factory = sqlite3.Row` を設定する（カラム名でのアクセス） |
| `load_vec=None` | ターゲットのデフォルトを使用: `rag` → True、`session`/`workflow` → False |
| `load_vec=True` | sqlite-vec 拡張を強制的にロードする |
| `load_vec=False` | vec 拡張をスキップする |

常に適用される: vec のロード（有効な場合）、WAL、NORMAL sync、busy_timeout。

### コアメソッド

| メソッド | シグネチャ | 補足 |
|---|---|---|
| `execute(sql, params=())` | `-> sqlite3.Cursor` | `params`: タプル（位置指定 `?`）または辞書（名前付き `:name`）。conn が None の場合は `RuntimeError`、sql が空の場合は `ValueError` |
| `executescript(sql_script)` | `-> None` | 複数の SQL ステートメントを実行する。実行前に保留中のトランザクションをコミットする |
| `executemany(sql, params_seq)` | `-> sqlite3.Cursor` | バッチ INSERT/UPDATE。`params_seq: list[tuple[Any, ...]]` |
| `fetchall(sql, params=())` | `-> list[Any]` | `execute + fetchall` を組み合わせたもの |
| `commit()` | `-> None` | `sqlite3.OperationalError` 発生時に ERROR をログ出力してから再スローする |
| `close()` | `-> None` | 冪等。クローズエラー時は WARNING をログ出力するが例外はスローしない |
| `begin_immediate()` | `@contextmanager` | `BEGIN IMMEDIATE ... COMMIT`。`Exception`（`BaseException` ではない）で自動 ROLLBACK |
| `begin_exclusive()` | `@contextmanager` | `BEGIN EXCLUSIVE ... COMMIT`。VACUUM/DDL 専用。`Exception`（`BaseException` ではない）で自動 ROLLBACK |
| `health_check()` | `-> DbHealthMetrics` | `PRAGMA quick_check`。`{journal_mode, integrity, page_count, page_size, freelist_count, db_size_bytes}` を返す |
| `checkpoint(mode="TRUNCATE")` | `-> WalCheckpointCounts` | モード: PASSIVE/FULL/RESTART/TRUNCATE。不正なモードは `ValueError` |
| `vacuum()` | `-> None` | DB をインプレースで再構築する。DB サイズの約2倍の空きディスク容量が必要。トランザクション外で呼び出すこと |

### 典型的な使用パターン

```python
# Read-only query
with SQLiteHelper("rag").open(row_factory=True) as db:
    rows = db.fetchall("SELECT url, title FROM documents WHERE lang = :lang", {"lang": "ja"})

# Write with transaction
with SQLiteHelper("session").open(write_mode=True) as db:
    db.execute("INSERT INTO sessions DEFAULT VALUES")
    db.commit()

# Atomic multi-statement write
with SQLiteHelper("rag").open(write_mode=True) as db:
    with db.begin_immediate():
        db.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        # COMMIT auto on exit; ROLLBACK on exception
```

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_05_02_db_api_and_operations-protocol-and-backend.md`
- `90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md`
- `90_shared_05_04_db_api_and_operations-recovery-and-reference.md`

## Keywords

DB store module boundaries
SQLiteHelper
db/helper.py
