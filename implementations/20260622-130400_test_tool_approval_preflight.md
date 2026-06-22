# Implementation: test_tool_approval_preflight.py — check_approval ユーザー入力検証テスト追加

## Goal

`tests/test_tool_approval_preflight.py` の `TestCheckApproval` クラスに、
medium/high リスク時のユーザー入力バリエーション・`audit_logger` が None の場合・
`audit_logger` が例外を投げる場合のテストを追加し、`check_approval()` のカバレッジを強化する。

## Scope

**In-Scope:**
- `tests/test_tool_approval_preflight.py` — `TestCheckApproval` にテストケース追加

**Out-of-Scope:**
- `scripts/agent/tool_approval.py` の実装変更
- `scripts/agent/tool_audit.py` の実装変更
- 他のテストクラスの変更

## Assumptions

1. `_prompt_user_approval()` は `asyncio.to_thread(input, ...)` の戻り値に `.strip().lower()` を適用する。
2. medium risk: `"y"` のみ approved。`" y "` は `.strip()` 後 `"y"` → approved。空文字列は denied。
3. high risk: `"yes"` のみ approved。`" yes "` は `.strip()` 後 `"yes"` → approved。`"y"` は denied。
4. `audit_approval()` は `ctx.services.audit_logger is None` のとき early return (no-op)。
5. `audit_approval()` 内の `ctx.services.audit_logger.info(...)` に try/except がないため、
   `audit_logger.info` が例外を投げると `check_approval()` に伝播する。

## Implementation

### Target File

- `tests/test_tool_approval_preflight.py` — 30件のテスト

### Procedure

Phase 1: ユーザー入力バリエーションのテスト追加 → **未完了**
Phase 2: audit_logger 境界条件のテスト追加 → **未完了**

### Method

既存テストは30件すべてパス。`check_approval()` のユーザー入力処理と audit_logger の境界条件をテストする。

### Details

#### Phase 1: ユーザー入力バリエーションのテスト追加

- [ ] `TestCheckApproval` に以下を追加:
  - `test_medium_risk_empty_input_denied`: medium で `""` → denied (`.lower()` 後も `""` != `"y"`)
  - `test_medium_risk_input_with_whitespace_approved`: medium で `" y "` → `.strip()` → `"y"` → approved
  - `test_high_risk_empty_input_denied`: high で `""` → denied
  - `test_high_risk_input_with_whitespace_approved`: high で `" yes "` → `.strip()` → `"yes"` → approved

#### Phase 2: audit_logger 境界条件のテスト追加

- [ ] `TestCheckApproval` に以下を追加:
  - `test_audit_log_skipped_when_no_logger_high_risk`: high risk, audit_logger=None → 例外なし、approved
  - `test_audit_logger_error_propagates`: `audit_logger.info` が `RuntimeError` を投げると `check_approval()` から伝播する

## Validation Plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| 追加テスト | Unit | `uv run pytest tests/test_tool_approval_preflight.py::TestCheckApproval -v` | all pass |
| 全テスト | Regression | `uv run pytest tests/test_tool_approval_preflight.py -v` | all pass |
| Lint | Static | `uv run ruff check tests/test_tool_approval_preflight.py` | 0 errors |
| Type check | Static | `uv run mypy tests/test_tool_approval_preflight.py` | no new errors |
| Pre-commit | Static | `uv run pre-commit run --files tests/test_tool_approval_preflight.py` | pass |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `test_audit_logger_error_propagates` が将来の実装変更 (try/except 追加) で失敗する | low | テストの docstring に「現状の実装では audit_logger エラーは伝播する; try/except を追加した場合はこのテストを削除すること」と明記 |
| `asyncio.to_thread` のモック方法が他のテストと不整合になる | low | 既存テストの `patch("asyncio.to_thread", new=AsyncMock(return_value=...))` パターンをそのまま踏襲する |
