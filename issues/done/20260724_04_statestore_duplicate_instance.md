# Workflow 実行中に StateStore インスタンスが重複して開かれる

## Priority

High

## Summary

`_handle_workflow_engine()` と `_init_workflow_task()` のそれぞれで独立した `StateStore()` インスタンスが開かれ、同じデータベースへの接続が重複する。

## Problem

`orchestrator.py:183`:

```python
store = StateStore()
engine = WorkflowEngine(self._workflow_def, store, tracer=self._tracer)
...
await engine.run(task, plan_fn, execute_fn, verify_fn)
```

`_init_workflow_task()` の中で `orchestrator.py:261`:

```python
store = create_task(store._db, ...)
```

`StateStore()` が2回インスタンス化され、それぞれが独立した SQLite 接続を持つ。

## Root Cause

`_handle_workflow_engine()` で engine.run() に渡す store と、`_init_workflow_task()` で create_task() に渡す store が別インスタンス。

## Fix Direction

`_handle_workflow_engine()` で開いた store を `_init_workflow_task()` に渡すようにする。または、`_init_workflow_task()` が store を引数を取るよう変更する。

## Acceptance Criteria

- [ ] Workflow 実行中に StateStore インスタンスが重複して開かれない
- [ ] 同じデータベース接続が再利用される
- [ ] 接続リークが発生しない
