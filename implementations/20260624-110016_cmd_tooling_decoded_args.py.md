# Implementation Procedure: scripts/agent/commands/cmd_tooling.py

## Goal

`_decode_args()` の戻り値を `DecodedArgs` 型付き DTO に変更する。

## Scope

**In:**
- `scripts/agent/commands/cmd_tooling.py` — `DecodedArgs` DTO 定義; `_decode_args()` 戻り値変更; `_to_tool_result_view()` 更新

**Out:** ツール実行の変更、ストアフォーマットの変更

## Assumptions

1. `cmd_tooling.py:23` — `def _decode_args(raw: str | None) -> dict[str, Any]:`
2. `orjson` がすでにインポート済み

## Implementation

### cmd_tooling.py — DecodedArgs DTO

```python
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class DecodedArgs:
    data: dict[str, Any]
    parse_error: str | None = None  # None = success
```

### cmd_tooling.py — _decode_args() 更新

```python
def _decode_args(raw: str | None) -> DecodedArgs:
    if raw is None:
        return DecodedArgs(data={})
    try:
        parsed = orjson.loads(raw)
        if not isinstance(parsed, dict):
            return DecodedArgs(data={}, parse_error="non-dict JSON")
        return DecodedArgs(data=parsed)
    except orjson.JSONDecodeError as e:
        return DecodedArgs(data={}, parse_error=str(e))
```

### cmd_tooling.py — _to_tool_result_view() caller 更新

```python
# Before:
decoded = _decode_args(row.args_raw)
# decoded はそのまま dict として使用

# After:
decoded = _decode_args(row.args_raw)
# decoded.data を使用; decoded.parse_error がある場合はログ
if decoded.parse_error:
    logger.debug("cmd_tooling: args decode error: %s", decoded.parse_error)
args_data = decoded.data
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/commands/cmd_tooling.py` | 0 errors |
| 型チェック | `uv run mypy scripts/agent/commands/cmd_tooling.py` | no new errors |
| Tests | `uv run pytest tests/ -k "tooling" -x -q` | all pass |
