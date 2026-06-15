# Implementation: Phase A2 — migrate_schema() 関数削除

## Goal

`scripts/db/create_schema.py` の `migrate_schema()` 関数（L198-211）を削除する。
この関数は "Add COLUMN" の ALTER TABLE 試行による incremental migration であり、
要望書の「旧スキーマ救済コード」にあたる。

## Scope

**In**: `scripts/db/create_schema.py` の `migrate_schema()` 関数のみ
**Out**: `IF NOT EXISTS` は維持（idempotent re-runs のための意図的設計）

## Assumptions

1. `migrate_schema()` の呼び出し元が存在しないことを `rg` で確認してから削除する。
2. `IF NOT EXISTS` は `create_schema.py:5` コメント "Existing tables are protected
   by IF NOT EXISTS for idempotent re-runs." の通り、意図的に維持する。
3. 削除対象は L198-211 の関数本体のみ。

## Implementation

### Target file

`scripts/db/create_schema.py`

### Procedure

1. `rg "migrate_schema" scripts/` で呼び出し元を確認
2. 呼び出し元が 0 件であれば関数本体を削除
3. lint/type チェック

### Method

```python
# 削除対象 (L198-211)
def migrate_schema(db_name: str = "rag") -> None:
    """Apply incremental schema migrations to an existing DB.

    Safe to call on an already-migrated DB — duplicate column errors are suppressed.
    """
    with SQLiteHelper(db_name).open(write_mode=True) as db:
        try:
            db.execute(
                "ALTER TABLE documents ADD COLUMN"
                " chunking_strategy TEXT NOT NULL DEFAULT 'text'"
            )
            db.commit()
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
```

### Details

この関数は "duplicate column name" エラーを無視してスキーマ差分を吸収する
rescue コードである。削除後は DB は正式な create_schema() から生成された
最新スキーマのみを持つ前提となる。

## Validation plan

1. `rg "migrate_schema" scripts/` → 0 件（関数定義も含めてヒットなし）
2. `ruff check scripts/db/create_schema.py` → 0 errors
3. `uv run mypy scripts/` → no new errors
4. `uv run pytest tests/test_create_schema.py -q` → all pass
