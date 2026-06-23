# Implementation: test_embedding_client.py — EmbeddingClient リトライ境界条件テスト追加

## Goal

`tests/test_embedding_client.py` の `TestRetry` クラスに、`max_retries=0/1/2` の
境界条件テストを追加し、`fetch()` のリトライループ (`range(max_retries + 1)`) が
正確な回数だけ試行することを明示的に確認する。

## Scope

**In-Scope:**
- `tests/test_embedding_client.py` — `TestRetry` にテストケース追加

**Out-of-Scope:**
- `scripts/agent/memory/embedding_client.py` の実装変更
- 他のテストクラスの変更

## Assumptions

1. `fetch()` は `range(max_retries + 1)` でループするため:
   - `max_retries=0` → 1回試行 (リトライなし)
   - `max_retries=1` → 最大2回試行
   - `max_retries=2` → 最大3回試行
2. サーキットブレーカーが途中で発動しないよう `fail_threshold` を十分大きく設定する。
3. 既存テスト `test_retries_on_failure_then_succeeds` (`max_retries=2`, 1回失敗後成功, call_count=2)
   および `test_all_retries_fail_returns_last_error` (`max_retries=1`, 全失敗) はそのまま維持する。

## Implementation

### Target File

- `tests/test_embedding_client.py` — 20件のテスト

### Procedure

Phase 1: TestRetry へのテストケース追加 → **完了**

### Method

既存テストは20件すべてパス。`fetch()` のリトライループが正確な回数だけ試行することを境界条件で検証する。

### Details

#### Phase 1: TestRetry へのテストケース追加

- [x] `test_max_retries_zero_single_attempt_on_failure`: `max_retries=0`, HTTPStatusError → `call_count==1`, `result.success is False`
- [x] `test_max_retries_zero_single_attempt_on_success`: `max_retries=0`, 正常応答 → `call_count==1`, `result.success is True`
- [x] `test_max_retries_two_all_fail_three_attempts`: `max_retries=2`, 全 HTTPStatusError → `call_count==3`, `result.success is False`
- [x] `test_max_retries_one_success_on_second_attempt`: `max_retries=1`, 1回失敗後成功 → `call_count==2`, `result.success is True`

## Validation Plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| 追加テスト | Unit | `uv run pytest tests/test_embedding_client.py::TestRetry -v` | all pass |
| 全テスト | Regression | `uv run pytest tests/test_embedding_client.py -v` | all pass |
| Lint | Static | `uv run ruff check tests/test_embedding_client.py` | 0 errors |
| Type check | Static | `uv run mypy tests/test_embedding_client.py` | no new errors |
| Pre-commit | Static | `uv run pre-commit run --files tests/test_embedding_client.py` | pass |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| サーキットブレーカーが `max_retries=2` の3回試行中に発動して `call_count<3` になる | medium | `config.fail_threshold=99` を設定してブレーカー干渉を防ぐ |
| `max_retries=0` の成功テストが既存クラスと重複する | low | `TestRetry` クラスの文脈で「リトライが0回時は1回試行で終了」を明示的に示す価値がある |
