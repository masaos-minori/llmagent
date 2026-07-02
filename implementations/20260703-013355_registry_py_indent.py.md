# Implementation: scripts/agent/commands/registry.py — Fix indentation in module docstring mixin list

**Plan source:** `plans/20260702-202752_plan.md` (Phase 1)
**Target file:** `scripts/agent/commands/registry.py`

---

## Goal

モジュール docstring 内の mixin 一覧(lines 9-19)において、cmd_debug.py および cmd_rag_export.py のエントリが他のエントリと列位置がずれているため、全エントリの列位置を統一する。

---

## Scope

**In:**
- `scripts/agent/commands/registry.py` の docstring 内 mixin リスト(lines 9-19)の空白調整
- cmd_debug.py エントリの列位置を他エントリに合わせる
- cmd_rag_export.py エントリの列位置を他エントリに合わせる

**Out:**
- コードロジックの変更(空白のみの差分)
- docstring 外の変更

---

## Assumptions

1. 他のエントリ(cmd_session.py, cmd_mcp.py 等)の列位置が正とする基準
2. 変更は docstring 内の whitespace のみで、ruff/mypy/pytest に影響しない

---

## Implementation

### Target file

`scripts/agent/commands/registry.py`

### Procedure

1. `scripts/agent/commands/registry.py` を開き lines 9-19 の docstring mixin リストを確認する
2. 各エントリの列位置を比較し、cmd_debug.py と cmd_rag_export.py のずれを特定する
3. Edit ツールで該当行の空白を修正し、全エントリの列位置を揃える
4. diff が whitespace-only であることを確認する
5. `ruff check scripts/agent/commands/registry.py` を実行し 0 エラーを確認する
6. `uv run pytest` を実行し全テストがパスすることを確認する

### Method

Edit tool for whitespace-only changes in docstring

### Details

現在の状態(lines 16-17):
```
  cmd_debug.py    — _DebugMixin:    /debug
  cmd_rag_export.py   — _RagExportMixin:   /export, /compact, /rag
```

他エントリとの列位置比較(基準: cmd_session.py 等):
- ファイル名フィールド: 16文字幅(左詰め、スペース埋め)
- `—` 区切り文字: 固定列
- クラス名フィールド: 固定列
- コマンド一覧: 固定列

修正後の期待形式(他エントリに揃えたもの):
```
  cmd_debug.py      — _DebugMixin:      /debug
  cmd_rag_export.py — _RagExportMixin:  /export, /compact, /rag
```

実際の修正内容は既存エントリの列位置を目視で確認して決定する。

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Lint | ruff check scripts/agent/commands/registry.py | 0 errors |
| Type check | mypy scripts/agent/commands/registry.py | no new errors |
| Tests | uv run pytest | all pass |
