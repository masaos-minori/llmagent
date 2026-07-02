# Implementation: tests/test_check_no_compat.py — Phase 4: pytest for check_no_compat

**Plan source:** `plans/20260702-202827_plan.md` (Phase 4)
**Target file:** `tests/test_check_no_compat.py`

---

## Goal

`check_no_compat.main()` または `check_all()` を現在のコードベースに対して実行し、allowlist 外でのパターン検出がないことをアサートするテストと、新パターン5件が合成文字列で正しく検出されることを確認するパラメータ化ネガティブテストを作成する。

---

## Scope

**In:**
- 新規ファイル `tests/test_check_no_compat.py` の作成
- 統合テスト: `check_no_compat.main()` / `check_all()` をコードベース全体に適用し、終了コード0をアサート
- パラメータ化ネガティブテスト: 5つの新パターン (`re-export stub`, `compatibility shim`, `existing imports continue to work`, `backward-compatible`, `_cast_enums`) が allowlist 外の合成文字列で検出されること

**Out:**
- `check_no_compat.py` 本体の変更
- 既存テストファイルの変更

---

## Assumptions

1. `scripts/checks/check_no_compat.py` は `main()` または `check_all()` 関数をエクスポートしており、テストから呼び出し可能である。
2. `check_no_compat` はパターンにマッチしたファイルのリストを返すか、終了コードを返すインターフェースを持つ。
3. 合成文字列を allowlist に含まない一時ファイルに書き込んでスキャンするか、内部関数を直接呼び出してテストできる。

---

## Implementation

### Target file

`tests/test_check_no_compat.py`

### Procedure

1. `scripts/checks/check_no_compat.py` を Read ツールで読み込み、公開インターフェース (`main`, `check_all`, `COMPAT_PATTERNS`, `DEFAULT_ALLOWLIST`) を確認する。
2. Write ツールで `tests/test_check_no_compat.py` を新規作成する。
3. `uv run pytest tests/test_check_no_compat.py -v` を実行してすべてのテストがパスすることを確認する。

### Method

Write ツールで新規ファイルを作成する。

### Details

テスト構成例:

```python
import sys
import pytest
import importlib
import scripts.checks.check_no_compat as checker

# 統合テスト: コードベース全体で exit 0
def test_no_compat_issues_in_codebase():
    """check_no_compat をコードベース全体に適用し、問題がないことを確認する。"""
    result = checker.check_all()  # または main() の戻り値/sys.exit コード
    assert result == 0, "Compatibility issues detected outside allowlist"


# パラメータ化ネガティブテスト: 各新パターンが検出される
NEW_PATTERNS = [
    "re-export stub",
    "compatibility shim",
    "existing imports continue to work",
    "backward-compatible",
    "_cast_enums",
]

@pytest.mark.parametrize("phrase", NEW_PATTERNS)
def test_pattern_detected_in_synthetic_string(phrase, tmp_path):
    """各新パターンが allowlist 外の合成ファイルで検出されることを確認する。"""
    synthetic = tmp_path / "synthetic_test.py"
    synthetic.write_text(f"# {phrase}\n")
    # checker の内部スキャン関数を直接呼び出すか、
    # COMPAT_PATTERNS に対して re.search を実行して検出を確認する
    import re
    matched = any(
        re.search(pat, synthetic.read_text())
        for pat in checker.COMPAT_PATTERNS
    )
    assert matched, f"Pattern for '{phrase}' was not detected"
```

実際の実装は `check_no_compat.py` の公開インターフェースを確認してから確定する。`check_all()` が存在しない場合は `main()` を `subprocess.run` でテストするか、内部スキャン関数を直接呼び出す。

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Lint | ruff check tests/test_check_no_compat.py | 0 errors |
| Type check | mypy tests/test_check_no_compat.py | no new errors |
| Tests | uv run pytest tests/test_check_no_compat.py -v | all pass |
