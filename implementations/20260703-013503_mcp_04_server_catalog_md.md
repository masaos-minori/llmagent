# Implementation: docs/04_mcp_04_server_catalog.md — Replace mcp.github.service import examples

**Plan source:** `plans/20260702-202849_plan.md` (Phase 2)
**Target file:** `docs/04_mcp_04_server_catalog.md`

---

## Goal

`docs/04_mcp_04_server_catalog.md` 内の `mcp.github.service` シムへのインポート例をすべて正規モジュール (`mcp.github.service_dispatch` / `mcp.github.service_init`) への参照に置き換える。

---

## Scope

**In:**
- `from mcp.github.service import GitHubService` -> `from mcp.github.service_dispatch import GitHubService`
- `from mcp.github.service import build_service` -> `from mcp.github.service_init import build_service`
- `from mcp.github.service import _GITHUB_TOKEN` -> `from mcp.github.service_init import _GITHUB_TOKEN`
- `from mcp.github import GitHubService` -> `from mcp.github.service_dispatch import GitHubService`

**Out:**
- ランタイム動作の変更
- シムファイル (`mcp/github/service.py`, `mcp/github/__init__.py`) の削除
- テストファイルの import 修正

---

## Assumptions

1. `mcp.github.service` および `mcp.github` (GitHubService を直接 import するパス) はシムであり、ドキュメントから除去する。
2. 正規の import 先:
   - `mcp.github.service_dispatch` — `GitHubService` (dispatch フォーマッタ付き)
   - `mcp.github.service_init` — `build_service`, `_GITHUB_TOKEN`

---

## Implementation

### Target file

`docs/04_mcp_04_server_catalog.md`

### Procedure

1. `docs/04_mcp_04_server_catalog.md` を全文読み込み、`mcp.github.service` および `mcp.github import` のパターンを特定する。
2. 各パターンを以下の通り置換する:
   - `from mcp.github.service import GitHubService` -> `from mcp.github.service_dispatch import GitHubService`
   - `from mcp.github.service import build_service` -> `from mcp.github.service_init import build_service`
   - `from mcp.github.service import _GITHUB_TOKEN` -> `from mcp.github.service_init import _GITHUB_TOKEN`
   - `from mcp.github import GitHubService` -> `from mcp.github.service_dispatch import GitHubService`
3. 変更後に grep で残存パターンがないことを確認する。

### Method

Read ツールで全文読み込み後、Edit ツールで各パターンを個別に置換する。

### Details

- 検索パターン:
  - `r"from\s+mcp\.github\.service\s+import"`
  - `r"from\s+mcp\.github\s+import\s+GitHubService"`
- 置換先モジュール対応表:

| 旧パス | 新パス |
|---|---|
| `mcp.github.service` (GitHubService) | `mcp.github.service_dispatch` |
| `mcp.github.service` (build_service, _GITHUB_TOKEN) | `mcp.github.service_init` |
| `mcp.github` (GitHubService) | `mcp.github.service_dispatch` |

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Grep 確認 | `grep -n "mcp\.github\.service\|from mcp\.github import" docs/04_mcp_04_server_catalog.md` | 0件 (シム参照なし) |
| Lint | `ruff check docs/` | 0 errors |
| Type check | `mypy docs/` | no new errors |
| Tests | `uv run pytest` | all pass |
