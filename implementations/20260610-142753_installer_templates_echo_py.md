# Implementation: installer_templates.py + echo_server.py — role dict, clarify purpose

## Goal

1. `installer_templates.py`: replace `if/elif` role chain in
   `generate_config_toml_for_role()` with a dict mapping; unknown role raises `ValueError`.
2. `echo_server.py`: add module-level comment clarifying it is for connectivity
   testing only and must not be used as a production server template.

## Scope

- `scripts/mcp/installer_templates.py`
- `scripts/mcp/echo_server.py`

## Implementation

### installer_templates.py

Locate `generate_config_toml_for_role()`. Replace if/elif with:

```python
_ROLE_PORT_MAP: dict[str, int] = {
    "shell": 8010,
    "sqlite": 8011,
    "rag": 8012,
}

def generate_config_toml_for_role(role: str, server_name: str, port: int) -> str:
    if role not in _ROLE_PORT_MAP:
        raise ValueError(
            f"Unknown role {role!r}. Must be one of {sorted(_ROLE_PORT_MAP)}"
        )
    ...
```

Also: add argument validation at the top of `generate_server_script()`:
```python
if not server_name or not module or not port:
    raise ValueError("server_name, module, and port must all be non-empty/non-zero")
```

### echo_server.py

Add to module docstring:
```
WARNING: This server is for connectivity testing only.
Do NOT use it as a template for production MCP servers.
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/mcp/installer_templates.py scripts/mcp/echo_server.py` | 0 errors |
| Type | `uv run mypy scripts/mcp/installer_templates.py` | no new errors |
| Tests | `uv run pytest tests/ -k "template or installer" -x -q` | all pass |
| No if/elif role | `grep -c "elif role ==" scripts/mcp/installer_templates.py` | 0 |
