# Implementation: scripts/checks/check_no_compat.py — Add deprecated import patterns to COMPAT_PATTERNS

**Plan source:** `plans/20260702-202849_plan.md` (Phase 3)
**Target file:** `scripts/checks/check_no_compat.py`

---

## Goal

`scripts/checks/check_no_compat.py` の `COMPAT_PATTERNS` に `agent.config` シムおよび `mcp.github.service` シムへのインポートを検知するパターンを追加し、既存のシム利用者を `DEFAULT_ALLOWLIST` に登録した上で CI チェックが exit 0 で完了することを確認する。

---

## Scope

**In:**
- `COMPAT_PATTERNS` への追加:
  - `r"from\s+agent\.config\s+import"` (from agent.config import シム)
  - `r"from\s+mcp\.github\.service\s+import"` (from mcp.github.service import シム)
  - `r"from\s+mcp\.github\s+import\s+GitHubService"` (from mcp.github import GitHubService)
- 現時点でシムを利用しているファイルを `DEFAULT_ALLOWLIST` に追加
- `python scripts/checks/check_no_compat.py` の実行で exit 0 確認

**Out:**
- ランタイム動作の変更
- シムファイル自体の削除
- テストファイル / `server_*.py` のインポート修正

---

## Assumptions

1. `scripts/checks/check_no_compat.py` には既に `COMPAT_PATTERNS` と `DEFAULT_ALLOWLIST` が存在する。
2. 現在シムを使用しているファイル (テストファイル、`server_pull_requests.py` 等) は許可リストへの登録で誤検知を防ぐ。
3. 新パターンを追加することで将来の新規シム利用を CI で検知できる。

---

## Implementation

### Target file

`scripts/checks/check_no_compat.py`

### Procedure

1. `scripts/checks/check_no_compat.py` を全文読み込み、`COMPAT_PATTERNS` と `DEFAULT_ALLOWLIST` の現在の定義を確認する。
2. 現在のシム利用者を grep で特定する:
   ```bash
   grep -rn "from agent\.config import\|from mcp\.github\.service import\|from mcp\.github import GitHubService" . \
     --include="*.py" | grep -v "^Binary"
   ```
3. `COMPAT_PATTERNS` に以下を追加する:
   ```python
   r"from\s+agent\.config\s+import",       # agent.config shim
   r"from\s+mcp\.github\.service\s+import", # mcp.github.service shim
   r"from\s+mcp\.github\s+import\s+GitHubService",  # mcp.github shim
   ```
4. 手順 2 で特定したファイルパスを `DEFAULT_ALLOWLIST` に追加する。
5. `python scripts/checks/check_no_compat.py` を実行して exit 0 を確認する。
   - exit 0 でなければ、未登録のシム利用者を特定して `DEFAULT_ALLOWLIST` に追加する。

### Method

Read ツールで既存ファイルを読み込み後、Edit ツールで `COMPAT_PATTERNS` リストと `DEFAULT_ALLOWLIST` リストを編集する。

### Details

- 追加するパターン (文字列):
  ```python
  r"from\s+agent\.config\s+import"
  r"from\s+mcp\.github\.service\s+import"
  r"from\s+mcp\.github\s+import\s+GitHubService"
  ```
- `DEFAULT_ALLOWLIST` に追加するファイルの候補 (grep で確認後確定):
  - `tests/` 配下のテストファイル (シムを直接インポートしているもの)
  - `server_pull_requests.py` 等 `server_*.py`
  - `agent/config.py` 自体 (シムファイルは自己参照のため許可リスト対象外の可能性あり)
- パターン追加後は必ず `python scripts/checks/check_no_compat.py` の実行結果を確認する。

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| スクリプト実行 | `python scripts/checks/check_no_compat.py` | exit 0, 0 issues |
| Lint | `ruff check scripts/checks/check_no_compat.py` | 0 errors |
| Type check | `mypy scripts/checks/check_no_compat.py` | no new errors |
| Tests | `uv run pytest` | all pass |
