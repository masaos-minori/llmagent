# MCPサーバー起動処理 — プロセスグループPIDリーク（getpgid失敗時）

**重大度:** CRITICAL
**関連ファイル:** `scripts/agent/http_lifecycle.py:290-323`

## 概要

`os.getpgid()` が `OSError` を発生させた場合、プロセスグループIDの取得に失敗するが、その後のクリーンアップでstderrファイルハンドルが閉じられない。

## 詳細

```python
self._http_pgids[server_key] = os.getpgid(proc.pid)
except OSError:
    # ... cleanup ...
    self._http_procs.pop(server_key, None)
    self._http_pgids.pop(server_key, None)
```

`os.getpgid()` の例外処理で `_http_procs` と `_http_pgids` は削除されるが、`stderr_fh` が閉じられない。ファイルディスクリプタがリークする。

また、行299で `proc.poll()` が `None` を返す場合（terminate/kill後もプロセスが生きている）、プロセスはゾンビとして残る。警告ログは出力されるが、再度 kill されない。

## 影響

- ファイルディスクリプタのリーク → FD exhaustion
- ゾンビプロセスの残留 → リソース枯渇

## 修正案

1. `stderr_fh.close()` を finally ブロックで確実に実行
2. `proc.poll()` が `None` の場合、明示的に `proc.kill()` を呼び出す

## 関連ファイル

- `scripts/agent/http_lifecycle.py:290-323`
