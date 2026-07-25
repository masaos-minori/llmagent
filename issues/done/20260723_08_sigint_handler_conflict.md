---
title: "SIGINT handler installed twice when NotImplementedError fallback triggers"
severity: Medium
confidence: High
status: new
created: 20260723-200000
---

## Title

SIGINT handler installed twice when NotImplementedError fallback triggers

## Severity

Medium

## Confidence

High

## Evidence

- `repl.py:485-492` — AgentREPL.run() signal handler installation

## Current Behavior

`loop.add_signal_handler(signal.SIGTERM, _sigterm_handler)`と`loop.add_signal_handler(signal.SIGINT, _sigterm_handler)`が呼ばれるが、`NotImplementedError`が発生した場合、`signal.signal()`で同じハンドラが再度インストールされる。ただし、**SIGTERMとSIGINTの両方が`NotImplementedError`でfallbackする場合、ハンドラは同じ関数を指すため、重複インストールの問題はない**。ただし、`add_signal_handler`が成功した後、`signal.signal`でオーバーライドすると、イベントループのシグナルハンドラが失われる可能性がある。

## Impact

Windows環境など`add_signal_handler`がサポートされていない場合、シグナルハンドラの競合が発生する可能性がある。

## Recommended Action

`add_signal_handler`の成功/失敗に応じて、どちらかの経路のみを使用するよう条件分岐を明確にする。

## Related Files

- scripts/agent/repl.py
