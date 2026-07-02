# Implementation: plugins/example.py — Fix import path for plugin_registry

**Plan source:** `plans/20260702-202800_plan.md` (Phase 1)
**Target file:** `plugins/example.py`

---

## Goal

`plugins/example.py` の import 文を `from plugin_registry import ...` から `from shared.plugin_registry import ...` に修正し、正しいモジュールパスを参照するようにする。

---

## Scope

**In:**
- `plugins/example.py` の1行の import 文を修正する
- `from plugin_registry import register_command, register_pipeline_stage, register_tool` を `from shared.plugin_registry import register_command, register_pipeline_stage, register_tool` に置換する

**Out:**
- 他のファイルの import 修正は対象外
- `shared/plugin_registry.py` 自体の変更は対象外

---

## Assumptions

1. `shared/plugin_registry.py` が既に存在し、`register_command`, `register_pipeline_stage`, `register_tool` をエクスポートしている
2. `plugins/example.py` 以外に `from plugin_registry import` を使用しているファイルがある場合、本タスクでは対象外とする

---

## Implementation

### Target file

`plugins/example.py`

### Procedure

1. `grep -r "from plugin_registry import" plugins/` を実行して修正前の状態を確認する
2. `plugins/example.py` の対象行を Edit ツールで修正する
3. `grep -r "from plugin_registry import" plugins/` を再実行して修正後に該当行がないことを確認する

### Method

Edit tool でコード変更を行う

### Details

- 変更前: `from plugin_registry import register_command, register_pipeline_stage, register_tool`
- 変更後: `from shared.plugin_registry import register_command, register_pipeline_stage, register_tool`
- 変更箇所は1行のみ

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| grep (before) | `grep -r "from plugin_registry import" plugins/` | 該当行が1件ヒットする |
| Edit | Edit tool で import 行を修正 | 差分が1行のみ |
| grep (after) | `grep -r "from plugin_registry import" plugins/` | 0件 |
| Lint | `ruff check plugins/example.py` | 0 errors |
| Type check | `mypy plugins/example.py` | no new errors |
| Tests | `uv run pytest` | all pass |
