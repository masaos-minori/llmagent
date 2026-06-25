# Implementation: tests/test_config_loader.py

## Goal

Add 3 new tests to `test_config_loader.py` verifying that `load_all()` skips missing files and raises `ConfigParseError` / `ConfigReadError` on parse or read failures.

## Scope

- Target: `tests/test_config_loader.py`
- Add `test_load_all_skips_missing_file`
- Add `test_load_all_raises_on_parse_error`
- Add `test_load_all_raises_on_read_error`
- Verify existing tests still pass with new exception hierarchy

## Assumptions

1. `ConfigMissingError`, `ConfigParseError`, `ConfigReadError` are importable from `shared.config_loader`.
2. Existing tests `test_missing_file_raises_value_error` and `test_invalid_toml_raises_value_error` pass because new exceptions inherit from `ValueError`.
3. `_BASE_CONFIG_FILES` can be patched or a minimal config dir with a bad file can be constructed.

## Implementation

### Target file
`tests/test_config_loader.py`

### Procedure
1. Import new exception classes from `shared.config_loader`.
2. Add test class or top-level functions for the 3 new test cases.
3. Use `tmp_path` fixture or `unittest.mock.patch` to control file presence and content.

### Method

```python
from shared.config_loader import ConfigLoader, ConfigMissingError, ConfigParseError, ConfigReadError

def test_load_all_skips_missing_file(tmp_path):
    loader = ConfigLoader(config_dir=str(tmp_path))
    # No files in tmp_path — load_all() should return empty dict without raising
    result = loader.load_all()
    assert result == {}

def test_load_all_raises_on_parse_error(tmp_path):
    bad = tmp_path / "common.toml"
    bad.write_text("not valid toml ][")
    # Patch _BASE_CONFIG_FILES to include only this file
    with patch("shared.config_loader._BASE_CONFIG_FILES", ["common.toml"]):
        loader = ConfigLoader(config_dir=str(tmp_path))
        with pytest.raises(ConfigParseError):
            loader.load_all()

def test_load_all_raises_on_read_error(tmp_path):
    bad = tmp_path / "common.toml"
    bad.write_text("[valid]")
    bad.chmod(0o000)
    with patch("shared.config_loader._BASE_CONFIG_FILES", ["common.toml"]):
        loader = ConfigLoader(config_dir=str(tmp_path))
        with pytest.raises(ConfigReadError):
            loader.load_all()
    bad.chmod(0o644)
```

### Details
- Use `pytest.raises` with the specific new exception type (not just `ValueError`).
- If `ConfigLoader` does not accept a `config_dir` param, use `unittest.mock.patch.object` to mock `_load_single` as needed.
- The `chmod(0o000)` test may not work on root-run CI — add `pytest.mark.skipif(os.getuid() == 0, ...)` guard if needed.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Tests | `uv run pytest tests/test_config_loader.py -q` | all pass incl. new tests |
| Regression | existing `test_missing_file_raises_value_error` | still passes |
