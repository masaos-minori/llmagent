# Implementation: Phase A2 — _ContextFilter を contextvars ベースに移行

## Goal

`shared/logger.py` の `_ContextFilter._fields` をスレッド共有 dict から
`contextvars.ContextVar` ベースの task-local 管理に変更し、
asyncio の並行ターン実行でコンテキストフィールドが混在しないようにする。

## Scope

**In**: `scripts/shared/logger.py` の `_ContextFilter` クラスのみ
**Out**: `Logger` クラスの公開 API（`set_context/clear_context`）は変更しない

## Assumptions

1. `_ContextFilter` は `Logger` インスタンスに 1 対 1 で紐付く。
2. asyncio はシングルスレッドだが `asyncio.create_task()` 等で並行するコルーチンが
   同一 `Logger` を使う場合、`set_context` → await → 他コルーチンの `set_context`
   → clear_context の順で呼ばれると値が上書きされる。
3. `contextvars.ContextVar` は asyncio タスク境界でコピーされるため、
   タスクごとに独立したコンテキストが維持される。
4. Python 3.13 では `contextvars` はデフォルトで使用可能。

## Implementation

### Target file

`scripts/shared/logger.py`

### Procedure

1. `from contextvars import ContextVar` を import に追加。
2. `_ContextFilter` の `_fields: dict` を `_cv: ContextVar[dict]` に置き換え。
3. `set()`、`clear()`、`filter()` を ContextVar API で実装。

### Method

```python
# 変更前
class _ContextFilter(logging.Filter):
    def __init__(self) -> None:
        super().__init__()
        self._fields: dict[str, Any] = {}

    def set(self, **fields: Any) -> None:
        self._fields = {k: v for k, v in fields.items() if v is not None}

    def clear(self) -> None:
        self._fields = {}

    def filter(self, record: logging.LogRecord) -> bool:
        for k, v in self._fields.items():
            setattr(record, k, v)
        return True

# 変更後
from contextvars import ContextVar

class _ContextFilter(logging.Filter):
    def __init__(self) -> None:
        super().__init__()
        self._cv: ContextVar[dict[str, Any]] = ContextVar(
            "_log_context", default={}
        )

    def set(self, **fields: Any) -> None:
        self._cv.set({k: v for k, v in fields.items() if v is not None})

    def clear(self) -> None:
        self._cv.set({})

    def filter(self, record: logging.LogRecord) -> bool:
        for k, v in self._cv.get().items():
            setattr(record, k, v)
        return True
```

### Details

- `_cv` は `_ContextFilter` インスタンスごとに作成される。
- `ContextVar.get()` はタスクローカルな値を返すため、並行コルーチン間で独立。
- `Token` による restore は不要（`set_context` → `clear_context` の明示的ライフサイクル）。

## Validation plan

1. `uv run ruff check scripts/shared/logger.py`
2. `uv run mypy scripts/shared/logger.py`
3. `uv run pytest -q` — no regressions
