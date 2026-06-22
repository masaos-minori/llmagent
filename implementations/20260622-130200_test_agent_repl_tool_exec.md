# Implementation: test_agent_repl_tool_exec.py — check_allowed_root パス検証境界条件テスト追加

## Goal

`tests/test_agent_repl_tool_exec.py` の `TestCheckAllowedRoot` クラスに、
相対パスの絶対パス変換とシンボリックリンク解決の境界条件テストを追加し、
`check_allowed_root()` のセキュリティカバレッジを強化する。

## Scope

**In-Scope:**
- `tests/test_agent_repl_tool_exec.py` — `TestCheckAllowedRoot` にテストケース追加

**Out-of-Scope:**
- `scripts/agent/tool_policy.py` の実装変更 (既に `Path.resolve()` で symlink 解決 + 絶対パス変換済み)
- 他のテストクラスの変更

## Assumptions

1. `check_allowed_root()` は `Path(val).resolve()` で相対パスを絶対パスに変換し、シンボリックリンクも解決する。
2. `Path.resolve()` で `ValueError` または `OSError` が発生した場合は `False` (denied) を返す。
3. `tmp_path` フィクスチャは pytest が各テストに独立したディレクトリを提供する。
4. `os.symlink()` は WSL2 Linux 環境で利用可能。

## Implementation

### Target File

- `tests/test_agent_repl_tool_exec.py` — 39件のテスト

### Procedure

Phase 1: 相対パスおよびパストラバーサルテストの追加 → **未完了**
Phase 2: シンボリックリンクテストの追加 → **未完了**

### Method

既存テストは39件すべてパス。`check_allowed_root()` のセキュリティ動作を境界条件で検証する。

### Details

#### Phase 1: 相対パスおよびパストラバーサルテストの追加

- [ ] `TestCheckAllowedRoot` に以下を追加:
  - `test_relative_path_within_root_is_allowed`: `"."` を resolve した絶対パスが allowed_root と一致する場合 True
  - `test_traversal_path_outside_root_is_denied`: `str(root / ".." / "outside.txt")` の形式が denied

#### Phase 2: シンボリックリンクテストの追加

- [ ] `TestCheckAllowedRoot` に以下を追加:
  - `test_symlink_inside_root_is_allowed`: allowed_root 内の実体を指す symlink → True
  - `test_symlink_outside_root_is_denied`: allowed_root 外の実体を指す symlink → False

## Validation Plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| 追加テスト | Unit | `uv run pytest tests/test_agent_repl_tool_exec.py::TestCheckAllowedRoot -v` | all pass |
| 全テスト | Regression | `uv run pytest tests/test_agent_repl_tool_exec.py -v` | all pass |
| Lint | Static | `uv run ruff check tests/test_agent_repl_tool_exec.py` | 0 errors |
| Type check | Static | `uv run mypy tests/test_agent_repl_tool_exec.py` | no new errors |
| Pre-commit | Static | `uv run pre-commit run --files tests/test_agent_repl_tool_exec.py` | pass |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `os.symlink()` が Windows/WSL2 で権限エラーになる | low | WSL2 Linux 環境では `os.symlink()` は通常利用可能; `tmp_path` 配下で作成するため権限問題なし |
| `test_relative_path_within_root_is_allowed` でカレントディレクトリ依存が生じる | low | `str(root)` を相対パスにせず `allowed_root` 自体を `resolve()` で絶対パス化して比較する実装のため安全 |
