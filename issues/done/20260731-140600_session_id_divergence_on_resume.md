---
title: "既存セッション再開時のセッションID分岐"
created: 2026-07-31
severity: medium
area: scripts/agent/workflow/workflow_engine.py
status: open
---

## 概要

`workflow_engine.py` でセッションが既に存在する場合（既存セッションの再開）、新しいUUIDが割り当てられてセッションが分岐する可能性がある。

## 証拠

```python
# scripts/agent/workflow/workflow_engine.py

session_id = str(uuid.uuid4())
```

## 影響

- 既存セッションのワークフロー状態が失われる
- 会話履歴とワークフロー状態の不一致
- ユーザーが意図したセッションと異なるセッションで処理が進む

## 再現手順

1. セッションAでワークフローを開始
2. Ctrl+Cで中断
3. 同じセッションAで再度ワークフローを開始
4. 新しいセッションIDが生成され、セッションBとして扱われる
5. セッションAのワークフロー状態が参照できなくなる

## 修正案

```python
async def start_workflow(self, session_id: Optional[str] = None):
    # 既存セッションの確認
    existing_session = await self._get_existing_session(session_id)
    
    if existing_session:
        # 既存セッションを使用
        workflow_session_id = existing_session.workflow_id
    else:
        # 新しいセッションを作成
        workflow_session_id = str(uuid.uuid4())
    
    return workflow_session_id
```

既存セッションのワークフローIDを取得するメソッドを追加し、セッション再開時は既存IDを使用するようにする。

## 関連ファイル

- `scripts/agent/workflow/workflow_engine.py`: start_workflow()
- `scripts/agent/session.py`: セッション管理
