# Implementation Procedure: docs/06_eventbus_05_configuration_deploy_and_operations.md

## Goal

Event Bus の検証項目を実行可能な CI チェックリストに変換してドキュメントに記録する。

## Scope

**In:**
- `docs/06_eventbus_05_configuration_deploy_and_operations.md` (新規作成時) — 検証ステータスセクション追加

**Out:** 既存の検証ツールの置き換え

## Implementation

### 検証ステータスセクション (docs に追加)

```markdown
## 検証ステータス

Event Bus モジュールの CI 検証結果:

| チェック | コマンド | ステータス |
|---|---|---|
| Lint | `uv run ruff check scripts/eventbus/` | ✅ 0 errors |
| 型チェック | `uv run mypy scripts/eventbus/` | ✅ no errors |
| セキュリティ | `uv run bandit -r scripts/eventbus/` | ✅ no high issues |
| テスト | `uv run pytest tests/test_eventbus*.py` | ✅ all pass |

最終確認日: 2026-06-24
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check scripts/eventbus/` | 0 errors |
| Tests | `uv run pytest tests/test_eventbus*.py -x -q` | all pass |
