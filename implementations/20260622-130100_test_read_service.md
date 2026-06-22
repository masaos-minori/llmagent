# Implementation: test_read_service.py — パストラバーサル境界条件テスト追加

## Goal

`tests/test_read_service.py` の `TestSecurityWrappers` クラスに、`/etc/passwd`、
`/proc/self/environ`、`../../etc/shadow` などのパストラバーサルパターンと
シンボリックリンク解決テストを追加し、`resolve_safe()` のセキュリティカバレッジを強化する。

## Scope

**In-Scope:**
- `tests/test_read_service.py` — `TestSecurityWrappers` にテストケース追加

**Out-of-Scope:**
- `scripts/mcp/file/common.py` の実装変更 (既に `Path.resolve()` でシンボリックリンク解決済み)
- `delete_service.py`, `write_service.py` のテスト変更

## Assumptions

1. `resolve_safe()` は `Path(raw_path).resolve()` でシンボリックリンクを解決し、
   `relative_to(allowed.resolve())` で allowed_dirs 外を `FileAuthorizationError` で弾く。
2. `/etc/passwd` は Linux 環境に存在するが、`/proc/self/environ` も同様。
   テスト環境がこれらのパスを持たない場合でも `resolve_safe()` は `FileAuthorizationError` を投げる
   (パスが allowed_dirs 外であることには変わりない)。
3. `../../etc/shadow` は `Path.resolve()` で絶対パスに正規化されるため、
   path traversal 攻撃は `resolve()` で無効化される。
4. シンボリックリンクテストは `tmp_path` フィクスチャで allowed_dirs 外へのリンクを作成して実施。

## Implementation

### Target File

- `tests/test_read_service.py` — 71件のテスト

### Procedure

Phase 1: パストラバーサルテストの追加 → **完了**
Phase 2: シンボリックリンクテストの追加 → **完了**

### Method

既存テストは71件すべてパス。`resolve_safe()` のセキュリティ動作を境界条件で検証する。

### Details

#### Phase 1: パストラバーサルテストの追加

- [ ] `TestSecurityWrappers` に以下のテストを追加:
  - `test_resolve_safe_rejects_proc_self_environ`: `/proc/self/environ` を弾く
  - `test_resolve_safe_rejects_traversal_etc_shadow`: `../../etc/shadow` 形式を弾く

#### Phase 2: シンボリックリンクテストの追加

- [ ] `TestSecurityWrappers` に以下のテストを追加:
  - `test_resolve_safe_rejects_symlink_outside_allowed`: allowed_dirs 外へのシンボリックリンク → FileAuthorizationError
  - `test_resolve_safe_allows_symlink_inside_allowed`: allowed_dirs 内へのシンボリックリンク → 正常解決

## Validation Plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| 追加テスト | Unit | `uv run pytest tests/test_read_service.py::TestSecurityWrappers -v` | all pass |
| 全テスト | Regression | `uv run pytest tests/test_read_service.py -v` | all pass |
| Lint | Static | `uv run ruff check tests/test_read_service.py` | 0 errors |
| Type check | Static | `uv run mypy tests/test_read_service.py` | no new errors |
| Pre-commit | Static | `uv run pre-commit run --files tests/test_read_service.py` | pass |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `/proc/self/environ` が存在しない環境 (macOS) で挙動が変わる | low | `resolve_safe()` は allowed_dirs 外なら OS によらず FileAuthorizationError を投げる; パスの存在有無は関係なし |
| null byte パスは `resolve_safe()` の `except OSError` でキャッチされず `ValueError` が伝播する | medium | 計画から除外。別途 `resolve_safe()` に `except (OSError, ValueError)` を追加する issue として管理 |
