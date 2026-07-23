---
title: "Memory injection during startup silently swallows all exceptions"
severity: Medium
confidence: High
status: new
created: 20260723-200000
---

## Title

Memory injection during startup silently swallows all exceptions

## Severity

Medium

## Confidence

High

## Evidence

- `startup.py:485-511` — StartupOrchestrator._setup_prompt() memory injection

## Current Behavior

`_setup_prompt()`でメモリインジェクションが失敗した場合、`Exception`をキャッチし、WARNINGログとCLI表示のみを行う。**メモリが起動時に失敗した場合、セッション全体でメモリ機能が無効化される可能性があり、その旨の明示的な通知がない**。

## Impact

ユーザーはセッションを通じてメモリ機能が無効になっていることに気づかない。

## Recommended Action

メモリインジェクションの失敗時に、フラグを設定し、以降のターンでも警告を表示する。

## Related Files

- scripts/agent/startup.py
