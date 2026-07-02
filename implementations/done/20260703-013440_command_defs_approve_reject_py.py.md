# Implementation: scripts/agent/commands/command_defs.py — Add /approve and /reject entries (Phase 1)

**Plan source:** `plans/20260702-202831_plan.md` (Phase 1)
**Target file:** `scripts/agent/commands/command_defs.py`

---

## Goal

`command_defs.py` を `registry.py` の `_COMMANDS` と完全に同期させるため、現在欠落している `/approve` と `/reject` の `CommandDef` エントリを追加する。

---

## Scope

**In:**
- `/approve` の `CommandDef` エントリを追加 (after `/audit`, before `/plugin`)
- `/reject` の `CommandDef` エントリを追加 (after `/approve`, before `/plugin`)
- 追加後の `command_defs._COMMANDS` エントリ数が `registry._COMMANDS` と一致することを確認

**Out:**
- `/help` UIのリデザイン
- `/exit` ハンドリングの変更
- `repl.py` の `AgentREPL.SLASH_COMMANDS` への変更
- `/db` の `is_async` フラグ修正 (既に `False` であれば不要; `registry.py` では `True` なので差異あり — 本フェーズでは同期のみ)

---

## Assumptions

1. `command_defs.py` はモジュール docstring が示すように「全ビルトイン slash コマンドの single source of truth」である。
2. `/approve` と `/reject` が `command_defs.py` に存在しないのは意図せぬ欠落であり、追加により解消する。
3. `registry.py` の `/approve` と `/reject` の定義が正しい仕様である: `prefix=True`, `is_async=False`, handler=`_cmd_approve`/`_cmd_reject`。
4. `/db` の `is_async` は `command_defs.py` で `False`、`registry.py` で `True` と差異があるが、本タスク (Phase 1) では `/approve`/`/reject` の追加のみに集中し、`/db` の差異は別途確認する。

---

## Implementation

### Target file

`scripts/agent/commands/command_defs.py`

### Procedure

1. `command_defs.py` を開き、現在の `/audit` エントリと `/plugin` エントリの間を確認する (行 186-198 付近)。
2. `/audit` エントリの直後、`/plugin` エントリの直前に以下の2エントリを挿入する。
3. `/db` の `is_async` フラグが `registry.py` と異なる (`command_defs.py`: `False`, `registry.py`: `True`) ことをメモしておき、Phase 2 完了後の整合確認時に報告する。

### Method

Edit tool を使用してファイルを編集する。

### Details

挿入位置: `command_defs.py` の `/audit` エントリ末尾の閉じ括弧 `)` の直後、かつ `/plugin` エントリの直前。

挿入するコード:

```python
    CommandDef(
        "/approve",
        True,
        False,
        "_cmd_approve",
        "[reason]  Approve the pending workflow task",
    ),
    CommandDef(
        "/reject",
        True,
        False,
        "_cmd_reject",
        "[reason]  Reject the pending workflow task",
    ),
```

挿入後の順序 (prefix sync セクション末尾):
```
/audit
/approve   ← 新規追加
/reject    ← 新規追加
/plugin
```

完了基準: `len(command_defs._COMMANDS) == len(registry._COMMANDS)` かつ全エントリが等価。

注意: `/db` の `is_async` 差異 (`command_defs.py` は `False`, `registry.py` は `True`) については、Phase 1 完了後に別途対処するか、Phase 2 のインポート置き換え前に修正する必要がある。

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Lint | ruff check scripts/agent/commands/command_defs.py | 0 errors |
| Type check | mypy scripts/agent/commands/command_defs.py | no new errors |
| Entry count | python -c "from agent.commands.command_defs import _COMMANDS as C; from agent.commands.registry import _COMMANDS as R; print(len(C), len(R))" | 両者の件数が一致 |
| Tests | uv run pytest | all pass |
