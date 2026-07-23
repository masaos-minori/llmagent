---
title: "MCP subprocess startup failure leaves orphaned processes"
severity: Critical
confidence: High
status: new
created: 20260723-200000
---

## Title

MCP subprocess startup failure leaves orphaned processes

## Severity

Critical

## Confidence

High

## Evidence

- `startup.py:62-78` — StartupOrchestrator.run() rollback path
- `http_lifecycle.py:200-306` — HttpServerLifecycleManager.start() health-poll

## Current Behavior

`_start_servers()`でHTTP subprocess MCPサーバーの起動に失敗した場合、productionモードでは`RuntimeError`が再送出される。`StartupOrchestrator.run()`のexcept節（69-78行目）で`shutdown_all()`が呼ばれるが、この`shutdown_all()`は`lifecycle.shutdown_all()`であり、既に成功した他のサブプロセスのみをシャットダウンする。既に成功したサブプロセスは正常に動作し続けるが、失敗したサブプロセスは**既に`_http_procs`にエントリが追加されている場合がある**（`http_lifecycle.py:256行目でprocが_http_procsに格納された後、health-poll失敗で例外送出）。

## Impact

特定のMCPサーバーの起動失敗時に、そのサブプロセスはオランザードとして残り、`/opt/llm/logs/mcp_servers/{key}.stderr.log`ファイルも開いたままになる。

## Recommended Action

`http_lifecycle.py:start()`で`_http_procs`への追加前にhealth-poll失敗を検出し、`_terminate_with_timeout()`を呼び出してクリーンアップする。または`startup.py:_start_servers()`のexcept節で`shutdown_all()`の前に各サーバーのstderrファイルを明示的に閉じる。

## Related Files

- scripts/agent/startup.py
- scripts/agent/http_lifecycle.py
