# Implementation: scripts/checks/check_no_compat.py — Phase 1: pattern and allowlist update

**Plan source:** `plans/20260702-202827_plan.md` (Phase 1)
**Target file:** `scripts/checks/check_no_compat.py`

---

## Goal

`COMPAT_PATTERNS` に5つの新パターンを追加し、既存の互換スタブファイルを `DEFAULT_ALLOWLIST` に登録することで、後退互換パターンの再導入をCIおよびローカルバリデーションで検出できるようにする。

---

## Scope

**In:**
- `COMPAT_PATTERNS` への追加: `r"re-export\s+stub"`, `r"compatibility\s+shim"`, `r"existing imports continue to work"`, `r"backward-compatible"`, `r"_cast_enums"`
- `DEFAULT_ALLOWLIST` への追加: `scripts/agent/config.py`, `scripts/mcp/github/service.py`, `scripts/mcp/github/__init__.py`, `scripts/shared/mcp_config.py`
- `docs/04_mcp_00_document-guide.md` がすでに allowlist にあることの確認
- `DEFAULT_ALLOWLIST` のコメントブロックに "plan 56 patterns" への言及を追加

**Out:**
- AST ベースの静的解析器の構築
- 上記以外の既存スタブへのパターン変更
- CI ワークフロー `backward-compat-check.yml` の変更

---

## Assumptions

1. `scripts/checks/check_no_compat.py` が後退互換ガードの正規実装場所であり、新パターンはここに追加する。
2. 対象の互換スタブ4ファイル (`agent/config.py`, `mcp/github/service.py`, `mcp/github/__init__.py`, `shared/mcp_config.py`) はこのガード有効化と前後して削除予定であり、それまで allowlist に登録する必要がある。

---

## Implementation

### Target file

`scripts/checks/check_no_compat.py`

### Procedure

1. `scripts/checks/check_no_compat.py` を Read ツールで読み込み、`COMPAT_PATTERNS` と `DEFAULT_ALLOWLIST` の現在の内容を確認する。
2. `COMPAT_PATTERNS` に以下の5エントリを追加する:
   - `r"re-export\s+stub"` — re-export stub フレーズ
   - `r"compatibility\s+shim"` — compatibility shim フレーズ
   - `r"existing imports continue to work"` — モジュール docstring フレーズ
   - `r"backward-compatible"` — docstring/コメント中のキーワード
   - `r"_cast_enums"` — メソッド名
3. `DEFAULT_ALLOWLIST` に以下の4ファイルを追加する:
   - `scripts/agent/config.py` — アクティブな re-export stub (削除待ち)
   - `scripts/mcp/github/service.py` — アクティブな re-export stub (削除待ち)
   - `scripts/mcp/github/__init__.py` — アクティブな re-export stub (削除待ち)
   - `scripts/shared/mcp_config.py` — アクティブな `_cast_enums` shim (削除待ち)
4. `docs/04_mcp_00_document-guide.md` が既存の allowlist にあることを確認する (なければ追加)。
5. `DEFAULT_ALLOWLIST` 直上のコメントブロックを編集し "plan 56 patterns" への参照を追加する。

### Method

Edit ツールで既存コードを変更する。

### Details

`COMPAT_PATTERNS` への追加例:

```python
r"re-export\s+stub",           # plan 56: re-export stub phrase
r"compatibility\s+shim",       # plan 56: compatibility shim phrase
r"existing imports continue to work",  # plan 56: module docstring phrase
r"backward-compatible",        # plan 56: backward-compatible keyword
r"_cast_enums",                # plan 56: cast_enums method name
```

`DEFAULT_ALLOWLIST` への追加例:

```python
# plan 56 patterns — active stubs pending removal
"scripts/agent/config.py",
"scripts/mcp/github/service.py",
"scripts/mcp/github/__init__.py",
"scripts/shared/mcp_config.py",
```

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Lint | ruff check scripts/checks/check_no_compat.py | 0 errors |
| Type check | mypy scripts/checks/check_no_compat.py | no new errors |
| Integration | python scripts/checks/check_no_compat.py | exit 0, "All checks passed" |
| Tests | uv run pytest | all pass |
