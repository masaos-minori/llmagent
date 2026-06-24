# Implementation Procedure: tests/test_eventbus_*.py (reorganize by feature)

## Goal

フェーズ別テストファイルを機能別に再編する。

## Scope

**In (新規 4 ファイル):**
- `tests/test_eventbus_publish.py` — health, publish, idempotency, schema validation
- `tests/test_eventbus_replay_subscribe.py` — replay, replay filtering, subscribe
- `tests/test_eventbus_offsets.py` — offset read/write, consumer resume
- `tests/test_eventbus_dlq.py` — DLQ promotion, listing, requeue

**削除:**
- `tests/test_eventbus_phase1.py`
- `tests/test_eventbus_phase2.py`
- `tests/test_eventbus_phase3.py`

**Out:** プロダクションコードの変更

## Procedure

### Phase 1: 既存テストのマッピング

```
test_eventbus_phase1.py → test_eventbus_publish.py (health, publish)
                        → test_eventbus_replay_subscribe.py (replay, subscribe)
test_eventbus_phase2.py → test_eventbus_offsets.py (offsets)
                        → test_eventbus_dlq.py (DLQ basics)
test_eventbus_phase3.py → test_eventbus_dlq.py (DLQ requeue, exhaustion)
```

### Phase 2: 共有 fixtures の移動

共有 `client` fixture → `tests/conftest.py` に移動 (既存の場合は確認)

### Phase 3: 旧ファイル削除

```bash
git rm tests/test_eventbus_phase1.py tests/test_eventbus_phase2.py tests/test_eventbus_phase3.py
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| 全テスト pass | `uv run pytest tests/test_eventbus_publish.py tests/test_eventbus_replay_subscribe.py tests/test_eventbus_offsets.py tests/test_eventbus_dlq.py -v` | all pass |
| 旧ファイルなし | `ls tests/test_eventbus_phase*.py` | no such file |
| カバレッジ維持 | テスト数: 旧 ≤ 新 | 同数以上 |
