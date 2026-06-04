# 02_implement_plan.md — db/ 層リファクタリング実装計画

ソース仕様: `00_llm_spec_tobe.md`

---

## Goal

`db/` 層 6 ファイルから後方互換レガシー機能・モジュールグローバル状態・暗黙的失敗を除去し、
明示的 DI・構造化レポート・単一責務モジュールへ移行する。

---

## Scope

**In scope:**
- `scripts/db/helper.py` — module-level `_cfg` 除去、責務分割
- `scripts/db/maintenance.py` — module-level `_cfg` 除去、`prune_old_memories` 監査化、`recover_corruption` 構造化
- `scripts/db/store.py` — `EMBEDDING_DIMS` config 化、`MemoryDeleteStore` Protocol + 実装追加
- `scripts/db/tool_results.py` — silent fallback への audit event 追加
- `scripts/db/create_schema.py` — migration エラー分類、`schema_version` テーブル、旧テーブル DROP
- `scripts/db/migrate.py` — named columns コピー、構造化レポート、schema 互換性チェック
- `config/common.toml` — `embedding_dims = 384` キー追加
- `docs/06_ref-sqlite.md` — 変更箇所の反映
- 上記モジュールのテストファイル (`test_sqlite_helper.py`, `test_db_maintenance.py`, `test_tool_result_store.py`, `test_create_schema.py`)

**Out of scope:**
- `agent/memory/store.py` など db 層外のコード (import 先は影響しない)
- `rag/` 層の変更
- MCP サーバの変更
- `config/agent.toml` の `embed_dim` / `memory_embed_dim` (agent 層の設定。db 層は `common.toml` の `embedding_dims` を参照)

---

## Assumptions

1. `SQLiteHelper` のパブリック API (`open`, `execute`, `fetchall`, `commit`, `close`, `begin_immediate`, `begin_exclusive`, `health_check`, `checkpoint`, `vacuum`) は変更しない。17 ファイルが import しておりインターフェース変更は別タスクとする。
2. `config/common.toml` に `embedding_dims = 384` を追加しても既存動作には影響しない（追加キーは無視される）。
3. 旧テーブル (`memory_entries`, `memory_vec`) の DROP は migration step として実施し、スキーマ初期化 DDL では IF NOT EXISTS の保護下に残す。本番環境での一回限り実行が前提。
4. Python 3.13、import-linter 境界 (`db → shared` のみ許可) は変更しない。
5. テストは `.venv` 経由 (`source .venv/bin/activate && python -m pytest`) で実行する。

---

## Unknowns

| Unknown | Evidence | Resolution | Blocking |
|---|---|---|---|
| SQLiteHelper への config DI 方式 | 17 callers が `SQLiteHelper("rag")` を直接呼び出し。コンストラクタ変更は破壊的 | class-level `_ensure_config()` を self-contained に (module-level `_get_cfg()` 廃止のみ)。class-level cache (`_config_loaded`) は保持 | YES → 解決済: class-level cache 維持 |
| embedding_dims の統一先 | `config/agent.toml` に `embed_dim = 384` 既存だが agent 層の設定。db 層は agent に依存不可 | `config/common.toml` に `embedding_dims = 384` を追加し db 層はそちらを参照 | YES → 解決済: common.toml 追加 |
| `prune_old_memories` の store-layer API 化 | 現在 `maintenance.py` で3テーブル削除。`db` → `agent` import は禁止 | `db/store.py` に `MemoryDeleteStore Protocol` + `SQLiteMemoryDeleteStore` 実装を追加し `maintenance.py` から委譲 | YES → 解決済: store.py に追加 |
| schema_version 管理方式 | 現在は `schema_version` テーブルなし | `schema_version(version INT, applied_at TEXT)` テーブルを session.sqlite / rag.sqlite 両方に追加。version 0→1 で旧テーブル DROP など | NO → シンプルな integer version テーブル |
| 旧テーブル (`memory_entries`, `memory_vec`) DROP タイミング | prod DB に存在する可能性あり。`create_schema.py` での DROP は既存データ破壊リスク | `_SESSION_MIGRATE_SQL` に DROP TABLE 文を migration step として追加。`_run_migrations()` の safe-only 改修後に適用 | NO → migration step に含める |

