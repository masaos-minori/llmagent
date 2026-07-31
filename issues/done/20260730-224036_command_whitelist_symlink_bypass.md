# MCPサブプロセスの起動コマンドホワイトリストがシンボリックリンクを回避できる

## Summary

`_ALLOWED_COMMANDS` のチェックは `cfg.cmd[0]` の basename のみを比較するため、シンボリックリンク経由の不正コマンド実行が可能。`os.path.realpath()` でシンボリックリンクを解決してからホワイトリストをチェックする必要がある。また、`cfg.cmd[0]` が空の場合、プロセスが開始されないがエラーは投げられない（静かな失敗）。

## Severity

High

## Confidence

High

## Evidence

- `agent/http_lifecycle.py:66-68` — `_ALLOWED_COMMANDS = frozenset({"node", "npm", "npx", "uvx", "python", "pipx"})`
- `agent/http_lifecycle.py:268-275` — `cmd_basename = os.path.basename(cfg.cmd[0])` のみがチェックされる
- `agent/http_lifecycle.py:269-275` — `cmd_basename not in self._ALLOWED_COMMANDS` が True の場合、ログ出力のみでプロセスが開始されない（`return` する）

## Current behavior

`cfg.cmd[0]` が `/usr/local/bin/python` のような絶対パスの場合、basename は `python` なので許可される。しかし、`cfg.cmd[0]` がシンボリックリンクの場合、basename は一致するが実際のバイナリは異なる可能性がある。また、`cfg.cmd[0]` が空文字列の場合、`cmd_basename not in self._ALLOWED_COMMANDS` が True になりログ出力のみでプロセスが開始されない（静かな失敗）。

## Impact

- シンボリックリンク経由の不正コマンド実行
- `cfg.cmd[0]` が空の場合、プロセスが開始されないがエラーは投げられない（静かな失敗）

## Recommended action

- `os.path.realpath()` でシンボリックリンクを解決してからホワイトリストをチェックする
- `cfg.cmd[0]` が空の場合は `HttpStartupError` を投げる

## Suggested Tests

- **Test target:** `agent/http_lifecycle.py::HttpServerLifecycleManager.start()`
- **Behavior to verify:** シンボリックリンク経由のコマンドがホワイトリストでブロックされること
- **Failure mode:** シンボリックリンクがホワイトリストのバイナリを指している場合、不正なコマンドが実行される
