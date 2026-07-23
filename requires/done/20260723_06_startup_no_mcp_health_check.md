---
title: "Startup readiness check doesn't verify MCP subprocess health after startup"
severity: Medium
confidence: High
status: new
created: 20260723-200000
---

## Title

Startup readiness check doesn't verify MCP subprocess health after startup

## Severity

Medium

## Confidence

High

## Evidence

- `startup.py:122-157` — StartupOrchestrator._check_services()
- `startup.py:194-305` — StartupOrchestrator._start_servers()

## Current Behavior

`_start_servers()`でHTTP subprocess MCPサーバーの起動は試みられるが、**起動後のヘルスチェックは行われない**。`_check_services()`で`check_readiness()`が呼ばれるが、これはLLM/Embedサービスのヘルスチェックのみを行い、MCPサーバーのヘルスは含まない。MCPサーバーのヘルスチェックは`_collect_server_tool_names()`で行われるが、これはツール名の収集が目的であり、ヘルスチェックではない。

## Impact

MCPサブプロセスが起動したがヘルスチェックに失敗した場合、ツール発見は失敗するが、エラーメッセージは「unreachable during discovery」だけで、実際の障害内容（例：ポート競合、内部エラー）はわからない。

## Recommended Action

`_start_servers()`の成功後に、起動した各サーバーに対して個別のヘルスチェックを追加する。

## Related Files

- scripts/agent/startup.py