---

## Affected Areas

| File | Change | Blast radius | Churn (git log) | Bus factor | deploy.sh |
|---|---|---|---|---|---|
| `scripts/db/helper.py` | module-level `_cfg` / `_get_cfg()` 廃止、`_ensure_config` 自己完結化 | high (17 ファイルが import; ただし public API 変更なし) | 6 commits | 1 author | existing |
| `scripts/db/maintenance.py` | module-level `_cfg` 廃止、`prune_old_memories` 監査化、`recover_corruption` 構造化 | medium (`cmd_db.py`, `memory/layer.py` が import) | 6 commits | 1 author | existing |
| `scripts/db/store.py` | `EMBEDDING_DIMS` config 化、`MemoryDeleteStore` 追加 | low (外部 caller 0: `EMBEDDING_DIMS` / `validate_embedding_blob` の外部 import なし) | 6 commits | 1 author | existing |
| `scripts/db/tool_results.py` | silent fallback に audit event 追加 | low (`agent/context.py` のみが import) | 6 commits | 1 author | existing |
| `scripts/db/create_schema.py` | migration error 分類、`schema_version` DDL、旧テーブル DROP | medium (`migrate.py` が import; デプロイ後の一回実行スクリプト) | 6 commits | 1 author | existing |
| `scripts/db/migrate.py` | named columns コピー、`MigrationReport` dataclass、schema 互換性チェック | low (stand-alone スクリプト; 外部 import なし) | 6 commits | 1 author | existing |
| `config/common.toml` | `embedding_dims = 384` 追加 | low (追加のみ) | — | — | existing |
| `docs/06_ref-sqlite.md` | API 変更箇所の反映 | doc only | — | — | — |
| `tests/test_sqlite_helper.py` | `_cfg` グローバルのモック削除、class-level reset | test only | — | — | — |
| `tests/test_db_maintenance.py` | `RecoveryResult`, `MemoryDeleteStore` 追加テスト | test only | — | — | — |
| `tests/test_tool_result_store.py` | audit event 追加に対応 | test only | — | — | — |
| `tests/test_create_schema.py` | `schema_version` テーブル確認テスト | test only | — | — | — |

---

## Design

### D1. helper.py — module-level global 廃止

**Before:**
```python
_cfg: dict[str, Any] | None = None  # module-level

def _get_cfg() -> dict[str, Any]:
    global _cfg
    if _cfg is None:
        _cfg = ConfigLoader().load("common.toml")
    return _cfg

class SQLiteHelper:
    @classmethod
    def _ensure_config(cls) -> None:
        if cls._config_loaded:
            return
        cfg = _get_cfg()   # module-level 経由
        cls._RAG_PATH = cfg.get(...)
```

**After:**
```python
# module-level _cfg, _get_cfg() 削除

class SQLiteHelper:
    @classmethod
    def _ensure_config(cls) -> None:
        if cls._config_loaded:
            return
        try:
            cfg = ConfigLoader().load("common.toml")  # 直接呼び出し
        except Exception as e:
            logger.warning(f"Config load failed: {e}")
            cfg = {}
        cls._RAG_PATH = cfg.get("rag_db_path", "")
        cls._SESSION_PATH = cfg.get("session_db_path", "")
        cls.SQLITE_VEC_SO = cfg.get("sqlite_vec_so", "")
        cls._config_loaded = True
```

class-level `_config_loaded` フラグによる重複呼び出し防止は維持する。module scope からの状態を class scope に集約する変更のみ。

### D2. store.py — embedding_dims 設定化

