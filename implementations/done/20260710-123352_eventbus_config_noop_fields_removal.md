# Implementation: Remove eventbus no-op config fields and add startup validation for stray keys (Phase B-1)

## Goal

Remove `EventBusConfig.poll_interval_ms` and `EventBusConfig.offset_checkpoint_interval` (both no-op fields that only ever emitted a `DeprecationWarning`), and make `load_config()` raise a startup error if either key is still present in the TOML file, per the user-approved policy: delete the fields, and turn stray keys into a hard failure rather than a silent warning.

## Scope

**In:**
- `scripts/eventbus/config.py`:
  - Remove `poll_interval_ms: int = 500` and `offset_checkpoint_interval: int = 10` fields from `EventBusConfig`
  - Remove their corresponding `__post_init__` validation (`< 1` checks) and `DeprecationWarning` blocks
  - Remove the `warnings` import if it becomes unused after the above removals (verify no other use in the file)
  - Add a check in `load_config()`: after parsing the raw TOML dict and before constructing `EventBusConfig`, raise `ValueError` if `"poll_interval_ms"` or `"offset_checkpoint_interval"` is present in the dict

**Out:**
- `port`, `max_retry`, `host`, `allow_public_bind` fields and their validation — unchanged
- `get_config_path()` / `get_schema_path()` / `_is_public_host()` — unchanged

## Assumptions

1. No other module constructs `EventBusConfig` directly with `poll_interval_ms=` or `offset_checkpoint_interval=` outside of `load_config()` and `tests/test_eventbus_config.py` — confirmed by `grep -rn "poll_interval_ms\|offset_checkpoint_interval" scripts/ tests/`.
2. `config/eventbus.toml` (this repository's own deployment config) does not set either key — confirmed by reading the file directly. This change has no effect on this repository's own runtime configuration.
3. `warnings` module import in `config.py` is used only by the two blocks being removed — must re-check after edits (`_is_public_host` and other functions do not use `warnings`).

## Implementation

### Target file

`scripts/eventbus/config.py`

### Procedure

1. Remove the two field declarations from `EventBusConfig`:
   ```python
   poll_interval_ms: int = (
       500  # deprecated: no longer used; push-mode delivery via EventBroker
   )
   offset_checkpoint_interval: int = (
       10  # deprecated: offset checkpointing removed; ack-only model
   )
   ```
2. Remove the corresponding blocks from `__post_init__`:
   ```python
   if self.poll_interval_ms < 1:
       raise ValueError(
           f"poll_interval_ms must be >= 1, got {self.poll_interval_ms}"
       )
   ...
   if self.offset_checkpoint_interval < 1:
       raise ValueError(
           f"offset_checkpoint_interval must be >= 1, got {self.offset_checkpoint_interval}"
       )
   ...
   if self.poll_interval_ms != 500:
       warnings.warn(...)
   if self.offset_checkpoint_interval != 10:
       warnings.warn(...)
   ```
3. Add a module-level constant and a check in `load_config()`:
   ```python
   _REMOVED_CONFIG_KEYS = ("poll_interval_ms", "offset_checkpoint_interval")

   def load_config(path: Path | None = None) -> EventBusConfig:
       p = path or _DEFAULT_CONFIG_PATH
       with p.open("rb") as f:
           data = tomllib.load(f)
       stale_keys = [k for k in _REMOVED_CONFIG_KEYS if k in data]
       if stale_keys:
           raise ValueError(
               f"eventbus config contains removed key(s): {', '.join(stale_keys)}. "
               "These fields were deprecated no-ops and have been removed; "
               f"delete them from {p}."
           )
       return EventBusConfig(
           port=data["port"],
           db_path=data["db_path"],
           storage_dir=data["storage_dir"],
           offsets_dir=data["offsets_dir"],
           deadletter_dir=data["deadletter_dir"],
           max_retry=data["max_retry"],
           host=data.get("host", "127.0.0.1"),
           allow_public_bind=data.get("allow_public_bind", False),
       )
   ```
4. Check whether `import warnings` is still needed anywhere in `config.py`; remove it if not (run `grep -n "warnings\." scripts/eventbus/config.py` to confirm before deleting the import).
5. Run `grep -n "poll_interval_ms\|offset_checkpoint_interval" scripts/eventbus/config.py` — expect matches only in the new `_REMOVED_CONFIG_KEYS` tuple and its error message.

### Method

Direct field/validation removal, plus a new fail-fast guard placed before dataclass construction — this is the earliest point at which the raw TOML dict is available, so the error message can reference the literal key names as they appeared in the file.

### Details

- Raising in `load_config()` rather than in `EventBusConfig.__post_init__` is deliberate: once the fields are removed from the dataclass, there is no longer any dataclass attribute to validate against — the only way to detect a stray key is to inspect the raw dict before it is discarded.
- The error message names the specific file path (`p`) so an operator can locate and fix the TOML directly from the stack trace.
- This is a breaking change for any external deployment that still has either key set in its `eventbus.toml` — those deployments will fail to start until the key is removed. This repository's own `config/eventbus.toml` is unaffected (Assumption 2).

## Validation plan

```bash
uv run ruff check scripts/eventbus/config.py
uv run mypy scripts/eventbus/config.py
grep -n "poll_interval_ms\|offset_checkpoint_interval" scripts/eventbus/config.py
grep -n "warnings\." scripts/eventbus/config.py   # confirm import still needed or safely removed
```

Expected outcome: no lint/type regressions; the only remaining references to the two key names are inside `_REMOVED_CONFIG_KEYS` and its error message. (Test coverage for `load_config()`'s new validation is added in the companion Phase B-2 implementation document, since this document's change alone would leave `tests/test_eventbus_config.py` failing to import — it still constructs `EventBusConfig` with the removed keyword arguments.)
