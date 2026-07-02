# Implementation: .pre-commit-config.yaml — Phase 3: add no-compat-stubs local hook

**Plan source:** `plans/20260702-202827_plan.md` (Phase 3)
**Target file:** `.pre-commit-config.yaml`

---

## Goal

`.pre-commit-config.yaml` に `check_no_compat.py` を呼び出すローカルフックを追加し、コミット時に後退互換パターンが自動検出されるようにする。

---

## Scope

**In:**
- `.pre-commit-config.yaml` への `no-compat-stubs` ローカルフック追加
- 既存ローカルフックの後、repoフックの前に挿入

**Out:**
- CI ワークフロー `backward-compat-check.yml` の変更
- 既存フックの変更

---

## Assumptions

1. `.pre-commit-config.yaml` には既存のローカルフックセクションが存在し、その後に挿入できる。
2. `python -m scripts.checks.check_no_compat` がプロジェクトルートから実行可能である (`.venv` が有効な環境で `language: system` が使用される)。

---

## Implementation

### Target file

`.pre-commit-config.yaml`

### Procedure

1. `.pre-commit-config.yaml` を Read ツールで読み込み、既存のローカルフックセクションの位置を確認する。
2. Edit ツールで、既存ローカルフックの末尾、任意の `repo:` エントリの前に以下の YAML ブロックを挿入する。

### Method

Edit ツールで YAML ファイルを変更する。

### Details

追加するフック定義:

```yaml
      - id: no-compat-stubs
        name: Check for compatibility stubs and shims
        entry: python -m scripts.checks.check_no_compat
        language: system
        pass_filenames: false
        types_or: [python, markdown]
```

挿入位置: ローカルフックセクション (`- repo: local` の `hooks:` リスト) の末尾。

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| YAML 構文確認 | pre-commit validate-config .pre-commit-config.yaml | 0 errors |
| フック実行確認 | pre-commit run no-compat-stubs --all-files | pass |
| Tests | uv run pytest | all pass |
