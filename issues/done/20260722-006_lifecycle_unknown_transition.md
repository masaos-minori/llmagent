# LIFECYCLE STATEのUNKNOWN→STARTING遷移の有効性確認欠如

## 深刻度: 低

## 概要

`LifecycleManager` の `_states` が空の辞書で初期化され、サーバーが起動前に
`get_transport_state()` を呼ぶと `LifecycleState.UNKNOWN` が返る。
`UNKNOWN→STARTING` 遷移が有効かどうかの確認がない。

## 該当コード

`scripts/agent/factory.py:63`

```python
self._states: dict[str, LifecycleState] = {}
```

## 問題の詳細

1. `LifecycleManager.__init__()` で `_states` が空の辞書で初期化される
2. サーバーが起動前に `get_transport_state(key)` を呼ぶと、キーが存在しないため
   `LifecycleState.UNKNOWN` が返る
3. `assert_valid_transition(LifecycleState.UNKNOWN, LifecycleState.STARTING)` は警告のみ出力
4. 遷移が有効かどうかのチェックはなく、無条件で状態が更新される
5. これは意図的かもしれないが、明示的なドキュメントがない

## 影響

- UNKNOWN→STARTING遷移が有効かどうか不明
- 予期せぬ状態遷移が発生する可能性がある
- デバッグ時に状態遷移の履歴を追えない

## 修正案

```python
def get_transport_state(self, key: str) -> LifecycleState:
    state = self._states.get(key)
    if state is None:
        # New server — start from STARTING directly
        logger.info("No previous state for %s; starting from STARTING", key)
        return LifecycleState.STARTING
    return state

def set_transport_state(self, key: str, new_state: LifecycleState) -> None:
    old_state = self._states.get(key)
    if old_state is not None:
        assert_valid_transition(old_state, new_state)
    else:
        # First time seeing this server — allow any initial state
        pass
    self._states[key] = new_state
```