```python
# Before:
EMBEDDING_DIMS: int = 384
EMBEDDING_BYTES: int = EMBEDDING_DIMS * 4

# After:
def get_embedding_dims() -> int:
    """Return embedding dimensions from config; fallback to 384."""
    try:
        cfg = ConfigLoader().load("common.toml")
        return int(cfg.get("embedding_dims", 384))
    except Exception:
        return 384

def get_embedding_bytes() -> int:
    return get_embedding_dims() * 4

# 後方互換用モジュール定数 (テスト・呼び出し元が参照している場合のみ残す)
# 現状外部 caller が 0 のため削除可
```

`validate_embedding_blob` も `get_embedding_dims()` 呼び出しに変更する。

### D3. store.py — MemoryDeleteStore Protocol + 実装

```python
@runtime_checkable
class MemoryDeleteStore(Protocol):
    """Atomic cross-table deletion for memories / memories_fts / memories_vec."""

    def delete_memories_before(
        self,
        older_than_days: int,
    ) -> "MemoryDeleteResult": ...

@dataclass(frozen=True)
class MemoryDeleteResult:
    deleted: int
    vec_skipped: bool      # memories_vec 削除が失敗した場合 True
    vec_error: str | None  # 失敗時のエラーメッセージ

class SQLiteMemoryDeleteStore:
    def __init__(self, db: SQLiteHelper) -> None:
        self._db = db

    def delete_memories_before(self, older_than_days: int) -> MemoryDeleteResult:
        rows = self._db.fetchall(...)
        # memories + memories_fts を削除 (atomic)
        # memories_vec を試みる; 失敗は MemoryDeleteResult.vec_skipped=True で返す
```

### D4. maintenance.py — prune_old_memories 委譲

```python
def prune_old_memories(db: SQLiteHelper, older_than_days: int) -> int:
    store = SQLiteMemoryDeleteStore(db)  # db/store.py の実装
    result = store.delete_memories_before(older_than_days)
    if result.vec_skipped:
        # 失敗を audit event で記録 (silent suppress ではなく visible)
        logger.warning(
            "prune_old_memories: memories_vec deletion failed",
            extra={"error": result.vec_error, "days": older_than_days},
        )
    logger.info(f"prune_old_memories: removed {result.deleted} entries")
    return result.deleted
```

### D5. maintenance.py — recover_corruption 構造化

```python
@dataclass(frozen=True)
class RecoveryResult:
    success: bool
    action: str        # "vacuum" | "restored" | "no_backup" | "error"
    detail: str | None = None
    dry_run: bool = False

def recover_corruption(
    backup_path: str | Path | None = None,
    *,
    dry_run: bool = False,
) -> RecoveryResult:
    ...
    if dry_run:
        return RecoveryResult(success=False, action="dry_run", detail="integrity check only", dry_run=True)
    ...
```

### D6. create_schema.py — migration error 分類

```python
_SAFE_MIGRATION_ERRORS: tuple[str, ...] = (
    "duplicate column name",   # ALTER TABLE ADD COLUMN が既適用
    "already exists",          # CREATE TRIGGER IF NOT EXISTS の余剰
)

def _run_migrations(db: SQLiteHelper, stmts: list[str]) -> None:
    for stmt in stmts:
        try:
            db.execute(stmt)
        except Exception as e:
            msg = str(e).lower()
            if any(safe in msg for safe in _SAFE_MIGRATION_ERRORS):
                logger.debug(f"Migration stmt skipped (already applied): {e}")
            else:
                logger.error(f"Migration DDL failed: {e!r}")
                raise  # 安全ではない失敗は re-raise
    db.commit()
```

### D7. migrate.py — named columns コピー

