# Issue: http_lifecycle.py - SIGINT handler not restored when ValueError occurs

## 概要

`shutdown_all()` でSIGINTハンドラを上書きする際、上書き直後（338行目）に `ValueError` が発生すると、元のハンドラが復元されない。

## 該当コード

`scripts/agent/http_lifecycle.py:335-341`

```python
old_sigint: object | None = None
try:
    old_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, self._absorb_sigint_during_shutdown)
except ValueError:
    # Not on the main thread — proceed without the guard rather than fail shutdown.
    old_sigint = None
```

`finally` ブロック（370-372行目）:

```python
finally:
    if old_sigint is not None:
        signal.signal(signal.SIGINT, old_sigint)
```

## 問題点

- `signal.getsignal(signal.SIGINT)` が成功し、`old_sigint` に値が代入された後
- `signal.signal(signal.SIGINT, handler)` で例外（`ValueError`）が発生
- `except ValueError:` ブロックで `old_sigint = None` が実行される
- `finally` ブロックで `if old_sigint is not None:` が False になり、元のハンドラが復元されない
- シグナルハンドラが吸着されたままになる

## 再現シナリオ

1. `signal.getsignal(signal.SIGINT)` が成功（main thread 以外ではない）
2. `signal.signal(signal.SIGINT, handler)` が `ValueError` を投げる（まれなケース）
3. `old_sigint = None` が設定される
4. 元のシグナルハンドラが失われる

## 改善案

- `getsignal` と `signal` の呼び出しを別々のtry/exceptに分ける
- または、`getsignal` の結果をローカル変数に保存した直後に例外が発生しないことを保証する

```python
old_sigint = signal.getsignal(signal.SIGINT)  # This can't raise ValueError
try:
    signal.signal(signal.SIGINT, self._absorb_sigint_during_shutdown)
except ValueError:
    # Not on the main thread — proceed without the guard
    pass  # old_sigint is already saved, will be restored in finally
```

## 優先度

低 - `getsignal` が `ValueError` を投げるのは稀だが、シグナルハンドラの喪失は重大
