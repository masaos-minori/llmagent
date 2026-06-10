# Implementation: installer_port.py — except Exception → specific exceptions

## Goal

Replace `except Exception: pass` in `_ports_from_config()` with specific exception
handling for `OSError` (file read failure) and `tomllib.TOMLDecodeError` (parse failure).
Other exceptions propagate.

## Scope

- `scripts/mcp/installer_port.py` — primary

## Implementation

```python
def _ports_from_config(config_dir: Path) -> set[int]:
    ports: set[int] = set()
    agent_toml = config_dir / "agent.toml"
    if not agent_toml.exists():
        return ports
    try:
        with agent_toml.open("rb") as f:
            cfg = tomllib.load(f)
    except OSError as e:
        raise OSError(f"Cannot read {agent_toml}: {e}") from e
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Invalid TOML in {agent_toml}: {e}") from e
    for srv in cfg.get("mcp_servers", {}).values():
        url = srv.get("url", "")
        m = re.search(r":(\d+)/?$", url)
        if m:
            ports.add(int(m.group(1)))
    return ports
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/mcp/installer_port.py` | 0 errors |
| Type | `uv run mypy scripts/mcp/installer_port.py` | no new errors |
| No broad except | `grep "except Exception" scripts/mcp/installer_port.py` | 0 hits |
