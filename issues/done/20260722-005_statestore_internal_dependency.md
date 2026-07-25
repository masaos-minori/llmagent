# StateStore内部実装への依存

## 深刻度: 低

## 概要

`StartupOrchestrator._recover_pending_approvals()` で `store._db` に直接アクセスしている。
`StateStore` の内部実装が変わると壊れる。

## 該当コード

`scripts/agent/startup.py:303-329`

```python
async def _recover_pending_approvals(self) -> None:
    store = StateStore()
    try:
        result = find_latest_pending_approval(store._db)
    finally:
        store.close()
```

## 問題の詳細

1. `StateStore` は公開API経由でDBにアクセスすべき
2. `_db` はプライベート属性（アンダースコア1つ）であり、内部実装の詳細
3. `StateStore` の内部実装が変わると、このコードは壊れる
4. また、`find_latest_pending_approval()` が複数の保留中承認を返す可能性があり、
   **最後のものだけが復旧される**（最初のものが失われる）

## 影響

- `StateStore` の内部実装変更で起動時に承認が復旧されない
- 複数の保留中承認がある場合、最初の承認が失われる

## 修正案

```python
async def _recover_pending_approvals(self) -> None:
    store = StateStore()
    try:
        # Use public API instead of internal attribute
        db_conn = store.get_connection()
        result = find_latest_pending_approval(db_conn)
    finally:
        store.close()
```

`StateStore` に `get_connection()` メソッドを追加:

```python
class StateStore:
    def get_connection(self):
        """Return the underlying DB connection for external queries."""
        return self._db
```
