# MCPサーバー起動処理 — ヘルスチェック中の早期プロセス終了でファイルハンドルリーク

**重大度:** LOW
**関連ファイル:** `scripts/agent/http_lifecycle.py:333-336`

## 概要

プロセスがヘルスチェック中に早く終了した場合、ファイルハンドルのクリーンアップは正しく行われるが、同じロジックがタイムアウトパスにも重複している。保守性の観点から懸念。

## 詳細

```python
if proc.poll() is not None:
    stderr_full = self._read_stderr_tail(server_key)
    fh = self._stderr_files.pop(server_key, None)
    if fh is not None:
        fh.close()
    self._stderr_log_paths.pop(server_key, None)
```

このパスはファイルを閉じるが、行366-370のタイムアウトパスでも同様のコードが重複している。修正漏れのリスクがある。

## 影響

- 保守性の低下
- 将来的な修正漏れの可能性

## 修正案

1. クリーンアップロジックをメソッドに抽出して重複を排除
2. テストカバレッジで両パスをカバー

## 関連ファイル

- `scripts/agent/http_lifecycle.py:333-336`
- `scripts/agent/http_lifecycle.py:366-370`
