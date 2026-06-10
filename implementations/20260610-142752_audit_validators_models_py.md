# Implementation: audit.py + tool_validators.py + models.py — type improvements

## Goal

1. `audit.py`: replace `Any` with `logging.Logger`.
2. `tool_validators.py`: tighten type annotations; add explicit `None` return type.
3. `models.py`: add comment clarifying `validate_args()` must be called explicitly.

## Scope

- `scripts/mcp/audit.py`
- `scripts/mcp/tool_validators.py`
- `scripts/mcp/models.py`

## Implementation

### audit.py

```python
import logging

def _audit_log(
    server_logger: logging.Logger,
    ...
) -> None:
```

Remove `from typing import Any`.

### tool_validators.py

Add return type to `validate_tool_args()`:
```python
def validate_tool_args(tool_name: str, args: dict[str, Any]) -> None:
```
(already has it; verify and keep.)

Add return type `None` to each `_validate_*` function if missing.

### models.py

Add docstring note to `validate_args()` clarifying it must be called explicitly
before dispatch (no automatic invocation from Pydantic).

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/mcp/audit.py scripts/mcp/tool_validators.py scripts/mcp/models.py` | 0 errors |
| Type | `uv run mypy scripts/mcp/audit.py scripts/mcp/models.py` | no new errors |
| No Any in audit | `grep "from typing import Any" scripts/mcp/audit.py` | 0 hits |
