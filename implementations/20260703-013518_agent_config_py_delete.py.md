# Implementation: scripts/agent/config.py — Confirm no remaining references and delete file

**Plan source:** `plans/20260702-202905_plan.md` (Phase 4 (steps 11-12))
**Target file:** `scripts/agent/config.py`

---

## Goal

`agent.config` への参照が完全に除去されたことを grep で確認してから `scripts/agent/config.py` を削除し、re-export スタブを廃止する。

---

## Scope

**In:**
- 残存参照の grep 確認: `grep -R "from agent.config import|import agent.config" --include="*.py" /home/masaos/llmagent/ | grep -v ".venv"` で出力なしを確認
- `scripts/agent/config.py` の削除
- 削除後の全体バリデーション実行

**Out:**
- 他ファイルの変更
- `agent.config_builders` や `agent.config_dataclasses` の変更

---

## Assumptions

1. Phase 1〜3 が完了しており、`agent.config` への参照が全て書き換え済みである
2. grep コマンドが出力を返さない場合のみ削除に進む
3. `PYTHONPATH=scripts uv run lint-imports` が利用可能

---

## Implementation

### Target file

`scripts/agent/config.py`

### Procedure

1. 残存参照チェックを実行する:
   ```
   grep -R "from agent.config import|import agent.config" --include="*.py" /home/masaos/llmagent/ | grep -v ".venv"
   ```
   出力がなければ次のステップへ進む。出力がある場合は該当ファイルを修正してから再確認する。
2. `scripts/agent/config.py` を削除する (例: `rm scripts/agent/config.py`)
3. 以下の全体バリデーションを実行する:
   - `uv run ruff check scripts/ tests/`
   - `PYTHONPATH=scripts uv run lint-imports`
   - `uv run pytest`

### Method

Bash ツールで grep 確認・ファイル削除・バリデーション実行

### Details

削除コマンド:
```bash
rm /home/masaos/llmagent/scripts/agent/config.py
```

全体バリデーションコマンド:
```bash
uv run ruff check scripts/ tests/
PYTHONPATH=scripts uv run lint-imports
uv run pytest
```

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 残存参照確認 | grep -R "from agent.config import\|import agent.config" --include="*.py" /home/masaos/llmagent/ \| grep -v ".venv" | 出力なし |
| Lint | uv run ruff check scripts/ tests/ | 0 errors |
| Import check | PYTHONPATH=scripts uv run lint-imports | 0 errors |
| Tests | uv run pytest | all pass |
