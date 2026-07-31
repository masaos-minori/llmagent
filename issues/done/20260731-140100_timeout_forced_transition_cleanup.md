---
title: "タイムアウト強制遷移時のステージクリーンアップ欠如"
created: 2026-07-31
severity: high
area: scripts/agent/workflow/workflow_engine.py
status: open
---

## 概要

`workflow_engine.py` の `_force_stage_transition()` でタイムアウト強制遷移時に、現在のステージのクリーンアップ（リソース解放、ステート保存）がスキップされる。`_transition_to()` は遷移前のクリーンアップを保証しない。

## 証拠

```python
# scripts/agent/workflow/workflow_engine.py

if stage_timeout and elapsed > stage_timeout:
    logger.warning(f"Stage timeout exceeded: {stage}")
    await self._transition_to(next_stage)
```

## 影響

- タイムアウト強制遷移時にリソースリークが発生する
- ワークフロー状態が不整合になり、次のステージで予期せぬエラー
- データベースに不完全な状態が永続化される

## 再現手順

1. ワークフローのあるステージで長時間実行中の処理を開始
2. タイムアウト閾値を超過させる
3. `_force_stage_transition()` が呼ばれ、強制遷移が発生
4. 現在のステージのリソースが解放されず、不整合状態が残る

## 修正案

```python
async def _force_stage_transition(self, current_stage, next_stage):
    # 現在のステージのクリーンアップを明示的に行う
    await self._cleanup_current_stage(current_stage)
    
    # 遷移を実行
    await self._transition_to(next_stage)

async def _cleanup_current_stage(self, stage):
    """現在のステージのリソースをクリーンアップ"""
    if stage == WorkflowStage.EXECUTE:
        # 実行中のツール呼び出しをキャンセル
        pass
    elif stage == WorkflowStage.APPROVAL:
        # 承認待ちのタスクを破棄
        pass
    # ... 他のステージのクリーンアップ
```

## 関連ファイル

- `scripts/agent/workflow/workflow_engine.py`: _force_stage_transition(), _transition_to()
- `scripts/agent/workflow/state_store.py`: ワークフロー状態保存
