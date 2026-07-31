# MCPサーバー起動処理 — SIGINTハンドラ競合（シャットダウン時）

**重大度:** HIGH
**関連ファイル:** `scripts/agent/http_lifecycle.py:421-438`

## 概要

`signal.signal()` が `ValueError` を発生させた場合、元のシグナルハンドラが復元されない。非メインスレッドからの呼び出しで発生する可能性あり。

## 詳細

```python
old_sigint = signal.getsignal(signal.SIGINT)
if old_sigint is not None:
    try:
        signal.signal(signal.SIGINT, self._absorb_sigint_during_shutdown)
    except ValueError as exc:
        logger.debug(...)
```

`signal.signal()` が失敗した場合:
1. `old_sigint` はまだセットされたまま
2. finallyブロックで `signal.signal(signal.SIGINT, old_sigint)` が呼ばれる
3. 新しいハンドラがインストールされている可能性があり、上書きされる

さらに、`signal.getsignal()` が `None` を返す場合（デフォルトハンドラが既に置き換えられている）、`signal.signal(signal.SIGINT, None)` は無効な呼び出しとなる。

## 影響

- シグナルハンドラの破損
- Ctrl-Cの意図しない動作
- シャットダウンの不完全

## 修正案

1. `signal.signal()` の失敗時は `old_sigint` もクリアする
2. `old_sigint` が `None` の場合は復元しない

## 関連ファイル

- `scripts/agent/http_lifecycle.py:421-438`
