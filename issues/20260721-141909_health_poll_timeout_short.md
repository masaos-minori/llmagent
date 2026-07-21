# Issue: http_lifecycle.py - Health poll timeout too short for slow-starting servers

## 概要

HTTP MCPサーバーのヘルスチェックポーリングで、1リクエストあたりのタイムアウトが2秒と短すぎる。サーバーの起動が遅い場合、全体の起動タイムアウト内でもヘルスチェックが失敗する。

## 該当コード

`scripts/agent/http_lifecycle.py:249`

```python
async with httpx.AsyncClient(timeout=2.0) as client:
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            # ... early exit handling
        try:
            resp = await client.get(health_url)
            if resp.status_code == HTTPStatus.OK:
                return
        except (httpx.HTTPError, OSError) as e:
            logger.debug(...)
        await asyncio.sleep(0.5)
```

## 問題点

- `timeout=2.0` は1回のリクエストのタイムアウト
- サーバーの起動が遅く、最初のヘルスチェックが2秒以内に完了しない場合、`httpx.HTTPError` が発生
- ポーリング間隔は0.5秒なので、合計で `cfg.startup_timeout_sec` 秒まで試行できるが、各リクエストが2秒でタイムアウトするのは不自然
- サーバーの起動に1〜3秒かかる環境では、最初の数回のヘルスチェックが常にタイムアウトする

## 再現シナリオ

1. `startup_timeout_sec = 30` を設定
2. サーバーの起動に2.5秒かかる
3. 最初のヘルスチェックが2秒でタイムアウト → `httpx.HTTPError`
4. 2回目のヘルスチェックも同様にタイムアウト
5. サーバーが実際に起動しているのに、タイムアウトによる false negative

## 改善案

- `timeout` をより現実的な値（5〜10秒）に引き上げる
- または、`timeout=httpx.Timeout(connect=5.0, read=5.0)` など、connect/readを分離
- タイムアウト時のログレベルを DEBUG から INFO に上げて、運用者が気づけるようにする

## 優先度

中 - 起動の遅いサーバーでfalse negativeが発生する可能性がある
