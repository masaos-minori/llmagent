# Implementation: installer_validation.py + callers — str|None → ValueError

## Goal

Change `validate_server_name()` from returning `str | None` to raising `ValueError`
on invalid input and returning the normalised name on success.
Update the two callers: `installer_writer.py` and `cmd_mcp.py`.

## Scope

- `scripts/mcp/installer_validation.py` — primary
- `scripts/mcp/installer_writer.py` — remove manual ValueError wrapping
- `scripts/agent/commands/cmd_mcp.py` — use try/except ValueError

## Implementation

### installer_validation.py

```python
def validate_server_name(server_name: str) -> str:
    """Return server_name when valid; raise ValueError with a clear message if not."""
    if not server_name:
        raise ValueError("Server name must not be empty.")
    if not _NAME_RE.match(server_name):
        raise ValueError(
            f"Invalid server name {server_name!r}. "
            "Use lowercase letters, digits, and hyphens; must start with a letter."
        )
    return server_name
```

Also add self-validation to `name_to_module()` and `name_to_class()`:
- both call `validate_server_name(server_name)` internally before converting.

### installer_writer.py

Remove lines:
```python
err = validate_server_name(server_name)
if err:
    raise ValueError(err)
```
Replace with:
```python
validate_server_name(server_name)  # raises ValueError on invalid input
```

### cmd_mcp.py

Replace:
```python
err = validate_server_name(server_name)
if err:
    print(err)
    print("Usage: /mcp install <server-name>  (e.g., my-api)")
    return
```
With:
```python
try:
    validate_server_name(server_name)
except ValueError as e:
    print(str(e))
    print("Usage: /mcp install <server-name>  (e.g., my-api)")
    return
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/mcp/installer_validation.py scripts/mcp/installer_writer.py scripts/agent/commands/cmd_mcp.py` | 0 errors |
| Type | `uv run mypy scripts/mcp/installer_validation.py` | no new errors |
| Tests | `uv run pytest tests/ -k "installer or mcp_install or mcp" -x -q` | all pass |
| No str None | `grep "str | None" scripts/mcp/installer_validation.py` | 0 hits |