```python
@dataclass(frozen=True)
class TableMigrationResult:
    table: str
    rows_copied: int
    skipped: bool        # source table が存在しない
    error: str | None    # エラーメッセージ

@dataclass(frozen=True)
class MigrationReport:
    tables: list[TableMigrationResult]
    total_rows: int
    post_migration_actions: list[str]  # "re-embed memories_vec" など

def _get_column_names(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [row[1] for row in rows]

def _copy_table(...) -> TableMigrationResult:
    src_cols = _get_column_names(src_conn, table)
    dst_cols = _get_column_names(dst_conn, table)
    # 共通列のみコピー (schema diff を検出・ログ)
    common_cols = [c for c in src_cols if c in dst_cols]
    cols_str = ", ".join(common_cols)
    placeholders = ", ".join("?" * len(common_cols))
    rows = src_conn.execute(f"SELECT {cols_str} FROM {table}").fetchall()
    dst_conn.executemany(
        f"INSERT OR IGNORE INTO {table} ({cols_str}) VALUES ({placeholders})",
        rows,
    )
    return TableMigrationResult(table=table, rows_copied=len(rows), skipped=False, error=None)
```

---

## Implementation Steps

各ステップは独立してコミット可能。

### Step 1: テスト行動ロック (behavior-lock tests)

対象モジュールに既存テストがある (`test_sqlite_helper.py` 51行, `test_db_maintenance.py` 340行, `test_tool_result_store.py` 182行, `test_create_schema.py` 196行)。

事前にフルスイートをグリーンにしてベースラインを確立する:

```bash
source .venv/bin/activate && python -m pytest tests/test_sqlite_helper.py tests/test_db_maintenance.py tests/test_tool_result_store.py tests/test_create_schema.py -v
```

### Step 2: helper.py + maintenance.py — module-level global 廃止

変更ファイル: `scripts/db/helper.py`, `scripts/db/maintenance.py`

- `helper.py`: `_cfg`, `_get_cfg()` 削除。`_ensure_config()` に ConfigLoader 呼び出しをインライン化。
- `maintenance.py`: 同様に `_cfg`, `_get_cfg()` 削除。`RetentionConfig.from_config()`、`checkpoint_wal()`、`_archive_db_file()` で都度 ConfigLoader を呼ぶ。

完了条件: `test_sqlite_helper.py`, `test_db_maintenance.py` pass。

### Step 3: common.toml — embedding_dims 追加

変更ファイル: `config/common.toml`

- `embedding_dims = 384` を追加 (コメント付き)。

完了条件: toml parse 正常確認 (`python -c "import tomllib; tomllib.load(open('config/common.toml','rb'))"`)。

### Step 4: store.py — EMBEDDING_DIMS 設定化 + MemoryDeleteStore 追加

変更ファイル: `scripts/db/store.py`

- `EMBEDDING_DIMS = 384`, `EMBEDDING_BYTES` を削除し `get_embedding_dims()`, `get_embedding_bytes()` に置換。
- `validate_embedding_blob()` を新関数ベースに更新。
- `MemoryDeleteResult` dataclass, `MemoryDeleteStore` Protocol, `SQLiteMemoryDeleteStore` 実装を追加。

完了条件: lint-imports pass、mypy pass (store.py)。

### Step 5: maintenance.py — prune + recover 改修

変更ファイル: `scripts/db/maintenance.py`

- `prune_old_memories`: `SQLiteMemoryDeleteStore` へ委譲、audit event 追加。
- `recover_corruption`: `RecoveryResult` dataclass 返り値、`dry_run=False` パラメータ追加。

完了条件: `test_db_maintenance.py` pass (新テスト追加込み)。

### Step 6: tool_results.py — audit event 追加

変更ファイル: `scripts/db/tool_results.py`

- `store()` / `get()` / `list_recent()` の except ブロックを `logger.warning` から `logger.error` + 構造化ログに変更。
- REPL 継続優先は維持 (fail-open) だが、失敗を不可視にしない。

完了条件: `test_tool_result_store.py` pass。

### Step 7: create_schema.py — migration error 分類 + schema_version + 旧テーブル DROP

変更ファイル: `scripts/db/create_schema.py`

- `_run_migrations()` を `_SAFE_MIGRATION_ERRORS` による分類に更新。
- `_RAG_SCHEMA_SQL`, `_SESSION_SCHEMA_SQL` に `schema_version` テーブル DDL を追加。
- `_SESSION_MIGRATE_SQL` に `DROP TABLE IF EXISTS memory_entries`, `DROP TABLE IF EXISTS memory_vec` を追加 (最末尾)。
- embedding dims を `get_embedding_dims()` 経由で DDL 文字列に注入。

