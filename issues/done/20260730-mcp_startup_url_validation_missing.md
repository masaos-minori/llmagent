# MCPサーバー起動処理 — URL検証なしでのヘルスチェック

**重大度:** MEDIUM
**関連ファイル:** `scripts/agent/http_lifecycle.py:180, 326`; `scripts/agent/startup.py:187`

## 概要

`cfg.url` が空または不正な場合、結果のURLが `"http:///health"` のようになり、DNS解決エラーとして失敗する。明確な設定バリデーションエラーではない。

## 詳細

```python
url = cfg.url.rstrip("/") + "/health"
```

`cfg.url` が `"http://"` の場合 → `"http:///health"`
`cfg.url` が空の場合 → `"/health"`

どちらも DNS解決エラーとして失敗し、原因が分かりにくい。

## 影響

- 設定ミスの検出が遅れる
- エラーメッセージが曖昧

## 修正案

1. `cfg.url` の形式を検証するバリデーションを追加
2. 不正なURLの場合は起動前に明確なエラーメッセージを出力

## 関連ファイル

- `scripts/agent/http_lifecycle.py:180`
- `scripts/agent/http_lifecycle.py:326`
- `scripts/agent/startup.py:187`
