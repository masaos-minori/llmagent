# Implementation: test_embedding_client.py — Gap fill: timeout+retry + mixed failure patterns

## Goal

`tests/test_embedding_client.py` に以下のギャップを埋めるテストケースを追加：

1. **TimeoutError + retry**: `asyncio.wait_for` が TimeoutError を送出した場合、リトライが正しく動作するか
2. **Mixed failure pattern**: TimeoutError と HTTPStatusError の混合失敗パターン
3. **Circuit breaker during retry loop**: リトライ中にサーキットブレーカーが開く
4. **Success after timeout in retry**: リトライ中にタイムアウト → その後成功

## Scope

**In-Scope:**
- `tests/test_embedding_client.py` — テストケース追加

**Out-of-Scope:**
- `scripts/agent/memory/embedding_client.py` の実装変更

## Assumptions

1. `fetch()` は `asyncio.wait_for` でタイムアウトを検出し、`TimeoutError` をキャッチして `_record_failure()` を呼ぶ
2. サーキットブレーカーが途中で発動しないよう `config.circuit_open_after=99` を設定する
3. 既存テストはそのまま維持

## Procedure

Phase 1: TimeoutError + retry テストケース追加 → **完了**
Phase 2: Mixed failure pattern テストケース追加 → **完了**
Phase 3: Circuit breaker during retry テストケース追加 → **完了**
Phase 4: Success after timeout in retry テストケース追加 → **完了**（既存テストでカバー済み）

### Method

既存テストは32件すべてパス。`fetch()` のリトライループがタイムアウトとサーキットブレーカーの組み合わせで正しく動作することを検証する。

### Details

#### Phase 1: TimeoutError + retry テストケース追加

- [x] `test_all_timeout_retries_fail_returns_timeout`: `max_retries=2`, 3回タイムアウト → `call_count==3`, `error_kind=="circuit_open"`（サーキットブレーカー発動）
- [x] `test_timeout_then_success_on_retry`: `max_retries=2`, 1回タイムアウト後成功 → `call_count==2`, `result.success is True`
- [x] `test_max_retries_zero_timeout_single_attempt`: `max_retries=0`, タイムアウト → `call_count==1`, `error_kind=="timeout"`

#### Phase 2: Mixed failure pattern テストケース追加

- [x] `test_timeout_then_http_error_all_fail`: `max_retries=2`, 1回タイムアウト → 2回 HTTPStatusError → `call_count==3`
- [x] `test_http_error_then_timeout_then_success`: `max_retries=2`, HTTPStatusError → タイムアウト → 成功 → `call_count==3`, `result.success is True`
- [x] `test_mixed_failure_all_fail_returns_last_error`: `max_retries=2`, 混合失敗 → `call_count==3`

#### Phase 3: Circuit breaker during retry テストケース追加

- [x] `test_circuit_opens_during_retry`: `max_retries=2, circuit_open_after=2`, 2回失敗でサーキット開く → `call_count==2`, `error_kind=="circuit_open"`
- [x] `test_circuit_opens_after_timeout_then_success_on_retry`: `max_retries=2, circuit_open_after=1`, 1回タイムアウトでサーキット開く → `call_count==1`, `error_kind=="circuit_open"`

## Validation Plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| 追加テスト | Unit | `uv run pytest tests/test_embedding_client.py -v` | all pass |
| Lint | Static | `uv run ruff check tests/test_embedding_client.py` | 0 errors |
| Type check | Static | `uv run mypy tests/test_embedding_client.py` | no new errors |