完了条件: `test_create_schema.py` pass。

### Step 8: migrate.py — named columns + MigrationReport

変更ファイル: `scripts/db/migrate.py`

- `_copy_table()` を named columns 版に置換。
- `MigrationReport`, `TableMigrationResult` dataclass 追加。
- `migrate()` が `MigrationReport` を返すよう変更。
- `memory_vec` の post-migration re-embed 必要性を `post_migration_actions` に明記。

完了条件: `python -m compileall -q scripts/db/migrate.py` pass、lint pass。

### Step 9: フルスイート検証

```bash
source .venv/bin/activate
ruff format scripts/db/
ruff check scripts/db/ --fix && ruff check scripts/db/
mypy scripts/
PYTHONPATH=scripts lint-imports
bandit -r scripts/db/ -c pyproject.toml
python -m pytest tests/ -v
```

### Step 10: ドキュメント更新

変更ファイル: `docs/06_ref-sqlite.md`

- `SQLiteHelper._ensure_config` の説明から module-level `_cfg` への参照を削除。
- `recover_corruption` のシグネチャ (`dry_run` パラメータ) を更新。
- `MigrationReport` の説明を追加。

### Step 11: デプロイ (本番反映)

`/deploy` スキルを使用。`create_schema.py` の実行が必要な場合はデプロイ後に一回実行する。

---

## Validation Plan

| Check | Tool | Target |
|---|---|---|
| Format | `ruff format scripts/db/` | 差分なし |
| Lint | `ruff check scripts/db/` | 0 errors |
| Type check | `mypy scripts/` | 新規エラーなし |
| Architecture | `PYTHONPATH=scripts lint-imports` | 0 violations (現状 4 kept 維持) |
| Constraint | `ast-grep --pattern 'except: $$$'` | 0 bare except |
| Security | `bandit -r scripts/db/ -c pyproject.toml` | HIGH/MEDIUM なし |
| Tests | `pytest tests/test_sqlite_helper.py tests/test_db_maintenance.py tests/test_tool_result_store.py tests/test_create_schema.py -v` | all pass |
| Full suite | `pytest -v` | 新規失敗なし |
| Coverage | `diff-cover coverage.xml --compare-branch=main` | ≥ 90% on changed lines |
| Pre-commit | `pre-commit run --all-files` | pass |

---

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `SQLiteHelper._config_loaded` class-level cache がテスト間で汚染される | high | テスト side-effect は現在 `test_sqlite_helper.py` で mock 管理済み。`_ensure_config` 変更後も同様にリセット処理を確認する |
| `_run_migrations` の safe/unsafe 分類ミスにより既適用済みの DDL が ERROR になる | medium | `_SAFE_MIGRATION_ERRORS` を実際の SQLite エラーメッセージに対して test_create_schema.py でカバーテストを追加する |
| `MemoryDeleteStore.delete_memories_before` が旧テスト環境 (sqlite-vec なし) でエラーになる | low | memories_vec 削除失敗は `vec_skipped=True` で返す設計なので、vec0 なし環境でも safe |
| `recover_corruption` の `dry_run` パラメータ追加が呼び出し元 (`cmd_db.py`) の型エラーを引き起こす | low | `dry_run=False` はデフォルト値なので既存呼び出し元は変更不要 |
| `migrate.py` の named columns コピーが production 環境の古スキーマと不一致を起こす | medium | `_copy_table` の common_cols 計算で差分をログ出力。本番実行前に dry-run 同等の column diff ログを確認する |
| `create_schema.py` の旧テーブル DROP が production DB の `memory_entries` データを失う | low | `DROP TABLE IF EXISTS` は migration step。`memory_entries` は新メモリ層 (memories テーブル) に移行済みであることを事前確認してから実行する |
