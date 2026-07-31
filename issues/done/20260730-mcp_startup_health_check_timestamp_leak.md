# MCPサーバー起動処理 — ヘルスチェックタイムスタンプのメモリリーク

**重大度:** LOW
**関連ファイル:** `scripts/agent/http_lifecycle.py:173`

## 概要

`_last_health_check` に格納されたタイムスタンプは、サーバーキーが動的に削除された場合（ホットリロードなど）、残ったままになる。

## 詳細

```python
last_check = self._last_health_check.get(server_key, 0.0)
```

`shutdown_all()` と `restart()` でクリアされるが、サーバーキーの設定削除時はクリアされない。

## 影響

- メモリのわずかな増加
- サーバー数に比例した上限あり

## 修正案

1. サーバーキーの削除時に `_last_health_check` もクリアする
2. GC対象となるように weakref を検討

## 関連ファイル

- `scripts/agent/http_lifecycle.py:173`
