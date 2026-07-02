# Implementation: tests/test_github_mcp_service.py — Update import to use service_dispatch directly

**Plan source:** `plans/20260702-202744_plan.md` (Phase 2)
**Target file:** `tests/test_github_mcp_service.py`

---

## Goal

`tests/test_github_mcp_service.py` の line 28 のインポートを `mcp.github.service` から `mcp.github.service_dispatch` に直接変更し、パッケージ経由の間接インポートを排除する。

---

## Scope

**In:**
- line 28: `from mcp.github.service import GitHubService` を `from mcp.github.service_dispatch import GitHubService` に置換

**Out:**
- テストのビジネスロジックや mock 設定の変更
- `mcp/github/service_dispatch.py` 自体の変更
- 他のテストファイルの変更

---

## Assumptions

1. `mcp.github.service_dispatch.GitHubService` は dispatch + business logic を統合したクラスであり、テストで mock を渡してインスタンス化する用途に適している。
2. line 28 のインポートは `GitHubService` のみであり、`build_service` や `_GITHUB_TOKEN` は同ファイルでインポートされていない。
3. Phase 1 (`__init__.py` の変更) が完了した後にこの変更を適用する。

---

## Implementation

### Target file

`tests/test_github_mcp_service.py`

### Procedure

1. ファイルを読み込み、line 28 の内容を確認する
2. `from mcp.github.service import GitHubService` を `from mcp.github.service_dispatch import GitHubService` に置換する
3. `uv run pytest tests/test_github_mcp_service.py -v` を実行してテストが通ることを確認する

### Method

Edit tool でコード変更

### Details

変更は line 28 の 1 行のみ。インポート元モジュールを `mcp.github.service` から `mcp.github.service_dispatch` に変更するだけで、`GitHubService` という名前自体は変わらないため、テストコード本体の修正は不要なはず。

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| テスト実行 | `uv run pytest tests/test_github_mcp_service.py -v` | all pass |
| Lint | `ruff check tests/test_github_mcp_service.py` | 0 errors |
| Type check | `mypy tests/test_github_mcp_service.py` | no new errors |
| Tests (全体) | `uv run pytest` | all pass |
