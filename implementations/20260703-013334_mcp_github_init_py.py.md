# Implementation: scripts/mcp/github/__init__.py — Remove service re-exports and update docstring

**Plan source:** `plans/20260702-202744_plan.md` (Phase 1)
**Target file:** `scripts/mcp/github/__init__.py`

---

## Goal

`mcp/github/__init__.py` からサービスシンボルの再エクスポートを削除し、パッケージ名前空間経由で `GitHubService`、`build_service`、`_GITHUB_TOKEN` がインポートできない状態にする。ファイルはモジュールdocstringのみを含む状態とする。

---

## Scope

**In:**
- `from mcp.github.service import _GITHUB_TOKEN, GitHubService, build_service  # noqa: F401` 行の削除
- `__all__ = ["GitHubService", "build_service", "_GITHUB_TOKEN"]` の削除
- docstring から `service — re-export stub for backward compatibility` 行の削除

**Out:**
- `mcp/github/service.py` 自体の変更
- `GitHubService` のビジネスロジックや dispatch 動作の変更
- `mcp/github/service_dispatch.py`、`mcp/github/service_init.py` その他サブモジュールの変更
- `mcp.github` パッケージ自体の削除

---

## Assumptions

1. `mcp/github/service.py` はこの変更中も引き続き存在し、`__init__.py` の再エクスポートのみを削除する。
2. `scripts/`、`tests/`、`docs/` の外部に `mcp.github` パッケージレベルのサービスシンボルをインポートするコードは存在しない (grep で確認済み)。
3. `__init__.py` に docstring のみが残り `__all__` が存在しない状態が意図された最終形である。

---

## Implementation

### Target file

`scripts/mcp/github/__init__.py`

### Procedure

1. ファイルを読み込み、現在の内容を確認する
2. `from mcp.github.service import _GITHUB_TOKEN, GitHubService, build_service  # noqa: F401` 行を削除する
3. `__all__ = [...]` 行を削除する
4. docstring から `service — re-export stub for backward compatibility` 行を削除する
5. ファイルが docstring のみを含む状態になっていることを確認する
6. `ruff check scripts/mcp/github/` を実行して lint エラーがないことを確認する

### Method

Edit tool でコード変更

### Details

変更後の `__init__.py` はモジュール docstring のみを含む。`from __future__ import annotations` が存在する場合はその必要性を確認した上で判断する。`__all__` は完全に削除し、後方互換性のための再エクスポートは一切残さない。

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Re-export なし確認 | `grep -R "from mcp.github import GitHubService\|build_service\|_GITHUB_TOKEN" scripts tests docs` | 0 matches |
| Lint | `ruff check scripts/mcp/github/` | 0 errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Tests | `uv run pytest` | all pass |
