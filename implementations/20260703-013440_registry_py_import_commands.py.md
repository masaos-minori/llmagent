# Implementation: scripts/agent/commands/registry.py — Remove duplicate _COMMANDS and import from command_defs (Phase 2)

**Plan source:** `plans/20260702-202831_plan.md` (Phase 2)
**Target file:** `scripts/agent/commands/registry.py`

---

## Goal

`registry.py` 内のローカルな `_COMMANDS` 定義ブロックを削除し、`command_defs.py` からインポートするよう変更することで、`/help` 出力が常に正規定義と同期されるようにする。

---

## Scope

**In:**
- `registry.py` の `_COMMANDS: list[CommandDef] = [...]` ブロック全体を削除 (行 48-213)
- 既存の `from agent.commands.command_defs import CommandDef` を `from agent.commands.command_defs import _COMMANDS, CommandDef, SubcommandSpec` に拡張
- `_cmd_help()` と `dispatch()` が引き続き `_COMMANDS` を正しく参照していることをコード検査で確認 (変数名が同じため変更不要)

**Out:**
- `_cmd_help()` の UI リデザイン
- `dispatch()` のロジック変更
- `repl.py` の変更
- Phase 1 (command_defs.py への `/approve`/`/reject` 追加) がまだ完了していない場合の本フェーズ着手

---

## Assumptions

1. Phase 1 が完了しており、`command_defs._COMMANDS` には `/approve` と `/reject` を含む全エントリが揃っている。
2. `registry.py` が `CommandDef` を `command_defs` からインポートしているため、`_COMMANDS` を同じパスから追加インポートしても循環インポートは発生しない。
3. `SubcommandSpec` は `command_defs.py` の `__all__` に含まれており、インポート可能。
4. `_cmd_help()` と `dispatch()` 内の `_COMMANDS` 参照はモジュールレベルの変数名をそのまま使っており、インポート元が変わっても動作に影響しない。
5. 外部コード (`factory.py` 等) は `registry.py` から `_COMMANDS` を直接インポートしていない。

---

## Implementation

### Target file

`scripts/agent/commands/registry.py`

### Procedure

1. `registry.py` の既存インポート行を確認する:
   ```python
   from agent.commands.command_defs import CommandDef
   ```
2. 上記を以下に置き換える:
   ```python
   from agent.commands.command_defs import _COMMANDS, CommandDef, SubcommandSpec
   ```
   (SubcommandSpec を使わない場合は省略可だが、将来の利用を見越して追加しても構わない。最低限 `_COMMANDS` と `CommandDef` が必要)
3. `registry.py` の `_COMMANDS: list[CommandDef] = [...]` ブロック全体 (コメント行含む) を削除する。
   - 削除対象: `# Single source of truth for all built-in slash commands.` コメントから最後の `]` までの全行。
4. `_cmd_help()` (行 258-274 付近) が `_COMMANDS` をループしていることを確認する — 変更不要。
5. `dispatch()` (行 276-306 付近) が `_COMMANDS` をループしていることを確認する — 変更不要。
6. `/db` の `is_async` 差異が解消されているか確認する (`command_defs.py` を Phase 1 で修正済みであるか、または `registry.py` 側の削除により自動解消されるか)。

### Method

Edit tool を使用して以下の2箇所を変更する:
1. インポート行の置き換え
2. `_COMMANDS` ブロックの削除

### Details

**変更 1: インポート行**

old_string:
```python
from agent.commands.command_defs import CommandDef
```

new_string:
```python
from agent.commands.command_defs import _COMMANDS, CommandDef, SubcommandSpec
```

**変更 2: `_COMMANDS` ブロック削除**

削除対象 (現在の registry.py 行 47-213):
```python

# Single source of truth for all built-in slash commands.
# Exact-match commands are listed first, followed by prefix commands.
_COMMANDS: list[CommandDef] = [
    ... (全エントリ)
]
```

このブロック全体を削除する。削除後、`class CommandRegistry(...)` 定義が直接続く形になる。

**注意:** `SubcommandSpec` のインポートは `registry.py` 内では直接使用されていないが、`command_defs.py` の `__all__` に含まれており、再エクスポートの観点から追加することが望ましい。不要ならば省略し、`_COMMANDS, CommandDef` のみのインポートでも動作する。

**スモークテスト手順:**
```bash
uv run python -m agent
# プロンプトで /help を入力
# /approve, /reject, /db, /mdq, /plugin が一覧表示されることを確認
```

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Lint | ruff check scripts/agent/commands/ | 0 errors |
| Type check | mypy scripts/agent/commands/registry.py scripts/agent/commands/command_defs.py | no new errors |
| Tests | uv run pytest tests/ -x -q | all pass |
| Smoke test | uv run python -m agent (then /help) | /approve, /reject, /db, /mdq, /plugin が表示される |
