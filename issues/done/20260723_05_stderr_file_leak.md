---
title: "MCP subprocess stderr log file leak on early exit"
severity: High
confidence: High
status: new
created: 20260723-200000
---

## Title

MCP subprocess stderr log file leak on early exit

## Severity

High

## Confidence

High

## Evidence

- `http_lifecycle.py:227-255` — HttpServerLifecycleManager.start() stderr log opening

## Current Behavior

`start()`メソッドで`_open_stderr_log()`が呼ばれて`_stderr_files`にファイルハンドルが格納されるが、その後`os.getpgid()`が失敗した場合（`http_lifecycle.py:243-255`）、`_stderr_files`からファイルハンドルが削除されるものの、**ファイル自体は閉じられない**（`fh.close()`が呼ばれていない）。

## Impact

ファイルディスクリプタリーク。長時間稼働するエージェントで累積的にファイルディスクリプタを使い切る可能性がある。

## Recommended Action

`os.getpgid()`失敗時のクリーンアップパスで`fh.close()`を必ず呼び出す。

## Related Files

- scripts/agent/http_lifecycle.py
