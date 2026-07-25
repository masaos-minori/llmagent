# Issue: session.py - DiagnosticStore uses stale session_id set at construction

## 概要

`AgentSession.__init__()` で `DiagnosticStore(self.session_id)` が初期化されるとき、`self.session_id` はまだ `None`。その後の `save_diagnostic()` 呼び出しで、`DiagnosticStore.save()` は内部に保持した `session_id=None` を使用するため、診断データが正しく保存されない可能性がある。

## 該当コード

`scripts/agent/session.py:33`

```python
class AgentSession:
    def __init__(self, *, strict_mode: bool = False) -> None:
        self.session_id: int | None = None  # current session DB row ID
        self._strict_mode = strict_mode
        self._title_pending: bool = False
        self._message_repo = SessionMessageRepository(
            self.session_id, strict_mode=strict_mode
        )
        self._diagnostic_store = DiagnosticStore(self.session_id)  # session_id is None here
```

`replace_messages()` では明示的にチェックがある（59-63行目）:

```python
def replace_messages(self, messages: list[LLMMessage]) -> None:
    if self.session_id is None:
        logger.warning(
            "replace_messages called before session.start(); skipping persist"
        )
        return
```

しかし `save_diagnostic()` には同様のガードがない。

## 問題点

- `DiagnosticStore.save()` が `session_id=None` の状態で呼ばれると、どのセッションに属する診断データか不明
- `replace_messages()` のようなガードがないため、警告なしで無視される可能性
- セッション開始前に `save_diagnostic()` が呼ばれると、データが破棄される

## 改善案

- `save_diagnostic()` に `replace_messages()` と同様のガードを追加
- または、`DiagnosticStore` の session_id をプロパティとして動的に取得するように変更

## 優先度

低 - セッション開始前の診断データの保存は稀だが、データ消失の原因となる
