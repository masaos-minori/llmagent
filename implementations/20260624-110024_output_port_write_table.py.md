# Implementation Procedure: scripts/agent/commands/output_port.py

## Goal

`write_table()` の先頭で行幅と headers 数の不一致を明示的に検証する。

## Scope

**In:**
- `scripts/agent/commands/output_port.py:39` — widths 計算前にバリデーション追加

**Out:** テーブルレンダリングの再設計

## Implementation

### output_port.py — write_table() バリデーション追加

```python
def write_table(self, headers: list[str], rows: list[list[str]]) -> None:
    if not rows:
        return
    expected = len(headers)
    for idx, row in enumerate(rows):
        if len(row) != expected:
            raise ValueError(
                f"write_table: row {idx} has {len(row)} cells, expected {expected}"
            )
    widths = [
        max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(headers)
    ]
    # ... 既存レンダリング ...
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/commands/output_port.py` | 0 errors |
| Tests | `uv run pytest tests/ -k "output" -x -q` | all pass |
