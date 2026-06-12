# Goal

Delete the `DeprecationWarning` legacy fallback in `_build_mcp_servers()` and add
per-field `isinstance` validation in `_build_single_server()` to replace the silent
`v.get()` calls on untyped `Any`.

# Scope

- `scripts/shared/mcp_config.py`

# Assumptions

1. `config/mcp_servers.toml` has `[mcp_servers.*]` sections (confirmed). The legacy
   fallback (`"web_search"` and `"github"` hardcoded) is dead code.
2. When `mcp_servers` key is missing or empty, raise `ValueError` with a clear message.
3. `_build_single_server(key, v: Any)` → `v: dict[str, Any]`. If `v` is not a dict,
   raise `ValueError` immediately (fail-fast at config load time).
4. Individual field validation: each `v.get("transport", "http")` call is safe for
   strings but silent for wrong types. Add `isinstance` check for `transport` and
   other required string fields.
5. The `warnings` import becomes unused after removing `DeprecationWarning` — delete it.

# Implementation

## Target file

`scripts/shared/mcp_config.py`

## Procedure

1. Replace `_build_mcp_servers()` body:
   ```python
   def _build_mcp_servers(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
       raw = cfg.get("mcp_servers")
       if not isinstance(raw, dict) or not raw:
           raise ValueError(
               "mcp_servers config section is missing or empty. "
               "Add [mcp_servers] to config/mcp_servers.toml."
           )
       return {key: _build_single_server(key, v) for key, v in raw.items()}
   ```

2. Change `_build_single_server(key: str, v: Any)` → `(key: str, v: Any)` (keep
   `Any` for the parameter since it comes from dict iteration), but add guard at start:
   ```python
   def _build_single_server(key: str, v: Any) -> McpServerConfig:
       if not isinstance(v, dict):
           raise ValueError(
               f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}"
           )
       transport = v.get("transport", "http")
       if not isinstance(transport, str):
           raise ValueError(
               f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
           )
       # remaining v.get() calls are safe — McpServerConfig.__post_init__ validates them
   ```

3. Remove `import warnings` (now unused).

4. Run ruff + mypy.

## Method

Delete fallback branch (~15 lines). Add isinstance guard at entry of `_build_single_server`.

# Validation plan

- `grep -n "DeprecationWarning\|import warnings" scripts/shared/mcp_config.py` → 0 hits
- `uv run ruff check scripts/shared/mcp_config.py`
- `uv run mypy scripts/shared/mcp_config.py`
- `uv run pytest tests/test_shared_mcp_config.py -v`
