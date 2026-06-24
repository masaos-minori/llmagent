# Implementation Procedure: Command-Layer Definition of Done 検証

## Goal

reqs 32-43 の実装が完了していることを検証し、全チェックをパスさせる。

## Scope

**In:**
- `scripts/agent/commands/` 以下の全ファイル (lint/typecheck/tests)

**Out:** `scripts/agent/commands/` 以外のリファクタリング

## Procedure

### Phase 1: .isdigit() 残存確認

```bash
grep -rn "isdigit" scripts/agent/commands/
# → cmd_db.py, cmd_session.py, cmd_memory.py, cmd_notes.py: 0 matches
```

### Phase 2: formatter.py 削除確認

```bash
ls scripts/agent/commands/formatter.py
# → no such file
```

### Phase 3: Lint

```bash
uv run ruff check scripts/agent/commands/
```

### Phase 4: Type check

```bash
uv run mypy scripts/agent/commands/
```

### Phase 5: テスト

```bash
uv run pytest tests/ -x -q
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| isdigit なし | `grep -rn "isdigit" scripts/agent/commands/*.py` | 0 matches |
| Lint | `uv run ruff check scripts/agent/commands/` | 0 errors |
| 型チェック | `uv run mypy scripts/agent/commands/` | no new errors |
| テスト | `uv run pytest tests/ -x -q` | all pass |
