---
title: "ワークフローエンジンタイムアウト強制遷移のテスト欠如"
created: 2026-07-31
severity: medium
area: scripts/agent/workflow/workflow_engine.py
status: open
---

## 概要

`workflow_engine.py` の `_force_stage_transition()` タイムアウト強制遷移パスがテストされていない。タイムアウト発生時のクリーンアップと状態移行が正しく動作するか検証できない。

## 影響

- タイムアウト強制遷移時のバグが検出されない
- 本番環境で予期せぬエラーが発生する可能性
- デグレードの検知が困難

## テストすべきケース

1. タイムアウト超過時に強制遷移が発生すること
2. 現在のステージのリソースがクリーンアップされること
3. 次のステージが正常に初期化されること
4. ワークフロー状態が正しく更新されること

## 修正案

```python
# tests/test_workflow_engine.py

@pytest.mark.asyncio
async def test_force_stage_transition_on_timeout():
    engine = WorkflowEngine(session_id="test")
    
    # タイムアウトを設定して実行
    with patch.object(engine, '_transition_to', new_callable=AsyncMock) as mock_transition:
        with patch.object(engine, '_cleanup_current_stage', new_callable=AsyncMock) as mock_cleanup:
            # タイムアウト超過をシミュレート
            result = await engine._force_stage_transition(
                current_stage=WorkflowStage.EXECUTE,
                next_stage=WorkflowStage.APPROVAL,
                stage_timeout=0.001  # 非常に短いタイムアウト
            )
            
            # クリーンアップが呼ばれたことを確認
            mock_cleanup.assert_called_once_with(WorkflowStage.EXECUTE)
            
            # 遷移が呼ばれたことを確認
            mock_transition.assert_called_once_with(WorkflowStage.APPROVAL)
```

## 関連ファイル

- `scripts/agent/workflow/workflow_engine.py`: _force_stage_transition()
- `tests/`: テストディレクトリ
