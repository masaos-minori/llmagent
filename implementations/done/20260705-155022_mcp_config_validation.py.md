# Implementation: shared/mcp_config.py — Add value validation to McpServerConfig

## Goal

Extend `McpServerConfig.__post_init__()` to validate 7 new constraints: timeout ranges, tool name validity, duplicate tool names, auth_token type, env dict types, HTTP URL scheme.

## Scope

**In**: Add `key` field to `McpServerConfig` dataclass. Extend `_validate_cross_fields()`. Set `key` in `_build_single_server()`.

**Out**: New transport types, config file format changes.

## Assumptions

1. `McpServerConfig` is a dataclass with `__post_init__` calling `_validate_enum_types()` and `_validate_cross_fields()`.
2. `call_timeout_sec: float = 60.0` — 0 means no timeout (valid); negative is invalid.
3. `startup_timeout_sec: int = 30` — zero or negative is invalid.
4. `auth_token: str = ""` — empty string is valid.
5. `env: dict[str, str]` — all keys and values must be strings.
6. HTTP URL validated only when `transport == TransportType.HTTP` and `url` is non-empty.
7. `_build_single_server(key, v)` constructs `McpServerConfig` and needs to set `key`.

## Implementation

### Target file
`scripts/shared/mcp_config.py`

### Procedure
1. Add `from urllib.parse import urlparse` import (if not present).
2. Add `key: str = field(default="", compare=False, repr=False)` to `McpServerConfig` dataclass.
3. Set `key` in `_build_single_server()` after construction.
4. Extend `_validate_cross_fields()` with 7 new checks.

### Method

**Updated dataclass field (add after existing fields):**
```python
from dataclasses import dataclass, field
from urllib.parse import urlparse

@dataclass
class McpServerConfig:
    # ... existing fields ...
    key: str = field(default="", compare=False, repr=False)
```

**Set key in `_build_single_server()` (after `McpServerConfig(...)` construction):**
```python
def _build_single_server(key: str, v: dict) -> McpServerConfig:
    cfg = McpServerConfig(
        transport=v.get("transport", "http"),
        url=v.get("url", ""),
        # ... other fields ...
    )
    cfg.key = key  # set key AFTER construction to avoid __post_init__ seeing empty key
    return cfg
```

Note: alternatively, pass `key=key` in constructor — works if `key` has default `""`.

**Extended `_validate_cross_fields()`:**
```python
def _validate_cross_fields(self) -> None:
    key_prefix = f"McpServerConfig[{self.key!r}]" if self.key else "McpServerConfig"

    # existing checks
    if self.transport == TransportType.HTTP and not self.url:
        raise ValueError(f"{key_prefix}: transport='http' requires a non-empty url")
    if self.transport == TransportType.SUBPROCESS and not self.cmd:
        raise ValueError(f"{key_prefix}: transport='subprocess' requires a non-empty cmd")

    # timeout checks
    if self.call_timeout_sec < 0:
        raise ValueError(
            f"{key_prefix}: call_timeout_sec must be >= 0, got {self.call_timeout_sec}"
        )
    if self.startup_timeout_sec <= 0:
        raise ValueError(
            f"{key_prefix}: startup_timeout_sec must be > 0, got {self.startup_timeout_sec}"
        )

    # tool_names checks
    for i, name in enumerate(self.tool_names):
        if not isinstance(name, str) or not name:
            raise ValueError(
                f"{key_prefix}: tool_names[{i}] must be a non-empty string, got {name!r}"
            )
    if len(self.tool_names) != len(set(self.tool_names)):
        dupes = sorted({n for n in self.tool_names if self.tool_names.count(n) > 1})
        raise ValueError(f"{key_prefix}: duplicate tool_names: {dupes}")

    # auth_token check
    if not isinstance(self.auth_token, str):
        raise ValueError(
            f"{key_prefix}: auth_token must be str, got {type(self.auth_token).__name__}"
        )

    # env check
    for k, v in self.env.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ValueError(
                f"{key_prefix}: env must be dict[str, str]; got key={k!r} value={v!r}"
            )

    # HTTP URL scheme check
    if self.transport == TransportType.HTTP and self.url:
        parsed = urlparse(self.url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(
                f"{key_prefix}: url must be a valid HTTP/HTTPS URL, got {self.url!r}"
            )
```

### Details

- `call_timeout_sec < 0` allows `0` (no timeout).
- URL scheme check runs only when transport is HTTP and url is non-empty — avoids false positives on subprocess configs.
- `key` field has `compare=False` so equality checks between configs aren't affected.

## Validation plan

- `uv run pytest tests/ -v -k "mcp_config_validation"` — all pass.
- Verify: valid config → no error.
- Verify: `call_timeout_sec=-1` → `ValueError` with key in message.
- Verify: `startup_timeout_sec=0` → `ValueError`.
- Verify: duplicate tool_names → `ValueError`.
- Verify: `url="ftp://bad"` → `ValueError`.
- `mypy scripts/shared/mcp_config.py` — no new errors.
- `ruff check scripts/shared/mcp_config.py` — 0 errors.
