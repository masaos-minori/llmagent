---
title: "stale attempt回復の排他制御欠如"
created: 2026-07-31
severity: high
area: scripts/agent/workflow/state_store.py
status: open
---

## 概要

`state_store.py` の `recover_stale_attempts()` で複数のプロセス/スレッドが同時に実行する場合、同じ stale attempt を複数回回復する可能性がある。SELECT FOR UPDATEのような排他制御がない。

## 証拠

```python
# scripts/agent/workflow/state_store.py

grace_period = timedelta(seconds=30)
stale_threshold = datetime.now() - grace_period

# staleなattemptを取得
cursor.execute("""
    SELECT id, workflow_id FROM workflow_attempts
    WHERE status = 'running'
    AND updated_at < ?
""", (stale_threshold.isoformat(),))
rows = cursor.fetchall()

# 各attemptを回復
for row in rows:
    await self._recover_attempt(row['id'])
```

## 影響

- 同じワークフローが複数回並列実行される
- データベースの不整合（重複レコード）
- リソースの無駄遣い（同じ作業の重複実行）

## 再現手順

1. プロセスAとプロセスBが同時に `recover_stale_attempts()` を実行
2. 両方が同じ stale attempt を取得
3. 両方が同じattemptを回復しようとする
4. 競合によりデータ不整合または重複実行が発生

## 修正案

```python
async def recover_stale_attempts(self):
    # SELECT FOR UPDATEで排他ロック
    cursor.execute("""
        SELECT id, workflow_id FROM workflow_attempts
        WHERE status = 'running'
        AND updated_at < ?
        ORDER BY created_at ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    """, (stale_threshold.isoformat(),))
    row = cursor.fetchone()
    
    if row:
        # ロックを取得できた場合のみ回復
        await self._recover_attempt(row['id'])
```

または、Redisなどの分散ロックを使用する。

## 関連ファイル

- `scripts/agent/workflow/state_store.py`: recover_stale_attempts()
- SQLite: FOR UPDATE / SKIP LOCKED句
