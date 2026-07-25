---
title: "AgentContext.__init__() always calls build_agent_config() — config error immediately fatal"
severity: High
confidence: High
status: new
created: 20260723-200000
---

## Title

AgentContext.__init__() always calls build_agent_config() — config error immediately fatal

## Severity

High

## Confidence

High

## Evidence

- `context.py:183-184` — AgentContext.__init__()

## Current Behavior

`AgentContext.__init__()`で`self.cfg = build_agent_config()`が常に呼ばれる。これはREPL起動の最初のステップであり、設定ファイルの読み込みエラー（TOMLパースエラー、必須キーの欠落など）が発生すると、**起動のどのフェーズでもなく、最も早い段階で即座に失敗する**。

## Impact

設定ファイルの構文エラーが発生した場合、ユーザーは「Session schema missing」のような具体的なエラーではなく、設定ファイルのパスや行番号が含まれたraw TOMLErrorを受け取る可能性がある。

## Recommended Action

`build_agent_config()`の例外をキャッチし、設定ファイルのパスとエラー種別をフォーマットして表示する。

## Related Files

- scripts/agent/context.py
