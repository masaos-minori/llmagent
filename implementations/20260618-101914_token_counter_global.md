# Implementation: shared/token_counter.py — remove _warned_unavailable global

## Goal

Remove module-level `_warned_unavailable` global; add `warn_once` parameter to
`get_token_count()` so callers control warning suppression (no global state).

## Changes

### `scripts/shared/token_counter.py`
- Remove line: `_warned_unavailable = _WarnOnce()`
- Add `warn_once: _WarnOnce | None = None` to `get_token_count()` signature
- Success path: `if warn_once is not None: warn_once.reset()`
- Error path: `if warn_once is not None: warn_once.log(...)` else `logger.warning(...)`

### `scripts/agent/history.py`
- Add `from shared.token_counter import _WarnOnce` to imports (or inline)
- Add `self._warn_once = _WarnOnce()` in `__init__`
- Pass `warn_once=self._warn_once` to `get_token_count()` at line 184

### `tests/test_token_counter.py`
- Remove `_reset_warned()` function (~lines 25-27)
- Remove all `_reset_warned()` calls from ~8 tests
- Update `test_warn_only_once_on_repeated_failure`: use local `_WarnOnce()` instance, pass as `warn_once=`

### `docs/06_shared_90_inconsistencies_and_known_issues.md` GLOBAL-01
- Change status: `Addressed` → `RESOLVED (global removed, state moved to caller)`
