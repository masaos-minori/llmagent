# shutdown_all()中のSIGINTシグナルハンドラ消失

## 深刻度: 中程度

## 概要

`McpServerLifecycle.shutdown_all()` でSIGINTシグナルハンドラを上書きしようとした際、
`ValueError` が発生するとシグナルハンドラをインストールしないため、SIGINTが失われる。

## 該当コード

`scripts/agent/http_lifecycle.py:335-347`

```python
old_sigint = signal.getsignal(signal.SIGINT)
if old_sigint is not None:
    try:
        signal.signal(signal.SIGINT, self._absorb_sigint_during_shutdown)
    except ValueError:
        old_sigint = None
```

## 問題の詳細

1. `shutdown_all()` 実行中にSIGINTを受信すると、メインスレッド以外からシグナルハンドラ変更を試みる
2. `signal.signal()` はメインスレッドからのみ呼び出せるため、`ValueError` を発生
3. `except ValueError:` で `old_sigint = None` に設定し、シグナルハンドラをインストールしない
4. この場合、SIGINTが何も処理されずにプロセスを終了させる
5. `finally` ブロックで `signal.signal(signal.SIGINT, old_sigint)` を呼ぶが、`old_sigint` がNoneのため
   「シグナルハンドラをNoneに戻す」という意味不明な状態になる

## 影響

- MCPサーバーシャットダウン中にCtrl+Cを押すと、シグナルが失われ
  プロセスが異常終了する可能性がある
- シャットダウンのグラースフルな完了が期待されるが、シグナルが失われるため
  プロセスが即座に終了する

## 修正案

```python
old_sigint = signal.getsignal(signal.SIGINT)
if old_sigint is not None:
    try:
        signal.signal(signal.SIGINT, self._absorb_sigint_during_shutdown)
    except ValueError:
        # Not main thread; cannot install handler.
        # Keep original handler intact.
        pass
```
