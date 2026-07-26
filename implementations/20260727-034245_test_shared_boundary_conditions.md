# Implementation Procedure: Guard Tests for Shared Layer Boundary Conditions

## Goal

Add guard tests for shared layer boundary conditions to establish behavioral baseline before refactoring.

## Scope

**In-Scope:**
- Create `tests/shared/test_shared_boundary_conditions.py` with three test methods documenting current behavior

**Out-of-Scope:**
- Changes beyond the three specific gaps listed above

## Target Files

- New file: `tests/shared/test_shared_boundary_conditions.py`

## Current Behavior Analysis

### SHARED-4: Dict Merge Conflicts

From `config_loader.py:96-100`:
```python
for key, val in data.items():
    if isinstance(val, dict) and isinstance(merged.get(key), dict):
        merged[key] = {**merged[key], **val}  # later file wins per-key
    else:
        merged[key] = val  # overwrite entire key
```

Current behavior: When two config files both define a dict-valued key (e.g., `[mcp_servers.<key>]`), the values are merged one level deep — later file's keys override earlier file's keys for the same sub-key. Non-dict values are overwritten entirely.

### SHARED-5: Extension-less Path Resolution

From `config_loader.py:142-145`:
```python
def _resolve_path(self, name: str) -> Path:
    p = Path(name) if name.endswith((".toml", ".json")) else Path(f"{name}.toml")
    return self._config_dir / p.name
```

Current behavior: If a config name does not end with `.toml` or `.json`, `.toml` is appended automatically.

### SHARED-6: known_tools=None Fallback

From `production_config_validator.py` — need to check current behavior when `known_tools` is None.

## Implementation Steps

### Step 1: Create test file structure

Create `tests/shared/test_shared_boundary_conditions.py` with imports and fixtures.

### Step 2: Add SHARED-4 test — dict merge conflicts

Test method: `test_dict_merge_conflict_resolution()`

Verify:
- Two config files defining the same dict-valued key (e.g., `mcp_servers`)
- Later file's sub-keys override earlier file's sub-keys for the same key
- Non-dict values in later file completely replace earlier value
- Use mock config files written to temp directory

```python
def test_dict_merge_conflict_resolution(tmp_path):
    """SHARED-4: Verify dict merge conflict resolution behavior."""
    # Write two config files with overlapping mcp_servers sections
    config1 = tmp_path / "agent.toml"
    config1.write_text("""
[mcp_servers.github]
url = "https://api.github.com"
[server]
name = "first"
""")
    config2 = tmp_path / "extra.toml"
    config2.write_text("""
[mcp_servers.github]
timeout = 30
[server]
version = "v2"
""")
    loader = ConfigLoader(config_dir=tmp_path)
    result = loader.load("agent.toml", "extra.toml")
    
    # mcp_servers.github should have merged keys (later overrides same key)
    assert result["mcp_servers"]["github"]["url"] == "https://api.github.com"
    assert result["mcp_servers"]["github"]["timeout"] == 30
    
    # server should be overwritten entirely (non-dict merge)
    assert result["server"]["name"] == "first"
    assert result["server"]["version"] == "v2"
```

### Step 3: Add SHARED-5 test — extension-less path resolution

Test method: `test_extension_less_path_defaults_to_toml()`

Verify:
- Passing a name without `.toml` or `.json` extension resolves to `.toml`
- Using temp directory with a config file named `agent.toml`

```python
def test_extension_less_path_defaults_to_toml(tmp_path):
    """SHARED-5: Verify extension-less paths default to .toml."""
    config_file = tmp_path / "agent.toml"
    config_file.write_text('key = "value"')
    loader = ConfigLoader(config_dir=tmp_path)
    result = loader.load("agent")  # no extension
    assert result["key"] == "value"
```

### Step 4: Add SHARED-6 test — known_tools=None fallback

Test method: `test_known_tools_none_fallback()`

Verify:
- When `known_tools` is None, the validator does not fail but instead skips tool validation
- Need to check `production_config_validator.py` to understand the exact behavior

```python
def test_known_tools_none_fallback():
    """SHARED-6: Verify known_tools=None does not cause validation failure."""
    # This test documents current behavior where None known_tools
    # results in skipping tool validation rather than raising an error
    pass  # TODO: Implement after reviewing production_config_validator.py
```

### Step 5: Run lint and type check

```bash
uv run ruff check tests/shared/test_shared_boundary_conditions.py --fix
uv run mypy tests/shared/test_shared_boundary_conditions.py
```

### Step 6: Run tests

```bash
uv run pytest -k "shared" -q
```

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_shared_boundary_conditions.py` | Characterization tests document current behavior | `uv run pytest -k "shared" -v` | All tests pass |

## Risks

- **Risk**: Characterization tests fail due to unexpected behavior → Mitigation: Investigate root cause; may indicate a bug needing fix
