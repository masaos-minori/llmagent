# 04_refactor.md — scripts/db/ リファクタリング計画

## 1. 現状分析

`scripts/db/` のモジュール構成と課題:

| ファイル | 行数 | 内容 | 課題 |
|---|---|---|---|
| `__init__.py` | 0 | 空 | パッケージエクスポートがない |
| `models.py` | 88 | DTO dataclass (7種) | 他モジュールにも重複定義がある |
| `config.py` | 60 | DbConfig + builder | `__post_init__` で親ディレクトリ検証がテスト困難 |
| `helper.py` | 254 | SQLiteHelper 接続管理 | なし（適切に分離済み） |
| `store.py` | 399 | Protocol(4種) + impl(4種) + embedding utility(3種) | **巨大**。責務が混在 |
| `tool_results.py` | 112 | ToolResultStore | なし（適切に分離済み） |
| `maintenance.py` | 290 | 保守関数群 + dataclass(2種) | dataclass が models.py と重複する可能性 |
| `create_schema.py` | 215 | スキーマ初期化 + SQL テンプレート | SQL テンプレートがコード内にハードコード |

## 2. 計画対象

### 2.1 store.py の分割（最優先）

**現状:** 399行で Protocol, SQLite impl, embedding utilities が混在

**目標:**
- `store_protocols.py` — Protocol定義 + embedding utilities (`get_embedding_dims`, `get_embedding_bytes`, `validate_embedding_blob`)
- `store_impl.py` — SQLite-backed implementations (`SQLiteVectorStore`, `SQLiteDocumentStore`, `SQLiteSessionStore`, `SQLiteMemoryDeleteStore`)

**エクスポートマッピング:**
```
旧: from db.store import VectorStore, DocumentStore, SessionStore, MemoryDeleteStore
    from db.store import SQLiteVectorStore, SQLiteDocumentStore, SQLiteSessionStore, SQLiteMemoryDeleteStore
    from db.store import get_embedding_dims, get_embedding_bytes, validate_embedding_blob

新: from db.store_protocols import (VectorStore, DocumentStore, SessionStore, MemoryDeleteStore,
                                     get_embedding_dims, get_embedding_bytes, validate_embedding_blob)
    from db.store_impl import (SQLiteVectorStore, SQLiteDocumentStore, SQLiteSessionStore, SQLiteMemoryDeleteStore)
```

**後方互換:** `db/store.py` を re-export stub に変更（既存インポートを壊さない）

### 2.2 SQL テンプレートの抽出

**現状:** `create_schema.py` に `_RAG_SCHEMA_TEMPLATE` と `_SESSION_SCHEMA_TEMPLATE` が文字列リテラルとして定義

**目標:** `schema_sql.py` に分離

```
新: from db.schema_sql import RAG_SCHEMA_TEMPLATE, SESSION_SCHEMA_TEMPLATE
    # または直接インライン参照
```

### 2.3 dataclass の統合

**現状:** `maintenance.py` に `RetentionConfig`, `RecoveryResult` が定義。`store.py` に `MemoryDeleteResult` が定義。

**目標:** これらを `models.py` に統合。`maintenance.py` と `store_impl.py` は `from db.models import` で参照。

### 2.4 __init__.py の整備

**目標:** パッケージの公開APIを一元エクスポート

```python
from db.config import DbConfig, build_db_config
from db.helper import SQLiteHelper
from db.models import (
    WalCheckpointCounts, PurgeCounts, ToolResultRow,
    DbHealthMetrics, DocumentRow, SessionRow, MessageRow, MemoryDeleteResult,
)
from db.store_protocols import (
    VectorStore, DocumentStore, SessionStore, MemoryDeleteStore,
    get_embedding_dims, get_embedding_bytes, validate_embedding_blob,
)
from db.store_impl import (
    SQLiteVectorStore, SQLiteDocumentStore, SQLiteSessionStore, SQLiteMemoryDeleteStore,
)
from db.tool_results import ToolResultStore
from db.maintenance import (
    checkpoint_wal, vacuum_db, purge_old_sessions, prune_old_memories,
    rotate_rag_db, rotate_session_db, rotate_db, recover_corruption,
    RetentionConfig, RecoveryResult,
)

__all__ = [ ... ]
```

## 3. ブラストレイサー表

### store.py 分割の影響

| ファイル | 変更内容 | 影響 |
|---|---|---|
| `scripts/db/create_schema.py` | `from db.store import get_embedding_dims` → `from db.store_protocols import get_embedding_dims` | インポートパス変更 |
| `scripts/db/maintenance.py` | `from db.store import SQLiteMemoryDeleteStore` → `from db.store_impl import SQLiteMemoryDeleteStore` | インポートパス変更 |
| `scripts/agent/document_repo.py` | `from db.helper import SQLiteHelper` → 変更なし | store.py を直接インポートしていない |
| `tests/test_db_maintenance.py` | `from db.maintenance import prune_old_memories` → 変更なし | store.py を直接インポートしていない |

### schema_sql.py 追加の影響

| ファイル | 変更内容 | 影響 |
|---|---|---|
| `scripts/db/create_schema.py` | SQL テンプレートを schema_sql.py からインポート | インポート追加、テンプレート定義削除 |

### models.py 拡張の影響

| ファイル | 変更内容 | 影響 |
|---|---|---|
| `scripts/db/maintenance.py` | `RetentionConfig`, `RecoveryResult` を models.py からインポート | ローカル定義をインポートに変更 |
| `scripts/db/store_impl.py` | `MemoryDeleteResult` を models.py からインポート | ローカル定義をインポートに変更 |

## 4. 手順（フェーズ別）

### Step 1: `store_protocols.py` の作成
- `store.py` から Protocol定義 + embedding utilities をコピー
- ruff + mypy チェック

### Step 2: `store_impl.py` の作成
- `store.py` から SQLite impl をコピー
- `store_protocols.py` と `models.py` にインポートを変更
- ruff + mypy チェック

### Step 3: `store.py` を re-export stub に変更
- 既存の import を両方の新モジュールから再エクスポート
- `from db.store_protocols import *` / `from db.store_impl import *`

### Step 4: `schema_sql.py` の作成
- `create_schema.py` から SQL テンプレートをコピー
- `create_schema.py` を更新して `schema_sql.py` からインポート

### Step 5: `models.py` に dataclass を統合
- `RetentionConfig`, `RecoveryResult` (maintenance.py から)
- `MemoryDeleteResult` (store.py から)
- 関係ファイルのインポートを更新

### Step 6: `__init__.py` の整備
- パッケージ公開APIを定義
- `from db.xxx import yyy` 形式で統一

### Step 7: 最終検証
- ruff format + ruff check
- mypy scripts/
- lint-imports
- pytest (affected tests)
- diff-cover

## 5. 後方互換性

すべての既存 import パスは `store.py` の re-export stub によって維持される:

```python
# これらすべてが動作し続ける:
from db.store import VectorStore, SQLiteVectorStore, get_embedding_dims
from db.store import DocumentStore, SQLiteDocumentStore
from db.store import SessionStore, SQLiteSessionStore
from db.store import MemoryDeleteStore, SQLiteMemoryDeleteStore
```

## 6. import-linter への影響

既存の契約は変更不要:
- `db → shared` の依存関係は維持
- 新しいモジュールはすべて `db` パッケージ内
