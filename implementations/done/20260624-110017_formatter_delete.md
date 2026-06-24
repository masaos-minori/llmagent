# Implementation Procedure: Delete formatter.py + test_command_formatter.py

## Goal

プロダクションコードからインポートされていない `formatter.py` ラッパー層とそのテストファイルを削除する。

## Scope

**In:**
- `scripts/agent/commands/formatter.py` — 削除
- `tests/test_command_formatter.py` — 削除

**Out:** `CliOutputPort` や `_out` インジェクションの変更

## Procedure

### Phase 1: プロダクションインポートがないことを確認

```bash
grep -rn "from agent.commands.formatter\|from .formatter\|import formatter" scripts/
# → 0 matches
```

### Phase 2: ファイル削除

```bash
git rm scripts/agent/commands/formatter.py
git rm tests/test_command_formatter.py
```

### Phase 3: テストスイート検証

```bash
uv run pytest tests/ -x -q
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| インポートなし | `grep -rn "from agent.commands.formatter" scripts/` | 0 matches |
| ファイル削除確認 | `ls scripts/agent/commands/formatter.py` | no such file |
| テストパス | `uv run pytest tests/ -x -q` | all pass |
