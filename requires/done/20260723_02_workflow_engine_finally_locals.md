---
title: "Workflow engine finally block uses locals().get('task') — fragile variable scope dependency"
severity: Critical
confidence: High
status: new
created: 20260723-200000
---

## Title

Workflow engine finally block uses locals().get('task') — fragile variable scope dependency

## Severity

Critical

## Confidence

High

## Evidence

- `orchestrator.py:236-248` — Orchestrator._handle_workflow_engine() finally block

## Current Behavior

`_handle_workflow_engine()`のfinallyブロックで`_task = locals().get("task")`を使用してタスクを取得している。これは**Pythonのローカル変数のスコープが関数スコープであることに依存している**。ただし、`async def`内では`locals()`の結果が信頼できないというPythonのドキュメントの警告がある。また、`task`変数が`_init_workflow_task()`で代入されるが、`_init_workflow_task()`が例外を送出した場合、`task`は未定義になる。

## Impact

ワークフローエンジン実行中にタスクステータスの更新が失敗し、タスクが`pending`状態のまま永続化する。

## Recommended Action

`locals().get("task")`を削除し、`task`変数をtryブロックの外側で`None`として初期化し、finally内で直接参照するように変更する。

## Related Files

- scripts/agent/orchestrator.py
