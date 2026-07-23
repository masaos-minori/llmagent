---
title: "ensure_ready() cooldown window allows silent tool call failures"
severity: Medium
confidence: High
status: new
created: 20260723-200000
---

## Title

ensure_ready() cooldown window allows silent tool call failures

## Severity

Medium

## Confidence

High

## Evidence

- `factory.py:111-140` — _ServerLifecycleRouter.ensure_ready()
- `factory.py:94-109` — _ServerLifecycleRouter._in_cooldown()

## Current Behavior

`ensure_ready()`でMCPサブプロセスが起動されていない場合、`_in_cooldown()`がTrueの場合、**何もしないでreturnする**。つまり、ツール呼び出しが失敗しても、30秒間は再試行が行われず、ユーザーには「tool not available」のエラーが表示されるだけ。

## Impact

一時的なネットワーク障害などでMCPサブプロセスが再起動中の際、30秒間すべてのツール呼び出しが失敗する。

## Recommended Action

コールドダウン中のツール呼び出しに対して、より良いエラーメッセージ（例：「Server restarting, try again in X seconds」）を提供する。

## Related Files

- scripts/agent/factory.py
