# Issue: repl_health.py - check_workflow_schema opens DB with write_mode=False but never writes

## 概要

`check_workflow_schema()` はワークフローDBのスキーマ検証を行うが、`write_mode=False` でDBを開いている。関数名と引数の組み合わせが直感的ではなく、誤って書き込みモードに変更するとスキーマ検証以外の操作が行われる可能性がある。

## 該当コード

`scripts/agent/repl_health.py:323-362`

```python
def check_workflow_schema(db_path: str | None = None) -> None:
    """Raise RuntimeError if the workflow DB is missing required tables or columns."""
    from db.helper import SQLiteHelper  # noqa: PLC0415
    from db.schema_sql import WORKFLOW_SCHEMA_VERSION  # noqa: PLC0415

    db = SQLiteHelper(target="workflow", db_path=db_path)
    db.open(write_mode=False, row_factory=False)  # ← write_mode=False
    try:
        tables = {
            row[0]
            for row in db.fetchall(
                "SELECT name FROM sqlite_master WHERE type='table'", ()
            )
        }
        # ... read-only queries follow
    finally:
        db.close()
```

## 問題点

- `write_mode=False` は読み取り専用だが、関数名には「schema」とあり、スキーマ変更を連想させる
- `write_mode=True` に誤って変更すると、スキーマ検証とは無関係な書き込みが可能になる
- ローカル変数 `db_path` が `None` の場合、デフォルトのワークフローDBパスが使用されるが、そのパスが存在しない場合は例外が発生する
- 例外ハンドリングがないため、DBファイルが存在しない場合は起動が完全に失敗する

## 改善案

- `write_mode=False` を定数や名前付き引数として明示化する
- DBファイルが存在しない場合のフォールバックまたは警告を追加
- スキーマ検証の結果を返すようにし、呼び出し側で判断できるようにする

```python
WORKFLOW_DB_READONLY = True

def check_workflow_schema(db_path: str | None = None) -> None:
    db = SQLiteHelper(target="workflow", db_path=db_path)
    db.open(write_mode=WORKFLOW_DB_READONLY, row_factory=False)
    # ...
```

## 優先度

低 - 現在も正しく動作しているが、保守性が低い
