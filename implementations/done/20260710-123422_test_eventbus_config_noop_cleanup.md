# Implementation: Rewrite `tests/test_eventbus_config.py` for no-op field removal (Phase B-2)

## Goal

Remove the 10 tests that exercise `EventBusConfig.poll_interval_ms` / `offset_checkpoint_interval` directly (both fields are being deleted in Phase B-1), and add new tests covering `load_config()`'s new stray-key startup validation.

## Scope

**In:**
- Delete `test_invalid_poll_interval_zero`, `test_invalid_offset_checkpoint_zero`, `test_valid_config_with_deprecated_defaults`, `test_no_warning_with_default_poll_interval`, `test_no_warning_with_default_offset_checkpoint`, `test_warning_poll_interval_ms_non_default`, `test_warning_offset_checkpoint_interval_non_default`, `test_both_warnings_when_both_non_default` (8 tests, lines 50-181) — all construct `EventBusConfig` with the removed keyword arguments and would raise `TypeError` otherwise
- Add new tests for `load_config()`'s stray-key rejection: one TOML key present, the other present, both present, and a baseline "no stray keys, loads successfully" case

**Out:**
- `test_invalid_port_too_low`, `test_invalid_port_too_high`, `test_invalid_max_retry_zero`, `test_valid_config_with_host_field` (lines 14-86) — unrelated to the removed fields, untouched

## Assumptions

1. `load_config(path: Path | None = None)` accepts an explicit `Path` argument (confirmed by its signature in `scripts/eventbus/config.py`), so new tests can point it at a `pytest` `tmp_path`-generated TOML file without needing to touch `/opt/llm/config/eventbus.toml`.
2. The minimum valid TOML for `load_config()` to succeed requires `port`, `db_path`, `storage_dir`, `offsets_dir`, `deadletter_dir`, `max_retry` (all accessed via `data[...]`, not `data.get(...)`, in `load_config()`) — a test TOML must set all six or the test would fail for an unrelated `KeyError` before reaching the stray-key check. (Note: Phase B-1 places the stray-key check *before* these required-key lookups, so a TOML with a stray key but missing required keys would still correctly raise on the stray key first — this should be exploited to keep the new tests minimal, only `port` plus the stray key(s) need to be set for the rejection tests; the "loads successfully" baseline test needs the full set.)

## Implementation

### Target file

`tests/test_eventbus_config.py`

### Procedure

1. Delete the 8 tests listed in Scope (lines 50-181 in the current file), and the now-unused `import warnings` if nothing else in the file uses it (check remaining tests first — none of the retained 4 tests use `warnings`, so the import can be removed).
2. Add `import tomllib` (or use `tomli_w`-style plain string writes, matching project convention — check whether `tomllib`/plain-text TOML writing is already used elsewhere in `tests/` for a consistent pattern) and `from scripts.eventbus.config import load_config` alongside the existing `EventBusConfig` import.
3. Add the following new tests:
   ```python
   def test_load_config_rejects_stray_poll_interval_ms(tmp_path: Path) -> None:
       toml_path = tmp_path / "eventbus.toml"
       toml_path.write_text(
           'port = 8015\n'
           'db_path = "/tmp/e.sqlite"\n'
           'storage_dir = "/tmp/storage"\n'
           'offsets_dir = "/tmp/offsets"\n'
           'deadletter_dir = "/tmp/deadletter"\n'
           'max_retry = 3\n'
           'poll_interval_ms = 1000\n'
       )
       with pytest.raises(ValueError, match="poll_interval_ms"):
           load_config(toml_path)

   def test_load_config_rejects_stray_offset_checkpoint_interval(tmp_path: Path) -> None:
       toml_path = tmp_path / "eventbus.toml"
       toml_path.write_text(
           'port = 8015\n'
           'db_path = "/tmp/e.sqlite"\n'
           'storage_dir = "/tmp/storage"\n'
           'offsets_dir = "/tmp/offsets"\n'
           'deadletter_dir = "/tmp/deadletter"\n'
           'max_retry = 3\n'
           'offset_checkpoint_interval = 30\n'
       )
       with pytest.raises(ValueError, match="offset_checkpoint_interval"):
           load_config(toml_path)

   def test_load_config_rejects_both_stray_keys(tmp_path: Path) -> None:
       toml_path = tmp_path / "eventbus.toml"
       toml_path.write_text(
           'port = 8015\n'
           'db_path = "/tmp/e.sqlite"\n'
           'storage_dir = "/tmp/storage"\n'
           'offsets_dir = "/tmp/offsets"\n'
           'deadletter_dir = "/tmp/deadletter"\n'
           'max_retry = 3\n'
           'poll_interval_ms = 1000\n'
           'offset_checkpoint_interval = 30\n'
       )
       with pytest.raises(ValueError) as exc_info:
           load_config(toml_path)
       assert "poll_interval_ms" in str(exc_info.value)
       assert "offset_checkpoint_interval" in str(exc_info.value)

   def test_load_config_succeeds_without_stray_keys(tmp_path: Path) -> None:
       toml_path = tmp_path / "eventbus.toml"
       toml_path.write_text(
           'port = 8015\n'
           'db_path = "/tmp/e.sqlite"\n'
           'storage_dir = "/tmp/storage"\n'
           'offsets_dir = "/tmp/offsets"\n'
           'deadletter_dir = "/tmp/deadletter"\n'
           'max_retry = 3\n'
       )
       cfg = load_config(toml_path)
       assert cfg.port == 8015
   ```
4. Add `from pathlib import Path` to the imports if not already present (needed for the `tmp_path: Path` type annotation).
5. Run `uv run pytest tests/test_eventbus_config.py -v` — expect all tests (4 original + 4 new = 8) to pass.

### Method

Delete-then-add: remove tests whose subject no longer exists, add tests for the new subject (`load_config()`'s stray-key validation) using `pytest`'s `tmp_path` fixture to write real TOML files, exercising the actual file-parsing path rather than only the dataclass constructor.

### Details

- Testing through `load_config()` with real temp files (rather than mocking `tomllib.load`) is preferred here because the behavior being validated is specifically about what happens when a TOML *file* contains a stray key — an integration-style test through the real parser is more faithful than mocking the dict that would be returned.
- `test_load_config_succeeds_without_stray_keys` is a regression guard: it ensures Phase B-1's new check does not accidentally reject valid, key-free configs.

## Validation plan

```bash
uv run ruff check tests/test_eventbus_config.py
uv run mypy tests/test_eventbus_config.py
uv run pytest tests/test_eventbus_config.py -v
grep -n "poll_interval_ms\|offset_checkpoint_interval" tests/test_eventbus_config.py
```

Expected outcome: 8 tests total, all passing; remaining references to the two key names appear only inside the new `load_config()`-rejection test bodies (as string literals being tested for), not as `EventBusConfig` constructor arguments.
